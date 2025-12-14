"""Unit tests for transformer modules."""

import pytest
from transformers.validators import validate_yards, validate_quarter, validate_down


def test_validate_yards():
    """Test yards validation."""
    assert validate_yards(10) is True
    assert validate_yards(-5) is True
    assert validate_yards(0) is True
    assert validate_yards(100) is False  # Out of range
    assert validate_yards(-100) is False  # Out of range


def test_validate_quarter():
    """Test quarter validation."""
    assert validate_quarter(1) is True
    assert validate_quarter(4) is True
    assert validate_quarter(5) is True  # Overtime
    assert validate_quarter(0) is False
    assert validate_quarter(6) is False


def test_validate_down():
    """Test down validation."""
    assert validate_down(1) is True
    assert validate_down(4) is True
    assert validate_down(None) is True
    assert validate_down(5) is False
    assert validate_down(0) is False

