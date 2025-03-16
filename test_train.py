import requests
import json

# Training data format - add your coin data here with adjusted confidence metrics
training_data = [
    {"symbol": "RON", "multiplier": 85.5},    # Increased due to consistent performance
    {"symbol": "CHIP", "multiplier": 82.3},   # Adjusted based on market data
    {"symbol": "MANUS", "multiplier": 75.1},  # Strong fundamentals
    {"symbol": "SS", "multiplier": 45.3},     # Moderate performance
    {"symbol": "CROAKCAT", "multiplier": 42.1}, # Adjusted for stability
    {"symbol": "PEPEPEPEPE", "multiplier": 25.6}, # Meta trend adjustment
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