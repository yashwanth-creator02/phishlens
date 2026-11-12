"""Format-only features: the shape of a message, with none of its content.

The point is to find out whether a model can tell which CORPUS a message came
from without reading it. If a provider fingerprint lives in the headers, the
fingerprint lives here: which header names are present, the shape of the Date
and the Message-ID, the charset, the MIME structure, the line endings, the
length of the Received chain.

Everything in this module is derived from the raw bytes. It deliberately does
not use the app's parser, because the app's parser normalises headers - and
normalising is exactly what a leak test has to see past.

Nothing here may look at the subject, the body text, the addresses or the URLs.
A feature that reads content is not a format feature.
"""
from __future__ import annotations

import email
import email.policy
import email.utils
import re

# Header names whose presence is a provider or pipeline fingerprint.
TRACKED_HEADERS = [
    "Received", "Return-Path", "Reply-To", "Message-ID", "Date", "Subject",
    "From", "To", "Cc", "Bcc", "Sender", "Delivered-To", "X-Originating-IP",
    "X-Mailer", "User-Agent", "MIME-Version", "Content-Type",
    "Content-Transfer-Encoding", "DKIM-Signature", "DomainKey-Signature",
    "ARC-Authentication-Results", "ARC-Seal", "ARC-Message-Signature",
    "Authentication-Results", "Received-SPF", "X-Gmail-Labels", "X-Received",
    "X-Forwarded-To", "List-Id", "List-Unsubscribe", "Precedence",
    "Auto-Submitted", "X-Google-Smtp-Source", "X-Enumerated-To",
    "X-Forefront-Antispam", "X-Microsoft-Antispam", "X-Original-To",
    "X-Priority", "X-Failed-Recipients", "Errors-To", "X-Ident", "Message-Id",
]

_MSGID_RE = re.compile(r"<([^@>]+)@([^>]+)>")
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_HEX_RE = re.compile(r"^[0-9a-f]+$", re.I)


def _header_names(msg: email.message.Message) -> set[str]:
    return {k.lower() for k in msg.keys()}


def _date_shape(date_header: str | None) -> list[float]:
    if not date_header:
        return [0.0] * 4
    d = date_header.strip()
    return [
        1.0,
        1.0 if re.search(r"[+-]\d{4}$", d) else 0.0,
        1.0 if d.split(",")[0].strip().isalpha() else 0.0,
        1.0 if re.search(r"\d{2}:\d{2}:\d{2}", d) else 0.0,
    ]


