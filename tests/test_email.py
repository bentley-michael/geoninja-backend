"""
Tests for email template helper functions (main.py lines 52–107).

These are pure Python functions with no I/O — no mocking needed.
They are the cheapest tests to write and the fastest to run.
"""

import pytest


class TestStreakReminderHtml:
    def test_contains_streak_count(self, main_module):
        html = main_module.streak_reminder_html(7, 15)
        assert "7 Day Streak" in html

    def test_contains_best_streak(self, main_module):
        html = main_module.streak_reminder_html(7, 15)
        assert "Best: 15 days" in html

    def test_zero_streak_renders(self, main_module):
        html = main_module.streak_reminder_html(0, 0)
        assert "0 Day Streak" in html

    def test_large_streak_renders(self, main_module):
        html = main_module.streak_reminder_html(365, 365)
        assert "365 Day Streak" in html

    def test_starts_with_doctype(self, main_module):
        html = main_module.streak_reminder_html(5, 10)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_contains_play_link(self, main_module):
        html = main_module.streak_reminder_html(5, 10)
        assert "geographyninja.com" in html

    def test_contains_unsubscribe_link(self, main_module):
        """CAN-SPAM compliance: unsubscribe link must be present."""
        html = main_module.streak_reminder_html(5, 10)
        assert "Unsubscribe" in html

    def test_streak_and_best_are_distinct_when_different(self, main_module):
        html = main_module.streak_reminder_html(3, 20)
        assert "3 Day Streak" in html
        assert "Best: 20 days" in html


class TestWelcomeHtml:
    def test_starts_with_doctype(self, main_module):
        html = main_module.welcome_html()
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_contains_welcome_heading(self, main_module):
        html = main_module.welcome_html()
        assert "Welcome to Geography" in html

    def test_contains_play_link(self, main_module):
        html = main_module.welcome_html()
        assert "geographyninja.com" in html

    def test_contains_unsubscribe_link(self, main_module):
        """CAN-SPAM compliance: unsubscribe link must be present."""
        html = main_module.welcome_html()
        assert "Unsubscribe" in html

    def test_not_empty(self, main_module):
        html = main_module.welcome_html()
        assert len(html) > 100

    def test_is_deterministic(self, main_module):
        """welcome_html takes no args and should return identical output each call."""
        assert main_module.welcome_html() == main_module.welcome_html()
