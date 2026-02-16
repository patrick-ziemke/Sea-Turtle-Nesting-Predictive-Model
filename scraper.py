import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from astral.moon import phase
import model_logic

# --- CONFIG ---
STATION_ID = "9684403" # Puntarenas
MAX_RANGE_PUNTARENAS = 3.3 # Maximum typical range in meters

def get_moon_info(date_obj):
    """Calculates moon illumination % and precise phase names."""
    p = phase(date_obj)
    illumination = 50 * (1 - np.cos(2 * np.pi * p / 28))

    # Narrower thresholds for precise phase naming
    if p < 0.9 or p > 27.1: name = "Luna nueva"
    elif p < 6.1: name = "Luna creciente"
    elif p < 7.9: name = "Cuarto creciente"
    elif p < 13.1: name = "Gibosa creciente"
    elif p < 14.9: name = "Luna llena"
    elif p < 20.1: name = "Gibosa menguante"
    elif p < 21.9: name = "Cuarto menguante"
    else: name = "Luna menguante"

    return round(illumination, 1), name

def fetch_tide_data():
    """Fetches 31 days of tide predictions from NOAA API."""
    start_date = datetime.now().strftime("%Y%m%d")
    url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={start_date}&range=744&station={STATION_ID}&product=predictions&datum=MLLW&time_zone=lst_ldt&interval=hilo&units=metric&application=TurtleForecaster&format=json"

    response = requests.get(url)
    data = response.json()
    if "predictions" not in data:
        raise Exception("Failed to fetch tide data from NOAA.")
    return pd.DataFrame(data["predictions"])

def prepare_forecast_csv():
    tide_df = fetch_tide_data()
    tide_df['t'] = pd.to_datetime(tide_df['t'])
    forecast_rows = []

    today = datetime.now()
    for i in range(31):
        target_date = today + timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")

        # Get all tides for this specific day
        day_tides = tide_df[tide_df['t'].dt.date == target_date.date()]
        
        # ISSUE 1 FIX: Find high tide closest to 19:00 (7 PM)
        high_tides = day_tides[day_tides['type'] == 'H'].copy()
        if not high_tides.empty:
            # Calculate minutes from 7 PM (1140 minutes)
            high_tides['diff'] = high_tides['t'].apply(lambda x: abs((x.hour * 60 + x.minute) - 1140))
            best_high = high_tides.loc[high_tides['diff'].idxmin()]
        else:
            best_high = None

        # Get the lowest tide of the day for the range calculation
        low_tides = day_tides[day_tides['type'] == 'L']
        best_low = low_tides.loc[pd.to_numeric(low_tides['v']).idxmin()] if not low_tides.empty else None
        
        # ISSUE 2 FIX: Refined moon info
        illum, phase_name = get_moon_info(target_date)

        # ISSUE 3 FIX: Calculate Tide Coefficient
        if best_high is not None and best_low is not None:
            tide_range = float(best_high['v']) - float(best_low['v'])
            # Normalize range to a 0-100 scale based on Puntarenas max range
            coeff = min(100, round((tide_range / MAX_RANGE_PUNTARENAS) * 100))
        else:
            coeff = 70 # Fallback

        forecast_rows.append({
            'date': date_str,
            'day': target_date.day,
            'month': target_date.month,
            'high_tide_time': best_high['t'].strftime("%H:%M") if best_high is not None else "19:00",
            'high_tide_height_m': float(best_high['v']) if best_high is not None else 2.5,
            'low_tide_height_m': float(best_low['v']) if best_low is not None else 0.2,
            'illumination_pct': illum,
            'lunar_phase': phase_name,
            'tide_coefficient': coeff,
            'prediction': 0
        })
    
    forecast_df = pd.DataFrame(forecast_rows)
    forecast_df.to_csv("forecast.csv", index=False)
    print("✅ Fixed forecast.csv updated with evening tides and dynamic coefficients.")

if __name__ == "__main__":
    prepare_forecast_csv()
    model_logic.run_prediction_engine()
