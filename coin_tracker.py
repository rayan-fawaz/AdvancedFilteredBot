
import json
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional

@dataclass
class CoinData:
    mint: str
    name: str
    symbol: str
    market_cap: float
    total_bundles: int
    holding_percentage: float
    price_changes: Dict[str, float]
    volumes: Dict[str, float]
    ath: float
    total_holders: int
    trades_1h: Dict[str, int]
    makers_1h: int
    makers_24h: int
    timestamp: float
    initial_price: float
    initial_market_cap: float
    prediction_score: float
    prediction_confidence: float
    prediction_result: str
    ath_24h: Optional[float] = None
    ath_market_cap_24h: Optional[float] = None
    ath_timestamp_24h: Optional[float] = None

class CoinTracker:
    def __init__(self):
        self.db_file = "coin_history.json"
        self.tracked_coins = self.load_history()
        
    def load_history(self) -> Dict:
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def save_history(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.tracked_coins, f, indent=2)
            
    def predict_profitability(self, holders_info, dex_data, trench_data):
        """Predict if a coin will be profitable based on CSV data analysis"""
        score = 0
        reasons = []
        
        # Volume analysis - based on profitable coins data
        if dex_data['volume_1h'] > 25000:  # Some profitable coins had >20k volume
            score += 2
            reasons.append("Strong hourly volume")
        elif dex_data['volume_1h'] > 10000:  # Most profitable had >10k
            score += 1
            reasons.append("Decent hourly volume")
        else:
            reasons.append("Low volume")
            
        # Price momentum check
        if dex_data['price_change_1h'] > 160:  # Several profitable had >150%
            score += 2
            reasons.append("Excellent price momentum")
        elif dex_data['price_change_1h'] > 85:  # Most profitable had >80%
            score += 1
            reasons.append("Good price momentum")
        else:
            reasons.append("Weak momentum")
            
        # Trade activity analysis
        if holders_info['trade_1h'] > 300:  # Profitable coins averaged >300
            score += 2
            reasons.append("High trading activity")
        elif holders_info['trade_1h'] > 150:  # Most had >150
            score += 1
            reasons.append("Good trading activity")
        else:
            reasons.append("Low trading activity")
            
        # Maker activity (unique wallets)
        if holders_info['unique_wallet_1h'] > 180:  # Some profitable had >200
            score += 2 
            reasons.append("Strong maker activity")
        elif holders_info['unique_wallet_1h'] > 90:  # Most had >80
            score += 1
            reasons.append("Good maker activity")
        else:
            reasons.append("Low maker activity")
            
        # Holder base check
        if holders_info['total_holders'] > 45:  # Most profitable had >40
            score += 2
            reasons.append("Solid holder base")
        elif holders_info['total_holders'] > 30:  # Minimum successful threshold
            score += 1
            reasons.append("Growing holder base")
        else:
            reasons.append("Few holders")
            
        # Bundle analysis - low count is positive
        if trench_data and trench_data.get('total_bundles', 0) < 50:
            score += 2
            reasons.append("Strong holder base")
        elif holders_info['total_holders'] > 45:
            score += 1
            reasons.append("Growing holder base")
        else:
            reasons.append("Few holders")
            
        # Trade activity - thresholds from profitable examples
        if holders_info['trade_1h'] > 500:
            score += 2
            reasons.append("Very active trading")
        elif holders_info['trade_1h'] > 300:
            score += 1  
            reasons.append("Good trading activity")
        else:
            reasons.append("Low trading activity")
            
        # Maker activity - new metric based on data
        if holders_info['unique_wallet_1h'] > 200:
            score += 2
            reasons.append("High maker engagement")
        elif holders_info['unique_wallet_1h'] > 100:
            score += 1
            reasons.append("Good maker activity")
        else:
            reasons.append("Low maker activity")
        
        # Bundle analysis - low bundle count is good
        if trench_data and trench_data.get('total_bundles', 0) < 50:
            score += 2
            reasons.append("Favorable low bundle count")
        
        result = "Likely Profitable" if score >= 6 else "High Risk"
        explanation = ""
        if score >= 6:
            explanation = "Strong fundamentals: " + ", ".join(r for r in reasons if not r.startswith("Low") and not r.startswith("Weak") and not r.startswith("Few"))
        else:
            explanation = "Concerning factors: " + ", ".join(r for r in reasons if r.startswith("Low") or r.startswith("Weak") or r.startswith("Few"))
        
        # Cap confidence at 100%
        confidence = min((score / 10) * 100, 100.0)
        return {
            'score': score,
            'confidence': confidence,
            'prediction': result,
            'explanation': explanation
        }

    def track_coin(self, coin, holders_info, dex_data, trench_data):
        prediction = self.predict_profitability(holders_info, dex_data, trench_data)
        coin_data = CoinData(
            mint=coin["mint"],
            name=coin["name"],
            symbol=coin["symbol"],
            market_cap=coin["usd_market_cap"],
            total_bundles=trench_data.get("total_bundles", 0) if trench_data else 0,
            holding_percentage=trench_data.get("total_holding_percentage", 0) if trench_data else 0,
            price_changes={
                "5m": dex_data["price_change_5m"],
                "1h": dex_data["price_change_1h"],
                "6h": dex_data["price_change_6h"],
                "24h": dex_data["price_change_24h"]
            },
            volumes={
                "5m": dex_data["volume_5m"],
                "1h": dex_data["volume_1h"],
                "6h": dex_data["volume_6h"],
                "24h": dex_data["volume_24h"]
            },
            ath=dex_data.get("ath_price", coin["usd_market_cap"]),
            total_holders=holders_info["total_holders"],
            trades_1h={
                "total": holders_info["trade_1h"],
                "buys": holders_info["buy_1h"],
                "sells": holders_info["sell_1h"]
            },
            makers_1h=holders_info["unique_wallet_1h"],
            makers_24h=holders_info["unique_wallet_24h"],
            timestamp=datetime.now().timestamp(),
            initial_price=dex_data.get("price_usd", 0),
            initial_market_cap=coin["usd_market_cap"],
            prediction_score=prediction['score'],
            prediction_confidence=prediction['confidence'],
            prediction_result=prediction['prediction'],
            ath_24h=None,
            ath_market_cap_24h=None,
            ath_timestamp_24h=None
        )
        
        self.tracked_coins[coin["mint"]] = asdict(coin_data)
        self.save_history()
        
    def analyze_returns(self, current_prices: Dict[str, float]) -> Dict:
        current_time = datetime.now().timestamp()
        results = {}
        for mint, data in self.tracked_coins.items():
            if mint in current_prices:
                initial_price = data["initial_price"]
                current_price = current_prices[mint]
                time_since_tracking = current_time - data["timestamp"]
                
                # Update 24h ATH if within first 24 hours
                if time_since_tracking <= 86400:  # 24 hours in seconds
                    current_market_cap = current_price * (data["initial_market_cap"] / data["initial_price"])
                    if not data["ath_24h"] or current_price > data["ath_24h"]:
                        self.tracked_coins[mint]["ath_24h"] = current_price
                        self.tracked_coins[mint]["ath_market_cap_24h"] = current_market_cap
                        self.tracked_coins[mint]["ath_timestamp_24h"] = current_time
                        self.save_history()
                
                roi = ((current_price - initial_price) / initial_price) * 100
                market_cap_roi = ((current_market_cap - data["initial_market_cap"]) / data["initial_market_cap"] * 100) if "initial_market_cap" in data else 0
                results[mint] = {
                    "name": data["name"],
                    "symbol": data["symbol"],
                    "roi": roi,
                    "market_cap_roi": market_cap_roi,
                    "initial_price": initial_price,
                    "current_price": current_price,
                    "initial_market_cap": data["initial_market_cap"],
                    "current_market_cap": current_market_cap,
                    "ath_24h": data["ath_24h"],
                    "ath_market_cap_24h": data["ath_market_cap_24h"],
                    "market_cap": data["market_cap"],
                    "total_bundles": data["total_bundles"],
                    "holding_percentage": data["holding_percentage"],
                    "price_changes": data["price_changes"],
                    "volumes": data["volumes"],
                    "total_holders": data["total_holders"],
                    "trades_1h": data["trades_1h"],
                    "makers": {
                        "1h": data["makers_1h"],
                        "24h": data["makers_24h"]
                    }
                }
        return results
