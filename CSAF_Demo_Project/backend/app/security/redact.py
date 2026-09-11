"""Log and payload redaction.

Activity events, X-Ray panels, and exception handlers must never echo API
keys, cookies, or payment fields. This is a teaching demo; leaking the
Gemini key in a projector view would still be a real incident.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import get_settings

_SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|authorization|cookie|password|secret|token|card|cvv|pan)",
    re.IGNORECASE,
)
_REDACTED = "[REDACTED]"


def _looks_sensitive_key(name: str) -> bool:
    return bool(_SENSITIVE_KEY_RE.search(name or ""))


def sanitize_value(value: Any, configured_secrets: list[str] | None = None) -> Any:
    secrets = configured_secrets
    if secrets is None:
        key = get_settings().gemini_api_key.strip()
        secrets = [key] if key else []

    if isinstance(value, dict):
        return {
            k: (_REDACTED if _looks_sensitive_key(str(k)) else sanitize_value(v, secrets))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize_value(item, secrets) for item in value]
    if isinstance(value, str):
        redacted = value
        for secret in secrets:
            if secret and secret in redacted:
                redacted = redacted.replace(secret, _REDACTED)
        return redacted
    return value


def sanitize_text(text: str) -> str:
    return str(sanitize_value(text))


def dumps_sanitized(payload: Any) -> str:
    clean = sanitize_value(payload)
    return json.dumps(clean, default=str)
