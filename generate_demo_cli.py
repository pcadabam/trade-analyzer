#!/usr/bin/env python3
"""
Simple CLI tool to generate demo trading data with real market prices.

Usage:
    python generate_demo_cli.py --stocks RELIANCE,TCS,INFY --days 30 --output bank_demo.csv
    python generate_demo_cli.py --stocks WIPRO,TECHM,HCLTECH --days 60 --output tech_demo.csv
"""

import yfinance as yf
import pandas as pd
import random
import argparse
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stock symbol mappings
STOCK_MAPPING = {
    'RELIANCE': {'symbol': 'RELIANCE.NS', 'isin': 'INE002A01018'},
    'TCS': {'symbol': 'TCS.NS', 'isin': 'INE467B01029'},
    'INFY': {'symbol': 'INFY.NS', 'isin': 'INE009A01021'},
    'HDFC': {'symbol': 'HDFCBANK.NS', 'isin': 'INE040A01034'},
    'ICICIBANK': {'symbol': 'ICICIBANK.NS', 'isin': 'INE090A01021'},
    'WIPRO': {'symbol': 'WIPRO.NS', 'isin': 'INE075A01022'},
    'TECHM': {'symbol': 'TECHM.NS', 'isin': 'INE669C01036'},
    'HCLTECH': {'symbol': 'HCLTECH.NS', 'isin': 'INE860A01027'},
    'AXISBANK': {'symbol': 'AXISBANK.NS', 'isin': 'INE238A01034'},
    'SBIN': {'symbol': 'SBIN.NS', 'isin': 'INE062A01020'}
}

