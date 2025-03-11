import requests
import asyncio
import logging
from datetime import datetime, timezone, timedelta

# Telegram API (still used for sending messages)
import os
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8046651136:AAGHoEFIJhW3zHTe6CI0iOcn6FgePpljXqM")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "-1002429691769")

# Featured Coins API
API_URL = "https://frontend-api-v3.pump.fun/coins/for-you?offset=0&limit=50&includeNsfw=false"

# Helius API
HELIUS_API_KEY = "d2eb41e9-0474-45d9-8c53-f487ac8fdd96"
HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Filter Constants
MIN_VOLUME = 4000
MIN_HOLDERS = 20
BIGGEST_WALLET_MAX = 4.0  # in percentage
MIN_MARKET_CAP = 7000
MAX_MARKET_CAP = 20000
MIN_BUYS = 7
MIN_SELLS = 7

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


async def send_telegram_message(message):
    """Send a message to the Telegram group."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")


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
        top_5 = [
            float(holder["amount"]) / total_supply * 100
            for holder in real_holders[:5]
        ]

        # Only proceed if the largest wallet is within acceptable limits (<= 4%)
        if max(top_5) > BIGGEST_WALLET_MAX:
            return None

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
    top_5 = " | ".join(f"{percent:.2f}"
                       for percent in holders_info["top_5_percentages"])
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


def format_coin_message(coin, holders_info, dex_data):
    """Format coin information into a readable Telegram message."""
    mint_address = coin["mint"]
    pumpfun_link = f"https://pump.fun/coin/{mint_address}"
    bullx_link = f"https://neo.bullx.io/terminal?chainId=1399811149&address={mint_address}&r=YEGC2RLRAUE&l=en"

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
        dex_paid = dex_data_orders.get(
            "status") == "approved" if dex_data_orders else False
    except Exception:
        dex_paid = False
    dex_status = "🟢" if dex_paid else "🔴"

    return (f"🔹 <b>{coin['name']}</b> ({coin['symbol']})\n"
            f"💰 <b>Market Cap:</b> ${coin['usd_market_cap']:,.2f}\n"
            f"🎯 <b>DEX Paid:</b> {dex_status}\n"
            f"{price_text}"
            f"{volume_text}"
            f"{ath_text}"
            f"{format_holders_message(holders_info)}"
            f"🔗 <a href='{pumpfun_link}'>PF</a> | "
            f"📊 <a href='{bullx_link}'>NEO</a>\n\n"
            f"🆔 Mint: <code>{mint_address}</code>\n"
            f"——————————————————————————————\n")


async def scan_coins():
    """Continuously scan the featured coins API for new coins meeting filter criteria."""
    seen_mints = {}
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

            # DEX data & volume filter
            dex_data = get_dex_data(mint)
            if not dex_data:
                continue
            if dex_data.get("volume_24h", 0) < MIN_VOLUME:
                continue

            new_coins.append((coin, holders_info, dex_data))
            seen_mints[mint] = market_cap

        if new_coins:
            message = "🚀 <b>NEW CREATION ALERT!</b> 🚀\n\n" + "\n".join(
                format_coin_message(coin, holders_info, dex_data)
                for coin, holders_info, dex_data in new_coins)
            await send_telegram_message(message)
        logging.info(f"Checked: {len(new_coins)} new coins meeting criteria")
        await asyncio.sleep(15)


from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            'status': 'running',
            'message': 'Crypto scanner is active'
        }
        self.wfile.write(json.dumps(response).encode())

def run_http_server():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    logging.info("Server started on port 8080")
    server.serve_forever()

if __name__ == "__main__":
    # Start HTTP server in a separate thread
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    # Run the main scanner
    asyncio.run(scan_coins())
