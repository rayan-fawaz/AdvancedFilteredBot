
import sqlite3
import pandas as pd
from datetime import datetime

class TokenDB:
    def __init__(self):
        self.conn = sqlite3.connect('tokens.db')
        self.create_tables()
        
    def create_tables(self):
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS token_calls (
            mint TEXT PRIMARY KEY,
            name TEXT,
            symbol TEXT,
            timestamp DATETIME,
            market_cap_at_call REAL,
            filters_passed INTEGER,
            reply_count INTEGER,
            reply_makers INTEGER,
            dex_paid INTEGER,
            bundle_info TEXT,
            active_snipers INTEGER,
            price_change_5m REAL,
            price_change_1h REAL,
            price_change_6h REAL,
            price_change_24h REAL,
            volume_5m REAL,
            volume_1h REAL,
            volume_6h REAL,
            volume_24h REAL,
            holders_total INTEGER,
            holders_top_10 REAL,
            holders_top_20 REAL,
            top_5_wallets TEXT,
            trades_1h INTEGER,
            unique_wallet_1h INTEGER,
            unique_wallet_24h INTEGER,
            ath_price REAL,
            ath_market_cap REAL,
            return_multiplier REAL
        )''')
        self.conn.commit()

    def insert_token(self, coin, holders_info, dex_data, trench_data):
        """Insert new token data into database"""
        self.conn.execute('''
        INSERT OR REPLACE INTO token_calls VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            coin['mint'],
            coin['name'], 
            coin['symbol'],
            datetime.now(),
            coin['usd_market_cap'],
            1, # filters_passed
            coin.get('reply_count', 0),
            holders_info.get('unique_wallet_1h', 0),
            1 if dex_data else 0, # dex_paid
            str(trench_data), # bundle_info as string
            len(trench_data.get('snipers', [])) if trench_data else 0,
            dex_data['price_change_5m'],
            dex_data['price_change_1h'],
            dex_data['price_change_6h'], 
            dex_data['price_change_24h'],
            dex_data['volume_5m'],
            dex_data['volume_1h'],
            dex_data['volume_6h'],
            dex_data['volume_24h'],
            holders_info['total_holders'],
            holders_info['top_10_percentage'],
            holders_info['top_20_percentage'],
            str(holders_info['top_5_addresses']),
            holders_info['trade_1h'],
            holders_info['unique_wallet_1h'],
            holders_info['unique_wallet_24h'],
            0, # ath_price (updated hourly)
            0, # ath_market_cap (updated hourly)
            0  # return_multiplier (updated hourly)
        ))
        self.conn.commit()

    def update_token_returns(self):
        """Update ATH and return metrics hourly"""
        cur = self.conn.cursor()
        cur.execute('''
        SELECT mint, market_cap_at_call FROM token_calls 
        WHERE datetime(timestamp) >= datetime('now', '-24 hours')
        ''')
        for mint, initial_mc in cur.fetchall():
            # Get current market cap from DEX
            try:
                response = requests.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
                data = response.json()
                if 'pairs' in data and len(data['pairs']) > 0:
                    pair = data['pairs'][0]
                    current_mc = float(pair['fdv'])
                    ath = float(pair.get('priceUsd', 0))
                    
                    self.conn.execute('''
                    UPDATE token_calls 
                    SET ath_price = ?,
                        ath_market_cap = ?,
                        return_multiplier = ?
                    WHERE mint = ?
                    ''', (ath, current_mc, current_mc/initial_mc if initial_mc > 0 else 0, mint))
                    
            except Exception as e:
                print(f"Error updating {mint}: {e}")
                
        self.conn.commit()

    def generate_leaderboard(self, period='1d'):
        """Generate leaderboard Excel file"""
        if period == '1d':
            query = '''
            SELECT * FROM token_calls 
            WHERE datetime(timestamp) >= datetime('now', '-24 hours')
            ORDER BY return_multiplier DESC
            '''
        elif period == '1h':
            query = '''
            SELECT * FROM token_calls 
            WHERE datetime(timestamp) >= datetime('now', '-1 hour')
            ORDER BY return_multiplier DESC
            '''
            
        df = pd.read_sql_query(query, self.conn)
        
        # Calculate tier percentages
        total = len(df)
        tiers = {
            '2x': len(df[df['return_multiplier'] >= 2]),
            '3x': len(df[df['return_multiplier'] >= 3]),
            '5x': len(df[df['return_multiplier'] >= 5]),
            '10x': len(df[df['return_multiplier'] >= 10]),
            '20x': len(df[df['return_multiplier'] >= 20]),
            '30x': len(df[df['return_multiplier'] >= 30]),
            '50x': len(df[df['return_multiplier'] >= 50]),
            '100x': len(df[df['return_multiplier'] >= 100])
        }
        
        tier_pcts = {k: (v/total)*100 if total > 0 else 0 for k,v in tiers.items()}
        
        # Format Excel
        writer = pd.ExcelWriter(f'leaderboard_{period}.xlsx', engine='openpyxl')
        
        # Token data sheet
        df.to_excel(writer, sheet_name='Tokens', index=False)
        
        # Tier stats sheet
        pd.DataFrame([tier_pcts]).T.rename(columns={0:'Percentage'}).to_excel(
            writer, sheet_name='Tier Stats')
            
        writer.close()
        return tier_pcts

db = TokenDB()
