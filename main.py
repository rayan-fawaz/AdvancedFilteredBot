import requests
import asyncio
import logging
from datetime import datetime, timezone, timedelta

# Telegram API (still used for sending messages)
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN",
                           "8046651136:AAGHoEFIJhW3zHTe6CI0iOcn6FgePpljXqM")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "-1002429691769")

# Featured Coins API
API_URL = "https://frontend-api-v3.pump.fun/coins/for-you?offset=0&limit=50&includeNsfw=false"

# Helius API
HELIUS_API_KEY = "d2eb41e9-0474-45d9-8c53-f487ac8fdd96"
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Filter Constants
MIN_HOLDERS = 25
MIN_TRADES_1H = 80
MAX_VOLUME_5M = 20000
BIGGEST_WALLET_MAX = 5  # Maximum percentage for the biggest wallet
MIN_BUYS = 40  # Minimum buy transactions in 1h
MIN_SELLS = 40  # Minimum sell transactions in 1h

# Price Momentum Filters
MIN_PRICE_5M = 30
MIN_PRICE_1H = 80
HIGH_PRICE_1H = 95

# Volume Filters
MIN_VOLUME_5M = 3000
MIN_VOLUME_1H = 10000

# Market Cap Limits
MIN_MARKET_CAP = 7000

def get_score_reasons(coin_data):
    reasons = []
    if coin_data.get('volumes', {}).get('1h', 0) > 50000:
        reasons.append('high volume')
    if coin_data.get('price_changes', {}).get('1h', 0) > 100:
        reasons.append('strong momentum')
    if coin_data.get('total_holders', 0) > 100:
        reasons.append('good holder count')
    if coin_data.get('trades_1h', {}).get('total', 0) > 1000:
        reasons.append('active trading')
    if coin_data.get('total_bundles', 0) < 50:
        reasons.append('low bundle count')
    return reasons or ['market metrics']


MAX_MARKET_CAP = 25000

# Logging Configuration
logging.basicConfig(level=logging.INFO)


async def fetch_active_coins():
    """Fetch featured coins from the Pump.Fun API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching coins: {e}")
        return []


async def send_telegram_message(message, chat_id=GROUP_ID):
    """Send a message to the Telegram group or specific chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")

async def handle_telegram_updates():
    """Handle incoming Telegram messages."""
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            response = requests.get(url, params=params)
            updates = response.json()

            if "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        message = update["message"]["text"]
                        chat_id = update["message"]["chat"]["id"]

                        if message.startswith("/train"):
                            try:
                                # Parse training data in format "TICKER [Xx]"
                                lines = message[6:].strip().split('\n')
                                training_data = {}
                                for line in lines:
                                    if '[' in line and ']' in line and 'x]' in line:
                                        parts = line.replace('$', '').strip().split('[')
                                        if len(parts) == 2:
                                            ticker = parts[0].strip()
                                            multiplier = float(parts[1].split('x]')[0].strip())
                                            # Consider trades >= 2.5x as successful
                                            training_data[ticker] = 1.0 if multiplier >= 2.5 else 0.0
                                
                                if training_data:
                                    logging.info(f"Training data parsed: {training_data}")
                                    await send_telegram_message("Parsed training data. Training model...", chat_id)
                                
                                if training_data:
                                    # Train the model
                                    tracker = CoinTracker()
                                    tracker.train_model_with_returns(training_data)
                                    await send_telegram_message(f"Model trained successfully with {len(training_data)} trades!", chat_id)
                                else:
                                    await send_telegram_message("No valid training data found. Format should be: TICKER [Xx]", chat_id)
                            except Exception as e:
                                await send_telegram_message(f"Error training model: {str(e)}", chat_id)
                                
        except Exception as e:
            logging.error(f"Error handling Telegram updates: {e}")
        await asyncio.sleep(1)


