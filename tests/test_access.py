"""Tests for bot.access module."""

import pytest

from bot.access import is_user_allowed


@pytest.mark.parametrize(
    ("allowed_ids", "user_id", "expected"),
    [
        (None, 123, True),
        (set(), 123, True),
        ({123, 456}, 123, True),
        ({123, 456}, 789, False),
    ],
)
def test_is_user_allowed(allowed_ids: set[int] | None, user_id: int, expected: bool) -> None:
    assert is_user_allowed(user_id, allowed_ids) is expected
