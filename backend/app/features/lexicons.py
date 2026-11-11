"""Word lists and constants used by the feature modules. Kept in one place so they can be reviewed
and tuned without touching extraction logic."""

URGENCY_PHRASES = [
    "immediately", "urgent", "right away", "as soon as possible", "asap", "within 24 hours", "within 48 hours",
    "act now", "final notice", "last warning", "expires today", "expires soon", "limited time", "today only",
    "before it is too late", "failure to", "will be suspended", "will be closed", "will be deactivated",
    "will be blocked", "account suspended", "action required", "immediate action", "respond now",
]
THREAT_PHRASES = [
    "suspended", "terminated", "blocked", "locked", "legal action", "penalty", "fine", "arrest",
    "unauthorized", "unauthorised", "suspicious activity", "security alert", "compromised", "deactivated",
    "closed permanently", "lose access",
]
CREDENTIAL_PHRASES = [
    "verify your account", "confirm your account", "confirm your identity", "verify your identity",
    "update your password", "reset your password", "enter your password", "login to", "log in to", "sign in to",
    "validate your", "re-enter", "update your payment", "update your billing", "confirm your details",
    "verify your details", "otp", "one time password", "pin number", "card number", "cvv",
]
PAYMENT_PHRASES = [
    "make a payment", "pay now", "approve the payment", "approve payment", "wire transfer", "bank transfer",
    "gift card", "invoice attached", "outstanding balance", "overdue", "send money", "transfer the amount",
    "payment details", "pay the", "remit",
]
DOWNLOAD_PHRASES = [
    "download the attached", "open the attached", "see attached", "attached file", "download now",
    "open the document", "enable macros", "enable content", "view the document", "download and open",
]
REPLY_INFO_PHRASES = [
    "reply with your", "send me your", "send your", "reply to this email with", "provide your",
    "share your", "kindly send", "kindly provide",
]
# Impersonal salutations: real correspondents address the recipient by name, mass phishing cannot.
GENERIC_GREETINGS = [
    "dear customer", "dear user", "dear client", "dear member", "dear account holder",
    "dear valued customer", "dear sir/madam", "dear sir or madam", "dear email user",
    "dear subscriber", "dear candidate", "dear employee",
]
CLICK_PHRASES = [
    "click here", "click the link", "click below", "click on the link", "follow the link", "tap here",
    "use the link", "visit the link", "click the button",
]
FINANCIAL_TERMS = [
    "bank", "account", "payment", "invoice", "refund", "transaction", "credit", "debit", "wallet", "bitcoin",
    "crypto", "wire", "salary", "tax", "fund", "balance", "loan", "prize", "lottery", "inheritance",
]

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly", "cutt.ly",
    "shorturl.at", "tiny.cc", "rb.gy", "lnkd.in", "t.ly",
}
SUSPICIOUS_TLDS = {
    "zip", "mov", "top", "xyz", "click", "link", "work", "gq", "tk", "ml", "cf", "ga", "country", "kim",
    "loan", "men", "party", "review", "stream", "science", "support", "icu", "rest", "cam", "monster",
}
FREEMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me", "protonmail.com",
                    "aol.com", "mail.com", "yandex.com", "rediffmail.com"}

# brand keyword -> legitimate registered domains
BRANDS: dict[str, set[str]] = {
    "paypal": {"paypal.com"}, "amazon": {"amazon.com", "amazon.in", "amazon.co.uk", "amazonaws.com"},
    "microsoft": {"microsoft.com", "office.com", "outlook.com", "live.com", "microsoftonline.com"},
    "google": {"google.com", "gmail.com", "youtube.com"}, "apple": {"apple.com", "icloud.com"},
    "netflix": {"netflix.com"}, "facebook": {"facebook.com", "facebookmail.com", "meta.com"},
    "instagram": {"instagram.com"}, "linkedin": {"linkedin.com"}, "whatsapp": {"whatsapp.com"},
    "dhl": {"dhl.com"}, "fedex": {"fedex.com"}, "ups": {"ups.com"},
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "sbi.bank.in"}, "hdfc": {"hdfcbank.com", "hdfc.com"},
    "icici": {"icicibank.com"}, "axis": {"axisbank.com"}, "paytm": {"paytm.com"},
    "flipkart": {"flipkart.com"}, "irctc": {"irctc.co.in"}, "github": {"github.com"},
    "dropbox": {"dropbox.com"}, "docusign": {"docusign.com", "docusign.net"},
}

RISKY_EXTENSIONS = {
    "exe", "scr", "bat", "cmd", "com", "pif", "js", "jse", "vbs", "vbe", "wsf", "ps1", "jar", "msi", "lnk",
    "hta", "iso", "img", "dll", "apk", "reg",
}
MACRO_EXTENSIONS = {"docm", "xlsm", "pptm", "dotm", "xlam"}
ARCHIVE_EXTENSIONS = {"zip", "rar", "7z", "gz", "tar", "ace", "cab"}
DOC_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg", "jpeg", "png", "gif"}
MIME_EXPECTED = {
    "pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif",
    "txt": "text/plain",
}
