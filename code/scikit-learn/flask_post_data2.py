# app.py
# save as app.py
from flask import Flask, request, jsonify
import pandas as pd
import random_forest_model as rfm
import json
import logging

# try to import requests; if unavailable, we'll fallback to urllib
try:
    import requests
except Exception:
    requests = None
    from urllib import request as urlrequest
    from urllib.error import URLError, HTTPError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

NODE_RED_URL = "http://localhost:1880/predictions"
  # endpoint to POST results to (adjust if you have a specific path)

#Instantiate model
try:
    models = {}
    for city in ["Lahore", "Islamabad", "Karachi"]:
        models[city] = rfm.model(city)
    
except Exception as e:
    logging.exception("Failed to instantiate random_forest_model")
    raise(f"errormodel initialization error: {e}")

def safe_mean(arr, key_candidates=("value", "_value")):
    """Compute mean of numeric values in array of dicts, checking several possible field names."""
    vals = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        for k in key_candidates:
            if k in item and item[k] is not None:
                try:
                    vals.append(float(item[k]))
                except Exception:
                    pass
                break
    if not vals:
        return None
    return sum(vals) / len(vals)

@app.route("/postData", methods=["POST"])
def postData():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid or missing json body"}), 400

    city = data.get("city")
    temps = data.get("temperature", [])
    aqis = data.get("aqi", [])

    if not city:
        return jsonify({"error": "missing city"}), 400

    if not isinstance(temps, list) or not isinstance(aqis, list):
        return jsonify({"error": "temperature and aqi must be arrays"}), 400

    if len(temps) == 0 and len(aqis) == 0:
        return jsonify({"error": "both temperature and aqi arrays are empty"}), 400

    # compute averages (try both 'value' and '_value' field names)
    avg_temp = safe_mean(temps, key_candidates=("value", "_value"))
    avg_aqi = safe_mean(aqis, key_candidates=("value", "_value"))

    if avg_temp is None and avg_aqi is None:
        return jsonify({"error": "no numeric values found in temperature or aqi arrays"}), 400

    # If one of them is missing, set to 0 (or you can choose to return error)
    if avg_temp is None:
        avg_temp = 0.0
    if avg_aqi is None:
        avg_aqi = 0.0

    logging.info(f"Received city={city}, avg_temp={avg_temp}, avg_aqi={avg_aqi}")

    # run predictions
    model = models[city]

    try:
        raw_result = model.run(avg_temp, avg_aqi)
    except Exception as e:
        logging.exception("Failed to run model")
        return jsonify({"error": f"model run error: {e}"}), 500

    # raw_result expected to be like: { "<city_key>": { "weather_satisfaction": float, "air_quality_satisfaction": float } }
    # Extract the predictions dict (first value)
    preds_dict = None
    if isinstance(raw_result, dict) and len(raw_result) > 0:
        # pick either the entry matching incoming city (if exists), else first key
        if city in raw_result:
            preds_dict = raw_result[city]
        else:
            # take first value
            preds_dict = next(iter(raw_result.values()))
    else:
        preds_dict = raw_result  # fallback if model returns a simple dict

    if not isinstance(preds_dict, dict):
        logging.error(f"Unexpected model output format: {raw_result}")
        return jsonify({"error": "unexpected model output format"}), 500

    # Extract floats and round them (nearest integer). Change rounding precision here if you prefer decimals.
    raw_weather = preds_dict.get("weather_satisfaction")
    raw_air = preds_dict.get("air_quality_satisfaction")

    def safe_round(v):
        try:
            return round(float(v), 3)
        except Exception:
            return None

    weather_rounded = safe_round(raw_weather)
    air_rounded = safe_round(raw_air)

    result_payload = {
        "city": city,
        "avg_temperature": avg_temp,
        "avg_aqi": avg_aqi,
        "predictions": {
            "weather_satisfaction": weather_rounded,
            "air_quality_satisfaction": air_rounded
        },
        # include raw_model_output for debugging
        "raw_model_output": raw_result
    }

    # Save CSV locally for debugging (optional) - safe path in current working dir
    try:
        # create a small diagnostic dataframe
        df_t = pd.DataFrame(temps)
        df_a = pd.DataFrame(aqis)
        df_t.to_csv(f"{city}_temperature_points.csv", index=False)
        df_a.to_csv(f"{city}_aqi_points.csv", index=False)
    except Exception:
        logging.exception("Failed to write CSVs (non-fatal)")

    # Try to POST the result back to Node-RED
    try:
        if requests is not None:
            r = requests.post(NODE_RED_URL, json=result_payload, timeout=60)
            logging.info(f"Posted results to Node-RED ({NODE_RED_URL}) - status {r.status_code}")
            node_red_status = {"success": True, "status_code": r.status_code, "response_text": r.text[:200]}
        else:
            # fallback using urllib
            req = urlrequest.Request(NODE_RED_URL, data=json.dumps(result_payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
            with urlrequest.urlopen(req, timeout=5) as resp:
                resp_text = resp.read().decode("utf-8", errors="ignore")
                node_red_status = {"success": True, "status_code": resp.getcode(), "response_text": resp_text[:200]}
    except Exception as e:
        logging.warning(f"Failed to POST to Node-RED at {NODE_RED_URL}: {e}")
        node_red_status = {"success": False, "error": str(e)}

    # Return final JSON to requestor, including node-red post status for transparency
    return jsonify({"result": result_payload, "node_red_post": node_red_status}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
