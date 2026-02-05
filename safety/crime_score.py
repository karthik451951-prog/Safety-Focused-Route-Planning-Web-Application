import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crime_path = os.path.join(BASE_DIR, "data", "crime.csv")

df = pd.read_csv(crime_path)

coords = np.radians(df[["lat", "long"]].values)
tree = BallTree(coords, metric="haversine")
crime_vals = df["crime/area"].values

MIN_C = crime_vals.min()
MAX_C = crime_vals.max()

def crime_score(route_coords):
    sampled = route_coords[::10]
    risks = []

    for lon, lat in sampled:
        point = np.radians([[lat, lon]])
        dist, ind = tree.query(point, k=1)
        risks.append(crime_vals[ind[0][0]])

    avg_risk = np.mean(risks)
    norm = (avg_risk - MIN_C) / (MAX_C - MIN_C)

    return round(1 - norm, 3)
