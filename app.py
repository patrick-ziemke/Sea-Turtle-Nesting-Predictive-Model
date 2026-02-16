import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Mobile Layout Config
st.set_page_config(page_title="Turtle Watch", layout="centered")

# Load the daily updated data
@st.cache_data
def load_data():
    return pd.read_csv("forecast.csv")

df = load_data()

st.title("🐢 Turtle Watch")
st.markdown("### Monthly Forecast")

# Calendar Logic
month = datetime.now().month
year = datetime.now().year
cal = calendar.monthcalendar(year, month)

# Display Grid
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            # Filter forecast for this specific day
            day_data = df[df['day'] == day]
            pred = day_data['prediction'].values[0] if not day_data.empty else 0
            
            # Coloring Logic
            bg_color = "transparent"
            if pred >= 7: bg_color = "#00FF00" # Bright Green
            elif pred >= 3: bg_color = "#90EE90" # Light Green
            
            with cols[i]:
                st.markdown(f"""
                    <div style="background-color:{bg_color}; border-radius:5px; text-align:center; padding:10px; border:1px solid #eee;">
                        <span style="font-weight:bold; color:black;">{day}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Mobile "Hover" equivalent: Expanders
                if pred >= 3:
                    with st.expander("View"):
                        st.write(f"Tide: {day_data['high_tide'].values[0]}")
                        st.write(f"Moon: {day_data['moon'].values[0]}%")
