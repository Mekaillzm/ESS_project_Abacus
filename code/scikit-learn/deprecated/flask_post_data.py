# app.py
# save as app.py
from flask import Flask, request, jsonify
import pandas as pd
# from sklearn... as needed

app = Flask(__name__)
# load your model (optional)
# model = joblib.load("/models/feel_model.joblib")

@app.route("/postData", methods=["POST"])
def postData():
    data = request.get_json()
    city = data.get("city")
    measurement = data.get("measurement")
    points = data.get("points", [])
    if not points:
        return jsonify({"error": "no points"}), 400

    # convert to DataFrame and compute features exactly as model expects
    df = pd.DataFrame(points)
    print(df)

    df.to_csv(f'M:\Arbeit\Schule\internship\python\{city}_{measurement}_data.csv')
    # do any preprocessing skipped in Node-RED
    # e.g., df['hour'] = pd.to_datetime(df['time']).dt.hour

    # Example: fake prediction (replace with model.predict)
    # preds = model.predict(X)  # X prepared as model expects

    preds = [float((row.get('temp',0) * 0.1) + (row.get('aqi',0) * 0.01)) for _, row in df.iterrows()]

    # return predictions aligned with input times
    results = [{"time": t, "predicted_feel": float(p)} for t, p in zip(df["time"], preds)]
    return jsonify({"city": city, "predictions": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
