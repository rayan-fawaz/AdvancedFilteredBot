
import requests
import json

# Training data format
training_data = [
    {"ticker": "PEPEPEPEPE", "multiplier": 16.4},
    {"ticker": "RUNNER", "multiplier": 4.9},
    {"ticker": "Maskhole", "multiplier": 4.5}
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