def get_dex_data(token_mint):
    """Get volume and price change data from DexScreener and Moralis APIs."""
    try:
        # DexScreener data
        dex_response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{token_mint}",
            timeout=10)
        dex_response.raise_for_status()

        # Moralis pair data for additional details (optional)
        moralis_url = f"https://solana-gateway.moralis.io/token/mainnet/{token_mint}/pairs"
        moralis_headers = {
            "Accept": "application/json",
            "X-API-Key":
            "YOUR_MORALIS_API_KEY"  # Replace with your Moralis API key
        }
        moralis_response = requests.get(moralis_url,
                                        headers=moralis_headers,
                                        timeout=10)
        pair_address = None
        if moralis_response.ok:
            pair_data = moralis_response.json()
            if isinstance(pair_data, dict) and "pairs" in pair_data:
                pairs = pair_data["pairs"]
                if pairs and isinstance(pairs, list) and len(pairs) > 0:
                    pair_address = pairs[0].get("pairAddress")

        # OHLCV data from Moralis (ATH estimation)
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        one_month_ago = (datetime.now(timezone.utc) -
                         timedelta(days=30)).strftime('%Y-%m-%d')
        ohlcv_url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pair_address}/ohlcv?timeframe=1M&currency=usd&fromDate={one_month_ago}&toDate={current_date}&limit=10"
        ohlcv_headers = {
            "Accept": "application/json",
            "X-API-Key":
            "YOUR_MORALIS_API_KEY"  # Replace with your Moralis API key
        }
        ohlcv_response = requests.get(ohlcv_url, headers=ohlcv_headers)
        ohlcv_data = ohlcv_response.json()

        ath_price = None
        if 'result' in ohlcv_data and len(ohlcv_data['result']) > 0:
            high = ohlcv_data['result'][0].get('high')
            if high:
                ath_price = round(high * 1000000000)

        data = dex_response.json()
        if 'pairs' in data and len(data['pairs']) > 0:
            pair = data['pairs'][0]
            return {
                'volume_24h':
                float(pair.get('volume', {}).get('h24', 0)),
                'volume_6h':
                float(pair.get('volume', {}).get('h6', 0)),
                'volume_1h':
                float(pair.get('volume', {}).get('h1', 0)),
                'volume_5m':
                float(pair.get('volume', {}).get('m5', 0)),
                'price_change_24h':
                float(pair.get('priceChange', {}).get('h24', 0)),
                'price_change_6h':
                float(pair.get('priceChange', {}).get('h6', 0)),
                'price_change_1h':
                float(pair.get('priceChange', {}).get('h1', 0)),
                'price_change_5m':
                float(pair.get('priceChange', {}).get('m5', 0)),
                'pair_address':
                pair_address,
                'ath_price':
                ath_price
            }
        return None
    except Exception as e:
        logging.error(f"Error fetching DEX data for {token_mint}: {e}")
        return None


