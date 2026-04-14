"""
API contract tests for all routes except POST /scores (see test_api_scores.py)
and POST /cron/send-reminders (see test_api_auth.py).

These tests verify HTTP status codes, response shapes, and edge-case behaviour.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestRoot:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_status_is_ok(self, client):
        assert client.get("/").json()["status"] == "ok"

    def test_service_name_present(self, client):
        assert "service" in client.get("/").json()


class TestHealth:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_status_is_healthy(self, client):
        assert client.get("/health").json()["status"] == "healthy"

    def test_time_field_present(self, client):
        assert "time" in client.get("/health").json()

    def test_time_is_valid_iso_string(self, client):
        time_str = client.get("/health").json()["time"]
        # Should not raise
        datetime.fromisoformat(time_str)


class TestGetStreak:
    def test_existing_user_returns_row(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "u1",
            "streak": 5,
            "best_streak": 10,
            "total_games": 20,
            "total_correct": 150,
            "email": "test@example.com",
        }]
        resp = client.get("/streaks/u1")
        assert resp.status_code == 200
        assert resp.json()["streak"] == 5
        assert resp.json()["best_streak"] == 10

    def test_unknown_user_returns_zero_defaults(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        resp = client.get("/streaks/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["streak"] == 0
        assert data["best_streak"] == 0
        assert data["total_games"] == 0
        assert data["total_correct"] == 0

    def test_returns_200_for_unknown_user(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        assert client.get("/streaks/nobody").status_code == 200


class TestDailyLeaderboard:
    def test_returns_200(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        assert client.get("/leaderboard/daily").status_code == 200

    def test_response_has_date_and_leaderboard(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        data = client.get("/leaderboard/daily").json()
        assert "date" in data
        assert "leaderboard" in data

    def test_leaderboard_is_list(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        assert isinstance(client.get("/leaderboard/daily").json()["leaderboard"], list)

    def test_leaderboard_entries_have_expected_fields(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = [
            {"username": "Ninja", "score": 10, "user_id": "u1"}
        ]
        entries = client.get("/leaderboard/daily").json()["leaderboard"]
        assert len(entries) == 1
        assert entries[0]["username"] == "Ninja"
        assert entries[0]["score"] == 10


class TestAlltimeLeaderboard:
    def test_returns_200(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        assert client.get("/leaderboard/alltime").status_code == 200

    def test_response_has_leaderboard(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        assert "leaderboard" in client.get("/leaderboard/alltime").json()

    def test_leaderboard_is_list(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        assert isinstance(client.get("/leaderboard/alltime").json()["leaderboard"], list)


class TestRegisterEmail:
    def test_existing_user_returns_ok(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"user_id": "u1"}
        ]
        with patch("resend.Emails.send"):
            resp = client.post("/register-email", json={
                "user_id": "u1", "email": "test@example.com"
            })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_new_user_returns_ok(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        with patch("resend.Emails.send"):
            resp = client.post("/register-email", json={
                "user_id": "u2", "email": "new@example.com"
            })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/register-email", json={
            "user_id": "u1", "email": "not-an-email"
        })
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client):
        resp = client.post("/register-email", json={"user_id": "u1"})
        assert resp.status_code == 422

    def test_missing_user_id_returns_422(self, client):
        resp = client.post("/register-email", json={"email": "test@example.com"})
        assert resp.status_code == 422


class TestUnsubscribe:
    def test_returns_200(self, client_with_mock):
        client, sb = client_with_mock
        resp = client.get("/unsubscribe?email=test@example.com")
        assert resp.status_code == 200

    def test_response_status_is_ok(self, client_with_mock):
        client, sb = client_with_mock
        data = client.get("/unsubscribe?email=test@example.com").json()
        assert data["status"] == "ok"

    def test_response_contains_message(self, client_with_mock):
        client, sb = client_with_mock
        data = client.get("/unsubscribe?email=test@example.com").json()
        assert "message" in data
        assert "Unsubscribed" in data["message"]

    def test_calls_db_update_with_null_email(self, client_with_mock):
        client, sb = client_with_mock
        client.get("/unsubscribe?email=test@example.com")
        # Verify the update call set email to None
        sb.table.return_value.update.assert_called_with({"email": None})
