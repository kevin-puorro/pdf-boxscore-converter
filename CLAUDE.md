# PDF Box Score to CSV Converter - Project Documentation

## Project Overview

**Goal:** Convert NCAA Division III football PDF box scores/play-by-play reports into structured CSV format matching Championship Analytics data schema.

**User Context:** Kevin is a Data Analyst at Championship Analytics with expertise in sports data, Python, SQL, and building automated data collection systems. This tool will streamline the process of converting unstructured game reports into analyzable data.

**Current Status:** Initial planning phase - need to build MVP

---

## Tech Stack (Production)

- **Framework:** Streamlit (Python web framework)
- **PDF Processing:** pdfplumber (superior table extraction vs PyPDF2)
- **Data Processing:** pandas, numpy
- **Text Parsing:** regex, potentially spaCy for NLP
- **Deployment:** Streamlit Cloud (free tier, can upgrade if needed)
- **Styling:** Custom CSS via st.markdown() for professional appearance
- **Caching:** Streamlit's @st.cache_data for performance

---

## Project Structure

```
pdf-boxscore-converter/
├── app.py                    # Streamlit main app
├── parsers/
│   ├── __init__.py
│   ├── pdf_extractor.py      # PDF text/table extraction
│   ├── play_parser.py        # Parse individual plays
│   ├── stats_parser.py       # Parse box score stats
│   └── drive_parser.py       # Parse drive chart
├── transformers/
│   ├── __init__.py
│   ├── csv_builder.py        # Build final CSV structure
│   ├── field_mapper.py       # Map PDF data to CSV columns
│   └── validators.py         # Data validation rules
├── utils/
│   ├── __init__.py
│   ├── patterns.py           # Regex patterns for parsing
│   └── helpers.py            # Utility functions
├── tests/
│   ├── test_parsers.py
│   └── test_transformers.py
├── sample_data/
│   ├── input_pdfs/          # Sample PDFs for testing
│   └── expected_outputs/    # Expected CSV outputs
├── CLAUDE.md                 # This file
├── requirements.txt
└── README.md
```

---

## Code Conventions

### Python Style
- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for all classes and functions (Google style)
- Maximum line length: 100 characters
- Use descriptive variable names (avoid abbreviations unless standard in sports analytics)

### Example Function Structure
```python
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
    pass
```

### Error Handling
- Use try/except blocks for PDF parsing (PDFs can be malformed)
- Log warnings for unparseable plays, don't crash
- Return None or empty dict for unparseable data, track in metadata
- Provide helpful error messages to users in Streamlit UI

---

## PDF Parsing Specifications

### Known PDF Format (from sample: UW-Oshkosh vs UW-La Crosse)

**Page Structure:**
- Page 1: Scoring Summary, Team Statistics
- Page 2-3: Individual Offense stats (Passing, Rushing, Receiving, Punting, Returns, Field Goals, Kickoffs)
- Page 4-5: Individual Defensive stats
- Page 6: Drive Chart
- Page 7+: Play-by-Play

### Play Description Patterns

**Standard Play Format:**
```
(CLOCK) (FORMATION) PLAYER action for YARDS. Additional context.
```

**Examples to Handle:**
```
"(15:00) (BAY 07) Bryson Washington rushes for 11 yards. Tackle by (HOU D98) Myles Parker."
"(14:42) No Huddle-Shotgun Haas,Kyle pass complete short to Rilling,Jack caught at Eagles30, for 6 yards"
"(04:29) Vera Trejo,Axel field goal attempt from 38 yards GOOD"
"(13:22) Stack,Michael kickoff 54 yards to the Titans11 muffed by Vallafskey,Ben"
```

### Regex Pattern Library (patterns.py)

Create patterns for:
- Clock time: `r'\((\d{1,2}:\d{2})\)'`
- Formation: `r'(No Huddle|Shotgun|No Huddle-Shotgun)'`
- Player names: `r'([A-Z][a-z]+,[A-Z][a-z]+)'`
- Yards: `r'for (-?\d+) yards?'`
- Play types: RUSH, PASS, PUNT, KICKOFF, FIELD GOAL, PENALTY, TIMEOUT, SAFETY
- Down/distance: `r'(\d)(?:st|nd|rd|th) and (\d+)'`

---

## CSV Output Specifications

### Target Schema (120+ columns)

**Critical Columns to Populate:**
1. **Identifiers** (auto-generate UUIDs or sequential IDs)
   - playId, gameId, uniqPlayId
   
2. **Game Context** (extract from PDF header)
   - date, seasonYear, week, home, away, venue
   - teamAbbrevName, opponentAbbrevName
   
