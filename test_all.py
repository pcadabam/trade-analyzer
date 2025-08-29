import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys
import warnings

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.trade_parser import TradeParser
from src.core.trade_matcher import TradeMatcher
from src.data.price_fetcher import PriceFetcher
from src.insights.insight_generator import InsightGenerator

warnings.filterwarnings('ignore')

class TestTradeParser(unittest.TestCase):
    def setUp(self):
        self.parser = TradeParser()
        self.sample_csv_path = '/Users/pcadabam/Projects/trade-analyzer/data/sample/tradebook-SIL558-EQ.csv'
    
    def test_parse_real_csv(self):
        df = self.parser.parse_csv(self.sample_csv_path)
        
        self.assertIsInstance(df, pd.DataFrame)
        
        self.assertFalse(df.empty)
        
        for col in self.parser.required_columns:
            self.assertIn(col, df.columns)
        
        self.assertTrue('datetime' in df.columns)
        
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['datetime']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['quantity']))
        self.assertTrue(pd.api.types.is_numeric_dtype(df['price']))
    
    def test_create_test_csv(self):
        test_data = {
            'symbol': ['RELIANCE', 'RELIANCE', 'TCS', 'TCS'],
            'trade_date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
            'order_execution_time': ['10:00:00', '14:00:00', '09:30:00', '15:00:00'],
            'trade_type': ['buy', 'sell', 'buy', 'sell'],
            'quantity': [10, 10, 5, 5],
            'price': [2500.00, 2550.00, 3500.00, 3450.00],
            'order_id': ['1001', '1002', '1003', '1004'],
            'isin': ['INE002A01018', 'INE002A01018', 'INE467B01029', 'INE467B01029'],
            'exchange': ['NSE', 'NSE', 'NSE', 'NSE'],
            'segment': ['EQ', 'EQ', 'EQ', 'EQ'],
            'series': ['EQ', 'EQ', 'EQ', 'EQ'],
            'auction': ['false', 'false', 'false', 'false'],
            'trade_id': ['5001', '5002', '5003', '5004']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame(test_data).to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            df = self.parser.parse_csv(temp_path)
            
            self.assertEqual(len(df), 4)
            
            self.assertEqual(df['symbol'].nunique(), 2)
            
            self.assertTrue(all(df['symbol'].str.isupper()))
            
        finally:
            os.unlink(temp_path)

class TestTradeMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = TradeMatcher()
        
    def test_match_simple_trades(self):
        trades_data = pd.DataFrame({
            'symbol': ['RELIANCE', 'RELIANCE', 'TCS', 'TCS'],
            'datetime': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-01 14:00:00',
                                       '2024-01-02 09:00:00', '2024-01-02 16:00:00']),
            'trade_type': ['buy', 'sell', 'buy', 'sell'],
            'quantity': [100, 100, 50, 50],
            'price': [150.00, 155.00, 2800.00, 2750.00],
            'order_id': ['1', '2', '3', '4']
        })
        
        closed_trades = self.matcher.match_trades(trades_data)
        
        self.assertEqual(len(closed_trades), 2)
        
        reliance_trade = closed_trades[closed_trades['symbol'] == 'RELIANCE'].iloc[0]
        self.assertEqual(reliance_trade['gross_pnl'], 500.00)
        self.assertEqual(reliance_trade['trade_result'], 'win')
        
        tcs_trade = closed_trades[closed_trades['symbol'] == 'TCS'].iloc[0]
        self.assertEqual(tcs_trade['gross_pnl'], -2500.00)
        self.assertEqual(tcs_trade['trade_result'], 'loss')
    
    def test_partial_fills(self):
        trades_data = pd.DataFrame({
            'symbol': ['XYZ', 'XYZ', 'XYZ'],
            'datetime': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-01 11:00:00', 
                                       '2024-01-01 14:00:00']),
            'trade_type': ['buy', 'buy', 'sell'],
            'quantity': [100, 50, 120],
            'price': [100.00, 102.00, 105.00],
            'order_id': ['1', '2', '3']
        })
        
        closed_trades = self.matcher.match_trades(trades_data)
        
        self.assertEqual(len(closed_trades), 2)
        
        first_close = closed_trades.iloc[0]
        self.assertEqual(first_close['quantity'], 100)
        self.assertEqual(first_close['entry_price'], 100.00)
        
        second_close = closed_trades.iloc[1]
        self.assertEqual(second_close['quantity'], 20)
        self.assertEqual(second_close['entry_price'], 102.00)
    
    def test_summary_stats(self):
        trades_data = pd.DataFrame({
            'symbol': ['A', 'A', 'B', 'B', 'C', 'C'],
            'datetime': pd.to_datetime([
                '2024-01-01 10:00:00', '2024-01-01 14:00:00',
                '2024-01-02 10:00:00', '2024-01-02 14:00:00',
                '2024-01-03 10:00:00', '2024-01-03 14:00:00'
            ]),
            'trade_type': ['buy', 'sell', 'buy', 'sell', 'buy', 'sell'],
            'quantity': [100, 100, 50, 50, 75, 75],
            'price': [100, 110, 200, 190, 300, 315],
            'order_id': ['1', '2', '3', '4', '5', '6']
        })
        
        closed_trades = self.matcher.match_trades(trades_data)
        stats = self.matcher.get_summary_stats(closed_trades)
        
        self.assertEqual(stats['total_trades'], 3)
        self.assertEqual(stats['winning_trades'], 2)
        self.assertEqual(stats['losing_trades'], 1)
        self.assertAlmostEqual(stats['win_rate'], 66.67, places=1)

class TestPriceFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = PriceFetcher()
    
    def test_fetch_real_stock_data(self):
        symbol = 'RELIANCE'
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = self.fetcher.get_stock_data(symbol, start_date, end_date, '1d')
        
        if not data.empty:
            self.assertIn('Close', data.columns)
            self.assertIn('Volume', data.columns)
            self.assertIn('High', data.columns)
            self.assertIn('Low', data.columns)
            
            self.assertTrue(pd.api.types.is_datetime64_any_dtype(data.index))
        else:
            print(f"Warning: Could not fetch data for {symbol} - API might be down")
    
    def test_technical_indicators(self):
        symbol = 'TCS'
        date = datetime.now()
        
        indicators = self.fetcher.get_technical_indicators(symbol, date)
        
        if indicators:
            possible_keys = ['rsi', 'sma_10', 'sma_20', 'vwap', 'volume_ratio']
            
            self.assertTrue(any(key in indicators for key in possible_keys))
            
            if 'rsi' in indicators and indicators['rsi'] is not None:
                self.assertTrue(0 <= indicators['rsi'] <= 100)
        else:
            print(f"Warning: Could not fetch indicators for {symbol}")
    
    def test_simulate_exits(self):
        symbol = 'INFY'
        entry_time = datetime.now() - timedelta(days=5)
        exit_time = datetime.now() - timedelta(days=2)
        
        scenarios = self.fetcher.simulate_exit_scenarios(
            symbol, 1500.00, entry_time, exit_time, 100
        )
        
        if scenarios:
            possible_keys = ['best_early_exit', 'best_late_exit', 'trailing_stop']
            
            self.assertTrue(any(key in scenarios for key in possible_keys))
            
            for key in scenarios:
                if key in scenarios:
                    self.assertIn('price', scenarios[key])
                    self.assertIn('potential_pnl', scenarios[key])
                    self.assertIn('time', scenarios[key])
        else:
            print(f"Warning: Could not simulate exits for {symbol}")
    
    def test_cache_functionality(self):
        symbol = 'WIPRO'
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        data1 = self.fetcher.get_stock_data(symbol, start_date, end_date, '1h')
        
        data2 = self.fetcher.get_stock_data(symbol, start_date, end_date, '1h')
        
        if not data1.empty and not data2.empty:
            pd.testing.assert_frame_equal(data1, data2)

class TestInsightGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = InsightGenerator()
        
    def create_sample_trades(self):
        return pd.DataFrame({
            'symbol': ['RELIANCE'] * 10 + ['TCS'] * 10 + ['INFY'] * 10,
            'entry_datetime': pd.date_range(start='2024-01-01', periods=30, freq='D'),
            'exit_datetime': pd.date_range(start='2024-01-01 04:00:00', periods=30, freq='D'),
            'entry_price': [150, 151, 152, 153, 154, 155, 156, 157, 158, 159] * 3,
            'exit_price': [155, 149, 158, 150, 160, 152, 162, 154, 164, 156] * 3,
            'quantity': [100] * 30,
            'gross_pnl': [500, -200, 600, -300, 600, -300, 600, -300, 600, -300] * 3,
            'pnl_percentage': [3.33, -1.32, 3.95, -1.96, 3.90, -1.94, 3.85, -1.91, 3.80, -1.89] * 3,
            'hold_hours': [4] * 30,
            'trade_result': ['win', 'loss', 'win', 'loss', 'win', 'loss', 'win', 'loss', 'win', 'loss'] * 3,
            'entry_value': [15000] * 30,
            'exit_value': [15500, 14900, 15800, 15000, 16000, 15200, 16200, 15400, 16400, 15600] * 3
        })
    
    def test_generate_insights(self):
        trades = self.create_sample_trades()
        
        insights = self.generator.generate_insights(trades)
        
        self.assertIsInstance(insights, list)
        
        if insights:
            for insight in insights:
                self.assertIn('title', insight)
                self.assertIn('type', insight)
                self.assertIn('description', insight)
                self.assertIn('action', insight)
                
                valid_types = ['exit_optimization', 'timing', 'stock_selection', 
                             'risk_management', 'behavioral']
                self.assertIn(insight['type'], valid_types)
    
    def test_exit_timing_analysis(self):
        trades = pd.DataFrame({
            'symbol': ['A'] * 4,
            'entry_datetime': pd.to_datetime(['2024-01-01 10:00:00'] * 4),
            'exit_datetime': pd.to_datetime([
                '2024-01-01 11:00:00',  
                '2024-01-01 11:30:00',  
                '2024-01-01 15:00:00',  
                '2024-01-01 16:00:00'   
            ]),
            'gross_pnl': [100, 150, 300, 350],
            'pnl_percentage': [1.0, 1.5, 3.0, 3.5],
            'hold_hours': [1.0, 1.5, 5.0, 6.0],
            'trade_result': ['win', 'win', 'win', 'win'],
            'entry_price': [100] * 4,
            'exit_price': [101, 101.5, 103, 103.5],
            'quantity': [100] * 4,
            'entry_value': [10000] * 4,
            'exit_value': [10100, 10150, 10300, 10350]
        })
        
        self.generator.insights = []
        self.generator._analyze_exit_timing(trades)
        
        self.assertTrue(len(self.generator.insights) > 0)
    
    def test_stock_performance_analysis(self):
        trades = pd.DataFrame({
            'symbol': ['WINNER', 'WINNER', 'WINNER', 'LOSER', 'LOSER', 'LOSER'],
            'gross_pnl': [1000, 500, 800, -600, -400, -700],
            'trade_result': ['win', 'win', 'win', 'loss', 'loss', 'loss'],
            'entry_datetime': pd.date_range('2024-01-01', periods=6),
            'exit_datetime': pd.date_range('2024-01-02', periods=6),
            'pnl_percentage': [10, 5, 8, -6, -4, -7],
            'hold_hours': [24] * 6,
            'entry_price': [100] * 6,
            'exit_price': [110, 105, 108, 94, 96, 93],
            'quantity': [100] * 6,
            'entry_value': [10000] * 6,
            'exit_value': [11000, 10500, 10800, 9400, 9600, 9300]
        })
        
        self.generator.insights = []
        self.generator._analyze_stock_performance(trades)
        
        insights = self.generator.insights
        
        self.assertTrue(any('WINNER' in str(i) for i in insights))
        
        self.assertTrue(any('LOSER' in str(i) for i in insights))

class TestIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        parser = TradeParser()
        matcher = TradeMatcher()
        generator = InsightGenerator()
        
        sample_csv = '/Users/pcadabam/Projects/trade-analyzer/data/sample/tradebook-SIL558-EQ.csv'
        
        if os.path.exists(sample_csv):
            trades_df = parser.parse_csv(sample_csv)
            
            self.assertFalse(trades_df.empty)
            
            closed_trades = matcher.match_trades(trades_df)
            
            if not closed_trades.empty:
                stats = matcher.get_summary_stats(closed_trades)
                
                self.assertIn('total_trades', stats)
                self.assertIn('win_rate', stats)
                self.assertIn('total_pnl', stats)
                
                insights = generator.generate_insights(closed_trades)
                
                self.assertIsInstance(insights, list)
                
                print(f"\n✅ Integration test passed!")
                print(f"   - Parsed {len(trades_df)} trades")
                print(f"   - Matched {len(closed_trades)} closed trades")
                print(f"   - Generated {len(insights)} insights")
                print(f"   - Total P&L: ₹{stats['total_pnl']:,.2f}")
                print(f"   - Win Rate: {stats['win_rate']:.1f}%")
        else:
            print(f"Sample CSV not found at {sample_csv}")

def run_tests():
    print("=" * 60)
    print("🧪 Running Trade Analyzer Tests")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTradeParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTradeMatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestPriceFetcher))
    suite.addTests(loader.loadTestsFromTestCase(TestInsightGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed successfully!")
    else:
        print(f"❌ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()