def fetch_unique_reply_makers(mint_address):
    """Fetch and count unique reply makers for a given coin."""
    try:
        # Try a different API endpoint that might work better
        replies_url = f"https://pump.fun/api/v1/replies?address={mint_address}"
        logging.info(f"Trying alternative replies API: {replies_url}")

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(replies_url, headers=headers, timeout=15)

        # Log detailed response info
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response headers: {response.headers}")

        # Try to parse the JSON response
        try:
            data = response.json()
            # Log a sample of the data to understand structure
            logging.info(f"API response structure: {str(data)[:1000]}"
                         )  # Log first 1000 chars
        except Exception as json_err:
            logging.error(f"JSON parsing error: {json_err}")
            logging.info(f"Raw response content: {response.text[:500]}..."
                         )  # Log first 500 chars

            # Let's try the original API endpoint as fallback
            fallback_url = f"https://frontend-api-v3.pump.fun/replies/{mint_address}?limit=1000&offset=0"
            logging.info(f"Trying fallback API: {fallback_url}")
            fallback_response = requests.get(fallback_url,
                                             headers=headers,
                                             timeout=15)
            try:
                data = fallback_response.json()
                logging.info(
                    f"Fallback API response structure: {str(data)[:1000]}")
            except Exception:
                return 0

        # Extract replies from various possible API structures
        replies = []

        # For original API structure (list format)
        if isinstance(data, list):
            replies = data
            logging.info(f"Found {len(replies)} replies in list format")

        # For newer API with nested 'data' structure
        elif isinstance(data, dict):
            if "data" in data:
                if isinstance(data["data"], list):
                    replies = data["data"]
                    logging.info(f"Found {len(replies)} replies in data list")
                elif isinstance(data["data"],
                                dict) and "replies" in data["data"]:
                    replies = data["data"]["replies"]
                    logging.info(
                        f"Found {len(replies)} replies in nested data.replies")
            elif "replies" in data:
                replies = data["replies"]
                logging.info(
                    f"Found {len(replies)} replies in top-level replies field")

        # Process the replies to count unique users
        unique_users = set()

        # Log one complete reply for debugging
        if len(replies) > 0:
            logging.info(f"Sample reply structure: {replies[0]}")

        for reply in replies:
            if not isinstance(reply, dict):
                continue

            # Log each reply's user info for debugging
            if "user" in reply:
                logging.info(f"User field in reply: {reply['user']}")

            # First try - standard user structure
            if "user" in reply and reply["user"]:
                user = reply["user"]
                if isinstance(user, dict):
                    user_id = None
                    # Try all possible ID fields
                    for id_field in [
                            "walletAddress", "id", "username", "address",
                            "publicKey", "wallet"
                    ]:
                        if id_field in user and user[id_field]:
                            user_id = user[id_field]
                            logging.info(
                                f"Found user ID in field {id_field}: {user_id}"
                            )
                            break

                    if user_id:
                        unique_users.add(user_id)
                    else:
                        # If we couldn't find an ID field, use the whole user object as a string
                        unique_users.add(str(user))

            # Try alternative field names
            for field in [
                    "owner", "author", "creator", "walletAddress", "publicKey"
            ]:
                if field in reply and reply[field]:
                    unique_users.add(str(reply[field]))
                    logging.info(
                        f"Found user in {field} field: {reply[field]}")

        maker_count = len(unique_users)
        logging.info(
            f"Found {maker_count} unique reply makers for {mint_address}")
        logging.info(f"Unique users: {unique_users}")
        return maker_count
    except Exception as e:
        logging.error(f"Error fetching reply makers for {mint_address}: {e}")
        # Print the full error for debugging
        import traceback
        logging.error(traceback.format_exc())
        return 0


