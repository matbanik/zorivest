"""Tests for RedactionFilter — MEU-3A (AC-1 through AC-14)."""

from __future__ import annotations

import logging


from zorivest_infra.logging.redaction import RedactionFilter


def _make_record(
    msg: str = "test",
    args: tuple | dict | None = None,
    **extras: object,
) -> logging.LogRecord:
    """Create a LogRecord with optional extras."""
    record = logging.LogRecord(
        name="zorivest.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg,
        args=args or (),
        exc_info=None,
    )
    for k, v in extras.items():
        setattr(record, k, v)
    return record


class TestRedactionRegexPatterns:
    """AC-1 through AC-9: Regex-based redaction of sensitive patterns."""

    def setup_method(self) -> None:
        self.f = RedactionFilter()

    def test_url_query_param_redaction(self) -> None:
        """AC-1: URL query param apikey=SECRET redacted to apikey=[REDACTED]."""
        record = _make_record(
            msg="Fetching https://api.example.com?apikey=MY_SECRET_KEY&format=json"
        )
        self.f.filter(record)
        assert "MY_SECRET_KEY" not in record.msg
        assert "apikey=[REDACTED]" in record.msg
        assert "format=json" in record.msg  # non-sensitive params preserved

    def test_bearer_token_redaction(self) -> None:
        """AC-2: Bearer token redacted."""
        record = _make_record(
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
        )
        self.f.filter(record)
        assert "eyJ" not in record.msg
        assert "Bearer [REDACTED]" in record.msg

    def test_fernet_encrypted_value_redaction(self) -> None:
        """AC-3: Fernet ENC:gAAAA... redacted to [ENCRYPTED_VALUE]."""
        record = _make_record(msg="Using key ENC:gAAAAABnFoo123Bar456Baz789==")
        self.f.filter(record)
        assert "gAAAA" not in record.msg
        assert "[ENCRYPTED_VALUE]" in record.msg

    def test_jwt_redaction(self) -> None:
        """AC-4: JWT eyJhbGci... redacted to [JWT_REDACTED]."""
        record = _make_record(
            msg="Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.signature123"
        )
        self.f.filter(record)
        assert "eyJhbGci" not in record.msg
        assert "[JWT_REDACTED]" in record.msg

    def test_aws_access_key_redaction(self) -> None:
        """AC-5: AWS access key AKIA... redacted."""
        record = _make_record(msg="Using AWS key AKIAIOSFODNN7EXAMPLE")
        self.f.filter(record)
        assert "AKIAIOSFODNN7EXAMPLE" not in record.msg
        assert "[AWS_KEY_REDACTED]" in record.msg

    def test_connection_string_redaction(self) -> None:
        """AC-6: Connection string credentials redacted."""
        record = _make_record(
            msg="Connecting to postgresql://admin:s3cret@db.host:5432/mydb"
        )
        self.f.filter(record)
        assert "admin" not in record.msg
        assert "s3cret" not in record.msg
        assert "://[REDACTED]:[REDACTED]@" in record.msg

    def test_credit_card_redaction(self) -> None:
        """AC-7: Credit card PAN redacted."""
        record = _make_record(msg="Card: 4111-1111-1111-1111")
        self.f.filter(record)
        assert "4111" not in record.msg
        assert "[CC_REDACTED]" in record.msg

    def test_ssn_redaction(self) -> None:
        """AC-8: SSN 123-45-6789 redacted."""
        record = _make_record(msg="Customer SSN: 123-45-6789")
        self.f.filter(record)
        assert "123-45-6789" not in record.msg
        assert "[SSN_REDACTED]" in record.msg

    def test_zorivest_api_key_redaction(self) -> None:
        """AC-9: Zorivest API key zrv_sk_... redacted."""
        record = _make_record(msg="Key: zrv_sk_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef")
        self.f.filter(record)
        assert "zrv_sk_" not in record.msg
        assert "[ZRV_KEY_REDACTED]" in record.msg


class TestRedactionKeyDenylist:
    """AC-10 through AC-12: Key-based denylist redaction for dict data."""

    def setup_method(self) -> None:
        self.f = RedactionFilter()

    def test_password_key_redacted(self) -> None:
        """AC-10: Dict key 'password' → value replaced with [REDACTED]."""
        record = _make_record(config={"password": "super_secret", "host": "db.local"})
        self.f.filter(record)
        assert record.config["password"] == "[REDACTED]"  # type: ignore[attr-defined]
        assert record.config["host"] == "db.local"  # type: ignore[attr-defined]

    def test_api_key_key_redacted(self) -> None:
        """AC-11: Dict key 'api_key' → value replaced regardless of format."""
        record = _make_record(settings={"api_key": "abc123", "timeout": 30})
        self.f.filter(record)
        assert record.settings["api_key"] == "[REDACTED]"  # type: ignore[attr-defined]
        assert record.settings["timeout"] == 30  # type: ignore[attr-defined]

    def test_nested_dict_redaction(self) -> None:
        """AC-12: Nested dict values redacted recursively."""
        record = _make_record(
            config={"connection": {"password": "deep_secret", "host": "db.local"}}
        )
        self.f.filter(record)
        assert record.config["connection"]["password"] == "[REDACTED]"  # type: ignore[attr-defined]
        assert record.config["connection"]["host"] == "db.local"  # type: ignore[attr-defined]


class TestRedactionBehavior:
    """AC-13, AC-14: Filter behavior and extras scanning."""

    def setup_method(self) -> None:
        self.f = RedactionFilter()

    def test_filter_always_returns_true(self) -> None:
        """AC-13: Filter always returns True (never drops records)."""
        record = _make_record(msg="Bearer eyJItsAToken")
        result = self.f.filter(record)
        assert result is True

    def test_msg_modified_in_place(self) -> None:
        """AC-13 continued: record.msg modified in-place, not dropped."""
        original_msg = "Key: zrv_sk_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
        record = _make_record(msg=original_msg)
        self.f.filter(record)
        assert record.msg != original_msg
        assert "[ZRV_KEY_REDACTED]" in record.msg

    def test_non_reserved_extras_scanned(self) -> None:
        """AC-14: Non-reserved extras on LogRecord scanned and redacted."""
        record = _make_record(api_response="Bearer eyJhbGciToken123")
        self.f.filter(record)
        assert "Bearer [REDACTED]" in record.api_response  # type: ignore[attr-defined]

    def test_string_args_redacted(self) -> None:
        """String args are redacted through Layer 1."""
        record = _make_record(
            msg="Connecting to %s",
            args=("postgresql://admin:s3cret@db:5432/mydb",),
        )
        self.f.filter(record)
        args = record.args
        assert isinstance(args, tuple)
        assert "s3cret" not in str(args[0])

    def test_clean_message_unchanged(self) -> None:
        """Messages with no sensitive data pass through unchanged."""
        clean_msg = "Portfolio balance updated: $50,000"
        record = _make_record(msg=clean_msg)
        self.f.filter(record)
        assert record.msg == clean_msg
