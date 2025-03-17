import requests
import json
from datetime import datetime

# Enhanced training data with comprehensive metrics and historical performance
training_data = [
    {"symbol": "Nicky", "multiplier": 44.5},
    {"symbol": "GREG", "multiplier": 43.1},
    {"symbol": "Boobs", "multiplier": 17.6},
    {"symbol": "YWH", "multiplier": 17.0},
    {"symbol": "horse", "multiplier": 16.3},
    {"symbol": "crane", "multiplier": 12.5},
    {"symbol": "HSEAL", "multiplier": 12.4},
    {"symbol": "thewolf", "multiplier": 12.4},
    {"symbol": "BLOCK0", "multiplier": 12.1},
    {"symbol": "lucky", "multiplier": 9.3},
    {"symbol": "BONGO", "multiplier": 8.6},
    {"symbol": "SOLCHAUN", "multiplier": 6.3},
    {"symbol": "Ermygosh", "multiplier": 6.1},
    {"symbol": "TEA", "multiplier": 6.0},
    {"symbol": "OMAR", "multiplier": 5.5},
    {"symbol": "Ethereum", "multiplier": 5.5},
    {"symbol": "Dino", "multiplier": 5.2},
    {"symbol": "LQPEPE", "multiplier": 5.2},
    {"symbol": "YECODE", "multiplier": 5.0},
    {"symbol": "Jacob", "multiplier": 4.8},
    {"symbol": "SHADOW", "multiplier": 4.8},
    {"symbol": "NISHIYAMA", "multiplier": 4.6},
    {"symbol": "fappi", "multiplier": 4.5},
    {"symbol": "bil", "multiplier": 4.0},
    {"symbol": "StPepe", "multiplier": 3.7},
    {"symbol": "clover", "multiplier": 3.4},
    {"symbol": "RLBC", "multiplier": 3.3},
    {"symbol": "Son", "multiplier": 3.3},
    {"symbol": "Dwude", "multiplier": 3.3},
    {"symbol": "MYZY", "multiplier": 3.2},
    {"symbol": "FLASHYE", "multiplier": 3.2},
    {"symbol": "FIGARO", "multiplier": 2.9},
    {"symbol": "KINGRAT", "multiplier": 2.8},
    {"symbol": "PWINDIAN", "multiplier": 2.8},
    {"symbol": "jemua", "multiplier": 2.8},
    {"symbol": "Fresita", "multiplier": 2.6},
    {"symbol": "ParentTok", "multiplier": 2.6},
    {"symbol": "royalty", "multiplier": 2.5},
    {"symbol": "KKKanye", "multiplier": 2.4},
    {"symbol": "lqquality", "multiplier": 2.2},
    {"symbol": "sharkybara", "multiplier": 2.2},
    {"symbol": "lqneji", "multiplier": 2.2},
    {"symbol": "pepe", "multiplier": 2.1},
    {"symbol": "UwU", "multiplier": 2.1},
    {"symbol": "LQL", "multiplier": 2.1},
    {"symbol": "Sharky", "multiplier": 2.1},
    {"symbol": "WATER", "multiplier": 2.1},
    {"symbol": "RETARD", "multiplier": 2.1},
    {"symbol": "Ruben", "multiplier": 2.1},
    {"symbol": "💸", "multiplier": 2.1},
    {"symbol": "JAPANESE", "multiplier": 1.9},
    {"symbol": "DOWNSAN", "multiplier": 1.9},
    {"symbol": "lq9/11", "multiplier": 1.8},
    {"symbol": "VANUATU", "multiplier": 1.8},
    {"symbol": "boringdude", "multiplier": 1.8},
    {"symbol": "LQY", "multiplier": 1.7},
    {"symbol": "PuffPuff", "multiplier": 1.6},
    {"symbol": "EILQ", "multiplier": 1.6},
    {"symbol": "Female", "multiplier": 1.6},
    {"symbol": "lqt", "multiplier": 1.5},
    {"symbol": "LQB", "multiplier": 1.5},
    {"symbol": "Ahegao", "multiplier": 1.5},
    {"symbol": "PARME-SAN", "multiplier": 1.5},
    {"symbol": "LQC", "multiplier": 1.5},
    {"symbol": "Bagay-san", "multiplier": 1.4},
    {"symbol": "STICK", "multiplier": 1.3},
    {"symbol": "Punny", "multiplier": 1.3},
    {"symbol": "LQP", "multiplier": 1.2},
    {"symbol": "LQI", "multiplier": 0},
    {"symbol": "YESAN", "multiplier": 0},
    {"symbol": "DOG(b²-4)", "multiplier": 0}
]

# Training configuration
config = {
    "volume_weight": 0.35,
    "holder_weight": 0.25,
    "price_momentum_weight": 0.25,
    "activity_weight": 0.15,
    "confidence_threshold": 65.0
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