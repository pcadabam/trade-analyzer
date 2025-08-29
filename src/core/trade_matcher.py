import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TradeMatcher:
    def __init__(self):
        self.closed_trades = []
        self.open_positions = {}
        
    def match_trades(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        trades_df = trades_df.sort_values('datetime').reset_index(drop=True)
        
        for _, trade in trades_df.iterrows():
            if trade['trade_type'] == 'buy':
                self._process_buy(trade)
            elif trade['trade_type'] == 'sell':
                self._process_sell(trade)
        
        closed_df = pd.DataFrame(self.closed_trades)
        
        if not closed_df.empty:
            closed_df = self._calculate_metrics(closed_df)
        
        return closed_df
    
    def _process_buy(self, trade):
        symbol = trade['symbol']
        
        if symbol not in self.open_positions:
            self.open_positions[symbol] = []
        
        self.open_positions[symbol].append({
            'quantity': trade['quantity'],
            'price': trade['price'],
            'datetime': trade['datetime'],
            'order_id': trade['order_id']
        })
    
    def _process_sell(self, trade):
        symbol = trade['symbol']
        
        if symbol not in self.open_positions or not self.open_positions[symbol]:
            logger.warning(f"Sell without open position for {symbol}")
            return
        
        remaining_sell_qty = trade['quantity']
        sell_price = trade['price']
        sell_datetime = trade['datetime']
        
        while remaining_sell_qty > 0 and self.open_positions[symbol]:
            position = self.open_positions[symbol][0]
            
            match_qty = min(remaining_sell_qty, position['quantity'])
            
            closed_trade = {
                'symbol': symbol,
                'entry_datetime': position['datetime'],
                'exit_datetime': sell_datetime,
                'entry_price': position['price'],
                'exit_price': sell_price,
                'quantity': match_qty,
                'entry_order_id': position['order_id'],
                'exit_order_id': trade['order_id']
            }
            
            self.closed_trades.append(closed_trade)
            
            position['quantity'] -= match_qty
            remaining_sell_qty -= match_qty
            
            if position['quantity'] <= 0:
                self.open_positions[symbol].pop(0)
    
    def _calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df['gross_pnl'] = (df['exit_price'] - df['entry_price']) * df['quantity']
        
        df['pnl_percentage'] = ((df['exit_price'] - df['entry_price']) / df['entry_price']) * 100
        
        df['hold_duration'] = df['exit_datetime'] - df['entry_datetime']
        df['hold_hours'] = df['hold_duration'].dt.total_seconds() / 3600
        
        df['trade_result'] = df['gross_pnl'].apply(lambda x: 'win' if x > 0 else 'loss')
        
        df['entry_value'] = df['entry_price'] * df['quantity']
        df['exit_value'] = df['exit_price'] * df['quantity']
        
        return df
    
    def get_summary_stats(self, closed_trades_df: pd.DataFrame) -> Dict:
        if closed_trades_df.empty:
            return {}
        
        total_trades = len(closed_trades_df)
        winning_trades = len(closed_trades_df[closed_trades_df['gross_pnl'] > 0])
        losing_trades = len(closed_trades_df[closed_trades_df['gross_pnl'] <= 0])
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': closed_trades_df['gross_pnl'].sum(),
            'avg_pnl': closed_trades_df['gross_pnl'].mean(),
            'max_profit': closed_trades_df['gross_pnl'].max(),
            'max_loss': closed_trades_df['gross_pnl'].min(),
            'avg_hold_hours': closed_trades_df['hold_hours'].mean(),
            'total_volume': closed_trades_df['entry_value'].sum()
        }