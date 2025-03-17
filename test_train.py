import requests
import json
from datetime import datetime
import asyncio

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

# Dummy CoinTracker class - REPLACE WITH ACTUAL IMPLEMENTATION
class CoinTracker:
    def __init__(self):
        self.tracked_coins = {} #replace with actual data structure

    def get_learning_insights(self):
        return {"status": "No new coins to analyze"} #replace with actual insights

    def predict_profitability(self, coin_data, holder_data, market_data, bundle_data):
      return {"prediction": "Unknown", "confidence": 0.0, "explanation": "No prediction available"}


async def print_learning_analysis():
    """Print learning analysis every 5 minutes"""
    while True:
        tracker = CoinTracker()
        insights = tracker.get_learning_insights()

        if insights["status"] != "No new coins to analyze":
            print("\n=== Learning Analysis Update ===")
            for mint, data in tracker.tracked_coins.items():
                prediction = tracker.predict_profitability(
                    {"name": data["name"], "symbol": data.get("symbol", ""), "mint": mint},
                    {"total_holders": data["total_holders"], "trade_1h": data["trades_1h"]["total"]},
                    {"volume_1h": data["volumes"]["1h"], "price_change_1h": data["price_changes"]["1h"]},
                    {"total_bundles": data["total_bundles"]}
                )
                print(f"\nCoin: {data['name']} ({data.get('symbol', '')})")
                print(f"Prediction: {prediction['prediction']}")
                print(f"Confidence: {prediction['confidence']:.1f}%")
                print(f"Reason: {prediction['explanation']}")

        await asyncio.sleep(300)  # Sleep for 5 minutes

if __name__ == "__main__":
    response = requests.post(
        'http://0.0.0.0:8080/train',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(training_data)
    )

    # Print response
    print(response.status_code)
    print(response.json())

    # Start periodic analysis
    asyncio.run(print_learning_analysis())