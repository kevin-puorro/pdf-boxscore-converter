"""PDF text and table extraction using pdfplumber."""

from typing import Any
import pdfplumber
import re


def extract_text_from_pdf(pdf_path: str) -> list[str]:
    """Extract text from all pages of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of text strings, one per page
    """
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return pages_text


def find_play_by_play_section(pages_text: list[str]) -> tuple[int, str]:
    """Find where play-by-play section starts in PDF.
    
    Args:
        pages_text: List of text strings, one per page
    
    Returns:
        Tuple of (start_page_index, combined_play_by_play_text)
        Returns (-1, "") if play-by-play section not found
    """
    # Keywords that indicate play-by-play section
    play_by_play_keywords = [
        "Play By Play",
        "Play-by-Play",
        "1st and 10 at",
        "2nd and",
        "3rd and",
        "4th and"
    ]
    
    combined_text = ""
    start_page = -1
    
    for i, page_text in enumerate(pages_text):
        # Check if this page contains play-by-play indicators
        has_play_by_play = any(keyword in page_text for keyword in play_by_play_keywords)
        
        if has_play_by_play:
            if start_page == -1:
                start_page = i
            
            # Combine text from play-by-play pages
            combined_text += page_text + "\n"
    
    if start_page == -1:
        return (-1, "")
    
    return (start_page, combined_text)


def extract_tables_from_pdf(pdf_path: str) -> list[list[list[str]]]:
    """Extract tables from all pages of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of tables, where each table is a list of rows (lists of strings)
    """
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)
    return all_tables


def extract_play_by_play_text(pdf_path: str) -> list[str]:
    """Extract play-by-play text from PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of play descriptions as strings
    """
    plays = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Play-by-play starts with "1st and 10" patterns
            if text and ("1st and 10" in text or "Play By Play" in text):
                # TODO: Implement parsing logic to split into individual plays
                plays.append(text)
    return plays


