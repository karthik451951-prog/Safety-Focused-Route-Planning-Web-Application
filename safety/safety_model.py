import joblib
from datetime import datetime
import pandas as pd

from safety.crime_score import crime_score
from safety.cctv_score import cctv_score
from safety.infra_score import infra_score
from safety.traffic_score import traffic_score

# Load trained ML model
model = joblib.load("time_aware_safety_model.pkl")


def get_time_category():
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def evaluate_route(route_coords, tomtom_key):

    crime = crime_score(route_coords)
    cctv = cctv_score(route_coords)
    infra = infra_score(route_coords)
    traffic = traffic_score(route_coords, tomtom_key)

    time_category = get_time_category()

    X = pd.DataFrame([{
    "crime": crime,
    "cctv": cctv,
    "infra": infra,
    "traffic": traffic,
    "time_category": time_category
}])
    predicted_safety = model.predict(X)[0]

    return {
        "crime": round(crime, 3),
        "cctv": round(cctv, 3),
        "infra": round(infra, 3),
        "traffic": round(traffic, 3),
        "time": time_category,
        "final": round(float(predicted_safety), 3)
    }
