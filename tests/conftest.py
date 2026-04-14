import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

ENV = {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_ANON_KEY": "fake-anon-key",
    "RESEND_API_KEY": "re_fake_key",
    "CRON_SECRET": "test-cron-secret",
}


def _fresh_import(mock_sb):
    """Re-import main.py — must be called inside an active os.environ patch."""
    sys.modules.pop("main", None)
    with patch("supabase.create_client", return_value=mock_sb):
        import main as m
    return m


@pytest.fixture()
def client_with_mock():
    """Yields (TestClient, supabase_mock) with ENV vars active for the whole test."""
    mock_sb = MagicMock()
    with patch.dict("os.environ", ENV, clear=False):
        m = _fresh_import(mock_sb)
        yield TestClient(m.app), mock_sb


@pytest.fixture()
def client():
    """Yields a plain TestClient with ENV vars active for the whole test."""
    mock_sb = MagicMock()
    with patch.dict("os.environ", ENV, clear=False):
        m = _fresh_import(mock_sb)
        yield TestClient(m.app)


@pytest.fixture()
def main_module():
    """Yields the imported main module with ENV vars active for the whole test."""
    mock_sb = MagicMock()
    with patch.dict("os.environ", ENV, clear=False):
        m = _fresh_import(mock_sb)
        yield m
