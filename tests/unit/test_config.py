import pytest
from packages.config import Settings, get_settings
from packages.utils import drop_pii_processor, get_logger, setup_logging


@pytest.mark.unit
def test_settings_defaults():
    settings = get_settings()
    assert settings.PROJECT_NAME == "SAATHI-AI"
    assert "localhost" in settings.DATABASE_URL
    assert "redis://" in settings.REDIS_URL


@pytest.mark.unit
def test_pii_redaction():
    event = {
        "event": "user_action",
        "phone_number": "+919876543210",
        "caller_name": "Test User",
        "secret_token": "abc123xyz",
        "status": "success",
    }
    sanitized = drop_pii_processor(None, "info", event)
    assert sanitized["phone_number"] == "[REDACTED_PII]"
    assert sanitized["caller_name"] == "[REDACTED_PII]"
    assert sanitized["secret_token"] == "[REDACTED_PII]"
    assert sanitized["status"] == "success"
