from app.config import get_settings
from app.security.redact import dumps_sanitized, sanitize_text


def test_logs_do_not_contain_configured_secrets(client, monkeypatch, caplog):
    monkeypatch.setenv("GEMINI_API_KEY", "secret_test_key_xyz")
    get_settings.cache_clear()
    payload = dumps_sanitized(
        {
            "api_key": "secret_test_key_xyz",
            "authorization": "Bearer secret_test_key_xyz",
            "note": "called with secret_test_key_xyz",
        }
    )
    assert "secret_test_key_xyz" not in payload
    assert "[REDACTED]" in payload
    assert "secret_test_key_xyz" not in sanitize_text("header secret_test_key_xyz")
    get_settings.cache_clear()
