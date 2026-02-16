import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Mobile Layout Config
st.set_page_config(page_title="Turtle Watch", layout="centered")

# Load the daily updated data
@st.cache_data
def load_data():
    df = pd.read_csv("forecast.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

try:
    df = load_data()

    st.title("🐢 Turtle Watch")
    st.markdown("### Monthly Forecast")
    st.info("Color indicates nesting probability based on tide and moon.")

    # Calendar Logic
    now = datetime.now()
    month = now.month
    year = now.year
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    st.subheader(f"{month_name} {year}")

    # Display Grid
    cols_header = st.columns(7)
    days_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, day_name in enumerate(days_abbr):
        cols_header[i].caption(day_name)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                # Filter forecast for this specific day
                day_data = df[df['date'].dt.day == day]
                
                if not day_data.empty:
                    pred = day_data['prediction'].values[0]
                    tide_time = day_data['high_tide_time'].values[0]
                    illum = day_data['illumination_pct'].values[0]
                    phase = day_data['lunar_phase'].values[0]
                    
                    # Coloring Logic based on prediction value
                    bg_color = "#ffffff" # White default
                    text_color = "black"
                    if pred >= 5: 
                        bg_color = "#1E5631" # Dark Green
                        text_color = "white"
                    elif pred >= 2: 
                        bg_color = "#A4DE02" # Lime Green
                    
                    with cols[i]:
                        st.markdown(f"""
                            <div style="background-color:{bg_color}; border-radius:5px; text-align:center; padding:5px; border:1px solid #eee; margin-bottom:5px;">
                                <span style="font-weight:bold; color:{text_color}; font-size:1.2rem;">{day}</span><br>
                                <span style="color:{text_color}; font-size:0.6rem;">{pred}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Detail view for high probability nights
                        with st.expander("Details"):
                            st.write(f"**Tide:** {tide_time}")
                            st.write(f"**Moon:** {phase} ({illum}%)")
                            st.write(f"**Score:** {pred}")
                else:
                    cols[i].write(f"{day}")

except Exception as e:
    st.error(f"Waiting for forecast data... (Error: {e})")
    st.write("Please run the scraper once to generate the forecast.csv file.")
