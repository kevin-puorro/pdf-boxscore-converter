"""Unit tests for parser modules."""

import pytest
from parsers.play_parser import parse_rush_play


def test_parse_rush_play():
    """Test parsing a rush play description."""
    play_text = "(15:00) (BAY 07) Bryson Washington rushes for 11 yards. Tackle by (HOU D98) Myles Parker."
    result = parse_rush_play(play_text)
    
    assert result is not None
    assert result['playType'] == 'RUSH'
    assert result['yards'] == 11
    assert result['gameClock'] == '15:00'


def test_parse_rush_play_negative_yards():
    """Test parsing a rush play with negative yards."""
    play_text = "(10:30) Smith,John rushes for -3 yards"
    result = parse_rush_play(play_text)
    
    assert result is not None
    assert result['yards'] == -3

