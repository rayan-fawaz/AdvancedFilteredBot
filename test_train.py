
import requests
import json

# Training data format - add your coin data here
training_data = [
    {"ticker": "PEPEPEPEPE", "multiplier": 16.4},
    {"ticker": "RUNNER", "multiplier": 4.9},
    {"ticker": "Maskhole", "multiplier": 4.5},
    {"ticker": "cwoak", "multiplier": 3.4},
    {"ticker": "croakcat", "multiplier": 3.1},
    {"ticker": "SOAP", "multiplier": 3.1},
    {"ticker": "CROCDOG", "multiplier": 2.8},
    {"ticker": "MEIN", "multiplier": 2.4},
    {"ticker": "POSTY", "multiplier": 1.6},
    {"ticker": "pwease", "multiplier": 1.5},
    {"ticker": "RIB", "multiplier": 1.5},
    {"ticker": "PCRAFT", "multiplier": 1.4},
    {"ticker": "YE-OS", "multiplier": 1.4},
    {"ticker": "STWEVE", "multiplier": 1.3},
    {"ticker": "CMG", "multiplier": 1.2},
    {"ticker": "STEVESTEVE", "multiplier": 0},
    {"ticker": "berrycat", "multiplier": 0},
    {"ticker": "Swasticat", "multiplier": 0},
    {"ticker": "NWard", "multiplier": 0},
    {"ticker": "RECESSION", "multiplier": 0},
    {"ticker": "sergio", "multiplier": 0},
    {"ticker": "KIKI", "multiplier": 0},
    {"ticker": "DOWNCANDLE", "multiplier": 0},
    {"ticker": "dogen", "multiplier": 0}
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
