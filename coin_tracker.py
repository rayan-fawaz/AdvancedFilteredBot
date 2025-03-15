
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
        import os
        # Use Replit's persistent storage directory if available
        storage_dir = os.getenv('REPL_HOME', '.')
        self.db_file = os.path.join(storage_dir, "coin_history.json")
        self.meta_file = os.path.join(storage_dir, "meta_scores.json")
        self.tracked_coins = self.load_history()
        self.meta_scores = self.load_meta_scores()

    def load_meta_scores(self):
        """Load current meta scores from file."""
        try:
            with open(self.meta_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_meta_scores(self):
        """Save current meta scores to file."""
        with open(self.meta_file, 'w') as f:
            json.dump(self.meta_scores, f, indent=2)

    def update_meta_scores(self, new_scores):
        """Update meta scores with new data."""
        self.meta_scores = new_scores
        self.save_meta_scores()
        
    def load_history(self) -> Dict:
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def save_history(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.tracked_coins, f, indent=2)
            
    def predict_profitability(self, coin, holders_info, dex_data, trench_data):
        """Predict if a coin will be profitable based on initial metrics and meta scores"""
        score = 0
        reasons = []
        
        # Check if coin name/symbol contains meta words
        coin_text = f"{coin['name']} {coin['symbol']}".lower()
        for meta_word, meta_score in self.meta_scores.items():
            if meta_word in coin_text:
                meta_boost = meta_score * 2  # Convert meta score to points
                score += meta_boost
                reasons.append(f"Contains meta '{meta_word}' (+{meta_boost:.1f})")
        
        # Volume analysis
        if dex_data['volume_1h'] > 50000:
            score += 2
            reasons.append("Strong hourly volume")
        elif dex_data['volume_1h'] > 20000:
            score += 1
            reasons.append("Decent hourly volume")
        else:
            reasons.append("Low volume")
        
        # Price momentum
        if dex_data['price_change_1h'] > 200:
            score += 2
            reasons.append("Excellent price momentum")
        elif dex_data['price_change_1h'] > 100:
            score += 1
            reasons.append("Good price momentum")
        else:
            reasons.append("Weak momentum")
        
        # Holder metrics
        if holders_info['total_holders'] > 200:
            score += 2
            reasons.append("Strong holder base")
        elif holders_info['total_holders'] > 100:
            score += 1
            reasons.append("Growing holder base")
        else:
            reasons.append("Few holders")
        
        # Trade activity
        if holders_info['trade_1h'] > 2000:
            score += 2
            reasons.append("Very active trading")
        elif holders_info['trade_1h'] > 1000:
            score += 1
            reasons.append("Good trading activity")
        else:
            reasons.append("Low trading activity")
        
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
        
        return {
            'score': score,
            'confidence': (score / 10) * 100,  # Convert to percentage
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
        
    def train_model_with_returns(self, returns_data: Dict[str, float]):
        """Train model with actual return data from tracked coins"""
        for mint, actual_return in returns_data.items():
            if mint in self.tracked_coins:
                # Update coin data with actual return
                self.tracked_coins[mint]['actual_return'] = actual_return
                self.tracked_coins[mint]['verified'] = True
                
                # Adjust prediction weights based on accuracy
                prediction = self.tracked_coins[mint]['prediction_result']
                if (prediction == "Likely Profitable" and actual_return > 0) or \
                   (prediction == "High Risk" and actual_return < 0):
                    # Correct prediction - strengthen the weights
                    self.volume_weight *= 1.1
                    self.momentum_weight *= 1.1
                else:
                    # Wrong prediction - reduce the weights
                    self.volume_weight *= 0.9
                    self.momentum_weight *= 0.9
                
        self.save_history()
        
    def get_learning_insights(self) -> Dict:
        """Analyze what the model has learned from training data"""
        # Analyze verified coins (ones we have actual returns for)
        verified_coins = {k: v for k, v in self.tracked_coins.items() if v.get('verified', False)}
        
        if not verified_coins:
            return {
                "status": "No verified training data yet",
                "insights": []
            }

        # Get profitable vs unprofitable counts
        profitable = [c for c in verified_coins.values() if c.get('actual_return', 0) > 0]
        unprofitable = [c for c in verified_coins.values() if c.get('actual_return', 0) <= 0]
        
        insights = []
        
        # Compare metrics between profitable and unprofitable coins
        if profitable and unprofitable:
            prof_avg_holders = sum(c['total_holders'] for c in profitable) / len(profitable)
            unprof_avg_holders = sum(c['total_holders'] for c in unprofitable) / len(unprofitable)
            
            prof_avg_bundles = sum(c['total_bundles'] for c in profitable) / len(profitable)
            unprof_avg_bundles = sum(c['total_bundles'] for c in unprofitable) / len(unprofitable)
            
            prof_avg_trades = sum(c['trades_1h']['total'] for c in profitable) / len(profitable)
            unprof_avg_trades = sum(c['trades_1h']['total'] for c in unprofitable) / len(unprofitable)
            
            insights.extend([
                f"Profitable coins avg {prof_avg_holders:.0f} holders vs {unprof_avg_holders:.0f} for unprofitable",
                f"Profitable coins avg {prof_avg_bundles:.1f} bundles vs {unprof_avg_bundles:.1f} for unprofitable",
                f"Profitable coins avg {prof_avg_trades:.0f} trades/hr vs {unprof_avg_trades:.0f} for unprofitable"
            ])
            
            # Add insights about prediction accuracy
            correct_predictions = sum(1 for c in verified_coins.values() 
                                   if (c['prediction_result'] == "Likely Profitable" and c.get('actual_return', 0) > 0) or
                                   (c['prediction_result'] == "High Risk" and c.get('actual_return', 0) <= 0))
            accuracy = (correct_predictions / len(verified_coins)) * 100
            insights.append(f"Model prediction accuracy: {accuracy:.1f}%")

        return {
            "status": "Learning from verified coins",
            "total_verified": len(verified_coins),
            "profitable_count": len(profitable),
            "unprofitable_count": len(unprofitable),
            "insights": insights
        }

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



    def analyze_coin_patterns(self):
        """Analyze patterns between profitable and unprofitable coins"""
        profitable_coins = []
        unprofitable_coins = []
        
        for mint, data in self.tracked_coins.items():
            if 'actual_return' in data:
                coin_metrics = {
                    'name': data['name'],
                    'initial_market_cap': data['initial_market_cap'],
                    'volume_1h': data['volumes']['1h'],
                    'price_change_1h': data['price_changes']['1h'],
                    'total_holders': data['total_holders'],
                    'total_bundles': data['total_bundles'],
                    'trades_1h': data['trades_1h']['total'],
                    'makers_1h': data['makers_1h'],
                    'return': data['actual_return']
                }
                
                if data['actual_return'] > 0:
                    profitable_coins.append(coin_metrics)
                else:
                    unprofitable_coins.append(coin_metrics)
        
        if not profitable_coins or not unprofitable_coins:
            return "Not enough data for analysis"
            
        analysis = {
            'profitable_averages': self._calculate_averages(profitable_coins),
            'unprofitable_averages': self._calculate_averages(unprofitable_coins),
            'key_differences': {}
        }
        
        # Calculate differences
        for metric in analysis['profitable_averages'].keys():
            if metric != 'count':
                diff = analysis['profitable_averages'][metric] - analysis['unprofitable_averages'][metric]
                analysis['key_differences'][metric] = {
                    'difference': diff,
                    'percentage': (diff / analysis['unprofitable_averages'][metric]) * 100 if analysis['unprofitable_averages'][metric] != 0 else 0
                }
        
        return analysis

    def _calculate_averages(self, coins):
        """Calculate average metrics for a group of coins"""
        if not coins:
            return {}
            
        totals = {
            'initial_market_cap': 0,
            'volume_1h': 0,
            'price_change_1h': 0,
            'total_holders': 0,
            'total_bundles': 0,
            'trades_1h': 0,
            'makers_1h': 0,
            'return': 0
        }
        
        for coin in coins:
            for key in totals:
                totals[key] += coin[key]
        
        return {
            'count': len(coins),
            'initial_market_cap': totals['initial_market_cap'] / len(coins),
            'volume_1h': totals['volume_1h'] / len(coins),
            'price_change_1h': totals['price_change_1h'] / len(coins),
            'total_holders': totals['total_holders'] / len(coins),
            'total_bundles': totals['total_bundles'] / len(coins),
            'trades_1h': totals['trades_1h'] / len(coins),
            'makers_1h': totals['makers_1h'] / len(coins),
            'avg_return': totals['return'] / len(coins)
        }