def fetch_stock_data(stock_names, days=30):
    """Fetch stock data for given stocks"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 10)  # Extra buffer
    
    stock_data = {}
    
    for stock_name in stock_names:
        if stock_name not in STOCK_MAPPING:
            logger.warning(f"Stock {stock_name} not found in mapping")
            continue
            
        symbol = STOCK_MAPPING[stock_name]['symbol']
        logger.info(f"Fetching data for {stock_name} ({symbol})...")
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date, interval='1h')
            
            if not data.empty:
                stock_data[stock_name] = data
                logger.info(f"✅ Got {len(data)} hours of data for {stock_name}")
            else:
                logger.warning(f"❌ No data for {stock_name}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching {stock_name}: {e}")
    
    return stock_data

def generate_trades(stock_data, win_rate=0.55, intraday_ratio=0.6, avg_quantity=30):
    """Generate realistic trades"""
    trades = []
    trade_id = 1000000
    order_id = 2000000000000000000
    
    # Generate trading days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    trading_days = pd.date_range(start_date, end_date, freq='B')
    
    for day in trading_days:
        if day.date() > datetime.now().date():
            continue
            
        # Generate 1-4 trades per day
        num_trades = random.choice([1, 1, 2, 2, 3, 4])
        
        for _ in range(num_trades):
            # Pick random stock
            stock_name = random.choice(list(stock_data.keys()))
            stock_df = stock_data[stock_name]
            
            # Get data for this day
            day_data = stock_df[stock_df.index.date == day.date()]
            if day_data.empty:
                continue
                
            # Generate entry time (9:30 AM to 3:00 PM)
            entry_hour = random.randint(9, 14)
            entry_minute = random.randint(0, 59)
            if entry_hour == 9 and entry_minute < 30:
                entry_minute = 30
                
            entry_time = day.replace(hour=entry_hour, minute=entry_minute, second=random.randint(0, 59))
            
            # Get closest price
            try:
                closest_idx = day_data.index.get_indexer([entry_time], method='nearest')[0]
                entry_price = round(day_data.iloc[closest_idx]['Close'], 2)
            except:
                entry_price = round(day_data['Close'].iloc[0], 2)
            
            quantity = max(1, int(random.gauss(avg_quantity, 10)))
            
            # Create entry trade
            entry_trade = {
                'symbol': stock_name,
                'isin': STOCK_MAPPING[stock_name]['isin'],
                'trade_date': entry_time.strftime('%Y-%m-%d'),
                'order_execution_time': entry_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'trade_type': 'buy',
                'quantity': quantity,
                'price': entry_price,
                'trade_id': trade_id,
                'order_id': order_id,
                'exchange': 'NSE',
                'segment': 'EQ',
                'series': 'EQ',
                'auction': 'false'
            }
            trades.append(entry_trade)
            trade_id += 1
            order_id += 1
            
            # Generate exit
            is_winning = random.random() < win_rate
            is_intraday = random.random() < intraday_ratio
            
            if is_intraday:
                # Exit same day
                exit_hour = random.randint(entry_hour + 1, 15)
                if exit_hour > 15:
                    exit_hour = 15
                    exit_minute = random.randint(0, 29)
                else:
                    exit_minute = random.randint(0, 59)
                    
                exit_time = entry_time.replace(hour=exit_hour, minute=exit_minute)
            else:
                # Exit 1-5 days later
                days_later = random.randint(1, 5)
                exit_date = day + timedelta(days=days_later)
                # Skip weekends
                while exit_date.weekday() >= 5:
                    exit_date += timedelta(days=1)
                    
                exit_hour = random.randint(9, 15)
                exit_minute = random.randint(0, 59)
                exit_time = exit_date.replace(hour=exit_hour, minute=exit_minute)
            
            # Get exit price
            exit_day_data = stock_df[stock_df.index.date == exit_time.date()]
            if not exit_day_data.empty:
                try:
                    closest_idx = exit_day_data.index.get_indexer([exit_time], method='nearest')[0]
                    market_exit_price = exit_day_data.iloc[closest_idx]['Close']
                except:
                    market_exit_price = exit_day_data['Close'].iloc[0]
                    
                # Adjust price based on winning/losing
                if is_winning:
                    exit_price = market_exit_price * random.uniform(1.01, 1.08)  # 1-8% gain
                else:
                    exit_price = market_exit_price * random.uniform(0.92, 0.99)  # 1-8% loss
                    
                exit_price = round(exit_price, 2)
                
                # Create exit trade
                exit_trade = {
                    'symbol': stock_name,
                    'isin': STOCK_MAPPING[stock_name]['isin'],
                    'trade_date': exit_time.strftime('%Y-%m-%d'),
                    'order_execution_time': exit_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'trade_type': 'sell',
                    'quantity': quantity,
                    'price': exit_price,
                    'trade_id': trade_id,
                    'order_id': order_id,
                    'exchange': 'NSE',
                    'segment': 'EQ',
                    'series': 'EQ',
                    'auction': 'false'
                }
                trades.append(exit_trade)
                trade_id += 1
                order_id += 1
    
    return trades

def save_trades_to_csv(trades, filename):
    """Save trades to CSV"""
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Sort by execution time
    trades.sort(key=lambda x: x['order_execution_time'])
    
    headers = [
        'symbol', 'isin', 'trade_date', 'exchange', 'segment', 'series',
        'trade_type', 'auction', 'quantity', 'price', 'trade_id', 'order_id',
        'order_execution_time'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(trades)
    
    logger.info(f"✅ Saved {len(trades)} trades to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Generate demo trading data')
    parser.add_argument('--stocks', required=True, help='Comma-separated stock names (e.g., RELIANCE,TCS,INFY)')
    parser.add_argument('--days', type=int, default=30, help='Number of days back to generate data (default: 30)')
    parser.add_argument('--output', required=True, help='Output CSV filename')
    parser.add_argument('--win-rate', type=float, default=0.55, help='Win rate (0.0-1.0, default: 0.55)')
    parser.add_argument('--intraday-ratio', type=float, default=0.6, help='Ratio of intraday trades (default: 0.6)')
    parser.add_argument('--avg-quantity', type=int, default=30, help='Average quantity per trade (default: 30)')
    
    args = parser.parse_args()
    
    # Parse stocks
    stock_names = [s.strip().upper() for s in args.stocks.split(',')]
    
    # Validate stocks
    invalid_stocks = [s for s in stock_names if s not in STOCK_MAPPING]
    if invalid_stocks:
        logger.error(f"Invalid stocks: {invalid_stocks}")
        logger.info(f"Available stocks: {list(STOCK_MAPPING.keys())}")
        return
    
    logger.info(f"🚀 Generating demo for stocks: {stock_names}")
    logger.info(f"📅 Time period: {args.days} days")
    logger.info(f"📊 Win rate: {args.win_rate:.0%}, Intraday: {args.intraday_ratio:.0%}")
    
    # Fetch data
    stock_data = fetch_stock_data(stock_names, args.days)
    
    if not stock_data:
        logger.error("❌ No stock data fetched")
        return
    
    # Generate trades
    trades = generate_trades(
        stock_data, 
        win_rate=args.win_rate,
        intraday_ratio=args.intraday_ratio, 
        avg_quantity=args.avg_quantity
    )
    
    if not trades:
        logger.error("❌ No trades generated")
        return
    
    # Save to CSV
    save_trades_to_csv(trades, args.output)
    
    # Show stats
    buy_trades = len([t for t in trades if t['trade_type'] == 'buy'])
    sell_trades = len([t for t in trades if t['trade_type'] == 'sell'])
    logger.info(f"📊 Generated {buy_trades} buy and {sell_trades} sell trades")

if __name__ == "__main__":
    main()