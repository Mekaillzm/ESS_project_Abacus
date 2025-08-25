import requests, math, time, csv, sys
from datetime import datetime, timedelta, timezone
import regression_model as rm

# ---- CONFIG ----
API_KEY = "7756e8f4ca3c6da6f03e15f5c36fd6b2d3790097f5cf98f48f9177bdea5c05ad"   # get one free at OpenAQ
RADIUS_M = 50000                  # 50 km search radius around city center
COUNTRY = "PK"
# City centers (lat, lon)
CITIES = {
    "lahore":    (31.5204, 74.3587),
    "karachi":   (24.8607, 67.0011),
    "islamabad": (33.6844, 73.0479),
}

HEADERS = {"X-API-Key": API_KEY}
BASE = "https://api.openaq.org/v3"

# --- US AQI from PM2.5 (µg/m³) using EPA 24h breakpoints ---
# https://www.airnow.gov/aqi/aqi-basics/  (piecewise linear)
BREAKS = [
    (0.0, 12.0,   0,  50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4,101, 150),
    (55.5,150.4,151, 200),
    (150.5,250.4,201, 300),
    (250.5,350.4,301, 400),
    (350.5,500.4,401, 500),
]
def us_aqi_from_pm25(c):
    if c is None: return None
    # truncate to 1 decimal like EPA guidance
    c = math.floor(c*10)/10.0
    for Cl, Ch, Il, Ih in BREAKS:
        if Cl <= c <= Ch:
            return round((Ih-Il)/(Ch-Cl)*(c-Cl)+Il)
    return 500  # cap

def get_locations_for_city(lat, lon, radius_m=RADIUS_M, country=COUNTRY):
    # PM2.5 parameter_id is 2 in OpenAQ v3 docs
    # We pull locations, then sensors for each location.
    params = {
        "coordinates": f"{lon},{lat}",  # OpenAQ expects lon,lat in docs
        "radius": radius_m,
        "limit": 1000,
        "country_id": country,
        "parameters_id": 2
    }
    r = requests.get(f"{BASE}/locations", params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])

def get_sensors_for_location(loc_id):
    r = requests.get(f"{BASE}/locations/{loc_id}/sensors", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return [s for s in r.json().get("results", []) if s.get("parameters_id") == 2]

def get_daily_pm25_for_sensor(sensor_id, date_from=None, date_to=None):
    # daily averages: /v3/sensors/{id}/days
    # we page through until exhausted
    limit = 1000
    page = 1
    out = []
    while True:
        params = {"limit": limit, "page": page}
        if date_from: params["date_from"] = date_from
        if date_to:   params["date_to"]   = date_to
        r = requests.get(f"{BASE}/sensors/{sensor_id}/days", params=params, headers=HEADERS, timeout=60)
        if r.status_code == 404:
            break
        r.raise_for_status()
        data = r.json().get("results", [])
        if not data: break
        for row in data:
            # row has fields: date (UTC ISO), average (µg/m3), parameter_id=2, etc.
            d = row.get("date")
            avg = row.get("average")
            out.append((d[:10], avg))  # YYYY-MM-DD
        page += 1
        time.sleep(0.2)
    return out

def merge_by_date_avg(values_list):
    # values_list = list of lists of (date, value)
    by_date = {}
    for vals in values_list:
        for d, v in vals:
            if v is None: continue
            by_date.setdefault(d, []).append(v)
    # average across sensors for city-day
    merged = []
    for d, arr in by_date.items():
        merged.append((d, sum(arr)/len(arr)))
    merged.sort(key=lambda x: x[0])
    return merged

def write_city_csv(city, rows_pm25):
    # convert to AQI and write CSV
    fname = f"{city}_aqi_daily.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date","aqi_us","pm25_ugm3"])
        for d, pm in rows_pm25:
            aqi = us_aqi_from_pm25(pm)
            w.writerow([d, aqi, round(pm,2) if pm is not None else ""])
    print(f"Wrote {fname}")

def earliest_date_available_for_sensor(sensor_id):
    # quick probe of first page and last page to infer range if available
    # Not strictly required; OpenAQ returns all days when paging.
    return None

def run():
    for city, (lat, lon) in CITIES.items():
        print(f"=== {city.title()} ===")
        locs = get_locations_for_city(lat, lon)
        if not locs:
            print("No locations with PM2.5 found.")
            continue
        sensor_series = []
        for loc in locs:
            loc_id = loc.get("id")
            try:
                sensors = get_sensors_for_location(loc_id)
            except Exception as e:
                # Some endpoints may not be available for all locs
                sensors = []
            for s in sensors:
                sid = s.get("id")
                try:
                    series = get_daily_pm25_for_sensor(sid)
                    if series:
                        sensor_series.append(series)
                except Exception as e:
                    pass
        if not sensor_series:
            print("No daily data found from sensors.")
            continue
        merged = merge_by_date_avg(sensor_series)
        write_city_csv(city, merged)

if __name__ == "__main__":
    if API_KEY == "API_KEY":
        sys.exit("Please set API_KEY to your OpenAQ API key.")
    run()
