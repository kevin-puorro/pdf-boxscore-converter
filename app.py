"""Streamlit main application for PDF box score converter."""

import streamlit as st
import pandas as pd
import tempfile
import os
from parsers.pdf_extractor import extract_basic_play_data
from parsers.stats_parser import extract_game_metadata
from utils.helpers import generate_game_id

st.set_page_config(
    page_title="PDF Box Score Converter",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""<style>
    .uploadedFile {font-size: 1rem; font-weight: 500;}
    .stProgress > div > div > div > div {background-color: #00A651;}
    .main {
        padding: 2rem;
    }
    .stButton>button {
        background-color: #003015;
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
</style>""", unsafe_allow_html=True)

st.title("🏈 PDF Box Score → CSV Converter")
st.caption("Convert PDF game reports to structured play-by-play CSV")
st.markdown("---")

# File upload
uploaded_file = st.file_uploader(
    "Upload PDF Box Score",
    type="pdf",
    help="Supported: NCAA D3 football box scores with play-by-play"
)

if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name} ({uploaded_file.size // 1024} KB)")
    
    # Processing with Phase 1 extraction
    with st.spinner("Processing PDF... This may take 10-20 seconds"):
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract basic play data (Phase 1)
            plays_data = extract_basic_play_data(tmp_path)
            
            # Extract game metadata
            from parsers.pdf_extractor import extract_text_from_pdf
            pages_text = extract_text_from_pdf(tmp_path)
            game_metadata = extract_game_metadata(pages_text)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            # Convert to DataFrame
            if plays_data:
                result = pd.DataFrame(plays_data)
            else:
                result = pd.DataFrame()
            
            # Calculate metadata
            total_plays = len(plays_data)
            parsed_plays = sum(1 for p in plays_data if p.get('down') is not None and p.get('playType') is not None)
            success_rate = (parsed_plays / total_plays * 100) if total_plays > 0 else 0.0
            
            # Find plays with issues
            unparsed_plays = []
            for i, play in enumerate(plays_data):
                if play.get('down') is None or play.get('playType') is None:
                    unparsed_plays.append(f"Play {i+1}: {play.get('PlayDesc', '')[:100]}")
            
            warnings = len(unparsed_plays)
            
            # Generate game ID
            game_id = generate_game_id()
            
            metadata = {
                'total_plays': total_plays,
                'parsed_plays': parsed_plays,
                'success_rate': success_rate,
                'warnings': warnings,
                'unparsed_plays': unparsed_plays,
                'game_id': game_id,
                'away': game_metadata.get('away', 'Unknown'),
                'home': game_metadata.get('home', 'Unknown'),
                'date': game_metadata.get('date', 'Unknown'),
                'away_score': 0,  # Will be populated in Phase 2
                'home_score': 0   # Will be populated in Phase 2
            }
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
            
            # Set empty results on error
            metadata = {
                'total_plays': 0,
                'parsed_plays': 0,
                'success_rate': 0.0,
                'warnings': 0,
                'unparsed_plays': [],
                'game_id': 'error',
                'away': 'Error',
                'home': 'Error',
                'date': 'Error',
                'away_score': 0,
                'home_score': 0
            }
            result = pd.DataFrame()
    
    # Show summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Plays", metadata['total_plays'])
    col2.metric("Parsed Successfully", metadata['parsed_plays'])
    col3.metric("Success Rate", f"{metadata['success_rate']:.1f}%")
    col4.metric("Warnings", metadata['warnings'])
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📊 Data Preview", "⚠️ Parsing Log"])
    
    with tab1:
        st.subheader("Data Preview")
        if not result.empty:
            st.dataframe(
                result,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No data to display yet")
    
    with tab2:
        if metadata['unparsed_plays']:
            st.warning(f"⚠️ {len(metadata['unparsed_plays'])} plays could not be parsed")
            for play in metadata['unparsed_plays']:
                st.text(play)
        else:
            st.success("✅ All plays parsed successfully!")
    
    # Download section
    st.markdown("---")
    st.subheader("📥 Download Results")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if not result.empty:
            csv_data = result.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Full CSV",
                data=csv_data,
                file_name=f"boxscore_{metadata['game_id']}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No data available for download")
    with col2:
        if not result.empty:
            csv_data = result.to_csv(index=False)
            st.info(f"📊 CSV Size: {len(csv_data) // 1024} KB")

else:
    pass  # No file uploaded yet

