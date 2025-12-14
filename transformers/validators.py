"""Data validation rules for parsed data."""

from typing import Any


# Valid play types
VALID_PLAY_TYPES = [
    "RUSH", "PASS", "PUNT", "KICKOFF", 
    "FIELD GOAL", "PAT", "PENALTY", "TIMEOUT", "SAFETY"
]


def validate_yards(yards: int) -> bool:
    """Validate yards are in realistic range.
    
    Args:
        yards: Yards gained/lost
    
    Returns:
        True if valid, False otherwise
    """
    return -99 <= yards <= 99


def validate_quarter(quarter: int) -> bool:
    """Validate quarter number.
    
    Args:
        quarter: Quarter number (1-4, 5 for OT)
    
    Returns:
        True if valid, False otherwise
    """
    return 1 <= quarter <= 5


def validate_down(down: int | None) -> bool:
    """Validate down number.
    
    Args:
        down: Down number (1-4) or None
    
    Returns:
        True if valid, False otherwise
    """
    return down is None or down in [1, 2, 3, 4]


def validate_score(score: int) -> bool:
    """Validate score is in realistic range.
    
    Args:
        score: Team score
    
    Returns:
        True if valid, False otherwise
    """
    return 0 <= score <= 100


def validate_line_of_scrimmage(los: int) -> bool:
    """Validate line of scrimmage is in bounds.
    
    Args:
        los: Line of scrimmage (1-100)
    
    Returns:
        True if valid, False otherwise
    """
    return 1 <= los <= 100


def validate_play_type(play_type: str) -> bool:
    """Validate play type is recognized.
    
    Args:
        play_type: Play type string
    
    Returns:
        True if valid, False otherwise
    """
    return play_type in VALID_PLAY_TYPES


def validate_play(play_data: dict[str, Any]) -> list[str]:
    """Validate a play's data and return list of errors.
    
    Args:
        play_data: Dictionary containing play data
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if 'yards' in play_data:
        if not validate_yards(play_data['yards']):
            errors.append(f"Yards out of range: {play_data['yards']}")
    
    if 'quarter' in play_data:
        if not validate_quarter(play_data['quarter']):
            errors.append(f"Invalid quarter: {play_data['quarter']}")
    
    if 'down' in play_data:
        if not validate_down(play_data['down']):
            errors.append(f"Invalid down: {play_data['down']}")
    
    if 'playType' in play_data:
        if not validate_play_type(play_data['playType']):
            errors.append(f"Invalid play type: {play_data['playType']}")
    
    return errors

