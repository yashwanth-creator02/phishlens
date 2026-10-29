"""Semi-synthetic email generator for DEVELOPMENT AND PIPELINE TESTING ONLY.

It exists so the whole system (features -> model -> SHAP -> reasons -> API) can run end-to-end before real
corpora are assembled. Models trained on it will score very high because the generator encodes the very
patterns the features look for. NEVER report these numbers as project results; use real corpora
(Nazario, SpamAssassin, Enron, ...) via training/corpus.py for evaluation (see docs/08-ml-pipeline.md).

Realism features that DO matter for testing the design:
  * confusable legitimate mail (bank alerts, password resets, newsletters with 'limited time' wording),
  * phishing without urgent wording (LLM-style), phishing from known senders (spoof / compromised),
  * forwarding wrappers: direct / forwarded-as-attachment / forwarded-inline (auth results lost),
  * sender histories (built with the production profile code) for behavioural features,
  * domain-age lookups available for only ~50% of messages (so the model learns to cope with 'missing').
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage

from app.features.behavioral_features import update_profile
from app.features.common import DomainAgeProvider, ExtractionContext, NullDomainAge, ProfileData
from app.features.feature_vector import extract_all
from app.ingestion.email_parser import parse_email

NOW = datetime(2026, 10, 1)


class DictDomainAge:
    def __init__(self, ages: dict[str, int]):
        self.ages = ages

    def age_days(self, d: str) -> int | None:
        return self.ages.get(d)


@dataclass
class Sender:
    name: str
    addr: str
    domain: str
    bounce: str          # Return-Path domain
    reply_to: str        # "" or address
    links: list[str]
    family: str
    sig: str
    profile: ProfileData | None = None


@dataclass
class Sample:
    raw: bytes
    label: int
    group: str
    profile: ProfileData | None
    domain_age: DomainAgeProvider


LEGIT_DEFS = [
    # name, domain, bounce, reply_to_local, links, family, signature/style line
    ("Medium Daily Digest", "medium.com", "mail.medium.com", "", ["medium.com"], "newsletter", "You are receiving this digest because you follow topics on Medium."),
    ("The Hindu Briefing", "thehindu.com", "mailer.thehindu.com", "", ["thehindu.com"], "newsletter", "Read more on thehindu.com. Unsubscribe any time."),
    ("Coursera", "coursera.org", "mail.coursera.org", "", ["coursera.org"], "newsletter", "Keep learning with Coursera. Limited time offer on selected courses."),
    ("Swiggy", "swiggy.com", "email.swiggy.com", "", ["swiggy.com"], "newsletter", "Hungry? Offer ends tonight, order now."),
    ("Amazon.in", "amazon.in", "amazonses.com", "", ["amazon.in"], "receipt", "Thank you for shopping with us."),
    ("Uber Receipts", "uber.com", "uber.com", "", ["uber.com"], "receipt", "Thanks for riding with Uber."),
    ("Zomato", "zomato.com", "mailer.zomato.com", "", ["zomato.com"], "receipt", "Your order has been delivered. Enjoy your meal."),
    ("Netflix", "netflix.com", "netflix.com", "", ["netflix.com"], "receipt", "Your Netflix membership payment was successful."),
    ("HDFC Bank Alerts", "hdfcbank.com", "alerts.hdfcbank.com", "", ["hdfcbank.com"], "bank_alert", "This is an auto-generated alert. Never share your OTP or PIN with anyone."),
    ("ICICI Bank", "icicibank.com", "alerts.icicibank.com", "", ["icicibank.com"], "bank_alert", "Do not share your OTP, CVV or password. Security alert from ICICI Bank."),
    ("State Bank of India", "sbi.co.in", "mail.sbi.co.in", "", ["sbi.co.in"], "bank_alert", "SBI never asks for your password by email. Suspicious activity? Call the number on your card."),
    ("Google", "google.com", "accounts.google.com", "", ["google.com"], "password_reset", "You can ignore this email if you did not request it."),
    ("Microsoft account team", "microsoft.com", "microsoft.com", "", ["microsoft.com"], "password_reset", "If this was not you, secure your account at account.microsoft.com."),
    ("LinkedIn", "linkedin.com", "linkedin.com", "", ["linkedin.com"], "password_reset", "You are receiving LinkedIn notification emails."),
    ("Prof. Rao", "bmsit.in", "bmsit.in", "", ["bmsit.in"], "internal", "Regards, Prof. Rao, Dept. of CSE"),
    ("HOD CSE", "bmsit.in", "bmsit.in", "", ["bmsit.in"], "internal", "Thanks and regards, HOD, Dept. of CSE"),
    ("Placement Cell", "bmsit.in", "bmsit.in", "placements@bmsit.in", ["bmsit.in", "forms.gle"], "internal", "Placement Cell, BMSIT&M"),
    ("GitHub", "github.com", "github.com", "", ["github.com"], "dev", "You are receiving this because you are subscribed to this thread."),
    ("Vercel", "vercel.com", "vercel.com", "", ["vercel.com"], "dev", "Vercel Inc., sent to you because you own this project."),
    ("Delhivery", "delhivery.com", "mail.delhivery.com", "", ["delhivery.com"], "delivery", "Track your shipment on delhivery.com."),
    ("Amazon Shipping", "amazon.in", "amazonses.com", "", ["amazon.in"], "delivery", "Your package is on the way."),
    ("Rahul Sharma", "gmail.com", "gmail.com", "", [], "friend", "cheers, Rahul"),
    ("Anita Menon", "outlook.com", "outlook.com", "", [], "friend", "Anita"),
    ("Project mentor", "example.org", "example.org", "", ["example.org"], "internal", "Best, your mentor"),
]

LEGIT_BODIES = {
    "newsletter": ["Top stories for you this week: {t1}, {t2}. Read now.", "New this week: {t1} and {t2}. Limited time offer ends soon."],
    "receipt": ["Order {oid}: total INR {amt}. Your invoice is attached. Thank you.", "Payment of INR {amt} received for order {oid}. View your receipt."],
    "bank_alert": ["Dear customer, INR {amt} was debited from your account ending {oid} on {d}. If you did not do this transaction, call the number printed on your card. Security alert.",
                   "Your account statement for {d} is ready. Sign in to net banking from the official app to view it."],
    "password_reset": ["We received a request to reset your password. Click the button to choose a new password. This link expires in 24 hours.",
                       "A new sign-in to your account was detected from {t1}. If this was you, you can ignore this message."],
    "internal": ["Hi all, the review for {t1} is scheduled on {d}. Please bring your progress report. {t2}", "Reminder: submit the {t1} documents by {d}. Thanks."],
    "dev": ["{t1} opened a pull request: {t2}. View it on the website.", "Build {oid} succeeded for your project. See deployment details."],
    "delivery": ["Your shipment {oid} is out for delivery today. Track your package.", "Delivery update for {oid}: arriving on {d}."],
    "friend": ["hey, are we meeting on {d}? also check this article {t1}", "sharing the notes for {t1}, let me know if the link works"],
}
TOPICS = ["machine learning", "web security", "campus placements", "cloud costs", "open source", "mobile apps", "data privacy", "exam schedule", "hackathon", "internship drive"]

PHISH_FAMILIES = ["bank_kyc", "paypal_verify", "microsoft_password", "delivery_fee", "payroll_update", "invoice_attachment",
                  "crypto_giveaway", "tax_refund", "shared_doc", "gift_card_ceo"]
PHISH_BRAND = {"bank_kyc": "hdfc", "paypal_verify": "paypal", "microsoft_password": "microsoft", "delivery_fee": "dhl",
               "payroll_update": "workday", "invoice_attachment": "docusign", "crypto_giveaway": "binance",
               "tax_refund": "incometax", "shared_doc": "google", "gift_card_ceo": ""}
PHISH_SUBJECT = {
    "bank_kyc": ["Your {b} account will be suspended: complete KYC", "{b} security alert: verify your account"],
    "paypal_verify": ["Action required: confirm your {b} account", "Unusual activity on your {b} account"],
    "microsoft_password": ["Your {b} password expires today", "{b} 365: mailbox storage full, verify now"],
    "delivery_fee": ["Package on hold: pay the delivery fee", "{b}: failed delivery, reschedule"],
    "payroll_update": ["Updated payroll details required", "HR: salary revision document"],
    "invoice_attachment": ["Invoice {oid} overdue", "Signed document waiting: {oid}"],
    "crypto_giveaway": ["You have won 2 BTC", "Claim your airdrop before it expires"],
    "tax_refund": ["Income tax refund of INR {amt} approved", "Final notice: tax refund pending"],
    "shared_doc": ["{n} shared a document with you", "Review the shared file"],
    "gift_card_ceo": ["Quick favour", "Are you available?"],
}
PHISH_BODY = {
    "bank_kyc": "Dear customer, your {b} account will be suspended within 24 hours unless you verify your account. Click here to confirm your details immediately.",
    "paypal_verify": "We noticed suspicious activity. Your account is locked. Log in to {b} and confirm your identity to restore access. Failure to act will result in permanent closure.",
    "microsoft_password": "Your password expires today. Update your password now to keep access to your mailbox. Click the link below.",
    "delivery_fee": "Your parcel could not be delivered. Pay the small redelivery fee now using the link to avoid return to sender.",
    "payroll_update": "Please review the updated payroll document and sign in to confirm your bank details before the deadline.",
    "invoice_attachment": "Please find the attached invoice. Payment is overdue. Open the attached file and arrange a bank transfer.",
    "crypto_giveaway": "Congratulations! Connect your wallet to claim your reward. Offer expires soon, act now.",
    "tax_refund": "You are eligible for a refund. Verify your identity and enter your card number to receive the payment.",
    "shared_doc": "A document was shared with you. Sign in with your email password to view the document.",
    "gift_card_ceo": "I am in a meeting and cannot talk. I need you to buy gift cards for a client. Reply with your phone number and I will send details. Keep this confidential.",
}
CALM_BODY = {  # fluent, no urgency (AI-written style)
    "bank_kyc": "As part of our periodic review we ask customers to confirm their contact information. You can do this through the secure page linked below at your convenience.",
    "paypal_verify": "To help us keep your account safe, please take a moment to review your recent sign-in details using the link below.",
    "microsoft_password": "Our records show that your mailbox settings may need a quick review. Please use the link below to take a look.",
    "delivery_fee": "We tried to deliver your parcel today. You can choose a new delivery slot using the link below.",
    "payroll_update": "Please review the attached update regarding payroll. Let me know if you have questions.",
    "invoice_attachment": "Hello, kindly find the attached invoice for last month's services. Thank you for your continued business.",
    "crypto_giveaway": "Thanks for being part of our community. A small reward is waiting in your account; use the link below to view it.",
    "tax_refund": "Our review shows a pending adjustment on your return. Please check the status using the link below.",
    "shared_doc": "A colleague has shared a file with you. You can view it using the link below.",
    "gift_card_ceo": "Are you free for a quick favour? I would like your help with something for a client today.",
}
LOOK_TLDS = ["xyz", "top", "click", "icu", "support", "com", "net", "info", "online"]
ATTACK_DOMAINS = ["secure-verify", "account-update", "login-portal", "support-center", "cloud-docs", "mail-security", "billing-review"]


def _rand_domain(rng: random.Random, brand: str) -> str:
    base = brand or rng.choice(["office", "finance", "hr", "docs"])
    typo = rng.choice([base.replace("l", "1").replace("o", "0"), base + "-" + rng.choice(ATTACK_DOMAINS), rng.choice(ATTACK_DOMAINS) + "-" + base, base + rng.choice(["secure", "verify", "login"])])
    return f"{typo}.{rng.choice(LOOK_TLDS)}"


def _build_msg(frm_name: str, frm_addr: str, subject: str, text: str, html: str | None, bounce: str, reply_to: str,
               auth: dict[str, str], attach: tuple[str, str, bytes] | None, hops: int, rng: random.Random) -> EmailMessage:
    m = EmailMessage()
    m["From"] = f'"{frm_name}" <{frm_addr}>' if frm_name else frm_addr
    m["To"] = "student@example.com"
    m["Subject"] = subject
    m["Date"] = (NOW - timedelta(hours=rng.randint(1, 500))).strftime("%a, %d %b %Y %H:%M:%S +0000")
    m["Message-ID"] = f"<{rng.getrandbits(48):x}@{frm_addr.split('@')[-1]}>"
    if bounce:
        m["Return-Path"] = f"<bounce@{bounce}>"
    if reply_to:
        m["Reply-To"] = reply_to
    for _ in range(hops):
        m["Received"] = f"from mx{rng.randint(1,99)}.example.net by mx.example.com; {m['Date']}"
    parts = [f"{k}={v}" for k, v in auth.items() if v != "missing"]
    if parts:
        m["Authentication-Results"] = "mx.example.com; " + "; ".join(parts)
    m.set_content(text)
    if html:
        m.add_alternative(html, subtype="html")
    if attach:
        name, ctype, data = attach
        mt, st = ctype.split("/")
        m.add_attachment(data, maintype=mt, subtype=st, filename=name)
    return m


def _wrap(orig: EmailMessage, mode: str, rng: random.Random) -> bytes:
    if mode == "direct":
        return orig.as_bytes()
    outer = EmailMessage()
    outer["From"] = "student@example.com"
    outer["To"] = "u-0a1b2c3d@phishlens.example"
    outer["Subject"] = "Fwd: " + str(orig["Subject"])
    if mode == "attachment":
        outer.set_content("Is this safe?")
        outer.add_attachment(orig)
        return outer.as_bytes()
    body = orig.get_body(preferencelist=("plain",))
    html = orig.get_body(preferencelist=("html",))
    text = body.get_content() if body else ""
    hdr = f"From: {orig['From']}\nDate: {orig['Date']}\nSubject: {orig['Subject']}\nTo: {orig['To']}\n"
    if orig["Reply-To"]:
        hdr += f"Reply-To: {orig['Reply-To']}\n"
    outer.set_content("Is this safe?\n\n---------- Forwarded message ---------\n" + hdr + "\n" + text)
    if html:
        outer.add_alternative(html.get_content(), subtype="html")
    return outer.as_bytes()


def _filler(rng: random.Random) -> dict:
    return dict(t1=rng.choice(TOPICS), t2=rng.choice(TOPICS), oid=str(rng.randint(10000, 99999)), amt=str(rng.randint(100, 9000)),
                d=f"{rng.randint(1, 28)} Oct", n=rng.choice(["Rahul", "Priya", "Admin", "Finance Team"]), b="")


def _legit_message(s: Sender, rng: random.Random, ages: dict[str, int]) -> EmailMessage:
    f = _filler(rng)
    body = rng.choice(LEGIT_BODIES[s.family]).format(**f) + "\n\n" + s.sig
    subj = {"newsletter": f"Your weekly digest: {f['t1']}", "receipt": f"Your receipt for order {f['oid']}",
            "bank_alert": rng.choice(["Transaction alert", "Security alert: new sign-in", "Account statement"]),
            "password_reset": rng.choice(["Reset your password", "New sign-in to your account"]),
            "internal": f"Review meeting: {f['t1']}", "dev": f"[repo] {f['t2']} (#{rng.randint(1, 900)})",
            "delivery": f"Shipment {f['oid']} update", "friend": rng.choice(["notes", "tomorrow?", "check this"])}[s.family]
    links = []
    if s.links and rng.random() < 0.7:          # ~30% of legitimate mail is plain text with no links
        for dom in rng.sample(s.links, k=min(len(s.links), rng.randint(1, 2))):
            scheme = "http" if rng.random() < 0.07 else "https"
            host = dom if rng.random() < 0.7 else f"www.{dom}"
            links.append((f"{scheme}://{host}/{rng.choice(['view', 'track', 'article', 'account'])}/{rng.randint(1, 999)}", rng.choice(["View online", "Track package", "Read more", "Open"])))
        if s.family == "newsletter" and rng.random() < 0.08:
            links.append((f"https://bit.ly/{rng.getrandbits(24):x}", "Special offer"))
        if s.family == "friend" or rng.random() < 0.0:
            pass
    html = "<html><body><p>" + body.replace("\n", "<br>") + "</p>" + "".join(f'<p><a href="{u}">{t}</a></p>' for u, t in links) + "</body></html>" if links else None
    if not html and s.family == "friend":
        body += " https://docs.google.com/document/d/" + f"{rng.getrandbits(40):x}"
    r = rng.random()
    auth = {"spf": "pass" if r < 0.93 else ("fail" if r < 0.96 else "none"),
            "dkim": "pass" if rng.random() < 0.88 else "none", "dmarc": "pass" if rng.random() < 0.82 else "none"}
    if s.domain in ("gmail.com", "outlook.com"):
        auth["dmarc"] = "pass"
    attach = None
    if s.family == "receipt" and rng.random() < 0.5:
        attach = (f"invoice_{f['oid']}.pdf", "application/pdf", b"%PDF-1.4 fake " + bytes(rng.getrandbits(8) for _ in range(20)))
    reply_to = s.reply_to
    return _build_msg(s.name, s.addr, subj, body, html, s.bounce, reply_to, auth, attach, rng.randint(2, 6), rng)


def _phish_message(fam: str, rng: random.Random, known: list[Sender], ages: dict[str, int]) -> tuple[EmailMessage, ProfileData | None]:
    brand = PHISH_BRAND[fam]
    f = _filler(rng)
    f["b"] = brand.title() if brand else "Support"
    spoof = None
    mode = rng.random()
    if mode < 0.2 and known:
        spoof = rng.choice(known)           # spoofed / compromised known sender
    attack_dom = _rand_domain(rng, brand)
    ages[attack_dom] = rng.randint(1, 45) if rng.random() < 0.85 else rng.randint(300, 2500)
    if spoof is not None:
        name, addr = spoof.name, spoof.addr
        profile = spoof.profile
    elif rng.random() < 0.18:
        name = f"{f['b']} Support"
        addr = f"{brand or 'support'}.help{rng.randint(1, 99)}@{rng.choice(['gmail.com', 'outlook.com', 'yahoo.com'])}"
        profile = None
    else:
        name = f"{f['b']} {rng.choice(['Support', 'Security', 'Team', 'Alerts'])}" if (brand and rng.random() < 0.8) else rng.choice(["Admin", "HR Department", "Accounts"])
        addr = f"{rng.choice(['security', 'support', 'noreply', 'alerts', 'admin'])}@{attack_dom}"
        profile = None
    calm = rng.random() < 0.28
    body = (CALM_BODY if calm else PHISH_BODY)[fam].format(**f)
    if not calm and rng.random() < 0.35:
        body += " " + rng.choice(["Immediate action required.", "This is your final notice.", "Respond now."])
    subj = rng.choice(PHISH_SUBJECT[fam]).format(**f)
    link_dom = attack_dom if rng.random() < 0.8 else _rand_domain(rng, brand)
    ages.setdefault(link_dom, rng.randint(1, 45))
    r = rng.random()
    url_kind = "ip" if r < 0.1 else ("short" if r < 0.25 else "plain")
    path = rng.choice(["login", "verify", "secure/update", "confirm"])
    if url_kind == "ip":
        href = f"http://{rng.randint(11, 220)}.{rng.randint(1, 250)}.{rng.randint(1, 250)}.{rng.randint(1, 250)}/{path}"
    elif url_kind == "short":
        href = f"https://bit.ly/{rng.getrandbits(24):x}"
    else:
        sub = (brand + ".") if (brand and rng.random() < 0.4) else ""
        href = f"{'http' if rng.random() < 0.3 else 'https'}://{sub}{link_dom}/{path}"
    shown = rng.choice([f"www.{brand}.com/secure" if brand else "docs.google.com/view", "Verify now", "Click here", "Review document", f"{brand}.com" if brand else "Open"])
    html = f"<html><body><p>{body}</p><p><a href=\"{href}\">{shown}</a></p></body></html>"
    if gift := (fam == "gift_card_ceo"):
        html = None
        body += f"\n\n{href}" if rng.random() < 0.3 else ""
    attach = None
    if fam == "invoice_attachment" or rng.random() < 0.12:
        nm = rng.choice(["invoice.pdf.exe", "document.docm", "payment_details.zip", "scan.html", "invoice.pdf", "report.js"])
        attach = (nm, "application/octet-stream" if nm.endswith(("exe", "zip", "js")) else "application/pdf", b"MZfake")
    if spoof is not None:
        auth = {"spf": "fail" if rng.random() < 0.65 else "none", "dkim": "none", "dmarc": "fail" if rng.random() < 0.5 else "none"}
        bounce, reply = attack_dom, f"help@{attack_dom}"
    else:
        a = rng.random()
        auth = {"spf": "pass" if a < 0.45 else ("fail" if a < 0.75 else "none"), "dkim": "pass" if rng.random() < 0.35 else "none",
                "dmarc": "fail" if rng.random() < 0.3 else ("pass" if rng.random() < 0.3 else "none")}
        bounce = attack_dom if rng.random() < 0.7 else _rand_domain(rng, "mailer")
        reply = f"{rng.choice(['help', 'claim'])}@{rng.choice(['gmail.com', attack_dom])}" if rng.random() < 0.4 else ""
    return _build_msg(name, addr, subj, body, html, bounce, reply, auth, attach, rng.randint(1, 4), rng), profile


def build_samples(n: int = 2400, seed: int = 7, phish_ratio: float = 0.4, history_per_sender: int = 5) -> list[Sample]:
    rng = random.Random(seed)
    # 1) senders with histories built by the production profile code
    senders: list[Sender] = []
    ages: dict[str, int] = {}
    for name, dom, bounce, reply_local, links, fam, sig in LEGIT_DEFS:
        s = Sender(name=name, addr=f"{name.split()[0].lower().strip('.')}.{rng.randint(1, 99)}@{dom}" if dom in ("gmail.com", "outlook.com", "bmsit.in", "example.org") else f"no-reply@{dom}",
                   domain=dom, bounce=bounce, reply_to=reply_local, links=links, family=fam, sig=sig)
        ages[dom] = rng.randint(1500, 9000)
        for ld in links:
            ages.setdefault(ld, rng.randint(1500, 9000))
        senders.append(s)
    for s in senders:
        prof = ProfileData()
        for i in range(history_per_sender):
            raw = _legit_message(s, rng, ages).as_bytes()
            p = parse_email(raw)
            ctx = ExtractionContext(profile=prof, min_history=3, now=NOW - timedelta(days=60 - i * 10))
            fx = extract_all(p, ctx)
            update_profile(prof, p, fx.urgency, fx.link_domains, ctx.now)
        s.profile = prof

    # 2) dataset messages
    samples: list[Sample] = []
    n_phish = int(n * phish_ratio)
    plan = [1] * n_phish + [0] * (n - n_phish)
    rng.shuffle(plan)
    for i, label in enumerate(plan):
        wrap = rng.choices(["direct", "attachment", "inline"], weights=[0.4, 0.3, 0.3])[0]
        if label == 0:
            s = rng.choice(senders)
            msg = _legit_message(s, rng, ages)
            # ~45% of legitimate mail is a first contact (no history). Without this the model would learn the
            # shortcut 'no history => phishing' (a leak caused by the generator, not a real signal).
            profile = s.profile if rng.random() < 0.55 else None
            group = f"legit-{s.family}-{senders.index(s) % 6}"
        else:
            fam = rng.choice(PHISH_FAMILIES)
            msg, profile = _phish_message(fam, rng, senders, ages)
            group = f"phish-{fam}-{rng.randint(0, 5)}"
        raw = _wrap(msg, wrap, rng)
        if rng.random() < 0.02:                      # label noise
            label = 1 - label
        provider: DomainAgeProvider = DictDomainAge(dict(ages)) if rng.random() < 0.5 else NullDomainAge()
        samples.append(Sample(raw=raw, label=label, group=group, profile=profile, domain_age=provider))
    return samples


def samples_to_matrix(samples: list[Sample], min_history: int = 3):
    import numpy as np
    X, y, g = [], [], []
    for s in samples:
        ctx = ExtractionContext(domain_age=s.domain_age, profile=s.profile, min_history=min_history, now=NOW)
        X.append(extract_all(parse_email(s.raw), ctx).vector)
        y.append(s.label)
        g.append(s.group)
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int), np.asarray(g)
