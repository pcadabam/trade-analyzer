import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

class PriceFetcher:
    def __init__(self, use_multi_source=True):
        self.cache = {}
        self.use_multi_source = use_multi_source
        
        # Initialize multi-source fetcher if enabled
        if use_multi_source:
            try:
                from .multi_source_fetcher import MultiSourcePriceFetcher
                self.multi_fetcher = MultiSourcePriceFetcher()
                logger.info("Multi-source data fetching enabled")
            except ImportError:
                logger.warning("Multi-source fetcher not available, using Yahoo Finance only")
                self.multi_fetcher = None
        else:
            self.multi_fetcher = None
        
    def get_stock_data(self, symbol: str, start_date: datetime, 
                       end_date: datetime, interval: str = '1h') -> pd.DataFrame:
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Use multi-source fetcher if available
        if self.multi_fetcher:
            try:
                data = self.multi_fetcher.get_stock_data(symbol, start_date, end_date, interval)
                if not data.empty:
                    self.cache[cache_key] = data
                return data
            except Exception as e:
                logger.warning(f"Multi-source fetcher failed for {symbol}: {str(e)}")
                # Fall back to original Yahoo Finance method
        
        # Original single-source implementation as fallback
        return self._get_stock_data_yahoo_only(symbol, start_date, end_date, interval)
    
    def _get_stock_data_yahoo_only(self, symbol: str, start_date: datetime, 
                                  end_date: datetime, interval: str = '1h') -> pd.DataFrame:
        """Original Yahoo Finance-only implementation as fallback"""
        
        # List of known problematic symbols to skip
        skip_symbols = ['IGIL', 'APLAPOLLO', 'ZEEL']  # Add more as needed
        if symbol in skip_symbols:
            logger.info(f"Skipping known problematic symbol: {symbol}")
            return pd.DataFrame()
        
        try:
            # Try NSE first
            ticker_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(ticker_symbol)
            
            # Suppress yfinance error logs temporarily
            import logging
            yfinance_logger = logging.getLogger("yfinance")
            original_level = yfinance_logger.level
            yfinance_logger.setLevel(logging.CRITICAL)
            
            try:
                data = ticker.history(
                    start=start_date,
                    end=pd.Timestamp(end_date) + pd.Timedelta(days=1),
                    interval=interval
                )
                
                # Try BSE if NSE fails
                if data.empty:
                    ticker_symbol = f"{symbol}.BO"
                    ticker = yf.Ticker(ticker_symbol)
                    data = ticker.history(
                        start=start_date,
                        end=pd.Timestamp(end_date) + pd.Timedelta(days=1),
                        interval=interval
                    )
                
                # Try daily data if intraday fails
                if data.empty and interval != '1d':
                    data = ticker.history(
                        start=start_date,
                        end=pd.Timestamp(end_date) + pd.Timedelta(days=1),
                        interval='1d'
                    )
            finally:
                # Restore original log level
                yfinance_logger.setLevel(original_level)
            
            if not data.empty:
                logger.info(f"Fetched {symbol} data from Yahoo Finance fallback")
            else:
                logger.info(f"No data available for {symbol} in the requested time period")
                
            return data
            
        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_price_during_trade(self, symbol: str, entry_time: datetime, 
                              exit_time: datetime) -> Dict:
        start = pd.Timestamp(entry_time) - pd.Timedelta(hours=1)
        end = pd.Timestamp(exit_time) + pd.Timedelta(days=2)
        
        interval = '15m' if (exit_time - entry_time).days < 1 else '1h'
        
        price_data = self.get_stock_data(symbol, start, end, interval)
        
        if price_data.empty:
            return {}
        
        # Handle timezone compatibility for filtering
        if price_data.index.tz is not None:
            # Price data has timezone, ensure entry/exit times match
            if pd.Timestamp(entry_time).tz is None:
                entry_time_tz = pd.Timestamp(entry_time).tz_localize(price_data.index.tz)
                exit_time_tz = pd.Timestamp(exit_time).tz_localize(price_data.index.tz)
            else:
                entry_time_tz = pd.Timestamp(entry_time).tz_convert(price_data.index.tz)
                exit_time_tz = pd.Timestamp(exit_time).tz_convert(price_data.index.tz)
        else:
            # Price data is timezone naive, ensure entry/exit times are also naive
            entry_time_tz = pd.Timestamp(entry_time).tz_localize(None) if pd.Timestamp(entry_time).tz is not None else pd.Timestamp(entry_time)
            exit_time_tz = pd.Timestamp(exit_time).tz_localize(None) if pd.Timestamp(exit_time).tz is not None else pd.Timestamp(exit_time)
        
        try:
            trade_period = price_data[
                (price_data.index >= entry_time_tz) & 
                (price_data.index <= exit_time_tz)
            ]
        except TypeError:
            # If comparison still fails, return empty dict
            return {}
        
        if trade_period.empty:
            return {}
        
        return {
            'max_price': trade_period['High'].max(),
            'min_price': trade_period['Low'].min(),
            'avg_volume': trade_period['Volume'].mean(),
            'price_volatility': trade_period['Close'].std(),
            'price_data': trade_period
        }
    
    def simulate_exit_scenarios(self, symbol: str, entry_price: float,
                               entry_time: datetime, exit_time: datetime,
                               quantity: int) -> Dict:
        extended_end = pd.Timestamp(exit_time) + pd.Timedelta(days=2)
        
        price_data = self.get_stock_data(
            symbol, entry_time, extended_end, '15m'
        )
        
        if price_data.empty:
            return {}
        
        # Handle timezone compatibility
        if price_data.index.tz is not None:
            # Price data has timezone, ensure exit_time matches
            if pd.Timestamp(exit_time).tz is None:
                exit_time_tz = pd.Timestamp(exit_time).tz_localize(price_data.index.tz)
            else:
                exit_time_tz = pd.Timestamp(exit_time).tz_convert(price_data.index.tz)
        else:
            # Price data is timezone naive, ensure exit_time is also naive
            exit_time_tz = pd.Timestamp(exit_time).tz_localize(None) if pd.Timestamp(exit_time).tz is not None else pd.Timestamp(exit_time)
        
        try:
            filtered_data = price_data[price_data.index <= exit_time_tz]
            if filtered_data.empty:
                return {}
            actual_exit_idx = price_data.index.get_loc(filtered_data.index[-1])
        except (IndexError, KeyError):
            return {}
        
        before_exit = price_data.iloc[:actual_exit_idx]
        after_exit = price_data.iloc[actual_exit_idx:]
        
        results = {}
        
        if not before_exit.empty:
            best_exit_before = before_exit['High'].max()
            results['best_early_exit'] = {
                'price': best_exit_before,
                'potential_pnl': (best_exit_before - entry_price) * quantity,
                'time': before_exit[before_exit['High'] == best_exit_before].index[0]
            }
        
        if not after_exit.empty and len(after_exit) > 1:
            best_exit_after = after_exit.iloc[1:]['High'].max()
            results['best_late_exit'] = {
                'price': best_exit_after,
                'potential_pnl': (best_exit_after - entry_price) * quantity,
                'time': after_exit[after_exit['High'] == best_exit_after].index[0]
            }
        
        trailing_stop_exit = self._simulate_trailing_stop(
            price_data, entry_time, entry_price, stop_percent=2.0
        )
        if trailing_stop_exit:
            results['trailing_stop'] = {
                'price': trailing_stop_exit['price'],
                'potential_pnl': (trailing_stop_exit['price'] - entry_price) * quantity,
                'time': trailing_stop_exit['time']
            }
        
        return results
    
    def _simulate_trailing_stop(self, price_data: pd.DataFrame, 
                               entry_time: datetime, entry_price: float,
                               stop_percent: float = 2.0) -> Optional[Dict]:
        # Handle timezone compatibility for entry_time
        if price_data.index.tz is not None:
            # Price data has timezone, ensure entry_time matches
            if pd.Timestamp(entry_time).tz is None:
                entry_time_tz = pd.Timestamp(entry_time).tz_localize(price_data.index.tz)
            else:
                entry_time_tz = pd.Timestamp(entry_time).tz_convert(price_data.index.tz)
        else:
            # Price data is timezone naive, ensure entry_time is also naive
            entry_time_tz = pd.Timestamp(entry_time).tz_localize(None) if pd.Timestamp(entry_time).tz is not None else pd.Timestamp(entry_time)
        
        try:
            trade_data = price_data[price_data.index >= entry_time_tz]
        except TypeError:
            # If comparison still fails, return None
            return None
        
        if trade_data.empty:
            return None
        
        highest_price = entry_price
        
        for idx, row in trade_data.iterrows():
            current_price = row['Close']
            
            if current_price > highest_price:
                highest_price = current_price
            
            stop_price = highest_price * (1 - stop_percent / 100)
            
            if current_price <= stop_price:
                return {
                    'price': current_price,
                    'time': idx,
                    'highest_price': highest_price
                }
        
        return None
    
    def get_technical_indicators(self, symbol: str, date: datetime) -> Dict:
        end_date = date
        start_date = pd.Timestamp(date) - pd.Timedelta(days=30)
        
        data = self.get_stock_data(symbol, start_date, end_date, '1d')
        
        if data.empty or len(data) < 14:
            return {}
        
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        
        data['RSI'] = self._calculate_rsi(data['Close'])
        
        data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
        
        latest = data.iloc[-1]
        
        return {
            'rsi': latest['RSI'] if not pd.isna(latest['RSI']) else None,
            'sma_10': latest['SMA_10'] if not pd.isna(latest['SMA_10']) else None,
            'sma_20': latest['SMA_20'] if not pd.isna(latest['SMA_20']) else None,
            'vwap': latest['VWAP'] if not pd.isna(latest['VWAP']) else None,
            'volume_ratio': latest['Volume'] / data['Volume'].mean() if data['Volume'].mean() > 0 else None
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_data_source_info(self) -> Dict:
        """Get information about available data sources"""
        info = {
            'multi_source_enabled': self.multi_fetcher is not None,
            'available_sources': [],
            'source_status': {}
        }
        
        if self.multi_fetcher:
            info['available_sources'] = self.multi_fetcher.get_available_sources()
            info['source_status'] = self.multi_fetcher.get_data_source_status()
        else:
            info['available_sources'] = ['yahoo_finance']
            info['source_status'] = {'yahoo_finance': '✅ Available (fallback only)'}
        
        return info