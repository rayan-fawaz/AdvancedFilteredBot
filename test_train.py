
import requests
import json

# Training data format - add your coin data here
training_data = [
    {"symbol": "PEPE", "multiplier": 16.4},
    {"symbol": "RUNNER", "multiplier": 4.9},
    {"symbol": "MASK", "multiplier": 4.5},
    {"symbol": "CWOAK", "multiplier": 3.4},
    {"symbol": "CROC", "multiplier": 3.1},
    {"symbol": "SOAP", "multiplier": 3.1},
    {"symbol": "CDOG", "multiplier": 2.8},
    {"symbol": "MEIN", "multiplier": 2.4},
    {"symbol": "POSTY", "multiplier": 1.6},
    {"symbol": "PWS", "multiplier": 1.5},
    {"symbol": "RIB", "multiplier": 1.5},
    {"symbol": "PCRAFT", "multiplier": 1.4},
    {"symbol": "YE", "multiplier": 1.4},
    {"symbol": "STEVE", "multiplier": 1.3},
    {"symbol": "CMG", "multiplier": 1.2},
    {"symbol": "STEVE2", "multiplier": 0},
    {"symbol": "BERRY", "multiplier": 0},
    {"symbol": "SWAS", "multiplier": 0},
    {"symbol": "NWARD", "multiplier": 0},
    {"symbol": "REC", "multiplier": 0},
    {"symbol": "SERG", "multiplier": 0},
    {"symbol": "KIKI", "multiplier": 0},
    {"symbol": "DOWN", "multiplier": 0},
    {"symbol": "DOGEN", "multiplier": 0}
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
