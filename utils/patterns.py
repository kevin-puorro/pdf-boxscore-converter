"""Regex patterns for parsing play descriptions and PDF text."""

import re

# Clock time pattern: (15:00) or (4:29)
CLOCK_PATTERN = re.compile(r'\((\d{1,2}:\d{2})\)')

# Formation patterns
FORMATION_PATTERN = re.compile(r'(No Huddle|Shotgun|No Huddle-Shotgun)')

# Player name pattern: LastName,FirstName
PLAYER_NAME_PATTERN = re.compile(r'([A-Z][a-z]+,[A-Z][a-z]+)')

# Yards pattern: for 11 yards or for -5 yards
YARDS_PATTERN = re.compile(r'for (-?\d+) yards?')

# Down and distance pattern: 1st and 10, 2nd and 5, etc.
# Also handles "1st and GOAL" cases
DOWN_DISTANCE_PATTERN = re.compile(r'(\d)(?:st|nd|rd|th) and (\d+|GOAL)', re.IGNORECASE)

# Field position pattern: at UWL31, at CMU44, etc. (team abbreviation + yard line)
FIELD_POSITION_PATTERN = re.compile(r'at ([A-Z]+)(\d+)')

# Down and distance with "at" - used to identify play starts
PLAY_START_PATTERN = re.compile(r'(\d+)(?:st|nd|rd|th) and \d+ at')

# Drive summary patterns
DRIVE_SUMMARY_PATTERN = re.compile(r'Total \d+ plays')
DRIVE_POSSESSION_PATTERN = re.compile(r'Time of Possession')
DRIVE_START_PATTERN = re.compile(r'at \d{1,2}:\d{2}')

# Play type patterns
RUSH_PATTERN = re.compile(r'rush(?:es)?')
PASS_PATTERN = re.compile(r'pass')
PUNT_PATTERN = re.compile(r'punt')
KICKOFF_PATTERN = re.compile(r'kickoff')
FIELD_GOAL_PATTERN = re.compile(r'field goal')
PAT_PATTERN = re.compile(r'PAT|point after')
PENALTY_PATTERN = re.compile(r'penalty')
TIMEOUT_PATTERN = re.compile(r'timeout')
SAFETY_PATTERN = re.compile(r'safety')