def fetch_token_holders(token_mint):
    """Fetch token holder count and distribution from Helius and Birdeye APIs."""
    try:
        # Get holder distribution from Helius
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [token_mint]
        }
        response = requests.post(HELIUS_RPC_URL, json=payload)
        response.raise_for_status()
        holders = response.json().get("result", {}).get("value", [])

        if not holders or len(holders) < 2:
            return None

        total_supply = sum(float(holder["amount"]) for holder in holders)
        if total_supply == 0:
            return None

        # Skip the first holder (bonding curve) and use the rest
        real_holders = holders[1:]
        top_5_amounts = [float(holder["amount"]) for holder in real_holders[:5]]
        top_5_percentages = [(amount / total_supply * 100) for amount in top_5_amounts]

        # Check for minimum and maximum wallet percentage limits
        if max(top_5_percentages) > BIGGEST_WALLET_MAX or min(top_5_percentages) < 2.0:
            return None

        top_5 = top_5_percentages

        # Birdeye request for additional holder/trade info
        birdeye_url = f"https://public-api.birdeye.so/defi/v3/token/trade-data/single?address={token_mint}"
        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": "114f18a5eb5e4d51a9ac7c6100dfe756"
        }
        birdeye_response = requests.get(birdeye_url, headers=headers)
        birdeye_response.raise_for_status()

        data = birdeye_response.json()
        total_holders = data.get('data', {}).get('holder', 0)
        buy_1h = data.get('data', {}).get('buy_1h', 0)
        sell_1h = data.get('data', {}).get('sell_1h', 0)
        trade_1h = data.get('data', {}).get('trade_1h', 0)
        unique_wallet_1h = data.get('data', {}).get('unique_wallet_1h', 0)
        unique_wallet_24h = data.get('data', {}).get('unique_wallet_24h', 0)

        if total_holders < MIN_HOLDERS:
            return None

        # Re-fetch holder distribution from Helius (if needed for more precise data)
        response = requests.post(HELIUS_RPC_URL, json=payload)
        response.raise_for_status()
        holders = response.json().get("result", {}).get("value", [])
        if not holders or len(holders) < 2:
            return None

        total_supply = sum(float(holder["amount"]) for holder in holders)
        if total_supply == 0:
            return None
        real_holders = holders[1:]
        top_10_percentage = sum(
            float(holder["amount"])
            for holder in real_holders[:10]) / total_supply * 100
        top_20_percentage = sum(
            float(holder["amount"])
            for holder in real_holders[:20]) / total_supply * 100
        top_5 = [
            float(holder["amount"]) / total_supply * 100
            for holder in real_holders[:5]
        ]

        return {
            "total_holders": total_holders,
            "top_5_percentages": top_5,
            "top_10_percentage": top_10_percentage,
            "top_20_percentage": top_20_percentage,
            "buy_1h": buy_1h,
            "sell_1h": sell_1h,
            "trade_1h": trade_1h,
            "unique_wallet_1h": unique_wallet_1h,
            "unique_wallet_24h": unique_wallet_24h
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching holders for {token_mint}: {e}")
        return None


def format_holders_message(holders_info):
    """Format holders information into a readable message."""
    top_5 = " | ".join(f"{percent:.2f}" for percent in holders_info["top_5_percentages"])
    makers_line = '├' if holders_info.get(
        'unique_wallet_1h') != holders_info.get('unique_wallet_24h') else '└'
    makers_24h = (
        f'└─ <b>24h Makers:</b> {holders_info.get("unique_wallet_24h", 0)}\n'
        if holders_info.get('unique_wallet_1h')
        != holders_info.get('unique_wallet_24h') else '')
    return (
        f"👥 <b>Holders</b>\n"
        f"├─ <b>Total Holders:</b> {holders_info.get('total_holders', 0):,}\n"
        f"├─ <b>TH 10:</b> {holders_info['top_10_percentage']:.2f}%\n"
        f"├─ <b>TH 20:</b> {holders_info['top_20_percentage']:.2f}%\n"
        f"└─ <b>TH:</b> {top_5}\n\n"
        f"🏧 <b>Trades 1h</b>\n"
        f"└─ <b>🅣</b> {holders_info.get('trade_1h', 0)} | <b>🅑</b> {holders_info.get('buy_1h', 0)} | <b>🅢</b> {holders_info.get('sell_1h', 0)}\n\n"
        f"🧑‍💻 <b>Makers</b>\n"
        f"{makers_line}─ <b>1h Makers:</b> {holders_info.get('unique_wallet_1h', 0)}\n"
        f"{makers_24h}\n")


def get_trench_data(mint_address, max_retries=3):
    """Fetch bundle data from Trench API with retries."""
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://trench.bot/api/bundle/bundle_advanced/{mint_address}",
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'bonded': data.get('bonded', False),
                    'total_bundles': data.get('total_bundles', 0),
                    'total_holding_percentage': data.get('total_holding_percentage', 0)
                }
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Error fetching Trench data after {max_retries} attempts: {e}")
            else:
                logging.warning(f"Retrying Trench API call ({attempt + 1}/{max_retries})")
                asyncio.sleep(1)
    return None