3. **Play Situation** (parse from play description)
   - quarter, gameClock, down, dist, los (line of scrimmage)
   - playType, playTypePrecise
   
4. **Play Results**
   - yds (yards gained/lost)
   - teamCurrentScore, opponentCurrentScore
   - Sack, Interception, FumbleLost, Incomplete
   
5. **Drive Data** (aggregate from plays)
   - driveNumber, driveStartQuarter, drivePlays, driveYards
   - driveHowEnded (Touchdown, Field Goal, Punt, Turnover, etc.)

6. **Description**
   - PlayDesc (cleaned play description text)

**Columns to Leave Blank (require external data):**
- Advanced metrics: epa, wpa, startEp, startWp
- PFF/proprietary IDs: pffPlayId, pffGameId
- Broadcast IDs: espnEventId, sdrEventId

**Default Values:**
- league: "NCAA"
- poss/possession: Team with ball (parse from play)

---

## Data Validation Rules

### Required Validations (validators.py)

```python
# Yards validation
assert -99 <= yards <= 99, "Yards out of realistic range"

# Quarter validation
assert 1 <= quarter <= 5, "Invalid quarter (1-4, 5 for OT)"

# Down validation
assert down in [1, 2, 3, 4, None], "Invalid down"

# Score validation
assert 0 <= score <= 100, "Score out of realistic range"

# Field position validation
assert 1 <= los <= 100, "Line of scrimmage out of bounds"

# Play type validation
VALID_PLAY_TYPES = [
    "RUSH", "PASS", "PUNT", "KICKOFF", 
    "FIELD GOAL", "PAT", "PENALTY", "TIMEOUT", "SAFETY"
]
```

---

## Parsing Strategy

### Step-by-Step Processing

1. **Extract PDF Text**
   ```python
   # Use pdfplumber to maintain layout structure
   with pdfplumber.open(pdf_path) as pdf:
       for page in pdf.pages:
           text = page.extract_text()
           tables = page.extract_tables()
   ```

2. **Identify Sections**
   - Scoring Summary (look for "Scoring Summary" header)
   - Team Statistics (look for "Team Statistics" header)
   - Play-by-Play (look for quarter markers "1st and 10 at")

3. **Parse Game Metadata**
   - Team names from first line
   - Date, venue from header
   - Final score from scoring summary

4. **Parse Play-by-Play**
   - Split by play (each line starting with clock time)
   - Extract: quarter, clock, down, distance, play type, yards, players
   - Track running score throughout game

5. **Aggregate Drive Data**
   - Group plays by possession changes
   - Calculate drive stats (plays, yards, time, result)

6. **Build CSV**
   - Create one row per play
   - Populate all available columns
   - Fill in drive-level data for each play in drive

---

## Testing Approach

### Unit Tests
- Test each regex pattern individually
- Test play parser with known play descriptions
- Test field position calculations

### Integration Tests
- Test full PDF → CSV pipeline with sample PDF
- Compare output CSV to expected output
- Validate all required columns are populated

### Edge Cases to Handle
- Overtime plays (quarter 5)
- Safeties (2 points, special scoring)
- Penalty plays (no yards gained)
- Incomplete passes (0 yards)
- Muffed kicks/fumbles (complex possession changes)
- Two-point conversions

---

## Professional Streamlit Styling

### Custom CSS for Branding
```python
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #003015;  /* Championship Analytics green */
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 2rem;
    }
    .stDownloadButton>button {
        background-color: #00A651;
        color: white;
    }
    h1 {
        color: #003015;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)
```

### Professional Layout Structure
```python
# Header with logo/branding
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 NCAA Box Score Converter")
    st.caption("Convert PDF game reports to structured play-by-play CSV")
with col2:
    st.image("logo.png", width=100)  # Add Championship Analytics logo

# Clean sections with expanders
with st.expander("ℹ️ How to Use", expanded=False):
    st.write("""
    1. Upload a PDF box score from an NCAA D3 football game
    2. Review the parsed data preview
    3. Download the structured CSV file
    """)
```

### Data Preview Best Practices
- Use `st.dataframe()` with custom column config for better display
- Add metrics for quick stats (st.metric())
- Show parsing success rate prominently
- Color-code validation warnings (st.warning(), st.success())

### Performance Optimizations
```python
@st.cache_data
def process_pdf(pdf_file) -> pd.DataFrame:
    """Cache processed results to avoid re-parsing on reruns"""
    pass

# Use st.spinner for long operations
with st.spinner("Processing PDF... This may take 10-20 seconds"):
    result = process_pdf(uploaded_file)
```

---

## Streamlit UI Requirements

