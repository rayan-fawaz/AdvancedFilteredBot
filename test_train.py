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
    {"symbol": "DOG(b²-4)", "multiplier": 0},
    {"symbol": "GOKU", "multiplier": 22.4},   
    {"symbol": "FA", "multiplier": 20.3},     
    {"symbol": "DOPE", "multiplier": 18.5},   
    {"symbol": "PEPE", "multiplier": 25.6},   
    {"symbol": "RUNNER", "multiplier": 8.2},  
    {"symbol": "MASK", "multiplier": 7.5},    
    {"symbol": "CWOAK", "multiplier": 5.8},   
    {"symbol": "CROC", "multiplier": 5.2},    
    {"symbol": "SOAP", "multiplier": 5.2},    
    {"symbol": "CDOG", "multiplier": 4.6},    
    {"symbol": "MEIN", "multiplier": 4.1},    
    {"symbol": "POSTY", "multiplier": 2.8},   
    {"symbol": "PWS", "multiplier": 2.5},     
    {"symbol": "RIB", "multiplier": 2.5},     
    {"symbol": "PCRAFT", "multiplier": 2.3},  
    {"symbol": "YE", "multiplier": 2.3},      
    {"symbol": "STEVE", "multiplier": 2.2},   
    {"symbol": "CMG", "multiplier": 2.0},     
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

# Training configuration
config = {
    "volume_weight": 0.35,
    "holder_weight": 0.25,
    "price_momentum_weight": 0.25,
    "activity_weight": 0.15,
    "confidence_threshold": 65.0
}

async def send_telegram_message(message):
    # Replace with your actual Telegram bot token and chat ID
    bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id = "YOUR_TELEGRAM_CHAT_ID"
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(api_url, json={"chat_id": chat_id, "text": message})
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")


async def analyze_and_print_learning():
    """Print and send learning analysis every 5 minutes"""
    while True:
        analysis_text = "\n=== AI Learning Analysis ===\n"

        # Group coins by performance tiers
        elite_performers = [c for c in training_data if c.get('multiplier', 0) > 40]
        strong_performers = [c for c in training_data if 10 < c.get('multiplier', 0) <= 40]
        good_performers = [c for c in training_data if 5 < c.get('multiplier', 0) <= 10]
        moderate_performers = [c for c in training_data if 2 < c.get('multiplier', 0) <= 5]
        weak_performers = [c for c in training_data if 0 < c.get('multiplier', 0) <= 2]
        non_performers = [c for c in training_data if c.get('multiplier', 0) == 0]

        # Build comprehensive analysis
        analysis_text += "🌟 Performance Analysis:\n\n"

        if elite_performers:
            analysis_text += "🏆 Elite Performers (>40x):\n"
            for coin in elite_performers:
                analysis_text += f"   • {coin['symbol']}: {coin['multiplier']}x\n"

        if strong_performers:
            analysis_text += "\n💪 Strong Performers (10-40x):\n"
            for coin in strong_performers:
                analysis_text += f"   • {coin['symbol']}: {coin['multiplier']}x\n"

        if good_performers:
            analysis_text += "\n✨ Good Performers (5-10x):\n"
            for coin in good_performers:
                analysis_text += f"   • {coin['symbol']}: {coin['multiplier']}x\n"

        if moderate_performers:
            analysis_text += "\n📈 Moderate Performers (2-5x):\n"
            for coin in moderate_performers:
                analysis_text += f"   • {coin['symbol']}: {coin['multiplier']}x\n"

        analysis_text += f"\n📊 Statistics:\n"
        analysis_text += f"   • Total Coins Analyzed: {len(training_data)}\n"
        analysis_text += f"   • High Performers (>10x): {len(elite_performers) + len(strong_performers)}\n"
        analysis_text += f"   • Active Performers (>0x): {len(training_data) - len(non_performers)}\n"

        # Print to console
        print(analysis_text)

        # Send to Telegram
        await send_telegram_message(analysis_text)

        # Wait for 5 minutes
        await asyncio.sleep(300)

# Send POST request to the training endpoint
response = requests.post(
    'http://0.0.0.0:8080/train',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(training_data)
)

# Print response
print(response.status_code)
print(response.json())

async def main():
    await analyze_and_print_learning()

if __name__ == "__main__":
    asyncio.run(main())