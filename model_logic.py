import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import warnings

warnings.filterwarnings('ignore')

class EnhancedTurtleForecaster:
    def __init__(self):
        self.model_rf = None
        self.model_gb = None
        
        # CREMA Historical Monthly Patterns (Influence Factor)
        self.monthly_patterns = {
            7: {'avg_per_night': 5.52, 'strength': 1.64},  # July Peak
            8: {'avg_per_night': 3.82, 'strength': 1.14},
            9: {'avg_per_night': 3.35, 'strength': 1.00},  # September Baseline
            10: {'avg_per_night': 3.37, 'strength': 1.01},
            11: {'avg_per_night': 1.67, 'strength': 0.50},
            12: {'avg_per_night': 1.75, 'strength': 0.53},
            1: {'avg_per_night': 1.12, 'strength': 0.34},
            2: {'avg_per_night': 0.75, 'strength': 0.25},   # Added Feb/March estimates
            3: {'avg_per_night': 0.62, 'strength': 0.20}
        }
        
        self.feature_names = [
            "Moon_sin", "Moon_cos", 
            "illumination_pct", "TimeFromHighTide", "TideRange", 
            "tide_coefficient", "high_tide_height_m",
            "monthly_strength"
        ]

    def get_monthly_strength(self, month):
        return self.monthly_patterns.get(month, {'strength': 1.0})['strength']

    def _engineer_features(self, df):
        """Standardizes features for both training and forecast data"""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["Month"] = df["date"].dt.month
        df["monthly_strength"] = df["Month"].apply(self.get_monthly_strength)
        
        # Calculate Time From High Tide (relative to 19:00 patrol start)
        def time_to_min(t):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        
        df["HighTideMinutes"] = df["high_tide_time"].apply(time_to_min)
        df["TimeFromHighTide"] = abs(df["HighTideMinutes"] - (19 * 60))
        
        # Tide Range
        df["TideRange"] = df["high_tide_height_m"] - df["low_tide_height_m"]
        
        # Lunar Cosine/Sine
        moon_map = {
            "Luna nueva": 0, "Luna creciente": 1, "Cuarto creciente": 2,
            "Gibosa creciente": 3, "Luna llena": 4, "Gibosa menguante": 5,
            "Cuarto menguante": 6, "Luna menguante": 7
        }
        df["MoonNum"] = df["lunar_phase"].map(moon_map).fillna(0)
        df["Moon_sin"] = np.sin(2 * np.pi * df["MoonNum"] / 8)
        df["Moon_cos"] = np.cos(2 * np.pi * df["MoonNum"] / 8)
        
        return df

    def train(self, csv_path="nesting_data.csv"):
        df = pd.read_csv(csv_path)
        df = self._engineer_features(df)
        
        # Filter arribadas and bad data
        df = df[df['arribada'] == 'n'].dropna(subset=self.feature_names + ["total_nests"])
        
        X = df[self.feature_names]
        y = df["total_nests"]
        
        self.model_rf = RandomForestRegressor(n_estimators=500, max_depth=15, random_state=42)
        self.model_gb = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
        
        self.model_rf.fit(X, y)
        self.model_gb.fit(X, y)
        print("✓ Model retrained on historical data.")

    def update_forecast(self, forecast_path="forecast.csv"):
        df_forecast = pd.read_csv(forecast_path)
        df_ready = self._engineer_features(df_forecast)
        
        X = df_ready[self.feature_names]
        pred_rf = self.model_rf.predict(X)
        pred_gb = self.model_gb.predict(X)
        
        # 1. Calculate raw prediction
        raw_pred = (pred_rf * 0.6 + pred_gb * 0.4).clip(0)
        df_forecast["prediction"] = raw_pred.round(1)
        
        # 2. Calculate 1-10 Viewing Score
        # We normalize based on a "Great Night" being ~8 nests for this sector
        def calculate_score(row):
            # Base score from prediction (0 to 7)
            score = (row['prediction'] / 8) * 7 
            
            # Bonus for High Tide Coefficient (Turtles love high energy water)
            if row['tide_coefficient'] > 80: score += 1.5
            
            # Penalty for too much moon (Harder to see/Turtles more shy)
            if row['illumination_pct'] > 90: score -= 1.0
            
            return min(10, max(1, round(score)))

        df_forecast["viewing_score"] = df_forecast.apply(calculate_score, axis=1)
        
        df_forecast.to_csv(forecast_path, index=False)
        print(f"✨ Forecast & 1-10 Scores updated.")

def run_prediction_engine():
    """Main entry point for the daily automation"""
    forecaster = EnhancedTurtleForecaster()
    try:
        forecaster.train("nesting_data.csv")
        forecaster.update_forecast("forecast.csv")
    except Exception as e:
        print(f"❌ Error in Prediction Engine: {e}")

if __name__ == "__main__":
    run_prediction_engine()
