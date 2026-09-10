"""
House Price Predictor - Backend API
------------------------------------
A small Flask API that replicates the rule-based pricing model
originally implemented in client-side JavaScript.

Run with:
    pip install flask flask-cors
    python app.py

The API will be available at http://localhost:5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow the frontend (served separately) to call this API

# ---------------------------------------------------------------------------
# Pricing model constants (mirrors the original frontend JS)
# ---------------------------------------------------------------------------

BASE_PRICE_PER_SQFT = 120

AREA_MULTIPLIER = {
    "Downtown": 1.5,
    "Coastal": 1.35,
    "Suburb": 1.0,
    "Rural": 0.7,
}

DIRECTION_BONUS = {
    "North": 1.03,
    "East": 1.05,
    "North-East": 1.06,
    "South": 0.98,
    "West": 1.0,
    "South-West": 0.97,
    "North-West": 1.01,
    "South-East": 1.02,
}

FURNISHING_BONUS = {
    "Furnished": 1.08,
    "Semi-Furnished": 1.03,
    "Unfurnished": 1.0,
}

PARKING_OPTIONS = ["Yes", "No"]

REQUIRED_FIELDS = [
    "sqft", "bedrooms", "bathrooms", "age", "floor",
    "direction", "area", "furnishing", "parking",
]


# ---------------------------------------------------------------------------
# Core prediction logic
# ---------------------------------------------------------------------------

def predict_price(data: dict) -> float:
    price = data["sqft"] * BASE_PRICE_PER_SQFT
    price *= AREA_MULTIPLIER[data["area"]]
    price *= DIRECTION_BONUS[data["direction"]]
    price *= FURNISHING_BONUS[data["furnishing"]]
    price += data["bedrooms"] * 8000
    price += data["bathrooms"] * 5000
    price -= data["age"] * 900
    price += data["floor"] * 400
    price += 15000 if data["parking"] == "Yes" else 0
    return max(price, 8000)


def validate_payload(data: dict):
    """Returns an error message string, or None if the payload is valid."""
    if data is None:
        return "Request body must be JSON."

    for field in REQUIRED_FIELDS:
        if field not in data:
            return f"Missing required field: {field}"

    try:
        sqft = float(data["sqft"])
        bedrooms = float(data["bedrooms"])
        bathrooms = float(data["bathrooms"])
        age = float(data["age"])
        floor = float(data["floor"])
    except (TypeError, ValueError):
        return "sqft, bedrooms, bathrooms, age, and floor must be numbers."

    if sqft < 100:
        return "sqft must be at least 100."
    if bedrooms < 0 or bathrooms < 0 or age < 0 or floor < 0:
        return "bedrooms, bathrooms, age, and floor cannot be negative."

    if data["area"] not in AREA_MULTIPLIER:
        return f"area must be one of: {', '.join(AREA_MULTIPLIER)}"
    if data["direction"] not in DIRECTION_BONUS:
        return f"direction must be one of: {', '.join(DIRECTION_BONUS)}"
    if data["furnishing"] not in FURNISHING_BONUS:
        return f"furnishing must be one of: {', '.join(FURNISHING_BONUS)}"
    if data["parking"] not in PARKING_OPTIONS:
        return f"parking must be one of: {', '.join(PARKING_OPTIONS)}"

    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/options", methods=["GET"])
def get_options():
    """Returns the valid dropdown options, so the frontend never hardcodes them."""
    return jsonify({
        "areas": list(AREA_MULTIPLIER.keys()),
        "directions": list(DIRECTION_BONUS.keys()),
        "furnishings": list(FURNISHING_BONUS.keys()),
        "parking": PARKING_OPTIONS,
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    error = validate_payload(data)
    if error:
        return jsonify({"error": error}), 400

    normalized = {
        "sqft": float(data["sqft"]),
        "bedrooms": float(data["bedrooms"]),
        "bathrooms": float(data["bathrooms"]),
        "age": float(data["age"]),
        "floor": float(data["floor"]),
        "direction": data["direction"],
        "area": data["area"],
        "furnishing": data["furnishing"],
        "parking": data["parking"],
    }

    price = predict_price(normalized)

    return jsonify({
        "price": round(price, 2),
        "input": normalized,
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
