
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
        try:
            tracked_coins = load_tracked_mints()
            current_time = datetime.now()
            
            for mint, data in tracked_coins.items():
                try:
                    # Check if coin was tracked in last 24 hours and hasn't been reported yet
                    coin_timestamp = float(data.get('timestamp', 0))
                    if coin_timestamp > last_day_cutoff.timestamp() and mint not in reported_bonds:
                        logging.info(f"Checking bond status for {data.get('name', 'Unknown')} ({mint})")
                        is_bonded = check_bond_status(mint)
                        if is_bonded:
                            message = f"\n{data.get('name', 'Unknown')} Just BONDED!!\n"
                            message += f"Market Cap: ${data.get('market_cap', 0):,.2f}\n"
                            message += f"Mint address: {mint}\n"
                            print(message)
                            reported_bonds.add(mint)  # Add to reported set
                except Exception as e:
                    logging.error(f"Error processing coin {mint}: {e}")
                    continue
                    
            # Update cutoff time
            last_day_cutoff = current_time - timedelta(days=1)
            time.sleep(60)  # Wait 1 minute before next check
            
        except Exception as e:
            logging.error(f"Error in monitor_bonds main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    monitor_bonds()
