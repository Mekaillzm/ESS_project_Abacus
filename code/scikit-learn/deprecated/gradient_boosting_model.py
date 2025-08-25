import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.ensemble import GradientBoostingRegressor
# ---------------------------
# Configuration: file paths
# ---------------------------
class model():
    def __init__(self, current_city):
        cities_files = {
            'Islamabad': {
                'weather': r"M:\Arbeit\Schule\internship\python\data\islamabad_weather.csv",
                'aqi':     r"M:\Arbeit\Schule\internship\python\data\islamabad_mock_AQI.csv",
                'feeling': r"M:\Arbeit\Schule\internship\python\data\islamabad_local_satisfaction_1980_2025.csv"
            },
            'Karachi': {
                'weather': r"M:\Arbeit\Schule\internship\python\data\karachi_weather.csv",
                'aqi':     r"M:\Arbeit\Schule\internship\python\data\karachi_mock_AQI.csv",
                'feeling': r"M:\Arbeit\Schule\internship\python\data\karachi_local_satisfaction_1980_2025.csv"
            },
            'Lahore': {
                'weather': r"M:\Arbeit\Schule\internship\python\data\lahore_weather.csv",
                'aqi':     r"M:\Arbeit\Schule\internship\python\data\lahore_mock_AQI.csv",
                'feeling': r"M:\Arbeit\Schule\internship\python\data\lahore_local_satisfaction_1980_2025.csv"
            }
        }
        self.city = current_city
        current_files = cities_files[self.city]

        # ---------------------------
        # Helper funcs
        # ---------------------------
        def to_date_only(df, date_col='date'):
            """Ensure the date column is datetime and normalized to date-only (midnight)."""
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            df[date_col] = df[date_col].dt.normalize()
            return df

        def load_and_prepare_city(files):
            """
            Load weather, aqi and feeling files for a city and return a daily-aligned dataframe with columns:
            date, temp (daily mean), aqi (daily interpolated), weather_satisfaction, air_quality_satisfaction
            """
            weather_path = Path(files['weather'])
            aqi_path = Path(files['aqi'])
            feeling_path = Path(files['feeling'])

            # --- Weather: hourly -> daily mean ---
            w_df = pd.read_csv(weather_path, parse_dates=['date'])
            w_df = to_date_only(w_df, 'date')
            if 'temp' not in w_df.columns:
                raise KeyError(f"'temp' column not found in weather file: {weather_path}")
            daily_temp = w_df.groupby('date', as_index=False)['temp'].mean().rename(columns={'temp': 'temp'})

            # --- AQI: likely weekly -> create daily index and interpolate (KEEP datetime index while interpolating) ---
            aqi_df = pd.read_csv(aqi_path, parse_dates=['date'])
            aqi_df = to_date_only(aqi_df, 'date')
            if aqi_df.empty:
                # no AQI rows: create empty DataFrame with date, aqi
                aqi_daily = pd.DataFrame(columns=['date', 'aqi'])
            else:
                if 'aqi' not in aqi_df.columns:
                    raise KeyError(f"'aqi' column not found in AQI file: {aqi_path}")
                aqi_df = aqi_df.set_index('date').sort_index()

                # Create continuous daily index from min to max of aqi file
                daily_idx = pd.date_range(start=aqi_df.index.min(), end=aqi_df.index.max(), freq='D')

                # Reindex to daily index (this yields a DataFrame with a DatetimeIndex)
                aqi_daily_df = aqi_df.reindex(daily_idx)

                # IMPORTANT FIX: interpolate with method='time' while the index is a DatetimeIndex
                aqi_daily_df['aqi'] = aqi_daily_df['aqi'].interpolate(method='time').ffill().bfill()

                # Reset index to have 'date' as a column (after interpolation)
                aqi_daily = aqi_daily_df.reset_index().rename(columns={'index': 'date'})

            # --- Feelings: parse expected columns ---
            f_df = pd.read_csv(feeling_path, parse_dates=['date'])
            f_df = to_date_only(f_df, 'date')
            required_cols = ['weather_satisfaction', 'air_quality_satisfaction']
            for col in required_cols:
                if col not in f_df.columns:
                    raise KeyError(f"'{col}' not found in feeling file: {feeling_path}")

            # --- Merge: keep only dates where feelings were recorded (left join on feelings) ---
            merged = pd.merge(f_df[['date'] + required_cols], daily_temp, on='date', how='left')
            if not aqi_daily.empty:
                merged = pd.merge(merged, aqi_daily[['date', 'aqi']], on='date', how='left')
            else:
                # if aqi data missing, add NaN column to keep pipeline consistent
                merged['aqi'] = np.nan

            # --- Handle missing temp/aqi for feeling dates ---
            merged['temp'] = pd.to_numeric(merged['temp'], errors='coerce')
            merged['aqi']  = pd.to_numeric(merged['aqi'], errors='coerce')

            # Interpolate small gaps in temp and aqi (linear) and then forward/back-fill extremes
            merged['temp'] = merged['temp'].interpolate(method='linear').ffill().bfill()
            merged['aqi']  = merged['aqi'].interpolate(method='linear').ffill().bfill()

            return merged

            # ---------------------------
            # Load, prepare all cities
            # ---------------------------
            
        city_data = {}
        try:
            df_city = load_and_prepare_city(current_files)
            if df_city.empty:
                print(f"Loaded {self.city} but resulting dataframe is empty; skipping.")
            else:
                df_city['city'] = self.city
                city_data[self.city] = df_city
                print(f"Loaded {self.city}: {len(df_city)} feeling rows (date range {df_city['date'].min().date()} -> {df_city['date'].max().date()})")
        except Exception as e:
            print(f"Skipping {self.city} due to error: {e}")

        # ---------------------------
        # Train models (two per city)
        # ---------------------------
        self.models = {}
        df_city = df_city.dropna(subset=['weather_satisfaction', 'air_quality_satisfaction'])
        self.models = {}
        X = df_city[['temp', 'aqi']].values



        # Weather satisfaction model
        
        
        y_weather = df_city['weather_satisfaction'].values
        if len(y_weather) >= 5:
            model_w = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42).fit(X, y_weather)
            r2_w = r2_score(y_weather, model_w.predict(X))
            self.models['weather'] = model_w
            self.models.setdefault('scores', {})['weather_r2'] = r2_w
            print(f"{self.city} - weather model trained on {len(y_weather)} rows, R^2 = {r2_w:.3f}")
        else:
            print(f"{self.city} - not enough samples for weather model ({len(y_weather)} rows).")

        # Air quality satisfaction model
        y_aq = df_city['air_quality_satisfaction'].values
        if len(y_aq) >= 5:
            model_aq = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42).fit(X, y_aq)
            r2_aq = r2_score(y_aq, model_aq.predict(X))
            self.models['air_quality'] = model_aq
            self.models.setdefault('scores', {})['air_quality_r2'] = r2_aq
            print(f"{self.city} - air quality model trained on {len(y_aq)} rows, R^2 = {r2_aq:.3f}")
        else:
            print(f"{self.city} - not enough samples for air quality model ({len(y_aq)} rows).")

        # ---------------------------
        # Prediction function
        # ---------------------------
    def clip_1_10(self, x):
        return float(max(1.0, min(10.0, x)))

    def predict_feelings(self, forecast_temp = 0, forecast_aqi = 0):
        inp = np.array([[float(forecast_temp), float(forecast_aqi)]])
        out = {}
        modelW = self.models.get('weather')
        out['weather_satisfaction'] = self.clip_1_10(modelW.predict(inp)[0]) if modelW is not None else None

        modelA = self.models.get('air_quality')
        out['air_quality_satisfaction'] = self.clip_1_10(modelA.predict(inp)[0]) if modelA is not None else None
        return out

    def runExample(self):
        try:
            print(self.predict_feelings(forecast_temp=1.0, forecast_aqi=1.0))
        except Exception as e:
            print(f"Prediction error for {self.city}: {e}")
    def run(self, forecast_temp, forecast_aqi):
        try:
            return {self.city: self.predict_feelings(forecast_temp = forecast_temp, forecast_aqi=forecast_aqi)}
        except Exception as e:
            print(f"Prediction error for {self.city}: {e}")

data = {}
index = 0
for city in ["Lahore", "Islamabad", "Karachi"]:
    _ = model(city)
    temps = range(-5, 60, 1)
    aqis = range(1, 325, 5)

    for i in range(len(temps)):
        values = _.run(temps[i], aqis[i])
        data[index] = {"city": city, "temperature": temps[i], "aqi": aqis[i], "aqi_sat": values[city]['air_quality_satisfaction'], "weather_sat": values[city]['weather_satisfaction']}
        index += 1

df = pd.DataFrame(data).transpose()
print(df)
df.to_csv("M:/Arbeit/Schule/internship/python/tests/forest_model_testA.csv")

