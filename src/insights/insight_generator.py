import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InsightGenerator:
    def __init__(self):
        self.insights = []
        
    def generate_insights(self, closed_trades: pd.DataFrame) -> List[Dict]:
        self.insights = []
        
        self._analyze_exit_timing(closed_trades)
        self._analyze_entry_timing(closed_trades)
        self._analyze_stock_performance(closed_trades)
        self._analyze_risk_patterns(closed_trades)
        self._analyze_behavioral_patterns(closed_trades)
        self._analyze_real_exit_opportunities(closed_trades)
        
        return self.insights
    
    def _analyze_exit_timing(self, trades: pd.DataFrame):
        short_duration_wins = trades[
            (trades['trade_result'] == 'win') & 
            (trades['hold_hours'] < 2)
        ]
        
        if len(short_duration_wins) > 0:
            avg_return = short_duration_wins['pnl_percentage'].mean()
            
            longer_duration_wins = trades[
                (trades['trade_result'] == 'win') & 
                (trades['hold_hours'] >= 2)
            ]
            
            if len(longer_duration_wins) > 0:
                longer_avg_return = longer_duration_wins['pnl_percentage'].mean()
                
                if longer_avg_return > avg_return * 1.5:
                    self.insights.append({
                        'title': 'Consider Holding Winners Longer',
                        'type': 'exit_optimization',
                        'description': f'Your winning trades held for <2 hours average {avg_return:.2f}% return, '
                                     f'while those held longer average {longer_avg_return:.2f}% return.',
                        'action': 'Consider using trailing stop-loss instead of quick profit booking.',
                        'data': {
                            'short_duration_avg': round(avg_return, 2),
                            'longer_duration_avg': round(longer_avg_return, 2),
                            'potential_improvement': round(longer_avg_return - avg_return, 2)
                        }
                    })
        
        losing_trades = trades[trades['trade_result'] == 'loss']
        if len(losing_trades) > 0:
            avg_loss = losing_trades['pnl_percentage'].mean()
            prolonged_losses = losing_trades[losing_trades['hold_hours'] > 24]
            
            if len(prolonged_losses) > 0:
                prolonged_avg_loss = prolonged_losses['pnl_percentage'].mean()
                
                if prolonged_avg_loss < avg_loss * 1.5:
                    self.insights.append({
                        'title': 'Cut Losses Earlier',
                        'type': 'exit_optimization',
                        'description': f'Losses held over 24 hours average {prolonged_avg_loss:.2f}% loss '
                                     f'vs {avg_loss:.2f}% for all losses.',
                        'action': 'Implement strict stop-loss at -2% to -3% to prevent larger drawdowns.',
                        'data': {
                            'avg_loss': round(avg_loss, 2),
                            'prolonged_loss': round(prolonged_avg_loss, 2),
                            'trades_affected': len(prolonged_losses)
                        }
                    })
    
    def _analyze_entry_timing(self, trades: pd.DataFrame):
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        
        morning_trades = trades[trades['entry_hour'] < 10]
        afternoon_trades = trades[trades['entry_hour'] >= 14]
        
        if len(morning_trades) > 5 and len(afternoon_trades) > 5:
            morning_win_rate = (morning_trades['trade_result'] == 'win').mean() * 100
            afternoon_win_rate = (afternoon_trades['trade_result'] == 'win').mean() * 100
            
            if abs(morning_win_rate - afternoon_win_rate) > 15:
                better_period = 'morning (9-10 AM)' if morning_win_rate > afternoon_win_rate else 'afternoon (2 PM onwards)'
                better_rate = max(morning_win_rate, afternoon_win_rate)
                worse_rate = min(morning_win_rate, afternoon_win_rate)
                
                self.insights.append({
                    'title': f'Better Performance in {better_period.title()}',
                    'type': 'timing',
                    'description': f'Your win rate in {better_period} is {better_rate:.1f}% '
                                 f'compared to {worse_rate:.1f}% in the other period.',
                    'action': f'Focus your trading activity during {better_period} when you perform better.',
                    'data': {
                        'morning_win_rate': round(morning_win_rate, 1),
                        'afternoon_win_rate': round(afternoon_win_rate, 1),
                        'morning_trades': len(morning_trades),
                        'afternoon_trades': len(afternoon_trades)
                    }
                })
        
        trades['weekday'] = pd.to_datetime(trades['entry_datetime']).dt.dayofweek
        weekday_performance = trades.groupby('weekday').agg({
            'gross_pnl': 'sum',
            'trade_result': lambda x: (x == 'win').mean() * 100
        })
        
        if len(weekday_performance) >= 3:
            best_day = weekday_performance['gross_pnl'].idxmax()
            worst_day = weekday_performance['gross_pnl'].idxmin()
            
            if weekday_performance.loc[best_day, 'gross_pnl'] > 0 and \
               weekday_performance.loc[worst_day, 'gross_pnl'] < 0:
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                self.insights.append({
                    'title': f'Best Trading Day: {days[best_day]}',
                    'type': 'timing',
                    'description': f'You make ₹{weekday_performance.loc[best_day, "gross_pnl"]:,.0f} on {days[best_day]} '
                                 f'but lose ₹{abs(weekday_performance.loc[worst_day, "gross_pnl"]):,.0f} on {days[worst_day]}.',
                    'action': f'Consider reducing position size or avoiding trades on {days[worst_day]}.',
                    'data': {
                        'best_day': days[best_day],
                        'worst_day': days[worst_day],
                        'best_day_pnl': round(weekday_performance.loc[best_day, 'gross_pnl'], 0),
                        'worst_day_pnl': round(weekday_performance.loc[worst_day, 'gross_pnl'], 0)
                    }
                })
    
    def _analyze_stock_performance(self, trades: pd.DataFrame):
        stock_stats = trades.groupby('symbol').agg({
            'gross_pnl': ['sum', 'count'],
            'trade_result': lambda x: (x == 'win').mean() * 100
        })
        
        stock_stats.columns = ['total_pnl', 'trade_count', 'win_rate']
        
        profitable_stocks = stock_stats[stock_stats['total_pnl'] > 0].sort_values('total_pnl', ascending=False)
        losing_stocks = stock_stats[stock_stats['total_pnl'] < 0].sort_values('total_pnl')
        
        if len(profitable_stocks) > 0:
            top_performer = profitable_stocks.index[0]
            self.insights.append({
                'title': f'Top Performing Stock: {top_performer}',
                'type': 'stock_selection',
                'description': f'{top_performer} generated ₹{profitable_stocks.loc[top_performer, "total_pnl"]:,.0f} '
                             f'with {profitable_stocks.loc[top_performer, "win_rate"]:.1f}% win rate.',
                'action': f'Consider increasing allocation to {top_performer} while maintaining risk management.',
                'data': {
                    'symbol': top_performer,
                    'total_pnl': round(profitable_stocks.loc[top_performer, 'total_pnl'], 0),
                    'win_rate': round(profitable_stocks.loc[top_performer, 'win_rate'], 1),
                    'trade_count': int(profitable_stocks.loc[top_performer, 'trade_count'])
                }
            })
        
        if len(losing_stocks) > 0 and losing_stocks.iloc[0]['trade_count'] >= 3:
            worst_performer = losing_stocks.index[0]
            self.insights.append({
                'title': f'Avoid Trading: {worst_performer}',
                'type': 'stock_selection',
                'description': f'{worst_performer} caused losses of ₹{abs(losing_stocks.loc[worst_performer, "total_pnl"]):,.0f} '
                             f'with only {losing_stocks.loc[worst_performer, "win_rate"]:.1f}% win rate.',
                'action': f'Avoid {worst_performer} or revise your strategy for this stock.',
                'data': {
                    'symbol': worst_performer,
                    'total_loss': round(abs(losing_stocks.loc[worst_performer, 'total_pnl']), 0),
                    'win_rate': round(losing_stocks.loc[worst_performer, 'win_rate'], 1),
                    'trade_count': int(losing_stocks.loc[worst_performer, 'trade_count'])
                }
            })
        
        high_frequency_stocks = stock_stats[stock_stats['trade_count'] >= 5]
        if len(high_frequency_stocks) > 0:
            high_freq_profitable = high_frequency_stocks[high_frequency_stocks['win_rate'] > 60]
            
            if len(high_freq_profitable) > 0:
                self.insights.append({
                    'title': 'Consistent Winners Found',
                    'type': 'stock_selection',
                    'description': f'Stocks like {", ".join(high_freq_profitable.index[:3])} show >60% win rate with multiple trades.',
                    'action': 'Focus on these high-probability setups and increase position sizing gradually.',
                    'data': {
                        'stocks': list(high_freq_profitable.index),
                        'avg_win_rate': round(high_freq_profitable['win_rate'].mean(), 1)
                    }
                })
    
    def _analyze_risk_patterns(self, trades: pd.DataFrame):
        max_loss = trades['gross_pnl'].min()
        max_profit = trades['gross_pnl'].max()
        
        if abs(max_loss) > max_profit * 2:
            self.insights.append({
                'title': 'Risk-Reward Imbalance Detected',
                'type': 'risk_management',
                'description': f'Your largest loss (₹{abs(max_loss):,.0f}) is {abs(max_loss)/max_profit:.1f}x your largest profit (₹{max_profit:,.0f}).',
                'action': 'Implement position sizing rules: risk max 2% per trade, aim for 1:2 risk-reward ratio.',
                'data': {
                    'max_loss': round(max_loss, 0),
                    'max_profit': round(max_profit, 0),
                    'ratio': round(abs(max_loss)/max_profit, 1)
                }
            })
        
        consecutive_losses = self._find_consecutive_losses(trades)
        if consecutive_losses >= 3:
            self.insights.append({
                'title': f'Streak of {consecutive_losses} Consecutive Losses',
                'type': 'risk_management',
                'description': f'You had {consecutive_losses} losses in a row, indicating possible tilt or poor market conditions.',
                'action': 'After 2 consecutive losses, reduce position size by 50% or take a break.',
                'data': {
                    'max_consecutive_losses': consecutive_losses
                }
            })
        
        daily_pnl = trades.groupby(pd.to_datetime(trades['exit_datetime']).dt.date)['gross_pnl'].sum()
        if len(daily_pnl) > 5:
            daily_volatility = daily_pnl.std()
            avg_daily_pnl = daily_pnl.mean()
            
            if daily_volatility > abs(avg_daily_pnl) * 3:
                self.insights.append({
                    'title': 'High Daily P&L Volatility',
                    'type': 'risk_management',
                    'description': f'Your daily P&L swings (±₹{daily_volatility:,.0f}) are very high compared to average (₹{avg_daily_pnl:,.0f}).',
                    'action': 'Reduce position sizes to smooth out daily returns and reduce emotional stress.',
                    'data': {
                        'daily_volatility': round(daily_volatility, 0),
                        'avg_daily_pnl': round(avg_daily_pnl, 0)
                    }
                })
    
    def _analyze_behavioral_patterns(self, trades: pd.DataFrame):
        avg_win = trades[trades['trade_result'] == 'win']['gross_pnl'].mean()
        avg_loss = abs(trades[trades['trade_result'] == 'loss']['gross_pnl'].mean())
        
        if avg_loss > avg_win * 1.5:
            self.insights.append({
                'title': 'Holding Losers Too Long',
                'type': 'behavioral',
                'description': f'Your average loss (₹{avg_loss:,.0f}) is {avg_loss/avg_win:.1f}x your average win (₹{avg_win:,.0f}).',
                'action': 'Set stop-loss orders immediately after entry. Never move stop-loss further away.',
                'data': {
                    'avg_win': round(avg_win, 0),
                    'avg_loss': round(avg_loss, 0),
                    'ratio': round(avg_loss/avg_win, 1)
                }
            })
        
        volume_analysis = trades.groupby('symbol')['quantity'].sum().sort_values(ascending=False)
        if len(volume_analysis) > 0:
            top_volume_stock = volume_analysis.index[0]
            stock_pnl = trades[trades['symbol'] == top_volume_stock]['gross_pnl'].sum()
            
            if stock_pnl < 0:
                self.insights.append({
                    'title': f'Overtrading {top_volume_stock}',
                    'type': 'behavioral',
                    'description': f'You trade {top_volume_stock} the most but have lost ₹{abs(stock_pnl):,.0f} on it.',
                    'action': 'Reduce frequency of trades in familiar but unprofitable stocks. Diversify your watchlist.',
                    'data': {
                        'symbol': top_volume_stock,
                        'total_quantity': int(volume_analysis[top_volume_stock]),
                        'total_loss': round(abs(stock_pnl), 0)
                    }
                })
        
        if len(trades) > 20:
            recent_trades = trades.tail(10)
            older_trades = trades.head(len(trades) - 10)
            
            recent_win_rate = (recent_trades['trade_result'] == 'win').mean() * 100
            older_win_rate = (older_trades['trade_result'] == 'win').mean() * 100
            
            if recent_win_rate < older_win_rate - 20:
                self.insights.append({
                    'title': 'Recent Performance Decline',
                    'type': 'behavioral',
                    'description': f'Your recent win rate ({recent_win_rate:.1f}%) is much lower than earlier ({older_win_rate:.1f}%).',
                    'action': 'Take a break to reset. Review what changed in your strategy or market conditions.',
                    'data': {
                        'recent_win_rate': round(recent_win_rate, 1),
                        'older_win_rate': round(older_win_rate, 1),
                        'decline': round(older_win_rate - recent_win_rate, 1)
                    }
                })
    
    def _find_consecutive_losses(self, trades: pd.DataFrame) -> int:
        max_consecutive = 0
        current_consecutive = 0
        
        for result in trades.sort_values('exit_datetime')['trade_result']:
            if result == 'loss':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _analyze_real_exit_opportunities(self, trades: pd.DataFrame):
        from ..data.price_fetcher import PriceFetcher
        
        if len(trades) == 0:
            return
        
        fetcher = PriceFetcher()
        missed_opportunities = []
        trailing_stop_benefits = []
        
        # Analyze a sample of trades (limit for performance)
        sample_size = min(10, len(trades))
        sample_trades = trades.head(sample_size)
        
        for idx, trade in sample_trades.iterrows():
            try:
                # Get exit scenarios for this trade
                scenarios = fetcher.simulate_exit_scenarios(
                    trade['symbol'],
                    trade['entry_price'],
                    trade['entry_datetime'],
                    trade['exit_datetime'],
                    int(trade['quantity'])
                )
                
                if scenarios:
                    # Check for missed opportunities
                    if 'best_late_exit' in scenarios:
                        late_pnl = scenarios['best_late_exit']['potential_pnl']
                        if late_pnl > trade['gross_pnl'] * 1.5:
                            missed_opportunity = late_pnl - trade['gross_pnl']
                            missed_opportunities.append({
                                'symbol': trade['symbol'],
                                'missed_amount': missed_opportunity,
                                'actual_pnl': trade['gross_pnl'],
                                'potential_pnl': late_pnl
                            })
                    
                    # Check trailing stop benefits
                    if 'trailing_stop' in scenarios:
                        trailing_pnl = scenarios['trailing_stop']['potential_pnl']
                        if trailing_pnl > trade['gross_pnl']:
                            benefit = trailing_pnl - trade['gross_pnl']
                            trailing_stop_benefits.append({
                                'symbol': trade['symbol'],
                                'benefit': benefit,
                                'actual_pnl': trade['gross_pnl'],
                                'trailing_pnl': trailing_pnl
                            })
                            
            except Exception as e:
                logger.warning(f"Could not analyze exit opportunities for {trade['symbol']}: {str(e)}")
                continue
        
        # Generate insights based on real data
        if missed_opportunities:
            total_missed = sum(opp['missed_amount'] for opp in missed_opportunities)
            avg_missed = total_missed / len(missed_opportunities)
            
            worst_miss = max(missed_opportunities, key=lambda x: x['missed_amount'])
            
            self.insights.append({
                'title': 'Significant Exit Opportunities Missed',
                'type': 'exit_optimization',
                'description': f'Based on actual price data, you missed ₹{total_missed:,.0f} in potential profits by exiting too early. '
                             f'Worst case: {worst_miss["symbol"]} - missed ₹{worst_miss["missed_amount"]:,.0f}',
                'action': 'Consider holding winning positions longer or using trailing stops to capture more upside.',
                'data': {
                    'total_missed_amount': round(total_missed, 0),
                    'avg_missed_per_trade': round(avg_missed, 0),
                    'trades_analyzed': len(missed_opportunities),
                    'worst_miss_symbol': worst_miss['symbol'],
                    'worst_miss_amount': round(worst_miss['missed_amount'], 0)
                }
            })
        
        if trailing_stop_benefits:
            total_benefit = sum(benefit['benefit'] for benefit in trailing_stop_benefits)
            avg_benefit = total_benefit / len(trailing_stop_benefits)
            
            self.insights.append({
                'title': 'Trailing Stop Strategy Would Help',
                'type': 'exit_optimization', 
                'description': f'A 2% trailing stop on {len(trailing_stop_benefits)} trades would have earned ₹{total_benefit:,.0f} more. '
                             f'Average benefit: ₹{avg_benefit:,.0f} per applicable trade.',
                'action': 'Implement trailing stop-loss orders to automatically capture more profits while limiting downside.',
                'data': {
                    'total_additional_profit': round(total_benefit, 0),
                    'avg_benefit_per_trade': round(avg_benefit, 0),
                    'applicable_trades': len(trailing_stop_benefits)
                }
            })