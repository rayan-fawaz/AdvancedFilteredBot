import requests
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Telegram API (still used for sending messages)
import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN",
                           "8046651136:AAGHoEFIJhW3zHTe6CI0iOcn6FgePpljXqM")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "-1002429691769")


def get_minutes_since_creation(created_timestamp: int) -> int:
    """
    Converts the created_timestamp from milliseconds to minutes elapsed since creation.
    """
    created_timestamp_s = created_timestamp / 1000
    created_datetime = datetime.fromtimestamp(created_timestamp_s, tz=timezone.utc)
    current_time_utc = datetime.now(timezone.utc)
    minutes_since_creation = (current_time_utc - created_datetime).total_seconds() / 60
    return int(minutes_since_creation)

def format_time_ago(minutes: int) -> str:
    """Convert minutes to a human readable time format."""
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    mins = minutes % 60
    if hours < 24:
        return f"{hours}h {mins}m ago"
    days = hours // 24
    hrs = hours % 24
    return f"{days}d {hrs}h ago"

# Featured Coins API
API_URL = "https://frontend-api-v3.pump.fun/coins/for-you?offset=0&limit=50&includeNsfw=false"

# Helius API
HELIUS_API_KEY = "d2eb41e9-0474-45d9-8c53-f487ac8fdd96"
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Filter Constants
MIN_HOLDERS = 25  # Increased from 25
MIN_TRADES_1H = 80  # Increased from 80
MAX_VOLUME_5M = 20000  # Decreased from 20000
BIGGEST_WALLET_MAX = 55  # Decreased from 5 for better distribution
MIN_BUYS = 40  # Increased from 40
MIN_SELLS = 40  # Increased from 40

# Price Momentum Filters
MIN_PRICE_5M = 30  # Increased from 30
MIN_PRICE_1H = 80  # Increased from 80
HIGH_PRICE_1H = 1000  # Increased from 95

# Volume Filters
MIN_VOLUME_5M = 3000  # Increased from 3000
MIN_VOLUME_1H = 10000  # Increased from 10000

# Market Cap Limits
MIN_MARKET_CAP = 7500  # Increased from 7000

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

class EnhancedHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        if self.path == '/command' and b'/learned' in post_data:
            asyncio.run(handle_learned_command())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            return

        if self.path == '/train':
            try:
                # Parse training data in format: [{"ticker": "NAME", "multiplier": X.X}, ...]
                data = json.loads(post_data)
                training_data = {}

                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and 'ticker' in entry and 'multiplier' in entry:
                            ticker = entry['ticker'].strip()
                            multiplier = float(entry['multiplier'])
                            training_data[ticker] = multiplier
                            logging.info(f"Added trade: {ticker} = {multiplier}x")

                if training_data:
                    # Train the model
                    tracker = CoinTracker()
                    tracker.train_model_with_returns(training_data)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'status': 'success',
                        'message': f'Model trained with {len(training_data)} trades',
                        'trades': training_data
                    }
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'status': 'error',
                        'message': 'No valid training data found'
                    }

                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())

        elif self.path == '/returns':
            current_prices = json.loads(post_data)
            tracker = CoinTracker()
            analysis = tracker.analyze_returns(current_prices)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(analysis).encode())