def _message_id_shape(msgid: str | None) -> list[float]:
    if not msgid:
        return [0.0] * 6
    m = _MSGID_RE.search(msgid.strip())
    if not m:
        return [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    local, domain = m.group(1), m.group(2)
    return [
        1.0,
        1.0,
        1.0 if _HEX_RE.match(local) else 0.0,
        1.0 if "." in local else 0.0,
        1.0 if "+" in local else 0.0,
        1.0 if _IPV4_RE.match(domain) else 0.0,
    ]


def _charset_shape(msg: email.message.Message) -> list[float]:
    params = msg.get_params() or []
    charsets = [str(p[2]).lower() for p in params if len(p) > 2 and p[2]]
    if not charsets:
        return [0.0, 0.0, 0.0]
    primary = charsets[0]
    return [
        1.0,
        1.0 if "utf-8" in primary or "utf8" in primary else 0.0,
        1.0 if "1252" in primary or "iso-8859-1" in primary else 0.0,
    ]


def _mime_shape(msg: email.message.Message) -> list[float]:
    parts = list(msg.walk())
    n = len(parts)
    subtypes = {str(p.get_content_subtype()).lower() for p in parts}
    ctes = {str(p.get("Content-Transfer-Encoding", "")).lower() for p in parts}
    has_html = any(str(p.get_content_type()).lower() == "text/html" for p in parts)
    has_plain = any(str(p.get_content_type()).lower() == "text/plain" for p in parts)
    has_attach = any(p.get_filename() is not None for p in parts)
    return [
        min(n, 10) / 10.0,
        1.0 if msg.is_multipart() else 0.0,
        1.0 if "mixed" in subtypes else 0.0,
        1.0 if "alternative" in subtypes else 0.0,
        1.0 if has_html else 0.0,
        1.0 if has_plain else 0.0,
        1.0 if has_attach else 0.0,
        1.0 if "base64" in ctes else 0.0,
        1.0 if "7bit" in ctes else 0.0,
        1.0 if "8bit" in ctes else 0.0,
        1.0 if "quoted-printable" in ctes else 0.0,
    ]


def _line_ending_shape(raw: bytes) -> list[float]:
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    cr = raw.count(b"\r") - crlf
    total = max(1, crlf + lf + cr)
    return [
        1.0 if crlf else 0.0,
        1.0 if lf else 0.0,
        1.0 if cr else 0.0,
        round(crlf / total, 3),
    ]


def _received_shape(msg: email.message.Message) -> list[float]:
    n = len(msg.get_all("Received") or [])
    return [min(n, 8) / 8.0]


def format_feature_names() -> list[str]:
    names = [f"header:{h}" for h in TRACKED_HEADERS]
    names += ["date:has", "date:has_tz", "date:has_weekday", "date:has_seconds"]
    names += ["msgid:has", "msgid:has_domain", "msgid:local_is_hex", "msgid:local_has_dot",
              "msgid:local_has_plus", "msgid:domain_is_ip"]
    names += ["charset:has", "charset:is_utf8", "charset:is_latin1"]
    names += ["mime:n_parts", "mime:is_multipart", "mime:has_mixed", "mime:has_alternative",
              "mime:has_html", "mime:has_plain", "mime:has_attachment", "mime:cte_base64",
              "mime:cte_7bit", "mime:cte_8bit", "mime:cte_qp"]
    names += ["eol:has_crlf", "eol:has_lf", "eol:has_bare_cr", "eol:crlf_ratio"]
    names += ["received:n_chain"]
    return names


def format_features(raw: bytes) -> list[float]:
    """The format fingerprint of one raw message."""
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
    except Exception:
        msg = email.message_from_bytes(raw)
    present = _header_names(msg)
    row = [1.0 if h in present else 0.0 for h in TRACKED_HEADERS]
    row += _date_shape(msg.get("Date"))
    row += _message_id_shape(msg.get("Message-ID") or msg.get("Message-Id"))
    row += _charset_shape(msg)
    row += _mime_shape(msg)
    row += _line_ending_shape(raw)
    row += _received_shape(msg)
    return row


# Headers that are a pure pipeline fingerprint: they are added by one transport
# and mean nothing about the message. If they are the only thing separating
# corpora, they are the leak.
PROVIDER_HEADERS = {
    "header:received", "header:x-gmail-labels", "header:x-received",
    "header:x-forwarded-to", "header:return-path", "header:x-originating-ip",
    "header:arc-authentication-results", "header:arc-seal",
    "header:arc-message-signature", "header:authentication-results",
    "header:received-spf", "header:x-google-smtp-source",
    "header:x-enumerated-to", "header:x-forefront-antispam",
    "header:x-microsoft-antispam", "header:x-original-to",
    "header:delivered-to", "header:errors-to", "header:x-failed-recipients",
    "header:x-ident", "header:user-agent", "header:x-mailer",
    "header:dkim-signature", "header:domainkey-signature",
}


def normalised_format_features(raw: bytes) -> list[float]:
    """The same fingerprint with the provider headers removed.

    If the leak disappears when the transport headers are dropped, the leak was
    the transport, and the fix is to not train on those headers.
    """
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
    except Exception:
        msg = email.message_from_bytes(raw)
    present = _header_names(msg)
    row = [0.0 if f"header:{h}" in PROVIDER_HEADERS and h in present else (1.0 if h in present else 0.0)
           for h in TRACKED_HEADERS]
    row += _date_shape(msg.get("Date"))
    row += _message_id_shape(msg.get("Message-ID") or msg.get("Message-Id"))
    row += _charset_shape(msg)
    row += _mime_shape(msg)
    row += _line_ending_shape(raw)
    row += _received_shape(msg)
    return row
