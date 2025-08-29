import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TradeParser:
    def __init__(self):
        self.required_columns = [
            'symbol', 'trade_date', 'order_execution_time', 
            'trade_type', 'quantity', 'price', 'order_id'
        ]
        
    def parse_csv(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(file_path)
            
            self._validate_columns(df)
            
            df = self._clean_data(df)
            
            df = self._parse_datetime(df)
            
            df = self._normalize_types(df)
            
            return df.sort_values('datetime').reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise
    
    def _validate_columns(self, df: pd.DataFrame):
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(subset=self.required_columns)
        
        df['symbol'] = df['symbol'].str.strip().str.upper()
        df['trade_type'] = df['trade_type'].str.strip().str.lower()
        
        return df
    
    def _parse_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        df['datetime'] = pd.to_datetime(df['order_execution_time'])
        return df
    
    def _normalize_types(self, df: pd.DataFrame) -> pd.DataFrame:
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['order_id'] = df['order_id'].astype(str)
        
        df = df.dropna(subset=['quantity', 'price'])
        
        return df