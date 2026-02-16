import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Mobile-first configuration
st.set_page_config(page_title="Turtle Watch Score", layout="centered")

# Custom CSS for a clean mobile look
st.markdown("""
    <style>
    .reportview-container .main .block-container { padding-top: 1rem; }
    .stExpander { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("forecast.csv")
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        return None

df = load_data()

st.title("🐢 Turtle Watch")
st.subheader("Nightly Viewing Forecast")

# Legend for the 1-10 Scale
st.markdown("""
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 20px; padding: 10px; background-color: #f0f2f6; border-radius: 10px;">
    <span>🔴 1-3: Low</span>
    <span>🟡 4-6: Fair</span>
    <span>🟢 7-8: Good</span>
    <span>🌟 9-10: Peak</span>
</div>
""", unsafe_allow_html=True)

if df is not None:
    # Calendar Setup
    now = datetime.now()
    cal = calendar.monthcalendar(now.year, now.month)
    month_name = calendar.month_name[now.month]

    st.markdown(f"### {month_name} {now.year}")

    # Weekday Headers
    cols_header = st.columns(7)
    days_abbr = ["M", "T", "W", "T", "F", "S", "S"]
    for i, day_abbr in enumerate(days_abbr):
        cols_header[i].markdown(f"<p style='text-align:center; color:gray;'>{day_abbr}</p>", unsafe_allow_html=True)

    # Calendar Grid
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                # Get data for this specific day
                day_data = df[df['date'].dt.day == day]
                
                if not day_data.empty:
                    # Pull values from CSV
                    score = int(day_data['viewing_score'].values[0])
                    tide_time = day_data['high_tide_time'].values[0]
                    phase = day_data['lunar_phase'].values[0]
                    
                    # Color Logic (Stoplight System)
                    if score >= 8:
                        bg, txt = "#1E5631", "white"   # Dark Green (Peak)
                    elif score >= 6:
                        bg, txt = "#A4DE02", "black"   # Lime Green (Good)
                    elif score >= 4:
                        bg, txt = "#FBC02D", "black"   # Yellow (Fair)
                    else:
                        bg, txt = "#FFCDD2", "black"   # Light Red (Low)
                    
                    with cols[i]:
                        # Square clickable-looking box
                        st.markdown(f"""
                            <div style="background-color:{bg}; border-radius:8px; text-align:center; padding:8px 2px; border:1px solid #ddd; min-height:60px;">
                                <span style="font-size:0.6rem; color:{txt}; opacity:0.8;">{day}</span><br>
                                <span style="font-weight:bold; color:{txt}; font-size:1.2rem;">{score}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Expandable details to keep the UI clean
                        with st.expander("🔍"):
                            st.caption(f"**Score: {score}/10**")
                            st.write(f"🌊 {tide_time}")
                            st.write(f"🌙 {phase}")
                else:
                    cols[i].markdown(f"<p style='text-align:center; padding-top:10px;'>{day}</p>", unsafe_allow_html=True)

    st.divider()
    st.caption("Data updates daily at midnight based on NOAA tides and CREMA historical nesting patterns.")

else:
    st.warning("No forecast data found. Please ensure the scraper has run successfully.")
