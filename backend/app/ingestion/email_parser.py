"""MIME parsing and forwarded-message handling.

A user forwards a suspicious email to the bot. Two forms exist:

* **forward as attachment** - the original arrives as a ``message/rfc822`` part with its headers intact;
* **inline forward** - the original is quoted in the body behind a marker such as
  ``---------- Forwarded message ---------``; the original authentication results are NOT recoverable.

A message that is neither (for example a file uploaded in development) is analysed as the original.
Attachment contents are never opened or executed: only name, declared type, size and SHA-256 are kept.
"""
from __future__ import annotations

import hashlib
import re
import warnings
from dataclasses import dataclass, field
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# A message body that is really XML reaches the HTML parser, and BeautifulSoup warns about it
# once per message. On a corpus run that is one warning per email, which buries the real output.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
FWD_MARKER_RE = re.compile(
    r"(-{3,}\s*forwarded message\s*-{3,}|begin forwarded message:|-{3,}\s*original message\s*-{3,})", re.I)
HDR_LINE_RE = re.compile(r"^\s*(from|date|subject|to|reply-to|sent)\s*:\s*(.+)$", re.I)


@dataclass
class Link:
    href: str
    text: str = ""


@dataclass
class Attachment:
    filename: str
    content_type: str
    size: int
    sha256: str


@dataclass
class ParsedEmail:
    scope: str                       # "forward_attachment" | "forward_inline" | "direct"
    forwarded_by: str                # address of the person who forwarded it ("" for direct)
    from_name: str
    from_addr: str
    from_domain: str
    reply_to_addr: str
    return_path_addr: str
    subject: str
    date: str
    auth: dict[str, str]             # spf/dkim/dmarc -> pass|fail|none|missing
    received_count: int
    text_body: str
    html_body: str
    links: list[Link] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    raw_sha256: str = ""


def domain_of(addr: str) -> str:
    return addr.rsplit("@", 1)[1].lower().strip(">") if "@" in addr else ""


def _body_parts(msg: EmailMessage) -> tuple[str, str]:
    text, html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart() or part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            try:
                content = part.get_content()
            except Exception:  # undecodable charset etc.
                continue
            if ctype == "text/plain" and not text:
                text = content
            elif ctype == "text/html" and not html:
                html = content
    else:
        try:
            content = msg.get_content()
        except Exception:
            content = ""
        if msg.get_content_type() == "text/html":
            html = content
        else:
            text = content
    if not text and html:
        text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    return text or "", html or ""


def _extract_links(text: str, html: str) -> list[Link]:
    links: list[Link] = []
    seen: set[tuple[str, str]] = set()
    if html:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith(("http://", "https://")):
                key = (href, a.get_text(" ", strip=True))
                if key not in seen:
                    seen.add(key)
                    links.append(Link(href=href, text=key[1]))
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:")
        if not any(l.href == url for l in links):
            links.append(Link(href=url, text=""))
    return links


def _attachments(msg: EmailMessage) -> list[Attachment]:
    out: list[Attachment] = []
    for part in msg.iter_attachments():
        if part.get_content_type() == "message/rfc822":
            continue
        payload = part.get_payload(decode=True) or b""
        out.append(Attachment(
            filename=part.get_filename() or "",
            content_type=part.get_content_type(),
            size=len(payload),
            sha256=hashlib.sha256(payload).hexdigest()))
    return out


def _auth_results(msg: EmailMessage) -> dict[str, str]:
    res = {"spf": "missing", "dkim": "missing", "dmarc": "missing"}
    values = msg.get_all("Authentication-Results") or []
    joined = " ".join(str(v) for v in values).lower()
    if joined:
        for k in res:
            m = re.search(rf"\b{k}\s*=\s*(pass|fail|softfail|neutral|none|temperror|permerror)", joined)
            res[k] = ("fail" if m.group(1) in ("fail", "softfail", "permerror") else m.group(1)) if m else "none"
    # Fallback to Received-SPF (RFC 7208) when Authentication-Results does not report SPF
    if res["spf"] in ("missing", "none"):
        rcvd_spf = " ".join(str(v) for v in (msg.get_all("Received-SPF") or [])).lower()
        if rcvd_spf:
            sm = re.search(r"\b(pass|fail|softfail|neutral|none|temperror|permerror)\b", rcvd_spf)
            if sm:
                res["spf"] = "fail" if sm.group(1) in ("fail", "softfail", "permerror") else sm.group(1)
    return res


