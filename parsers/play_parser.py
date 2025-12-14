"""Parse individual play descriptions from play-by-play text."""

from typing import Optional, Any
import re
from utils.patterns import (
    DOWN_DISTANCE_PATTERN,
    PLAY_START_PATTERN,
    DRIVE_SUMMARY_PATTERN,
    DRIVE_POSSESSION_PATTERN,
    DRIVE_START_PATTERN,
    FIELD_POSITION_PATTERN
)


def is_play_line(line: str) -> bool:
    """Determine if a line is a play description.
    
    Args:
        line: Text line to check
    
    Returns:
        True if line appears to be a play description
    """
    # Must contain down/distance pattern (doesn't have to be at start)
    # This handles cases like "1st and GOAL at CMU09 ... drive start"
    if PLAY_START_PATTERN.search(line) or DOWN_DISTANCE_PATTERN.search(line):
        return True
    return False


def is_drive_summary(line: str) -> bool:
    """Identify drive summary lines that should be skipped.
    
    Only skip lines that are pure drive summaries, not actual plays
    that happen to mention "drive start".
    
    Args:
        line: Text line to check
    
    Returns:
        True if line is a drive summary (should be skipped)
    """
    # Skip "Total X plays" summaries
    if DRIVE_SUMMARY_PATTERN.search(line):
        return True
    
    # Skip "Time of Possession" lines
    if DRIVE_POSSESSION_PATTERN.search(line):
        return True
    
    # Skip pure drive start markers like "Team Name at 03:34" or "Team Name drive start at 03:34"
    # But NOT if it's part of an actual play (e.g., "1st and 10 at CMU27 ... drive start")
    if "drive start" in line.lower():
        # Only skip if it doesn't start with a down/distance pattern
        # If it has a play pattern, it's a valid play
        if not PLAY_START_PATTERN.search(line):
            return True
    
    # Skip team name at time patterns that aren't plays
    # Pattern: "Team Name at HH:MM" without a play pattern
    if DRIVE_START_PATTERN.search(line) and not PLAY_START_PATTERN.search(line):
        # Check if it's just a team name and time, not a play
        if not any(keyword in line.lower() for keyword in ["rush", "pass", "punt", "kick", "field goal", "penalty"]):
            return True
    
    return False


def split_into_play_strings(play_by_play_text: str) -> list[str]:
    """Split play-by-play text into individual play descriptions.
    
    Args:
        play_by_play_text: Combined text from play-by-play section
    
    Returns:
        List of play description strings
    """
    plays = []
    lines = play_by_play_text.split('\n')
    
    current_play = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip drive summaries
        if is_drive_summary(line):
            # If we have accumulated a play, save it
            if current_play:
                plays.append(' '.join(current_play))
                current_play = []
            continue
        
        # Check if this line starts a new play
        if is_play_line(line):
            # If we have accumulated a play, save it first
            if current_play:
                plays.append(' '.join(current_play))
            # Start new play
            current_play = [line]
        elif current_play:
            # Continue accumulating current play (multi-line play)
            current_play.append(line)
        # If no current play and not a play line, skip (headers, etc.)
    
    # Don't forget the last play
    if current_play:
        plays.append(' '.join(current_play))
    
    return plays


def extract_down_and_distance(play_text: str) -> tuple[Optional[int], Optional[int], bool]:
    """Extract down and distance to go from play text.
    
    Looks for the first occurrence of "Xst/nd/rd/th and Y" pattern in the play text.
    This should be at the start of the play description.
    
    Args:
        play_text: Play description text
    
    Returns:
        Tuple of (down, distance, is_goal_to_go)
        - down: Down number (1-4) or None
        - distance: Distance to first down or None
        - is_goal_to_go: True if "GOAL" was found (goal-to-go situation)
    """
    # Find all matches to see if there are multiple
    all_matches = list(DOWN_DISTANCE_PATTERN.finditer(play_text))
    
    if not all_matches:
        return (None, None, False)
    
    # Use the first match (should be at the start of the play)
    match = all_matches[0]
    
    down = int(match.group(1))
    distance_str = match.group(2).upper()
    
    # Check for "GOAL" instead of distance
    if distance_str == "GOAL":
        return (down, None, True)
    else:
        try:
            distance = int(distance_str)
            return (down, distance, False)
        except (ValueError, IndexError):
            return (down, None, False)


