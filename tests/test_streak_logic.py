"""
Pure unit tests for the streak calculation formula (main.py lines 169–172).

These tests exercise the logic directly without HTTP or database calls.
The formulas under test:
  new_streak = current_streak + 1 if last == yesterday else (current_streak if last == today else 1)
  best       = max(row.best_streak, new_streak)
  total_games   += 0 if last == today else 1
  total_correct += 0 if last == today else score
"""

TODAY = "2026-04-14"
YESTERDAY = "2026-04-13"
TWO_DAYS_AGO = "2026-04-12"
LONG_AGO = "2026-01-01"


def _compute_streak(last, current_streak, best_streak):
    """Mirror of the streak formula in main.py:169."""
    new_streak = (
        current_streak + 1 if last == YESTERDAY
        else (current_streak if last == TODAY else 1)
    )
    best = max(best_streak, new_streak)
    return new_streak, best


def _compute_totals(last, total_games, total_correct, score):
    """Mirror of the totals formula in main.py:171–172."""
    games_delta = 0 if last == TODAY else 1
    correct_delta = 0 if last == TODAY else score
    return total_games + games_delta, total_correct + correct_delta


class TestStreakCalculation:
    def test_consecutive_day_increments_streak(self):
        new_streak, _ = _compute_streak(YESTERDAY, 5, 5)
        assert new_streak == 6

    def test_streak_of_one_extends_to_two_next_day(self):
        new_streak, _ = _compute_streak(YESTERDAY, 1, 1)
        assert new_streak == 2

    def test_same_day_replay_preserves_streak(self):
        new_streak, _ = _compute_streak(TODAY, 5, 5)
        assert new_streak == 5

    def test_broken_streak_two_days_ago_resets_to_one(self):
        new_streak, _ = _compute_streak(TWO_DAYS_AGO, 10, 10)
        assert new_streak == 1

    def test_very_long_gap_resets_to_one(self):
        new_streak, _ = _compute_streak(LONG_AGO, 99, 99)
        assert new_streak == 1

    def test_zero_streak_on_consecutive_day_becomes_one(self):
        # Edge case: streak was somehow 0 but last_played was yesterday
        new_streak, _ = _compute_streak(YESTERDAY, 0, 0)
        assert new_streak == 1

    def test_large_streak_continues(self):
        new_streak, _ = _compute_streak(YESTERDAY, 100, 100)
        assert new_streak == 101


class TestBestStreakTracking:
    def test_best_streak_updates_when_surpassed(self):
        _, best = _compute_streak(YESTERDAY, 10, 10)
        assert best == 11

    def test_best_streak_preserved_when_streak_breaks(self):
        _, best = _compute_streak(LONG_AGO, 20, 20)
        assert best == 20  # reset to 1 but best stays at 20

    def test_best_streak_preserved_on_same_day_replay(self):
        _, best = _compute_streak(TODAY, 5, 10)
        # streak stays 5, best was already 10
        assert best == 10

    def test_best_streak_not_decreased_below_current(self):
        # Scenario: current streak 5, old best was 3 (shouldn't happen, but defensive)
        _, best = _compute_streak(YESTERDAY, 5, 3)
        assert best == 6  # new_streak=6 > old best=3

    def test_best_streak_never_negative(self):
        _, best = _compute_streak(LONG_AGO, 0, 0)
        assert best >= 0


class TestTotalsAccumulation:
    def test_new_game_increments_games_and_correct(self):
        games, correct = _compute_totals(YESTERDAY, 5, 40, 7)
        assert games == 6
        assert correct == 47

    def test_same_day_replay_increments_neither(self):
        games, correct = _compute_totals(TODAY, 5, 40, 9)
        assert games == 5
        assert correct == 40

    def test_zero_score_still_increments_games(self):
        games, correct = _compute_totals(YESTERDAY, 5, 40, 0)
        assert games == 6
        assert correct == 40  # 0 added but games still bumped

    def test_perfect_score_increments_by_ten(self):
        games, correct = _compute_totals(YESTERDAY, 0, 0, 10)
        assert games == 1
        assert correct == 10

    def test_broken_streak_day_still_increments_totals(self):
        # Even if the streak resets, the game still counts toward totals
        games, correct = _compute_totals(LONG_AGO, 20, 150, 8)
        assert games == 21
        assert correct == 158

    def test_totals_start_from_zero_for_new_user(self):
        games, correct = _compute_totals(YESTERDAY, 0, 0, 5)
        assert games == 1
        assert correct == 5
