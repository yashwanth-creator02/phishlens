"""Request-size limits shared by the upload and inbound-webhook endpoints."""
from __future__ import annotations

MAX_MESSAGE_BYTES = 10 * 1024 * 1024
# Base64 expands the payload by 4/3; leave headroom for the JSON envelope
# and for encoders that escape '/' as '\/'.
MAX_BASE64_BYTES = 4 * ((MAX_MESSAGE_BYTES + 2) // 3) + 512 * 1024