def format_coin_message(coin, holders_info, dex_data, coin_tracker):
    """Format coin information into a readable Telegram message."""
    mint_address = coin["mint"]
    pumpfun_link = f"https://pump.fun/coin/{mint_address}"
    bullx_link = f"https://neo.bullx.io/terminal?chainId=1399811149&address={mint_address}&r=YEGC2RLRAUE&l=en"
    
    # Get Trench data and filter out bonded coins
    trench_data = get_trench_data(mint_address)
    if trench_data and trench_data.get('bonded', False):
        return None
        
    trench_info = ""
    if trench_data:
        trench_info = (
            f"📚 <b>Bundle Info</b>\n"
            f"├─ <b>Total Bundles:</b> {trench_data['total_bundles']}\n"
            f"└─ <b>Held Bundles:</b> {trench_data['total_holding_percentage']:.2f}%\n\n"
        )

    # Get reply count from the coin data
    reply_count = coin.get("reply_count", 0)

    # Get unique reply makers
    unique_reply_makers = fetch_unique_reply_makers(mint_address)

    volume_text = ""
    price_text = ""

    if dex_data:
        # Prepare price changes info
        period_order = ['5m', '1h', '6h', '24h']
        price_changes = {
            '24h': dex_data['price_change_24h'],
            '6h': dex_data['price_change_6h'],
            '1h': dex_data['price_change_1h'],
            '5m': dex_data['price_change_5m']
        }
        unique_changes = {}
        for period in period_order:
            change = price_changes[period]
            if change not in unique_changes:
                unique_changes[change] = period
        price_parts = [
            f"{period}: {change:+.0f}%"
            for change, period in unique_changes.items()
        ]
        price_text = f"📈 <b>Price Changes:</b>\n{' | '.join(price_parts)}\n\n"

        # Prepare volume info
        volumes = {
            '24h': dex_data['volume_24h'],
            '6h': dex_data['volume_6h'],
            '1h': dex_data['volume_1h'],
            '5m': dex_data['volume_5m']
        }
        unique_volumes = {}
        for period in period_order:
            vol = volumes[period]
            if vol not in unique_volumes:
                unique_volumes[vol] = period
        volume_parts = []
        num_volumes = len(unique_volumes)
        for i, (vol, period) in enumerate(unique_volumes.items()):
            marker = '├─' if i < num_volumes - 1 else '└─'
            volume_parts.append(f"{marker} {period}: ${vol:,.2f}")
        volume_text = f"📊 <b>Volume:</b>\n" + "\n".join(volume_parts) + "\n\n"

        # ATH (all-time high) price estimation
        market_cap = float(coin.get('usd_market_cap', 0))
        ath_price = market_cap
        if dex_data and isinstance(dex_data, dict):
            ath_from_dex = dex_data.get('ath_price')
            if ath_from_dex is not None:
                try:
                    ath_from_dex = float(ath_from_dex)
                    ath_price = max(ath_from_dex, market_cap)
                except (ValueError, TypeError):
                    pass
        ath_text = f"📈 <b>ATH: ${int(ath_price):,}</b>\n\n"

    # Check DEX paid status (optional additional info)
    try:
        dex_response = requests.get(
            f"https://api.dexscreener.com/orders/v1/solana/{mint_address}",
            timeout=5)
        dex_data_orders = dex_response.json()
        dex_paid = dex_data_orders.get("status") == "approved" if dex_data_orders else False
    except Exception:
        dex_paid = False
    dex_status = "🟢" if dex_paid else "🔴"

    return (
        f"🔹 <b>{coin['name']}</b> ({coin['symbol']})\n"
        f"💰 <b>Market Cap:</b> ${coin['usd_market_cap']:,.2f}\n"
        #f"🤖 <b>AI Prediction:</b> {coin_tracker.tracked_coins[mint_address]['prediction_result']} ({coin_tracker.tracked_coins[mint_address]['prediction_confidence']:.1f}% confidence)\n"
        f"🎯 <b>DEX Paid:</b> {dex_status}\n\n"
        f"{trench_info}"
        f"{price_text}"
        f"{volume_text}"
        f"{ath_text}"
        f"💬 <b>Replies:</b> {reply_count} | <b>Reply Makers:</b> {unique_reply_makers}\n\n"
        f"{format_holders_message(holders_info)}"
        f"🔗 <a href='{pumpfun_link}'>PF</a> | "
        f"📊 <a href='{bullx_link}'>NEO</a>\n\n"

         f"🤖 <b>AI Prediction:</b>  {coin_tracker.predict_profitability(holders_info, dex_data, trench_data)['prediction']} ({coin_tracker.predict_profitability(holders_info, dex_data, trench_data)['confidence']:.1f}% confidence)\n"
         f"📊 <b>Analysis:</b> {coin_tracker.predict_profitability(holders_info, dex_data, trench_data)['explanation']}\n\n"
        f"🆔 Mint: <code>{mint_address}</code>\n"
        f"——————————————————————————————\n")


from coin_tracker import CoinTracker

