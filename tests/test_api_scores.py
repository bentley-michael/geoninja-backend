"""
Integration tests for POST /scores.

These tests verify the full HTTP layer including streak calculation, Supabase
interactions, and Pydantic validation. Supabase is mocked; no real DB calls
are made.
"""

import pytest


def _streak_row(last_played, streak, best_streak=None, total_games=5, total_correct=40):
    """Helper to build a fake user_streaks row."""
    return [{
        "user_id": "user-1",
        "last_played": last_played,
        "streak": streak,
        "best_streak": best_streak if best_streak is not None else streak,
        "total_games": total_games,
        "total_correct": total_correct,
    }]


def _post_score(client, game_date="2026-04-14", score=7, user_id="user-1",
                username="Ninja", total=10):
    return client.post("/scores", json={
        "user_id": user_id,
        "username": username,
        "score": score,
        "total": total,
        "game_date": game_date,
    })


class TestNewUser:
    def test_returns_200(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        resp = _post_score(client)
        assert resp.status_code == 200

    def test_streak_starts_at_one(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        data = _post_score(client, score=8).json()
        assert data["streak"] == 1
        assert data["best_streak"] == 1

    def test_total_games_is_one(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        data = _post_score(client, score=8).json()
        assert data["total_games"] == 1

    def test_total_correct_equals_score(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        data = _post_score(client, score=9).json()
        assert data["total_correct"] == 9

    def test_zero_score_new_user(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        data = _post_score(client, score=0).json()
        assert data["streak"] == 1
        assert data["total_correct"] == 0
        assert data["total_games"] == 1


class TestConsecutiveDayPlay:
    def test_streak_increments(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-13", streak=5)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["streak"] == 6

    def test_best_streak_updates_when_surpassed(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-13", streak=10, best_streak=10)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["best_streak"] == 11

    def test_total_games_increments(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-13", streak=5, total_games=20)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["total_games"] == 21

    def test_total_correct_increments_by_score(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-13", streak=5, total_correct=50)
        data = _post_score(client, game_date="2026-04-14", score=8).json()
        assert data["total_correct"] == 58


class TestSameDayReplay:
    def test_streak_unchanged(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-14", streak=7)
        data = _post_score(client, game_date="2026-04-14", score=3).json()
        assert data["streak"] == 7

    def test_total_games_unchanged(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-14", streak=5, total_games=20)
        data = _post_score(client, game_date="2026-04-14", score=9).json()
        assert data["total_games"] == 20

    def test_total_correct_unchanged(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-14", streak=5, total_correct=80)
        data = _post_score(client, game_date="2026-04-14", score=10).json()
        assert data["total_correct"] == 80


class TestBrokenStreak:
    def test_streak_resets_to_one(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-10", streak=20)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["streak"] == 1

    def test_best_streak_preserved_after_break(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-10", streak=20, best_streak=20)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["best_streak"] == 20

    def test_total_games_still_increments_on_break(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = \
            _streak_row("2026-04-01", streak=10, total_games=15)
        data = _post_score(client, game_date="2026-04-14").json()
        assert data["total_games"] == 16


class TestValidation:
    def test_missing_score_returns_422(self, client):
        resp = client.post("/scores", json={
            "user_id": "u1",
            "game_date": "2026-04-14",
        })
        assert resp.status_code == 422

    def test_missing_user_id_returns_422(self, client):
        resp = client.post("/scores", json={
            "score": 7,
            "game_date": "2026-04-14",
        })
        assert resp.status_code == 422

    def test_missing_game_date_returns_422(self, client):
        resp = client.post("/scores", json={
            "user_id": "u1",
            "score": 7,
        })
        assert resp.status_code == 422

    def test_invalid_score_type_returns_422(self, client):
        resp = client.post("/scores", json={
            "user_id": "u1",
            "score": "not-a-number",
            "game_date": "2026-04-14",
        })
        assert resp.status_code == 422

    def test_username_defaults_to_ninja(self, client_with_mock):
        client, sb = client_with_mock
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        # No username in payload — should not raise
        resp = client.post("/scores", json={
            "user_id": "u1",
            "score": 5,
            "game_date": "2026-04-14",
        })
        assert resp.status_code == 200