def _inline_forward(text: str) -> tuple[dict[str, str], str] | None:
    """Locate a quoted original header block; return (headers, body_after_block)."""
    m = FWD_MARKER_RE.search(text)
    if not m:
        return None
    lines = text[m.end():].splitlines()
    hdrs: dict[str, str] = {}
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    start = i
    while i < len(lines):
        hm = HDR_LINE_RE.match(lines[i])
        if hm:
            hdrs[hm.group(1).lower()] = hm.group(2).strip()
            i += 1
        elif not lines[i].strip() and i > start:
            i += 1
            break
        else:
            break
    if "from" not in hdrs:
        return None
    return hdrs, "\n".join(lines[i:]).strip()


def _build(msg: EmailMessage, scope: str, forwarded_by: str, raw_sha: str) -> ParsedEmail:
    name, addr = parseaddr(str(msg.get("From", "")))
    _, rt = parseaddr(str(msg.get("Return-Path", "")))
    _, rp = parseaddr(str(msg.get("Reply-To", "")))
    text, html = _body_parts(msg)
    return ParsedEmail(
        scope=scope, forwarded_by=forwarded_by, from_name=name, from_addr=addr.lower(),
        from_domain=domain_of(addr), reply_to_addr=rp.lower(), return_path_addr=rt.lower(),
        subject=str(msg.get("Subject", "")), date=str(msg.get("Date", "")),
        auth=_auth_results(msg), received_count=len(msg.get_all("Received") or []),
        text_body=text, html_body=html, links=_extract_links(text, html), attachments=_attachments(msg),
        headers={k: str(v)[:500] for k, v in msg.items() if k.lower() in (
            "from", "to", "reply-to", "return-path", "subject", "date", "message-id",
            "authentication-results", "received-spf", "dkim-signature", "x-mailer")},
        raw_sha256=raw_sha)


def parse_email(raw: bytes) -> ParsedEmail:
    sha = hashlib.sha256(raw).hexdigest()
    outer: EmailMessage = BytesParser(policy=policy.default).parsebytes(raw)  # type: ignore[assignment]
    _, forwarder = parseaddr(str(outer.get("From", "")))

    # 1) forwarded as attachment
    for part in outer.walk():
        if part.get_content_type() == "message/rfc822":
            inner = part.get_payload(0)
            if isinstance(inner, EmailMessage):
                return _build(inner, "forward_attachment", forwarder.lower(), sha)

    # 2) inline forward
    text, html = _body_parts(outer)
    fwd = _inline_forward(text)
    if fwd:
        hdrs, body = fwd
        name, addr = parseaddr(hdrs.get("from", ""))
        _, rp = parseaddr(hdrs.get("reply-to", ""))
        return ParsedEmail(
            scope="forward_inline", forwarded_by=forwarder.lower(), from_name=name, from_addr=addr.lower(),
            from_domain=domain_of(addr), reply_to_addr=rp.lower(), return_path_addr="",
            subject=hdrs.get("subject", ""), date=hdrs.get("date", hdrs.get("sent", "")),
            auth={"spf": "missing", "dkim": "missing", "dmarc": "missing"}, received_count=0,
            text_body=body, html_body=html, links=_extract_links(body, html), attachments=_attachments(outer),
            headers={"from": hdrs.get("from", ""), "subject": hdrs.get("subject", "")}, raw_sha256=sha)

    # 3) direct
    return _build(outer, "direct", "", sha)