async def scan_coins():
    """Continuously scan the featured coins API for new coins meeting filter criteria."""
    seen_mints = {}
    coin_tracker = CoinTracker()
    while True:
        coins = await fetch_active_coins()
        new_coins = []
        for coin in coins:
            mint = coin.get("mint")
            market_cap = coin.get("usd_market_cap", 0)
            # Skip coins that have a Telegram link
            if coin.get("telegram"):
                continue
            # Ensure we have a mint address
            if not mint:
                continue

            # Skip coin if it's already been seen
            if mint in seen_mints:
                continue

            # Market cap filter
            if market_cap < MIN_MARKET_CAP or market_cap > MAX_MARKET_CAP:
                continue

            # Get holders data and apply filters
            holders_info = fetch_token_holders(mint)
            if not holders_info:
                continue
            if holders_info.get("total_holders", 0) < MIN_HOLDERS:
                continue
            if holders_info.get("buy_1h", 0) < MIN_BUYS or holders_info.get(
                    "sell_1h", 0) < MIN_SELLS:
                continue

            # DEX data
            dex_data = get_dex_data(mint)
            if not dex_data:
                continue

            # Get volumes and price changes
            volume_5m = dex_data.get("volume_5m", 0)
            volume_1h = dex_data.get("volume_1h", 0)
            price_change_5m = dex_data.get("price_change_5m", 0)
            price_change_1h = dex_data.get("price_change_1h", 0)
            trades_1h = holders_info.get("trade_1h", 0)

            # Check if 5m volume is too high
            if volume_5m > MAX_VOLUME_5M:
                continue

            # 1. Price Momentum Check
            price_momentum_check = (
                (price_change_5m >= MIN_PRICE_5M) or 
                (price_change_1h >= HIGH_PRICE_1H) or 
                (price_change_1h >= MIN_PRICE_1H)
            )

            # 2. Volume Liquidity Check
            volume_check = (
                (volume_5m >= MIN_VOLUME_5M) or
                (volume_1h >= MIN_VOLUME_1H)            )

            # 3. Trades Check
            trades_check = trades_1h >= MIN_TRADES_1H

            # 4. Holders Check
            holders_check = holders_info.get("total_holders", 0) >= MIN_HOLDERS

            # All conditions must be true
            if not all([price_momentum_check, volume_check, trades_check, holders_check]):
                continue

            # Get Trench data before tracking
            trench_data = get_trench_data(mint)
            
            # Track the coin in our AI system
            coin_tracker.track_coin(coin, holders_info, dex_data, trench_data)
            new_coins.append((coin, holders_info, dex_data))
            seen_mints[mint] = market_cap

        if new_coins:
            message = "🚀 <b>NEW CREATION ALERT!</b> 🚀\n\n" + "\n".join(
                format_coin_message(coin, holders_info, dex_data, coin_tracker)
                for coin, holders_info, dex_data in new_coins)
            await send_telegram_message(message)
        total_replies = sum(coin[0].get("reply_count", 0)
                            for coin in new_coins) if new_coins else 0
        total_makers = sum(
            fetch_unique_reply_makers(coin[0]["mint"])
            for coin in new_coins) if new_coins else 0
        logging.info(
            f"Checked: {len(new_coins)} new coins meeting criteria. Total replies: {total_replies}, Total reply makers: {total_makers}"
        )
        await asyncio.sleep(15)


from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'status': 'running', 'message': 'Crypto scanner is active'}
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/train':
            # Handle training data submission
            training_data = json.loads(post_data)
            tracker = CoinTracker()
            tracker.train_model_with_returns(training_data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'message': 'Model trained with new data'}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/returns':
            current_prices = json.loads(post_data)
            tracker = CoinTracker()
            analysis = tracker.analyze_returns(current_prices)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(analysis).encode())


def run_http_server():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    logging.info("Server started on port 8080")
    server.serve_forever()


if __name__ == "__main__":
    # Start HTTP server in a separate thread
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    # Run both the scanner and Telegram handler
    async def main():
        await asyncio.gather(
            scan_coins(),
            handle_telegram_updates()
        )

    asyncio.run(main())
