import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

# ==========================================
# LOAD TRAINING DATA
# Columns:
# crime, cctv, infra, traffic, time_category, safety_score
# ==========================================

df = pd.read_csv("../data/training_safety_data.csv")

X = df[["crime", "cctv", "infra", "traffic", "time_category"]]
y = df["safety_score"]

# ==========================================
# PREPROCESSING
# ==========================================

numeric_features = ["crime", "cctv", "infra", "traffic"]
categorical_features = ["time_category"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_features),
        ("time", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ]
)

# ==========================================
# MODEL
# ==========================================

model = LinearRegression()

pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", model)
])

# ==========================================
# TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline.fit(X_train, y_train)

# ==========================================
# EVALUATION
# ==========================================

preds = pipeline.predict(X_test)
preds = np.clip(preds, 0, 1)

print("\nModel Performance:")
print("R2 Score:", r2_score(y_test, preds))
rmse = np.sqrt(mean_squared_error(y_test, preds))
print("RMSE:", rmse)
# ==========================================
# SAVE MODEL
# ==========================================

joblib.dump(pipeline, "../time_aware_safety_model.pkl")
print("\n✅ Time-aware safety model trained and saved.")
