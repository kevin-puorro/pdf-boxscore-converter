"""Parse box score statistics from PDF."""

from typing import Any
import re
from datetime import datetime


def parse_scoring_summary(text: str) -> dict[str, Any]:
    """Parse scoring summary section from PDF text.
    
    Args:
        text: Text content from PDF containing scoring summary
    
    Returns:
        Dictionary with scoring summary data
    """
    # TODO: Implement scoring summary parsing
    return {}


def parse_team_statistics(text: str) -> dict[str, Any]:
    """Parse team statistics section from PDF text.
    
    Args:
        text: Text content from PDF containing team statistics
    
    Returns:
        Dictionary with team statistics data
    """
    # TODO: Implement team statistics parsing
    return {}


def extract_game_metadata(pages_text: list[str]) -> dict[str, Any]:
    """Extract game metadata from first page of PDF.
    
    Args:
        pages_text: List of text strings, one per page
    
    Returns:
        Dictionary with game metadata:
        - date: str (YYYY-MM-DD format)
        - home: str (home team name)
        - away: str (away team name)
        - venue: str (venue name)
        - seasonYear: int
    """
    if not pages_text:
        return {}
    
    first_page = pages_text[0]
    metadata = {}
    
    # Extract date - look for patterns like "9/13/2025" or "11/01/2025"
    date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
    date_match = re.search(date_pattern, first_page)
    if date_match:
        month, day, year = date_match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            metadata['date'] = date_obj.strftime('%Y-%m-%d')
            metadata['seasonYear'] = int(year)
        except ValueError:
            pass
    
    # Extract team names - pattern: "Team A -vs- Team B"
    vs_pattern = r'([^-]+)\s*-vs-\s*([^-]+)'
    vs_match = re.search(vs_pattern, first_page)
    if vs_match:
        team1 = vs_match.group(1).strip()
        team2 = vs_match.group(2).strip()
        
        # Remove records in parentheses like "(1-0)" or "(5-3 , 3-2)"
        team1 = re.sub(r'\([^)]+\)', '', team1).strip()
        team2 = re.sub(r'\([^)]+\)', '', team2).strip()
        
        # First team listed is typically away, second is home
        # But we'll determine this from score box position
        metadata['away'] = team1
        metadata['home'] = team2
    
    # Extract venue - pattern: "at City, State (Venue)" or "at City, State"
    venue_pattern = r'at\s+([^(\n]+(?:\([^)]+\))?)'
    venue_match = re.search(venue_pattern, first_page)
    if venue_match:
        venue = venue_match.group(1).strip()
        metadata['venue'] = venue
    
    return metadata


def extract_team_abbreviations(pages_text: list[str]) -> dict[str, str]:
    """Extract team abbreviations from PDF.
    
    Team listed first in header is away team (top of score box).
    Team listed second is home team (bottom of score box).
    
    Args:
        pages_text: List of text strings, one per page
    
    Returns:
        Dictionary mapping abbreviations to team names:
        {"UWL": "Wis.-La Crosse", "CMU": "Carnegie Mellon"}
    """
    if not pages_text:
        return {}
    
    first_page = pages_text[0]
    abbreviations = {}
    
    # Extract team names from header
    vs_pattern = r'([^-]+)\s*-vs-\s*([^-]+)'
    vs_match = re.search(vs_pattern, first_page)
    if not vs_match:
        return {}
    
    team1 = re.sub(r'\([^)]+\)', '', vs_match.group(1)).strip()
    team2 = re.sub(r'\([^)]+\)', '', vs_match.group(2)).strip()
    
    # Look for abbreviations in play-by-play text
    # Common patterns: "at UWL31", "at CMU44", etc.
    play_by_play_text = " ".join(pages_text[6:] if len(pages_text) > 6 else pages_text)
    
    # Find all field position patterns: "at ABBREV##"
    field_pos_pattern = r'at ([A-Z]{2,4})(\d+)'
    matches = re.findall(field_pos_pattern, play_by_play_text)
    
    # Get unique abbreviations
    unique_abbrevs = set(match[0] for match in matches)
    
    # Try to map abbreviations to team names
    # Strategy: Look for abbreviations that appear near team names in play-by-play
    # Or use common patterns (first 3-4 letters of team name)
    
    # Simple heuristic: Try to match first few letters
    for abbrev in unique_abbrevs:
        # Check if abbreviation matches start of team name
        team1_abbrev = "".join([c for c in team1 if c.isupper()])[:len(abbrev)]
        team2_abbrev = "".join([c for c in team2 if c.isupper()])[:len(abbrev)]
        
        if abbrev.upper() in team1_abbrev.upper() or team1_abbrev.upper() in abbrev.upper():
            abbreviations[abbrev] = team1
        elif abbrev.upper() in team2_abbrev.upper() or team2_abbrev.upper() in abbrev.upper():
            abbreviations[abbrev] = team2
        else:
            # If no match, we'll need to infer from context
            # For now, store as unknown
            abbreviations[abbrev] = f"Unknown_{abbrev}"
    
    return abbreviations