### Main Interface
```python
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="NCAA Box Score Converter",
    page_icon="🏈",
    layout="wide",  # Use full width
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""<style>
    .uploadedFile {font-size: 1rem; font-weight: 500;}
    .stProgress > div > div > div > div {background-color: #00A651;}
</style>""", unsafe_allow_html=True)

st.title("🏈 NCAA Box Score → CSV Converter")
st.markdown("---")

# File upload with clear instructions
uploaded_file = st.file_uploader(
    "Upload PDF Box Score", 
    type="pdf",
    help="Supported: NCAA D3 football box scores with play-by-play"
)

if uploaded_file:
    # Show file info
    st.success(f"✅ Uploaded: {uploaded_file.name} ({uploaded_file.size // 1024} KB)")
    
    # Processing with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner("Processing PDF..."):
        status_text.text("Extracting text from PDF...")
        progress_bar.progress(25)
        
        # Process PDF
        result, metadata = process_pdf(uploaded_file)
        progress_bar.progress(100)
    
    # Show summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Plays", metadata['total_plays'])
    col2.metric("Parsed Successfully", metadata['parsed_plays'])
    col3.metric("Success Rate", f"{metadata['success_rate']:.1f}%")
    col4.metric("Warnings", metadata['warnings'])
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Data Preview", "⚠️ Parsing Log", "📈 Summary Stats"])
    
    with tab1:
        st.subheader("Preview (first 20 plays)")
        st.dataframe(
            result.head(20),
            use_container_width=True,
            height=400
        )
    
    with tab2:
        if metadata['unparsed_plays']:
            st.warning(f"⚠️ {len(metadata['unparsed_plays'])} plays could not be parsed")
            for play in metadata['unparsed_plays']:
                st.text(play)
        else:
            st.success("✅ All plays parsed successfully!")
    
    with tab3:
        # Show game summary
        st.write(f"**Game:** {metadata['away']} @ {metadata['home']}")
        st.write(f"**Date:** {metadata['date']}")
        st.write(f"**Final Score:** {metadata['away']} {metadata['away_score']} - {metadata['home']} {metadata['home_score']}")
    
    # Download section
    st.markdown("---")
    st.subheader("📥 Download Results")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        csv_data = result.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Full CSV",
            data=csv_data,
            file_name=f"boxscore_{metadata['game_id']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        st.info(f"📊 CSV Size: {len(csv_data) // 1024} KB")

else:
    # Instructions when no file uploaded
    st.info("👆 Upload a PDF box score to get started")
    
    # Show example/demo
    with st.expander("📖 See Example Output"):
        # Load sample CSV
        sample_df = pd.read_csv("sample_data/expected_outputs/sample.csv")
        st.dataframe(sample_df.head(10))
```

### Additional Features to Add
- **Batch Processing:** Upload multiple PDFs, process all, download as ZIP
- **Validation Dashboard:** Show data quality metrics
- **Export Options:** CSV, Excel, JSON
- **Game Comparison:** If multiple files uploaded, show side-by-side comparison
- **Settings Sidebar:** Configure parsing options (strict vs. lenient mode)

---

## Development Workflow

### Iterative Approach
1. Start with ONE sample PDF (the UW game provided)
2. Build parsers to handle that specific format
3. Test on 2-3 more PDFs from same source
4. Generalize patterns to handle variations
5. Add error handling for edge cases

### Don't Over-Engineer Early
- Get basic parsing working first
- Don't worry about all 120 columns initially
- Focus on core columns: down, distance, yards, play type, score
- Add more columns incrementally

### Priority Column Tiers

**Tier 1 (MVP - Must Have):**
- playId, gameId, date, week, quarter
- team, opponent, teamCurrentScore, opponentCurrentScore
- down, dist, los, playType, yds
- PlayDesc (original text)

**Tier 2 (Important):**
- driveNumber, drivePlays, driveYards, driveHowEnded
- Sack, Interception, FumbleLost, Incomplete
- Player names (QB, receiver/rusher, tackler)

**Tier 3 (Nice to Have):**
- Detailed player stats
- Formation information
- Penalty details

**Tier 4 (Future/External Data Required):**
- EPA, WPA, advanced metrics
- PFF IDs, broadcast IDs

---

## Common Pitfalls to Avoid

1. **Don't assume consistent formatting**
   - Team abbreviations vary (BAY vs Baylor vs BAY)
   - Clock formats differ (15:00 vs 15.00)
   
2. **Handle missing data gracefully**
   - Not all plays have down/distance (kickoffs)
   - Some plays don't have yards (timeouts)

3. **Track context across plays**
   - Running score throughout game
   - Current possession
   - Drive continuity