def extract_play_type(play_text: str) -> Optional[str]:
    """Identify play type from play description.
    
    Args:
        play_text: Play description text
    
    Returns:
        Play type string (RUSH, PASS, PUNT, etc.) or None
    """
    play_text_lower = play_text.lower()
    
    # Check in order of specificity (most specific first)
    # Check for kick attempt - these are extra point attempts (XPA)
    if "kick attempt" in play_text_lower:
        return "XPA"
    if "field goal" in play_text_lower or "fg" in play_text_lower:
        return "FIELD GOAL"
    # PAT logic removed per user request
    if "kickoff" in play_text_lower:
        return "KICKOFF"
    if "punt" in play_text_lower:
        return "PUNT"
    if "penalty" in play_text_lower:
        return "PENALTY"
    if "timeout" in play_text_lower:
        return "TIMEOUT"
    if "safety" in play_text_lower:
        return "SAFETY"
    # Check for sack - sacks are pass plays
    if "sacked" in play_text_lower or "sack" in play_text_lower:
        return "PASS"
    if "pass" in play_text_lower:
        return "PASS"
    if "rush" in play_text_lower or "run" in play_text_lower:
        return "RUSH"
    
    return None


def extract_yards(play_text: str) -> Optional[int]:
    """Extract yards gained/lost from play text.
    
    Args:
        play_text: Play description text
    
    Returns:
        Yards (negative for loss) or 0 for incomplete passes, or None if not found
    """
    play_text_lower = play_text.lower()
    
    # Check for incomplete pass - set to 0
    if "pass incomplete" in play_text_lower or "incomplete" in play_text_lower:
        return 0
    
    # Pattern 1: "for X yards" or "for -X yards"
    yards_pattern1 = r'for\s+(-?\d+)\s+yards?'
    match = re.search(yards_pattern1, play_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Pattern 2: "for loss of X yard(s)"
    loss_pattern = r'for\s+loss\s+of\s+(\d+)\s+yard'
    match = re.search(loss_pattern, play_text, re.IGNORECASE)
    if match:
        return -int(match.group(1))
    
    # Pattern 3: "sacked for loss of X yards" - already handled by pattern 1, but explicit check
    sack_pattern = r'sacked\s+for\s+(?:a\s+)?loss\s+of\s+(\d+)\s+yards?'
    match = re.search(sack_pattern, play_text, re.IGNORECASE)
    if match:
        return -int(match.group(1))
    
    # Pattern 4: "gain to" - would need to calculate from field position
    # This is more complex, handle in Phase 2
    
    return None


def detect_possession_change(
    play_text: str,
    play_type: Optional[str],
    current_possession: Optional[str],
    team_abbreviations: dict[str, str]
) -> Optional[str]:
    """Detect if possession changes on this play.
    
    Possession changes on:
    - Turnovers (interceptions, fumbles recovered by opponent)
    - Punts (ball goes to receiving team)
    - Kickoffs (ball goes to receiving team)
    - Field goal attempts (if missed, goes to opponent)
    - Change of possession on downs (4th down failure)
    
    Args:
        play_text: Play description text
        play_type: Type of play (PASS, PUNT, etc.)
        current_possession: Current team with possession (abbreviation)
        team_abbreviations: Dict mapping abbreviations to team names
    
    Returns:
        New team with possession (abbreviation) if possession changed, None otherwise
    """
    play_text_lower = play_text.lower()
    
    if not current_possession:
        return None
    
    # Get the other team (defense becomes offense)
    other_team = None
    for abbrev in team_abbreviations.keys():
        if abbrev != current_possession:
            other_team = abbrev
            break
    
    if not other_team:
        return None
    
    # Check for turnovers
    if "intercepted" in play_text_lower or "interception" in play_text_lower:
        # Interception - possession changes
        return other_team
    
    if "fumble" in play_text_lower and "recovered" in play_text_lower:
        # Check if fumble was recovered by the other team
        # Look for pattern: "recovered by [TEAM]" or "recovered by [TEAM abbreviation]"
        for abbrev in team_abbreviations.keys():
            if abbrev != current_possession:
                # Check if this team recovered
                if abbrev.lower() in play_text_lower or team_abbreviations[abbrev].lower() in play_text_lower:
                    return abbrev
    
    # Check for punts - possession changes to receiving team
    if play_type == "PUNT":
        return other_team
    
    # Check for kickoffs - possession changes to receiving team
    if play_type == "KICKOFF":
        return other_team
    
    # Check for missed field goals - possession changes (if not made)
    if play_type == "FIELD GOAL":
        if "no good" in play_text_lower or "missed" in play_text_lower or "blocked" in play_text_lower:
            return other_team
    
    # Check for 4th down failure (turnover on downs)
    # This is trickier - we'd need to track down/distance and see if it's 4th down
    # For now, we'll handle this in the main loop
    
    return None


def extract_field_position(
    play_text: str,
    team_abbreviations: dict[str, str],
    current_possession: Optional[str] = None
) -> Optional[int]:
    """Extract line of scrimmage in 1-100 format.
    
    LOS represents distance from offense's current position to opponent's endzone.
    - If at opponent's X yard line (e.g., "at CMU06" when UWL has ball) → LOS = 6
    - If at own X yard line (e.g., "at UWL06" when UWL has ball) → LOS = 100 - 6 = 94
    
    Args:
        play_text: Play description text
        team_abbreviations: Dict mapping abbreviations to team names
        current_possession: Current team with possession (abbreviation)
    
    Returns:
        Line of scrimmage (1-100) or None if not found
    """
    match = FIELD_POSITION_PATTERN.search(play_text)
    if not match:
        return None
    
    abbrev = match.group(1)
    yard_line = int(match.group(2))
    
    # Determine if this is own territory or opponent territory
    # LOS = distance to opponent's endzone
    
    if current_possession and abbrev == current_possession:
        # Own territory: at own X yard line
        # Distance to opponent's endzone = 100 - X
        # Example: at own 6 → LOS = 94 (94 yards to opponent's endzone)
        return 100 - yard_line
    elif current_possession and abbrev != current_possession:
        # Opponent territory: at opponent's X yard line
        # Distance to opponent's endzone = X
        # Example: at opponent's 6 → LOS = 6 (6 yards to opponent's endzone)
        return yard_line
    else:
        # No possession info - try to infer from context
        # If we see the abbreviation in team_abbreviations, assume it's the team with ball
        # This is a fallback for when possession isn't tracked yet
        if abbrev in team_abbreviations:
            # Assume this team has the ball (own territory)
            return 100 - yard_line
        else:
            # Unknown, use as-is (will be corrected when possession is determined)
            return yard_line


def parse_play_description(
    play_text: str,
    quarter: int,
    game_clock: str
) -> dict[str, Any]:
    """Parse a single play description into structured data.
    
    Args:
        play_text: Raw play description from PDF
        quarter: Quarter number (1-4, 5 for OT)
        game_clock: Time remaining in quarter (MM:SS format)
    
    Returns:
        Dictionary containing parsed play data with keys:
        - play_type: str (RUSH, PASS, PUNT, etc.)
        - yards: int
        - down: int
        - distance: int
        - etc.
    
    Raises:
        ValueError: If play_text cannot be parsed
    """
    # TODO: Implement play parsing logic
    return {}


def parse_rush_play(play_text: str) -> Optional[dict]:
    """Parse a rushing play description.
    
    Args:
        play_text: Raw play description
    
    Returns:
        Dictionary with parsed rush play data, or None if not a rush play
    """
    pattern = r'\((\d{1,2}:\d{2})\).*?([A-Z][a-z]+,[A-Z][a-z]+) rush(?:es)? .*? for (-?\d+) yards?'
    match = re.search(pattern, play_text)
    
    if match:
        return {
            'gameClock': match.group(1),
            'rusher': match.group(2),
            'yards': int(match.group(3)),
            'playType': 'RUSH'
        }
    return None

