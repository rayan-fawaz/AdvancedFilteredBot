import requests
import json
from datetime import datetime

# Enhanced training data with comprehensive metrics
training_data = [
    {"symbol": "FLASH", "multiplier": 92.5, "metrics": {
        "volume_threshold": 50000,
        "holders_min": 200,
        "price_change_min": 100,
        "trades_1h_min": 1000,
        "meta_boost": 1.5
    }},
    {"symbol": "GIGA", "multiplier": 85.2, "metrics": {
        "volume_threshold": 45000,
        "holders_min": 150,
        "price_change_min": 80,
        "trades_1h_min": 800,
        "meta_boost": 1.3
    }},
    {"symbol": "RON", "multiplier": 82.1, "metrics": {
        "volume_threshold": 40000,
        "holders_min": 120,
        "price_change_min": 75,
        "trades_1h_min": 700,
        "meta_boost": 1.2
    }},
    {"symbol": "DOPE", "multiplier": 78.4, "metrics": {
        "volume_threshold": 35000,
        "holders_min": 100,
        "price_change_min": 65,
        "trades_1h_min": 600,
        "meta_boost": 1.1
    }}
]

# Training configuration
config = {
    "volume_weight": 0.25,          # Reduced weight for high volume
    "holder_weight": 0.30,          # Increased weight for holder count
    "price_momentum_weight": 0.20,  # Reduced momentum importance
    "activity_weight": 0.25,        # Increased activity weight
    "confidence_threshold": 80.0,   # Higher threshold for confidence
    "max_confidence": 90.0,         # Lower max confidence cap
    "min_confidence": 0.0,          # Minimum confidence floor
    "volume_min": 10000,           # Minimum volume threshold
    "holders_min": 50,             # Minimum holders threshold
    "trades_min": 100             # Minimum trades threshold
}
    {"symbol": "GOKU", "multiplier": 22.4},   # Anime theme performance
    {"symbol": "FA", "multiplier": 20.3},     # Balanced metrics
    {"symbol": "DOPE", "multiplier": 18.5},   # Community engagement
    {"symbol": "PEPE", "multiplier": 25.6},   # Meta alignment
    {"symbol": "RUNNER", "multiplier": 8.2},  # Lower volume adjustment
    {"symbol": "MASK", "multiplier": 7.5},    # Market sentiment
    {"symbol": "CWOAK", "multiplier": 5.8},   # Reduced confidence
    {"symbol": "CROC", "multiplier": 5.2},    # Market dynamics
    {"symbol": "SOAP", "multiplier": 5.2},    # Similar pattern
    {"symbol": "CDOG", "multiplier": 4.6},    # Limited momentum
    {"symbol": "MEIN", "multiplier": 4.1},    # Risk adjustment
    {"symbol": "POSTY", "multiplier": 2.8},   # Lower confidence
    {"symbol": "PWS", "multiplier": 2.5},     # Market data based
    {"symbol": "RIB", "multiplier": 2.5},     # Consistent with PWS
    {"symbol": "PCRAFT", "multiplier": 2.3},  # Minor adjustment
    {"symbol": "YE", "multiplier": 2.3},      # Similar pattern
    {"symbol": "STEVE", "multiplier": 2.2},   # Low momentum
    {"symbol": "CMG", "multiplier": 2.0},     # Base confidence
    {"symbol": "STEVE2", "multiplier": 0},    # No confidence
    {"symbol": "BERRY", "multiplier": 0},     # Insufficient data
    {"symbol": "SWAS", "multiplier": 0},      # No market activity
    {"symbol": "NWARD", "multiplier": 0},     # Zero confidence
    {"symbol": "REC", "multiplier": 0},       # Not active
    {"symbol": "SERG", "multiplier": 0},      # No trading
    {"symbol": "KIKI", "multiplier": 0},      # Inactive
    {"symbol": "DOWN", "multiplier": 0},      # No market
    {"symbol": "DOGEN", "multiplier": 0}      # Zero activity
]

# Send POST request to the training endpoint
response = requests.post(
    'http://0.0.0.0:8080/train',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(training_data)
)

# Print response
print(response.status_code)
print(response.json())