4. **Validate continuously**
   - Check that scores only increase
   - Verify field position stays 1-100
   - Ensure quarter progresses logically

---

## Performance Considerations

- PDFs can be 10-20 pages → processing should complete in <10 seconds
- Cache parsed results to avoid re-processing
- Stream large CSV outputs (don't load entire dataframe in memory if >10k plays)

---

## Future Enhancements

### Version 1.1 Features
- **Batch processing:** Upload ZIP of PDFs, process all, download combined CSV
- **Settings panel:** Configure parsing strictness, column selection
- **Export formats:** Add Excel (.xlsx) and JSON export options
- **Validation dashboard:** Visual charts showing data quality metrics
- **Save/load presets:** Remember user preferences

### Version 1.2 Features
- **Database integration:** Store processed games in PostgreSQL/SQLite
- **Game library:** Browse previously processed games
- **Search functionality:** Find specific games or plays
- **Comparison mode:** Compare two games side-by-side
- **Player tracking:** Link plays to player profiles over time

### Version 2.0 Features
- **Multi-source support:** Handle different PDF formats (other conferences, sources)
- **Auto-roster matching:** Link player names to rosters automatically
- **Calculate EPA/WPA:** Build models to populate advanced metrics
- **Analytics dashboard:** Generate insights from CSV data
- **API mode:** Programmatic access via Streamlit API endpoints

### Championship Analytics Integration
- **Direct database upload:** Push CSV directly to CAI database
- **Template matching:** Auto-detect CAI data schema
- **Bulk processing:** Process entire season's worth of games
- **Quality control:** Flag anomalies for manual review

---

## Production Deployment Checklist

### Streamlit Cloud Setup
- [ ] Create Streamlit Cloud account
- [ ] Connect GitHub repository
- [ ] Set up secrets management (if needed for future DB connections)
- [ ] Configure custom domain (optional: converter.championshipanalytics.com)
- [ ] Set resource limits (Community tier: 1GB RAM, sufficient for this app)

### Pre-Deployment
- [ ] Add comprehensive error handling
- [ ] Test with 10+ different PDFs
- [ ] Validate output CSVs match expected schema
- [ ] Add usage analytics (optional: track number of conversions)
- [ ] Create user documentation
- [ ] Add "Report Issue" button linking to GitHub issues

### Performance Optimization
- [ ] Cache PDF processing results
- [ ] Limit uploaded file size (e.g., 10MB max)
- [ ] Add timeout for very large PDFs (fail gracefully after 60s)
- [ ] Compress output CSV for large games (offer .zip download)

### Monitoring (Post-Launch)
- Streamlit Cloud provides built-in metrics
- Monitor: Processing time, error rates, user sessions
- Add custom logging for unparseable plays (help improve parsers)

---

## Key Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app locally
streamlit run app.py

# Run tests
pytest tests/

# Type checking
mypy parsers/ transformers/
```

### Deployment
```bash
# Deploy to Streamlit Cloud
# Just push to GitHub and connect repo in Streamlit Cloud UI
```

---

## Example Code Snippets

### PDF Extraction
```python
import pdfplumber

def extract_play_by_play_text(pdf_path: str) -> list[str]:
    """Extract play-by-play text from PDF."""
    plays = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Play-by-play starts with "1st and 10" patterns
            if "1st and 10" in text or "Play By Play" in text:
                plays.extend(parse_plays_from_page(text))
    return plays
```

### Play Parsing
```python
import re
from typing import Optional

def parse_rush_play(play_text: str) -> Optional[dict]:
    """Parse a rushing play description."""
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
```

---

## Making This Portfolio-Worthy

### For Job Interviews, Emphasize:

**Technical Breadth:**
- "Built full-stack web app using Python and Streamlit"
- "Implemented complex regex parsing for unstructured data"
- "Designed ETL pipeline converting PDFs to structured datasets"
- "Deployed production application on cloud infrastructure"

**Business Impact:**
- "Automated manual data entry that previously took 2+ hours per game"
- "Enabled analysis of 100+ games with consistent data schema"
- "Built tool currently used by Championship Analytics for client deliverables"

**Problem-Solving:**
- "Handled edge cases: overtime, safeties, defensive TDs, muffed kicks"
- "Implemented data validation ensuring 95%+ parsing accuracy"
- "Created extensible architecture supporting multiple PDF formats"

### Demo Talking Points

**The Problem (30 seconds):**
"College football analytics requires converting PDF box scores into structured data. Manual entry is error-prone and slow. I built an automated converter."

**The Solution (30 seconds):**
"Users upload a PDF, my tool extracts play-by-play using custom parsers, validates the data, and outputs a standardized CSV matching our database schema."

**The Impact (15 seconds):**
"Processes a game in under 10 seconds vs. 2+ hours manually. Used by Championship Analytics for 100+ D3 football programs."

**Live Demo (45 seconds):**
- Upload sample PDF
- Show processing with progress bar
- Preview parsed data with metrics
- Download CSV
- (Optional) Show one unparsed play in error log, explain edge case

### GitHub README Structure

```markdown
# NCAA Box Score to CSV Converter

## Overview
Automated tool to convert NCAA Division III football PDF box scores into structured play-by-play CSV data.

## Features
- 🚀 Processes complete games in <10 seconds
- ✅ 95%+ parsing accuracy on standard box scores
- 📊 Outputs 120+ column schema matching industry standards
- 🎯 Handles edge cases: OT, safeties, defensive TDs, penalties
- 🌐 Live demo: [converter.streamlit.app](...)

## Tech Stack
- Python 3.11+
- Streamlit (web framework)
- pdfplumber (PDF extraction)
- pandas (data manipulation)
- regex (pattern matching)

## Usage
[screenshot of interface]

## Sample Output
[screenshot of CSV preview]

## Roadmap
- [ ] Batch processing
- [ ] Multi-source PDF support
- [ ] EPA/WPA calculation

## About
Built by Kevin, Data Analyst @ Championship Analytics
```

### Video Demo Script (2 minutes)

**Intro (15s):**
"Hi, I'm Kevin. I built this tool to solve a real problem in sports analytics: converting unstructured PDF reports into analyzable data."

**Problem (20s):**
"College football teams get box scores as PDFs. To analyze them, we need structured data. Manual entry takes hours and is error-prone."

**Demo (60s):**
- Show PDF box score
- Upload to Streamlit app
- Explain processing: "Regex patterns extract plays, validate data, track game state"
- Show metrics dashboard
- Download CSV
- Open in Excel/spreadsheet, show structured columns

**Technical Highlights (20s):**
"Built with Python and Streamlit. Custom parsers handle 20+ play types. Validation ensures data quality. Deployed on Streamlit Cloud."

**Impact (5s):**
"Now used by Championship Analytics for all D3 football analysis."

### LinkedIn Post Template

```
🏈 Built an automated NCAA football data converter!

The problem: Converting PDF box scores to analyzable data took 2+ hours per game and was error-prone.

The solution: A Streamlit web app that processes PDFs in <10 seconds with 95%+ accuracy.

Tech: Python, pdfplumber, pandas, regex, Streamlit

Impact: Now used by Championship Analytics to process 100+ D3 programs.

Try it: [link]
Code: [GitHub link]

#DataAnalytics #SportsAnalytics #Python #Portfolio
```

---

## Notes for Claude/Cursor

- When building parsers, test incrementally with print statements
- If a regex pattern doesn't match, print the actual text to debug
- Use pandas for CSV building, not manual CSV writing
- Prioritize working code over perfect code initially
- Ask for clarification if PDF format seems ambiguous
- Suggest validation checks as you write parsing logic

---

## Questions to Resolve

- [ ] Should we support multiple PDF formats or just one initially?
- [ ] How to handle games that go to overtime?
- [ ] What to do with unparseable plays (skip, log, or error)?
- [ ] Should drive numbers be cumulative or reset by team?
- [ ] How to handle defensive scores (pick-six, fumble return TD)?

---

## Success Criteria

**MVP is successful when (Week 1-2):**
1. ✅ Can upload sample PDF and get CSV output
2. ✅ CSV has all Tier 1 columns populated correctly
3. ✅ At least 90% of plays are parsed successfully
4. ✅ Output CSV matches expected format (120+ columns, even if many empty)
5. ✅ Can be demoed in under 2 minutes

**Production-ready when (Week 3-4):**
1. ✅ Professional UI with custom styling
2. ✅ Handles errors gracefully (no crashes on bad PDFs)
3. ✅ Shows parsing success metrics and warnings
4. ✅ Deployed on Streamlit Cloud with public URL
5. ✅ GitHub repo with comprehensive README
6. ✅ Can process 5+ different games consistently
7. ✅ Total processing time <15 seconds per game
8. ✅ Validation catches unrealistic data (scores, yards, etc.)

**Portfolio-ready when (Final polish):**
1. ✅ 2-minute demo video recorded
2. ✅ LinkedIn post published with link
3. ✅ Added to resume as "Built automated sports data ETL pipeline"
4. ✅ Sample outputs available for download
5. ✅ Can explain technical decisions confidently in interviews

---

Last Updated: 2025-12-13
Project Owner: Kevin