def extract_basic_play_data(pdf_path: str) -> list[dict[str, Any]]:
    """Extract basic play data from PDF (Phase 1).
    
    This function orchestrates the Phase 1 extraction process:
    1. Extract all text from PDF
    2. Find play-by-play section
    3. Split into individual plays
    4. Extract basic fields: down, distance, los, playType, yds, PlayDesc
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of dictionaries, each containing basic play data:
        {
            "down": int | None,
            "dist": int | None,
            "los": int | None,
            "playType": str | None,
            "yds": int | None,
            "PlayDesc": str
        }
    """
    from parsers.stats_parser import extract_team_abbreviations, extract_game_metadata
    from parsers.play_parser import (
        split_into_play_strings,
        extract_down_and_distance,
        extract_play_type,
        extract_yards,
        extract_field_position,
        detect_possession_change
    )
    
    # Step 1: Extract all text
    pages_text = extract_text_from_pdf(pdf_path)
    if not pages_text:
        return []
    
    # Step 2: Find play-by-play section
    start_page, play_by_play_text = find_play_by_play_section(pages_text)
    if start_page == -1:
        return []
    
    # Step 3: Extract team abbreviations and game metadata
    team_abbreviations = extract_team_abbreviations(pages_text)
    game_metadata = extract_game_metadata(pages_text)
    
    # Get team names for possession tracking
    # Determine which team abbreviations correspond to home/away
    # This is a simplified approach - in Phase 2 we'll refine this
    team_list = list(team_abbreviations.keys())
    away_team_abbrev = team_list[0] if len(team_list) > 0 else None
    home_team_abbrev = team_list[1] if len(team_list) > 1 else None
    
    # Step 4: Split into individual play strings
    play_strings = split_into_play_strings(play_by_play_text)
    
    # Step 5: Extract basic data from each play
    plays_data = []
    current_possession = None  # Track which team has the ball (abbreviation)
    
    for play_text in play_strings:
        # Extract basic fields
        down, dist, is_goal_to_go = extract_down_and_distance(play_text)
        play_type = extract_play_type(play_text)
        yds = extract_yards(play_text)
        
        # Extract field position (needs team abbreviations and possession)
        # For now, we'll try to infer possession from field position
        # If we see "at UWL31" and UWL is in abbreviations, assume UWL has ball
        los = extract_field_position(play_text, team_abbreviations, current_possession)
        
        # Handle goal-to-go situations: distance should equal LOS
        # Works for 1st and GOAL, 2nd and GOAL, 3rd and GOAL, 4th and GOAL
        if is_goal_to_go:
            # For goal-to-go, we need to find the LOS that corresponds to the GOAL
            # Look for pattern: "Xst/nd/rd/th and GOAL at TEAM##"
            goal_pattern = r'(\d+)(?:st|nd|rd|th)\s+and\s+GOAL\s+at\s+([A-Z]+)(\d+)'
            goal_match = re.search(goal_pattern, play_text, re.IGNORECASE)
            
            if goal_match:
                # Found explicit goal-to-go with field position
                goal_los_abbrev = goal_match.group(2)
                goal_los_yard = int(goal_match.group(3))
                
                # Convert to 1-100 scale (distance to opponent's endzone)
                if current_possession and goal_los_abbrev == current_possession:
                    # Own territory: at own X → LOS = 100 - X
                    los = 100 - goal_los_yard
                elif current_possession and goal_los_abbrev != current_possession:
                    # Opponent territory: at opponent's X → LOS = X
                    los = goal_los_yard
                else:
                    # No possession info, try to infer
                    if goal_los_abbrev in team_abbreviations:
                        # Assume own territory
                        los = 100 - goal_los_yard
                    else:
                        # Assume opponent territory
                        los = goal_los_yard
                
                # Set distance equal to LOS for goal-to-go
                dist = los
            elif los is not None:
                # We have LOS from regular extraction, use it
                dist = los
            else:
                # Try to extract LOS one more time
                los = extract_field_position(play_text, team_abbreviations, current_possession)
                if los is not None:
                    dist = los
        
        # Update possession if we can infer it from field position
        # Look for field position pattern: "at TEAM##"
        field_pos_match = re.search(r'at ([A-Z]+)(\d+)', play_text)
        if field_pos_match:
            abbrev = field_pos_match.group(1)
            if abbrev in team_abbreviations:
                # If we don't have possession tracked yet, set it
                if not current_possession:
                    current_possession = abbrev
        
        # Detect possession changes (turnovers, punts, kickoffs, etc.)
        new_possession = detect_possession_change(
            play_text, play_type, current_possession, team_abbreviations
        )
        if new_possession:
            current_possession = new_possession
        
        # Check for 4th down failure (turnover on downs)
        # If it's 4th down and the play didn't result in a first down or score
        if down == 4 and current_possession:
            # Check if play resulted in first down or score
            # If not, it's a turnover on downs
            is_first_down = False
            is_score = False
            
            play_text_lower = play_text.lower()
            if "first down" in play_text_lower or "touchdown" in play_text_lower:
                is_first_down = True
            if "touchdown" in play_text_lower or "field goal" in play_text_lower:
                is_score = True
            
            # If it's 4th down, not a first down, and not a score, it's turnover on downs
            # Exception: punts are already handled by detect_possession_change
            if not is_first_down and not is_score and play_type != "PUNT":
                # Find the other team
                for abbrev in team_abbreviations.keys():
                    if abbrev != current_possession:
                        current_possession = abbrev
                        break
        
        # Determine which team is on defense (after all possession changes)
        defense_team_abbrev = None
        if current_possession:
            for abbrev in team_abbreviations.keys():
                if abbrev != current_possession:
                    defense_team_abbrev = abbrev
                    break
        
        # Create play data dictionary
        play_data = {
            "down": down,
            "dist": dist,
            "los": los,
            "playType": play_type,
            "yds": yds,
            "possessionAbbrev": current_possession,  # Team abbreviation with the ball
            "defenseAbbrev": defense_team_abbrev,  # Defense team abbreviation
            "PlayDesc": play_text  # Store exact raw text
        }
        
        plays_data.append(play_data)
    
    return plays_data

