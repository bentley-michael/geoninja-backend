"""
Security tests for POST /cron/send-reminders authentication.

The endpoint requires a CRON_SECRET query parameter. These tests verify that
authorization is correctly enforced, including a test that documents the
empty-string bypass vulnerability (which is fixed in main.py).
"""

import pytest
from unittest.mock import patch


def _cron_call(client, secret=None):
    url = "/cron/send-reminders"
    if secret is not None:
        url += f"?secret={secret}"
    return client.post(url)


def _cron_stub(sb):
    """Wire the supabase mock so the cron route can execute without error."""
    sb.table.return_value.select.return_value \
        .not_.return_value.is_.return_value \
        .eq.return_value.execute.return_value.data = []


class TestCronAuthentication:
    def test_missing_secret_returns_401(self, client):
        resp = _cron_call(client)
        assert resp.status_code == 401

    def test_wrong_secret_returns_401(self, client):
        resp = _cron_call(client, secret="wrong-secret")
        assert resp.status_code == 401

    def test_correct_secret_returns_200(self, client_with_mock):
        client, sb = client_with_mock
        _cron_stub(sb)
        with patch("resend.Emails.send"):
            resp = _cron_call(client, secret="test-cron-secret")
        assert resp.status_code == 200

    def test_correct_secret_returns_sent_count(self, client_with_mock):
        client, sb = client_with_mock
        _cron_stub(sb)
        with patch("resend.Emails.send"):
            data = _cron_call(client, secret="test-cron-secret").json()
        assert "sent" in data
        assert isinstance(data["sent"], int)

    def test_correct_secret_returns_date(self, client_with_mock):
        client, sb = client_with_mock
        _cron_stub(sb)
        with patch("resend.Emails.send"):
            data = _cron_call(client, secret="test-cron-secret").json()
        assert "date" in data

    def test_empty_string_secret_returns_401(self, client):
        """
        Regression test for the empty-string auth bypass.

        If CRON_SECRET is unset, os.environ.get("CRON_SECRET", "") returns "".
        Without the fix, a request with ?secret= (empty string) would authenticate.
        The fix in main.py rejects requests when the env secret is falsy OR mismatched.
        """
        resp = _cron_call(client, secret="")
        assert resp.status_code == 401

    def test_case_sensitive_secret(self, client):
        """Secrets are case-sensitive — uppercase should not match."""
        resp = _cron_call(client, secret="TEST-CRON-SECRET")
        assert resp.status_code == 401

    def test_partial_secret_returns_401(self, client):
        resp = _cron_call(client, secret="test-cron")
        assert resp.status_code == 401
