
import requests
import json
import time
import logging
from datetime import datetime, timedelta

def load_tracked_mints():
    try:
        with open("coin_history.json", "r") as f:
            coin_data = json.load(f)
            return {mint: data for mint, data in coin_data.items()}
    except Exception as e:
        logging.error(f"Error loading tracked mints: {e}")
        return {}

def check_bond_status(mint_address):
    try:
        response = requests.get(
            f"https://trench.bot/api/bundle/bundle_advanced/{mint_address}",
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json'
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('bonded', False)
        return False
    except Exception as e:
        logging.error(f"Error checking bond status for {mint_address}: {e}")
        return False

def monitor_bonds():
    logging.basicConfig(level=logging.INFO)
    last_day_cutoff = datetime.now() - timedelta(days=1)
    reported_bonds = set()  # Keep track of coins already reported as bonded
    
    while True:
        tracked_coins = load_tracked_mints()
        
        for mint, data in tracked_coins.items():
            # Check if coin was tracked in last 24 hours and hasn't been reported yet
            if float(data['timestamp']) > last_day_cutoff.timestamp() and mint not in reported_bonds:
                is_bonded = check_bond_status(mint)
                if is_bonded:
                    print(f"\n{data['name']} Just BONDED!!")
                    print(f"Market Cap: ${data['market_cap']:,.2f}")
                    print(f"Mint address: {mint}\n")
                    reported_bonds.add(mint)  # Add to reported set
                    
        time.sleep(60)  # Wait 1 minute before next check

if __name__ == "__main__":
    monitor_bonds()