def get_dex_data(token_mint):
    """Get volume and price change data from DexScreener, Moralis, and Birdeye APIs."""
    try:
        # Get ATH from Birdeye
        birdeye_url = f"https://public-api.birdeye.so/defi/ohlcv?address={token_mint}&type=3D&currency=usd&time_from=10&time_to=10000000000"
        birdeye_headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": "114f18a5eb5e4d51a9ac7c6100dfe756"
        }
        try:
            url = f"https://public-api.birdeye.so/defi/ohlcv?address={token_mint}&type=3D&currency=usd&time_from=10&time_to=10000000000"
            headers = {
                "accept": "application/json",
                "x-chain": "solana",
                "X-API-KEY": "114f18a5eb5e4d51a9ac7c6100dfe756"
            }
            response = requests.get(url, headers=headers)
            data = response.json()
            logging.info(f"Birdeye ATH response: {response.text}")

            if 'data' in data and 'items' in data['data'] and isinstance(data['data']['items'], list):
                # Get the highest 'h' value across all time periods
                ath = max((float(item.get('h', 0)) for item in data['data']['items']), default=0)
                ath_price = ath * 1000000000
            else:
                ath_price = 0
        except Exception as e:
            logging.error(f"Error fetching Birdeye ATH data: {e}")
            ath_price = 0

        # DexScreener data
        dex_response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{token_mint}",
            timeout=10)
        dex_response.raise_for_status()

        # Moralis pair data for additional details
        moralis_url = f"https://solana-gateway.moralis.io/token/mainnet/{token_mint}/pairs"
        moralis_headers = {
            "Accept": "application/json",
            "X-API-Key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImNkNjVlMDM4LWE4ODktNDYyNC1iNzIyLWQwODY1ZDdmODFkMyIsIm9yZ0lkIjoiNDMyNTIwIiwidXNlcklkIjoiNDQ0OTExIiwidHlwZUlkIjoiZmU1OTFkNmYtNTYyYi00OTYwLWI0ZjQtYzUxMTZmMTk3ZWNlIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDAwMTUzOTUsImV4cCI6NDg5NTc3NTM5NX0.xrYHL35_6-yXMT5qksrqjGIe8Z5YbiuAgdh6FpL_fpQ"
        }
        moralis_response = requests.get(moralis_url,
                                        headers=moralis_headers,
                                        timeout=10)
        pair_address = None
        if moralis_response.ok:
            pair_data = moralis_response.json()
            if isinstance(pair_data, list) and len(pair_data) > 0:
                pair_address = pair_data[0].get("pairAddress")


        data = dex_response.json()
        if 'pairs' in data and len(data['pairs']) > 0:
            pair = data['pairs'][0]
            return {
                'ath_price': ath_price,
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
                pair_address
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

            # If we have a user field, extract the user ID
            if "user" in reply and reply["user"]:
                user_id = str(reply["user"])
                unique_users.add(user_id)
                logging.info(f"Found user: {user_id}")

            # Try alternative field names only if no user field found
            if "user" not in reply:
                for field in ["owner", "author", "creator", "walletAddress", "publicKey"]:
                    if field in reply and reply[field]:
                        unique_users.add(str(reply[field]))
                        logging.info(f"Found user in {field} field: {reply[field]}")

        maker_count = len(unique_users)
        logging.info(f"Found {maker_count} unique reply makers for {mint_address}")
        logging.info(f"Unique users: {unique_users}")
        return maker_count
    except Exception as e:
        logging.error(f"Error fetching reply makers for {mint_address}: {e}")
        # Print the full error for debugging
        import traceback
        logging.error(traceback.format_exc())
        return 0


def fetch_token_holders(token_mint):
    """Fetch token holder count and distribution from Birdeye API."""
    try:
        # Get holder distribution from Birdeye
        url = f"https://public-api.birdeye.so/defi/v3/token/holder?address={token_mint}&offset=0&limit=100"
        headers = {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": "114f18a5eb5e4d51a9ac7c6100dfe756"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data or 'data' not in data or 'items' not in data['data']:
            return None

        holders = data['data']['items']
        if not holders or len(holders) < 6:  # Need at least 6 holders for analysis
            return None

        # Calculate total supply from actual holder amounts
        total_supply = sum(float(holder.get('amount', 0)) for holder in holders)
        if total_supply == 0:
            return None

        # Calculate holder percentages
        holder_amounts = [float(holder.get('amount', 0)) for holder in holders[:6]]
        holder_percentages = [(amount / total_supply * 100) for amount in holder_amounts]

        # Skip first holder (assumed bonding curve) and get next 5
        top_5_percentages = holder_percentages[1:6]
        top_5_addresses = [holder.get('owner', '') for holder in holders[1:6]]

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

        # Calculate additional percentages from Birdeye data
        real_holders = holders[1:]  # Skip first holder (usually liquidity)
        total_supply = sum(float(holder.get('amount', 0)) for holder in holders)

        top_10_percentage = sum(
            float(holder.get('amount', 0))
            for holder in real_holders[:10]) / total_supply * 100

        top_20_percentage = sum(
            float(holder.get('amount', 0))
            for holder in real_holders[:20]) / total_supply * 100

        return {
            "total_holders": total_holders,
            "top_5_percentages": top_5,
            "top_5_addresses": top_5_addresses[1:6],  # Skip first (bonding curve)
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


async def get_wallet_pnl(wallet_address):
    """Placeholder for PnL data - not available via public APIs."""
    return {'total': 0, 'winPercentage': 0}

async def format_holders_message(holders_info):
    """Format holders information into a readable message."""
    # Create top 5 percentages with embedded Solscan links and PnL data
    top_5_links = []
    for percent, addr in zip(holders_info["top_5_percentages"], holders_info["top_5_addresses"]):
        top_5_links.append(
            f"<a href='https://solscan.io/account/{addr}'>{percent:.2f}%</a>"
        )
    top_5 = "\n".join(top_5_links)

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


async def get_insider_data(mint_address):
    """Fetch and analyze insider data from RugCheck API."""
    try:
        response = requests.get(
            f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/insiders/graph",
            headers={'accept': 'application/json'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            insider_count = sum(1 for node in data.get('nodes', []) 
                              if node.get('participant', False))
            return insider_count
        return 0
    except Exception as e:
        logging.error(f"Error fetching insider data: {e}")
        return 0

async def get_trench_data(mint_address, max_retries=3):
    """Fetch bundle data from Trench API with retries."""
    for attempt in range(max_retries):
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
                bundles = data.get('bundles', {})
                sniper_info = []

                for bundle_id, bundle_data in bundles.items():
                    wallet_categories = bundle_data.get('wallet_categories', {})
                    wallet_info = bundle_data.get('wallet_info', {})

                    for wallet, category in wallet_categories.items():
                        if category == "sniper" and wallet in wallet_info:
                            info = wallet_info[wallet]
                            sniper_info.append({
                                'bundle_id': bundle_id,
                                'wallet': wallet,
                                'tokens': info.get('tokens', 0),
                                'sol': info.get('sol', 0)
                            })

                return {
                    'bonded': data.get('bonded', False),
                    'total_bundles': data.get('total_bundles', 0),
                    'total_holding_percentage': data.get('total_holding_percentage', 0),
                    'snipers': sniper_info
                }
            elif response.status_code == 429:  # Rate limit
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            elif response.status_code >= 500:  # Server error
                await asyncio.sleep(1)
                continue
            else:
                return {'bonded': False, 'total_bundles': 0, 'total_holding_percentage': 0}
        except requests.exceptions.Timeout:
            await asyncio.sleep(1)
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Error fetching Trench data after {max_retries} attempts: {e}")
            else:
                logging.warning(f"Retrying Trench API call ({attempt + 1}/{max_retries})")
                await asyncio.sleep(1)
    return {'bonded': False, 'total_bundles': 0, 'total_holding_percentage': 0}

async def format_coin_message(coin, holders_info, dex_data, coin_tracker):
    """Format coin information into a readable Telegram message."""
    # Get Trench data first
    mint_address = coin["mint"]
    trench_data = await get_trench_data(mint_address)

    # Add to database
    db.insert_token(coin, holders_info, dex_data, trench_data)
    mint_address = coin["mint"]
    pumpfun_link = f"https://pump.fun/coin/{mint_address}"
    bullx_link = f"https://neo.bullx.io/terminal?chainId=1399811149&address={mint_address}&r=YEGC2RLRAUE&l=en"

    # Get Trench data and filter out bonded coins
    trench_data = await get_trench_data(mint_address)
    if trench_data and trench_data.get('bonded', False):
        return None

    trench_info = ""
    if trench_data:
        active_snipers = [s for s in trench_data.get('snipers', []) if s['tokens'] > 0]
        total_snipers = len(active_snipers)
        if total_snipers > 0:
            total_tokens = sum(sniper['tokens'] for sniper in active_snipers)
            total_supply = 10_000_000_000_000_000  # 10 quadrillion total supply
            percentage = (total_tokens / total_supply) * 100
            sniper_text = f"├─ Active Snipers: {total_snipers}\n└─ Supply Sniped: {percentage:.2f}%\n"
        else:
            sniper_text = f"└─ Active Snipers: 0\n"

        trench_info = (
            f"📚 <b>Bundle Info</b>\n"
            f"├─ <b>Total Bundles:</b> {trench_data['total_bundles']}\n"
            f"├─ <b>Held Bundles:</b> {trench_data['total_holding_percentage']:.2f}%\n\n"
            f"🔫 <b>Snipers:</b>\n{sniper_text}\n"
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


    # Check DEX paid status
    try:
        dex_response = requests.get(
            f"https://api.dexscreener.com/latest/dex/pairs/solana/{mint_address}",
            headers={'accept': 'application/json'},
            timeout=5)
        if dex_response.status_code == 200:
            dex_data_orders = dex_response.json()
            dex_paid = len(dex_data_orders.get("pairs", [])) > 0
        else:
            dexpaid = False
    except Exception as e:
        logging.error(f"Error checking DEX status: {e}")        dex_paid = False
    dex_status = "🟢" if dex_paid else "🔴"



    # Get creation time and format it
    minutes_old = get_minutes_since_creation(coin.get('created_timestamp', 0))
    time_ago = format_time_ago(minutes_old)

    # Get bond status from trench
    bond_status = "🟢 BONDED" if trench_data.get('bonded', False) else "🔴 NOT BONDED"

    return (
        f"🔹 <b>{coin['name']}</b> ({coin['symbol']})\n"
        f"🔒 <b>Bond Status:</b> {bond_status}\n"
        f"💰 <b>Market Cap:</b>${coin['usd_market_cap']:,.2f}\n"
        f"📈 <b>ATH:</b> ${dex_data.get('ath_price', 0):,.2f}\n"
        f"⏰ <b>Age:</b> {time_ago}\n"
        #f"🤖 <b>AI Prediction:</b> {coin_tracker.tracked_coins[mint_address]['prediction_result']} ({coin_tracker.tracked_coins[mint_address]['prediction_confidence']:.1f}% confidence)\n"
        f"🎯 <b>DEX Paid:</b> {dex_status}\n"
        f"🥷 <b>Insiders:</b> {await get_insider_data(mint_address)}\n\n"
        f"{trench_info}"
        f"{price_text}"
        f"{volume_text}"
        f"💬 <b>Replies:</b> {reply_count} | <b>Reply Makers:</b> {unique_reply_makers}\n\n"
        f"{await format_holders_message(holders_info)}"
        f"🔗 <a href='{pumpfun_link}'>PF</a> | "
        f"📊 <a href='{bullx_link}'>NEO</a>\n\n"

         f"🤖 <b>AI Analysis</b>\n"
         f"├─ <b>Prediction:</b> {coin_tracker.predict_profitability(coin, holders_info, dex_data, trench_data)['prediction']}\n"
         f"├─ <b>Confidence:</b> {coin_tracker.predict_profitability(coin, holders_info, dex_data, trench_data)['confidence']:.1f}%\n"
         f"└─ <b>Reason:</b> {coin_tracker.predict_profitability(coin, holders_info, dex_data, trench_data)['explanation']}\n\n"
         f"📊 <b>Meta Matches:</b> {' | '.join(f'{word} ({score:.2f})' for word, score in coin_tracker.meta_scores.items() if word.lower() in (coin['name'] + ' ' + coin['symbol']).lower())}\n\n"
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

            # 1. Initial Market Cap Filter (No API calls)
            if market_cap < MIN_MARKET_CAP or market_cap > MAX_MARKET_CAP:
                continue

            # 2. DexScreener Data (Less expensive API)
            try:
                dex_response = requests.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
                    timeout=10)
                dex_response.raise_for_status()

                data = dex_response.json()
                if 'pairs' not in data or not data['pairs']:
                    continue

                pair = data['pairs'][0]
                dex_data = {
                    'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                    'volume_6h': float(pair.get('volume', {}).get('h6', 0)),
                    'volume_1h': float(pair.get('volume', {}).get('h1', 0)),
                    'volume_5m': float(pair.get('volume', {}).get('m5', 0)),
                    'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                    'price_change_6h': float(pair.get('priceChange', {}).get('h6', 0)),
                    'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                    'price_change_5m': float(pair.get('priceChange', {}).get('m5', 0)),
                    'ath_price': 0  # Will be updated later if needed
                }
            except Exception as e:
                logging.error(f"Error fetching base DEX data for {mint}: {e}")
                continue

            # 3. Volume and Price Checks
            if dex_data["volume_5m"] > MAX_VOLUME_5M:
                continue

            price_momentum_check = (
                (dex_data["price_change_5m"] >= MIN_PRICE_5M) or 
                (dex_data["price_change_1h"] >= HIGH_PRICE_1H) or 
                (dex_data["price_change_1h"] >= MIN_PRICE_1H)
            )

            volume_check = (
                (dex_data["volume_5m"] >= MIN_VOLUME_5M) or
                (dex_data["volume_1h"] >= MIN_VOLUME_1H)
            )

            if not all([price_momentum_check, volume_check]):
                continue

            # 4. Get Trench data before Birdeye requests
            trench_data = await get_trench_data(mint)
            if not trench_data:
                continue

            # 5. Finally fetch Birdeye data (Most expensive API) - Only if all other checks pass
            # Get Birdeye holder info and ATH data
            try:
                # First get holder info
                holders_info = fetch_token_holders(mint)
                if not holders_info:
                    continue
                if holders_info.get("total_holders", 0) < MIN_HOLDERS:
                    continue
                if holders_info.get("buy_1h", 0) < MIN_BUYS or holders_info.get("sell_1h", 0) < MIN_SELLS:
                    continue

                # Then get ATH data
                birdeye_url = f"https://public-api.birdeye.so/defi/ohlcv?address={mint}&type=3D&currency=usd&time_from=10&time_to=10000000000"
                headers = {
                    "accept": "application/json",
                    "x-chain": "solana",
                    "X-API-KEY": "114f18a5eb5e4d51a9ac7c6100dfe756"
                }
                response = requests.get(birdeye_url, headers=headers)
                data = response.json()

                if 'data' in data and 'items' in data['data'] and isinstance(data['data']['items'], list):
                    ath = max((float(item.get('h', 0)) for item in data['data']['items']), default=0)
                    dex_data['ath_price'] = ath * 1000000000
            except Exception as e:
                logging.error(f"Error fetching Birdeye data for {mint}: {e}")
                continue

            # 2. DexScreener Data (Less expensive API)
            try:
                dex_response = requests.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
                    timeout=10)
                dex_response.raise_for_status()

                data = dex_response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    pair = data['pairs'][0]
                    dex_data.update({
                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                        'volume_6h': float(pair.get('volume', {}).get('h6', 0)),
                        'volume_1h': float(pair.get('volume', {}).get('h1', 0)),
                        'volume_5m': float(pair.get('volume', {}).get('m5', 0)),
                        'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                        'price_change_6h': float(pair.get('priceChange', {}).get('h6', 0)),
                        'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                        'price_change_5m': float(pair.get('priceChange', {}).get('m5', 0))
                    })
                else:
                    continue
            except Exception as e:
                logging.error(f"Error fetching base DEX data for {mint}: {e}")
                continue

            # 3. Secondary Filters
            # Check if 5m volume is too high
            if dex_data["volume_5m"] > MAX_VOLUME_5M:
                continue

            # Price Momentum Check
            price_momentum_check = (
                (dex_data["price_change_5m"] >= MIN_PRICE_5M) or 
                (dex_data["price_change_1h"] >= HIGH_PRICE_1H) or 
                (dex_data["price_change_1h"] >= MIN_PRICE_1H)
            )

            # Volume Liquidity Check
            volume_check = (
                (dex_data["volume_5m"] >= MIN_VOLUME_5M) or
                (dex_data["volume_1h"] >= MIN_VOLUME_1H)
            )

            # All secondary conditions must be true including new range-specific filters
            def check_range_filters(market_cap, ath_drop, price_change_5m, volume_5m, top_10_pct, top_20_pct, total_holders, 
                                 makers_1h):
                # Get Supply Sniped from trench data
                supply_sniped = trench_data.get('Supply Sniped', 0)

                # 7,000 - 8,500 range
                if 7000 <= market_cap <= 8500:
                    return (
                        ath_drop < 65 and
                        price_change_5m > -40 and 
                        volume_5m > -800 and
                        top_10_pct > 10 and 
                        top_20_pct > 17 and 
                        supply_sniped < 16 and
                        total_holders <= 220
                    )
                # 8,500 - 10,000 range
                elif 8500 < market_cap <= 10000:
                    return (
                        ath_drop < 70 and
                        price_change_5m > -45 and
                        volume_5m > -300 and
                        top_10_pct > 11 and
                        top_20_pct > 18 and
                        supply_sniped < 16.5 and
                        total_holders <= 230 and
                        makers_1h < 655
                    )
                # 10,000 - 12,500 range
                elif 10000 < market_cap <= 12500:
                    return (
                        ath_drop < 70 and
                        price_change_5m > -30 and
                        volume_5m > 700 and
                        top_10_pct > 12 and
                        top_20_pct > 20 and
                        snipe_percentage < 17 and
                        total_holders <= 240 and
                        makers_1h < 675
                    )
                # 12,500 - 15,000 range
                elif 12500 < market_cap <= 15000:
                    return (
                        ath_drop < 70 and
                        price_change_5m > -30 and
                        volume_5m > 1200 and
                        top_10_pct > 12 and
                        top_20_pct > 21 and
                        snipe_percentage < 17 and
                        total_holders <= 260 and
                        makers_1h < 695
                    )
                # 15,000 - 18,000 range
                elif 15000 < market_cap <= 18000:
                    return (
                        ath_drop < 72 and
                        price_change_5m > -25 and
                        volume_5m > 1700 and
                        top_10_pct > 13 and
                        top_20_pct > 22 and
                        snipe_percentage < 17 and
                        total_holders <= 280 and
                        makers_1h < 725
                    )
                # 18,000 - 21,000 range
                elif 18000 < market_cap <= 21000:
                    return (
                        ath_drop < 75 and
                        price_change_5m > -70 and
                        volume_5m > 2700 and
                        top_10_pct > 11 and
                        top_20_pct > 21 and
                        snipe_percentage < 18 and
                        total_holders <= 320 and
                        makers_1h < 775
                    )
                # 21,000 - 25,000 range
                elif 21000 < market_cap <= 25000:
                    return (
                        ath_drop < 78 and
                        price_change_5m > -70 and
                        volume_5m > 3700 and
                        top_10_pct > 11 and
                        top_20_pct > 20 and
                        snipe_percentage < 18 and
                        total_holders <= 340 and
                        makers_1h < 825
                    )
                return False

            # Apply both core and range-specific filters
            if not all([
                price_momentum_check, 
                volume_check,
                check_range_filters(
                    market_cap, 
                    ath_drop,
                    dex_data['price_change_5m'],
                    dex_data['volume_5m'],
                    holders_info['top_10_percentage'],
                    holders_info['top_20_percentage'],
                    holders_info['total_holders'],
                    holders_info['unique_wallet_1h']
                )
            ]):
                continue

            # Track the coin in our AI system
            coin_tracker.track_coin(coin, holders_info, dex_data, trench_data)
            new_coins.append((coin, holders_info, dex_data))
            seen_mints[mint] = market_cap

        if new_coins:
            formatted_messages = []
            for coin, holders_info, dex_data in new_coins:
                msg = await format_coin_message(coin, holders_info, dex_data, coin_tracker)
                if msg:
                    formatted_messages.append(msg)
            message = "🚀 <b>NEW CREATION ALERT!</b> 🚀\n\n" + "\n".join(formatted_messages)
            await send_telegram_message(message)
        total_replies = sum(coin[0].get("reply_count", 0)
                            for coin in new_coins) if new_coins else 0
        total_makers = sum(
            fetch_unique_reply_makers(coin[0].get("mint"))
            for coin in new_coins) if new_coins else 0
        logging.info(
            f"Checked: {len(new_coins)} new coins meeting criteria. Total replies: {total_replies}, Total reply makers: {total_makers}"
        )
        await asyncio.sleep(15)


async def update_database():
    """Update token returns and clean old data hourly"""
    while True:
        db.update_token_returns()
        await asyncio.sleep(3600)  # 1 hour

async def send_hourly_leaderboard():
    """Send /lb 1h message at the start of each hour."""
    while True:
        # Get current time
        now = datetime.now()
        # Calculate time until next hour
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()

        # Wait until next hour
        await asyncio.sleep(wait_seconds)
        await send_telegram_message("/lb 1h")

async def main():
    # Run both the coin scanner and hourly leaderboard sender
    await asyncio.gather(
        scan_coins(),
        send_hourly_leaderboard(),
        update_database()
    )

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
from db import TokenDB

# Initialize database instance
db = TokenDB()


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

        if self.path == '/command' and b'/learned' in post_data:
            asyncio.run(handle_learned_command())
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            return

        if self.path == '/train':
            try:
                # Parse training data in format: {"TICKER": X.X} where X.X is return multiplier
                training_data = json.loads(post_data)

                if not isinstance(training_data, dict):
                    raise ValueError("Training data must be a dictionary")

                # Validate data format
                for ticker, multiplier in training_data.items():
                    if not isinstance(multiplier, (int, float)):
                        raise ValueError(f"Invalid multiplier for {ticker}: {multiplier}")

                # Train model
                tracker = CoinTracker()
                tracker.train_model_with_returns(training_data)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'status': 'success',
                    'message': f'Model trained with {len(training_data)} trades',
                    'trades': training_data
                }
                self.wfile.write(json.dumps(response).encode())

                # Also send confirmation to Telegram
                asyncio.run(send_telegram_message(
                    f"✅ Model trained successfully with {len(training_data)} trades:\n" +
                    "\n".join(f"- {k}: {v}x" for k, v in training_data.items())
                ))

            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'error', 'message': str(e)}
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


async def handle_lb_command(period='1d'):
    """Handle /lb command"""
    # Generate Excel leaderboard
    tier_stats = db.generate_leaderboard(period)

    # Format message
    msg = f"📊 Leaderboard {period.upper()}\n\n"
    msg += "Return Tiers:\n"
    for tier, pct in tier_stats.items():
        msg += f"{tier}: {pct:.1f}%\n"

    await send_telegram_message(msg)
    await send_telegram_message(file=f'leaderboard_{period}.xlsx')

async def handle_learned_command():
    tracker = CoinTracker()
    learned_info = tracker.get_learning_insights()

    # Format the message
    if learned_info["status"] == "No verified training data yet":
        message = "🤖 No verified training data available yet."
    else:
        message = (
            "🤖 Learning Analysis\n\n"
            f"Total verified coins: {learned_info['total_verified']}\n"
            f"Profitable: {learned_info['profitable_count']}\n"
            f"Unprofitable: {learned_info['unprofitable_count']}\n\n"
            "📊 Insights:\n" + 
            "\n".join(f"• {insight}" for insight in learned_info['insights'])
        )

    await send_telegram_message(message)


async def fetch_meta_words():
    """Fetch meta words and update coin tracker with current meta scores."""
    try:
        response = requests.get("https://frontend-api-v3.pump.fun/metas/current")
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # Create dictionary of word:score pairs
            meta_scores = {item['word'].lower(): float(item['score']) 
                         for item in data if 'word' in item and 'score' in item}

            # Update CoinTracker with new meta scores
            coin_tracker = CoinTracker()
            coin_tracker.update_meta_scores(meta_scores)

            # Format for display
            word_scores = [f"{word} ({score:.3f})" for word, score in meta_scores.items()]
            words_str = ', '.join(word_scores)

            # Send update to Telegram
            message = (
                "🔄 Meta Update\n\n"
                f"📊 Current Meta Words (score):\n{words_str}\n\n"
                "Higher scores indicate stronger market potential."
            )
            await send_telegram_message(message)

            # Schedule next update
            asyncio.create_task(schedule_meta_update())

        else:
            logging.error("Invalid meta API response format")

    except Exception as e:
        logging.error(f"Error fetching meta words: {e}")

async def schedule_meta_update():
    """Schedule periodic meta updates."""
    await asyncio.sleep(600)  # Update every 5 minutes
    await fetch_meta_words()

if __name__ == "__main__":
    logging.info("Starting HTTP server on port 8080")

    # Start HTTP server in a thread
    server = HTTPServer(('0.0.0.0', 8080), EnhancedHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # Start bond monitoring in separate thread
    from bond_monitor import monitor_bonds
    bond_monitor_thread = threading.Thread(target=monitor_bonds, daemon=True)
    bond_monitor_thread.start()

    # Run all async tasks
    async def main():
        await asyncio.gather(
            fetch_meta_words(),
            scan_coins(),
            send_hourly_leaderboard(),
            update_database()
        )

    # Run the event loop
    asyncio.run(main())