import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import logging
import numpy as np
import time

logger = logging.getLogger(__name__)

class MultiSourcePriceFetcher:
    """Enhanced price fetcher with multiple data sources and intelligent fallback"""
    
    def __init__(self):
        self.cache = {}
        self.data_sources = [
            'yahoo_finance',      # Primary - most reliable
            'google_finance',     # Secondary - sometimes works
            'nse_api',           # Tertiary - under development
            'investing_com',     # Quaternary - under development  
            'alpha_vantage',     # Last resort - has rate limits (25 calls/day)
        ]
        
        # Load environment variables from .env file
        import os
        from dotenv import load_dotenv
        
        load_dotenv()  # Load .env file
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Rate limiting
        self.last_request = {}
        self.rate_limits = {
            'yahoo_finance': 0.1,     # 100ms between calls
            'google_finance': 1,      # 1 second between calls  
            'nse_api': 2,            # 2 seconds between calls
            'investing_com': 2,      # 2 seconds between calls
            'alpha_vantage': 12,     # 12 seconds between calls (conservative for 25/day limit)
        }
    
    def get_stock_data(self, symbol: str, start_date: datetime, 
                       end_date: datetime, interval: str = '1h') -> pd.DataFrame:
        """Fetch stock data with multiple source fallback"""
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Skip known problematic symbols
        skip_symbols = ['IGIL', 'APLAPOLLO', 'ZEEL', 'SUZLON', 'JETAIRWAYS']
        if symbol in skip_symbols:
            logger.info(f"Skipping known delisted/problematic symbol: {symbol}")
            return pd.DataFrame()
        
        # Try each data source in order
        for source in self.data_sources:
            try:
                data = self._fetch_from_source(source, symbol, start_date, end_date, interval)
                
                if not data.empty:
                    logger.info(f"Successfully fetched {symbol} data from {source}")
                    self.cache[cache_key] = data
                    return data
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {source}: {str(e)}")
                continue
        
        logger.error(f"Failed to fetch data for {symbol} from all sources")
        return pd.DataFrame()
    
    def _fetch_from_source(self, source: str, symbol: str, start_date: datetime, 
                          end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch data from specific source"""
        
        # Rate limiting
        self._apply_rate_limit(source)
        
        if source == 'yahoo_finance':
            return self._fetch_yahoo_finance(symbol, start_date, end_date, interval)
        elif source == 'alpha_vantage':
            return self._fetch_alpha_vantage(symbol, start_date, end_date, interval)
        elif source == 'google_finance':
            return self._fetch_google_finance(symbol, start_date, end_date, interval)
        elif source == 'nse_api':
            return self._fetch_nse_api(symbol, start_date, end_date, interval)
        elif source == 'investing_com':
            return self._fetch_investing_com(symbol, start_date, end_date, interval)
        else:
            raise ValueError(f"Unknown data source: {source}")
    
    def _apply_rate_limit(self, source: str):
        """Apply rate limiting for API calls"""
        now = time.time()
        last_call = self.last_request.get(source, 0)
        min_interval = self.rate_limits.get(source, 1)
        
        if now - last_call < min_interval:
            sleep_time = min_interval - (now - last_call)
            time.sleep(sleep_time)
        
        self.last_request[source] = time.time()
    
    def _fetch_yahoo_finance(self, symbol: str, start_date: datetime, 
                           end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch from Yahoo Finance (existing logic enhanced)"""
        
        # Suppress yfinance error logs
        yfinance_logger = logging.getLogger("yfinance")
        original_level = yfinance_logger.level
        yfinance_logger.setLevel(logging.CRITICAL)
        
        try:
            # Try NSE first, then BSE
            for exchange in ['.NS', '.BO']:
                ticker_symbol = f"{symbol}{exchange}"
                ticker = yf.Ticker(ticker_symbol)
                
                data = ticker.history(
                    start=start_date,
                    end=pd.Timestamp(end_date) + pd.Timedelta(days=1),
                    interval=interval
                )
                
                if not data.empty:
                    return data
            
            # Try without exchange suffix for international symbols
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=pd.Timestamp(end_date) + pd.Timedelta(days=1),
                interval=interval
            )
            
            return data if not data.empty else pd.DataFrame()
            
        finally:
            yfinance_logger.setLevel(original_level)
    
    def _fetch_google_finance(self, symbol: str, start_date: datetime, 
                            end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch from Google Finance using unofficial API"""
        
        try:
            # Google Finance unofficial API endpoint
            # Note: This is not official and may break at any time
            
            # Convert interval to Google Finance format
            if interval == '1h':
                gf_interval = '3600'  # seconds
            elif interval == '1d':
                gf_interval = '86400'  # seconds
            else:
                gf_interval = '86400'  # default to daily
            
            # Calculate period in seconds
            period_seconds = int((end_date - start_date).total_seconds())
            
            # Try NSE first, then different formats
            for exchange_format in [f'NSE:{symbol}', f'BOM:{symbol}', symbol]:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{exchange_format}"
                
                params = {
                    'period1': int(start_date.timestamp()),
                    'period2': int(end_date.timestamp()),
                    'interval': interval,
                    'includePrePost': 'true',
                    'events': 'div%2Csplits'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'chart' in data and data['chart']['result']:
                        result = data['chart']['result'][0]
                        
                        timestamps = result.get('timestamp', [])
                        quotes = result.get('indicators', {}).get('quote', [{}])[0]
                        
                        if timestamps and quotes:
                            df_data = {
                                'Open': quotes.get('open', []),
                                'High': quotes.get('high', []),
                                'Low': quotes.get('low', []),
                                'Close': quotes.get('close', []),
                                'Volume': quotes.get('volume', [])
                            }
                            
                            # Create DataFrame
                            df = pd.DataFrame(df_data)
                            df.index = pd.to_datetime(timestamps, unit='s')
                            
                            # Remove None values
                            df = df.dropna()
                            
                            if not df.empty:
                                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            raise ValueError(f"Google Finance error: {str(e)}")
    
    def _fetch_alpha_vantage(self, symbol: str, start_date: datetime, 
                           end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch from Alpha Vantage API"""
        
        if not self.alpha_vantage_key:
            logger.info("Alpha Vantage API key not available")
            return pd.DataFrame()
        
        # Alpha Vantage interval mapping
        av_interval = '60min' if interval == '1h' else 'daily'
        function = 'TIME_SERIES_INTRADAY' if interval == '1h' else 'TIME_SERIES_DAILY'
        
        # Add NSE exchange for Indian stocks
        av_symbol = f"{symbol}.BSE"  # Alpha Vantage uses BSE format
        
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': function,
            'symbol': av_symbol,
            'apikey': self.alpha_vantage_key,
            'outputsize': 'full',
            'datatype': 'json'
        }
        
        if function == 'TIME_SERIES_INTRADAY':
            params['interval'] = av_interval
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Parse Alpha Vantage response
        if 'Error Message' in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        
        if 'Note' in data:
            raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
        
        # Extract time series data
        if function == 'TIME_SERIES_INTRADAY':
            time_series = data.get(f'Time Series ({av_interval})', {})
        else:
            time_series = data.get('Time Series (Daily)', {})
        
        if not time_series:
            return pd.DataFrame()
        
        # Convert to pandas DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df = df.sort_index()
        
        # Filter by date range
        mask = (df.index >= start_date) & (df.index <= end_date)
        return df[mask]
    
    def _fetch_nse_api(self, symbol: str, start_date: datetime, 
                      end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch from NSE API (unofficial/web scraping)"""
        
        try:
            # NSE API is complex and requires headers/sessions
            # This is a simplified version - full implementation would need more work
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # NSE historical data endpoint (this may change)
            # Note: This is a placeholder - NSE API access is restricted
            url = f"https://www.nseindia.com/api/historical/cm/equity"
            params = {
                'symbol': symbol,
                'from': start_date.strftime('%d-%m-%Y'),
                'to': end_date.strftime('%d-%m-%Y')
            }
            
            # For now, return empty DataFrame as NSE API requires complex authentication
            logger.info("NSE API requires complex authentication - skipping")
            return pd.DataFrame()
            
        except Exception as e:
            raise ValueError(f"NSE API error: {str(e)}")
    
    def _fetch_investing_com(self, symbol: str, start_date: datetime, 
                           end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch from Investing.com (web scraping)"""
        
        try:
            # Investing.com requires web scraping which can be unreliable
            # This is a placeholder implementation
            
            # For now, return empty DataFrame as web scraping is complex
            logger.info("Investing.com scraping not implemented - skipping")
            return pd.DataFrame()
            
        except Exception as e:
            raise ValueError(f"Investing.com error: {str(e)}")
    
    def get_data_source_status(self) -> Dict[str, str]:
        """Check status of all data sources"""
        status = {}
        
        for source in self.data_sources:
            try:
                if source == 'yahoo_finance':
                    # Test with a known stock
                    test = yf.Ticker('RELIANCE.NS')
                    test.history(period='5d')
                    status[source] = "✅ Available"
                    
                elif source == 'alpha_vantage':
                    if self.alpha_vantage_key:
                        status[source] = "✅ Available (API key configured)"
                    else:
                        status[source] = "⚠️ API key required"
                        
                elif source == 'nse_api':
                    status[source] = "🚧 Under development"
                    
                elif source == 'investing_com':
                    status[source] = "🚧 Under development"
                    
            except Exception as e:
                status[source] = f"❌ Error: {str(e)}"
        
        return status
    
    def get_available_sources(self) -> List[str]:
        """Get list of currently available data sources"""
        available = []
        
        # Always available
        available.append('yahoo_finance')
        
        # Conditional availability
        if self.alpha_vantage_key:
            available.append('alpha_vantage')
        
        return available