#!/usr/bin/env python3
"""
Generate a realistic demo tradebook CSV using real Yahoo Finance prices
for the top 5 most actively traded Indian stocks over 1 month.

This simulates an active trader's behavior with realistic entries/exits based on actual market data.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DemoTradebookGenerator:
    def __init__(self):
        # Top 5 most actively traded Indian stocks
        self.stocks = {
            'RELIANCE': {'symbol': 'RELIANCE.NS', 'isin': 'INE002A01018'},
            'TCS': {'symbol': 'TCS.NS', 'isin': 'INE467B01029'},
            'INFY': {'symbol': 'INFY.NS', 'isin': 'INE009A01021'},
            'HDFC': {'symbol': 'HDFCBANK.NS', 'isin': 'INE040A01034'},
            'ICICIBANK': {'symbol': 'ICICIBANK.NS', 'isin': 'INE090A01021'}
        }
        
        # Trading period - last 30 days
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=45)  # Extra buffer for weekends
        
        self.trades = []
        self.trade_id_counter = 1000000
        self.order_id_counter = 2000000000000000000
        
        # Simulate trader behavior patterns
        self.trader_patterns = {
            'morning_trader': 0.4,  # 40% trades in morning (9-12)
            'afternoon_trader': 0.35,  # 35% trades in afternoon (12-3)
            'late_trader': 0.25,  # 25% trades late (3-3:30)
            'intraday_ratio': 0.6,  # 60% intraday, 40% swing trades
            'win_rate': 0.58,  # 58% win rate (realistic for active trader)
            'avg_quantity': 25,  # Average quantity per trade
        }
    
    def fetch_stock_data(self):
        """Fetch real price data for all stocks"""
        logger.info("Fetching real stock price data from Yahoo Finance...")
        
        stock_data = {}
        for name, info in self.stocks.items():
            try:
                ticker = yf.Ticker(info['symbol'])
                # Get both daily and hourly data
                daily_data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
                hourly_data = ticker.history(start=self.start_date, end=self.end_date, interval='1h')
                
                if not daily_data.empty and not hourly_data.empty:
                    stock_data[name] = {
                        'daily': daily_data,
                        'hourly': hourly_data,
                        'isin': info['isin']
                    }
                    logger.info(f"✅ Fetched data for {name}: {len(daily_data)} days, {len(hourly_data)} hours")
                else:
                    logger.warning(f"⚠️ No data for {name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch {name}: {str(e)}")
        
        return stock_data
    
    def generate_trading_day_pattern(self, date):
        """Generate realistic trading times for a given day"""
        base_date = pd.Timestamp(date).replace(hour=9, minute=15, second=0)
        
        # Market hours: 9:15 AM to 3:30 PM
        market_open = base_date
        market_close = base_date.replace(hour=15, minute=30)
        
        times = []
        
        # Morning session (9:15 - 12:00) - High activity
        morning_trades = np.random.poisson(3)  # Average 3 trades in morning
        for _ in range(morning_trades):
            hour_offset = np.random.exponential(1.5)  # Exponential distribution favoring early hours
            if hour_offset > 2.75:  # Cap at 12:00
                hour_offset = 2.75
            trade_time = market_open + timedelta(hours=hour_offset)
            times.append(trade_time)
        
        # Afternoon session (12:00 - 15:30) - Moderate activity
        afternoon_trades = np.random.poisson(2)  # Average 2 trades in afternoon
        for _ in range(afternoon_trades):
            hour_offset = 2.75 + np.random.uniform(0, 3.5)  # 12:00 to 15:30
            trade_time = market_open + timedelta(hours=hour_offset)
            if trade_time <= market_close:
                times.append(trade_time)
        
        return sorted(times)
    
    def should_be_winning_trade(self, stock_data, entry_time, stock_name):
        """Determine if this should be a winning trade based on actual price movement"""
        try:
            hourly_data = stock_data[stock_name]['hourly']
            
            # Handle timezone compatibility
            if hourly_data.index.tz is not None and entry_time.tz is None:
                entry_time = entry_time.tz_localize(hourly_data.index.tz)
            elif hourly_data.index.tz is None and entry_time.tz is not None:
                entry_time = entry_time.tz_localize(None)
            
            # Find the closest price data to entry time
            entry_idx = hourly_data.index.get_indexer([entry_time], method='nearest')[0]
            
            # Look ahead for potential profit opportunities
            future_data = hourly_data.iloc[entry_idx:entry_idx+10]  # Next 10 hours
            
            if len(future_data) < 2:
                return random.random() < self.trader_patterns['win_rate']
            
            entry_price = future_data.iloc[0]['Close']
            max_future_price = future_data['High'].max()
            
            # If price went up by more than 1.5%, likely winning trade
            potential_gain = (max_future_price - entry_price) / entry_price
            
            if potential_gain > 0.015:  # 1.5% gain available
                return random.random() < 0.75  # 75% chance of winning
            else:
                return random.random() < 0.35  # 35% chance of winning
                
        except Exception:
            return random.random() < self.trader_patterns['win_rate']
    
    def generate_exit_time_and_price(self, stock_data, entry_time, entry_price, stock_name, is_winning):
        """Generate realistic exit time and price based on actual market data"""
        try:
            # Determine if intraday or swing trade first (before timezone operations)
            is_intraday = random.random() < self.trader_patterns['intraday_ratio']
            
            # Generate exit time as timezone-naive first
            if is_intraday:
                # Exit same day or next day
                max_hold_hours = random.uniform(0.5, 6)  # 30 mins to 6 hours
                exit_time = entry_time + timedelta(hours=max_hold_hours)
                
                # Don't exit after market hours (use timezone-naive comparison)
                market_close = entry_time.replace(hour=15, minute=30, second=0)
                if exit_time > market_close:
                    # Exit next day morning
                    next_day = entry_time + timedelta(days=1)
                    exit_time = next_day.replace(hour=random.randint(9, 11), 
                                               minute=random.randint(0, 59))
            else:
                # Swing trade: 1-7 days
                hold_days = random.randint(1, 7)
                exit_time = entry_time + timedelta(days=hold_days)
                exit_time = exit_time.replace(hour=random.randint(9, 15), 
                                            minute=random.randint(0, 30))
            
            # Simple pricing based on win/loss target (avoid complex data lookup that causes timezone issues)
            if is_winning:
                # Winning trade: 0.5% to 5% gain
                gain_pct = random.uniform(0.005, 0.05)
                exit_price = entry_price * (1 + gain_pct)
            else:
                # Losing trade: 0.5% to 4% loss
                loss_pct = random.uniform(0.005, 0.04)
                exit_price = entry_price * (1 - loss_pct)
            
            return exit_time, round(exit_price, 2)
            
        except Exception as e:
            logger.warning(f"Error generating exit for {stock_name}: {str(e)}")
            # Fallback to simple calculation
            if is_intraday:
                exit_time = entry_time + timedelta(hours=random.uniform(1, 4))
            else:
                exit_time = entry_time + timedelta(days=random.randint(1, 5))
            
            if is_winning:
                exit_price = entry_price * (1 + random.uniform(0.01, 0.03))
            else:
                exit_price = entry_price * (1 - random.uniform(0.01, 0.03))
            
            return exit_time, round(exit_price, 2)
    
    def generate_realistic_trades(self, stock_data):
        """Generate realistic trades based on actual market data"""
        logger.info("Generating realistic trades based on market patterns...")
        
        # Get trading days (exclude weekends)
        trading_days = pd.date_range(
            start=self.start_date + timedelta(days=10), 
            end=self.end_date - timedelta(days=5), 
            freq='B'  # Business days only
        )
        
        trades_list = []
        
        for date in trading_days:
            # Skip some days (trader doesn't trade every day)
            if random.random() < 0.3:  # 30% chance to skip the day
                continue
                
            # Generate trading times for this day
            trading_times = self.generate_trading_day_pattern(date)
            
            if not trading_times:
                continue
            
            for trade_time in trading_times:
                # Choose a random stock
                stock_name = random.choice(list(stock_data.keys()))
                
                try:
                    # Get entry price from actual data
                    hourly_data = stock_data[stock_name]['hourly']
                    
                    # Handle timezone compatibility for entry price lookup
                    lookup_time = trade_time
                    if hourly_data.index.tz is not None and lookup_time.tz is None:
                        lookup_time = lookup_time.tz_localize(hourly_data.index.tz)
                    elif hourly_data.index.tz is None and lookup_time.tz is not None:
                        lookup_time = lookup_time.tz_localize(None)
                    
                    entry_idx = hourly_data.index.get_indexer([lookup_time], method='nearest')[0]
                    entry_price = round(hourly_data.iloc[entry_idx]['Close'], 2)
                    
                    # Determine if this should be a winning trade
                    is_winning = self.should_be_winning_trade(stock_data, trade_time, stock_name)
                    
                    # Generate realistic quantity
                    base_qty = self.trader_patterns['avg_quantity']
                    quantity = max(1, int(np.random.gamma(2, base_qty/2)))  # Gamma distribution
                    
                    # Generate exit time and price
                    exit_time, exit_price = self.generate_exit_time_and_price(
                        stock_data, trade_time, entry_price, stock_name, is_winning
                    )
                    
                    # Create buy trade
                    buy_trade = {
                        'symbol': stock_name,
                        'isin': stock_data[stock_name]['isin'],
                        'trade_date': trade_time.strftime('%Y-%m-%d'),
                        'exchange': 'NSE',
                        'segment': 'EQ',
                        'series': 'EQ',
                        'trade_type': 'buy',
                        'auction': 'false',
                        'quantity': quantity,
                        'price': entry_price,
                        'trade_id': self.trade_id_counter,
                        'order_id': self.order_id_counter,
                        'order_execution_time': trade_time.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                    
                    # Create sell trade
                    sell_trade = {
                        'symbol': stock_name,
                        'isin': stock_data[stock_name]['isin'],
                        'trade_date': exit_time.strftime('%Y-%m-%d'),
                        'exchange': 'NSE',
                        'segment': 'EQ',
                        'series': 'EQ',
                        'trade_type': 'sell',
                        'auction': 'false',
                        'quantity': quantity,
                        'price': exit_price,
                        'trade_id': self.trade_id_counter + 1,
                        'order_id': self.order_id_counter + 1,
                        'order_execution_time': exit_time.strftime('%Y-%m-%dT%H:%M:%S')
                    }
                    
                    trades_list.extend([buy_trade, sell_trade])
                    
                    # Update counters
                    self.trade_id_counter += 2
                    self.order_id_counter += 2
                    
                    # Log trade
                    pnl = (exit_price - entry_price) * quantity
                    trade_type = "WIN" if pnl > 0 else "LOSS"
                    logger.debug(f"{trade_type}: {stock_name} {quantity}@{entry_price} -> {exit_price} = ₹{pnl:.2f}")
                    
                except Exception as e:
                    logger.warning(f"Error generating trade for {stock_name} at {trade_time}: {str(e)}")
                    continue
        
        return trades_list
    
    def save_to_csv(self, trades, filename='data/demo/demo_tradebook.csv'):
        """Save trades to CSV file"""
        # Ensure directory exists
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Sort trades by execution time
        trades.sort(key=lambda x: x['order_execution_time'])
        
        # Define CSV headers matching Zerodha format
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
        
        # Generate summary
        buy_trades = [t for t in trades if t['trade_type'] == 'buy']
        sell_trades = [t for t in trades if t['trade_type'] == 'sell']
        
        total_trades = len(buy_trades)
        total_value = sum(t['quantity'] * t['price'] for t in buy_trades)
        
        print(f"""
📊 Demo Tradebook Generated Successfully!
==========================================
📈 Total Trades: {total_trades}
💰 Total Trade Value: ₹{total_value:,.0f}
📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}
🏢 Stocks: {', '.join(self.stocks.keys())}
📁 File: {filename}

🚀 Use this file to test your Trading Coach Dashboard!
        """)

def main():
    """Generate demo tradebook"""
    print("🤖 Generating Demo Tradebook with Real Market Data...")
    print("=" * 60)
    
    generator = DemoTradebookGenerator()
    
    # Fetch real stock data
    stock_data = generator.fetch_stock_data()
    
    if not stock_data:
        logger.error("❌ No stock data fetched. Please check your internet connection.")
        return
    
    # Generate realistic trades
    trades = generator.generate_realistic_trades(stock_data)
    
    if not trades:
        logger.error("❌ No trades generated.")
        return
    
    # Save to CSV
    generator.save_to_csv(trades)

if __name__ == "__main__":
    main()