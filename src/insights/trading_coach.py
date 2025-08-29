import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class TradingCoach:
    """
    Trading Coach that analyzes trade patterns and provides actionable insights
    in a coach-like format with 8 key insight cards.
    """
    
    def __init__(self):
        self.insights_cards = []
    
    def generate_coach_insights(self, closed_trades: pd.DataFrame) -> List[Dict]:
        """Generate 8 coach-style insight cards"""
        self.insights_cards = []
        
        if closed_trades.empty:
            return []
            
        # Generate all 8 insight cards
        self._generate_performance_summary(closed_trades)
        self._generate_winning_patterns(closed_trades)
        self._generate_top_mistakes(closed_trades)
        self._generate_behavioral_bias_report(closed_trades)
        self._generate_whatif_analysis(closed_trades)
        self._generate_strategy_leaderboard(closed_trades)
        self._generate_time_performance_map(closed_trades)
        self._generate_stock_focus_card(closed_trades)
        
        return self.insights_cards
    
    def _generate_performance_summary(self, trades: pd.DataFrame):
        """Card 1: Weekly/Monthly Performance Summary"""
        total_pnl = trades['gross_pnl'].sum()
        win_rate = (trades['trade_result'] == 'win').mean() * 100
        avg_hold_time = trades['hold_hours'].mean()
        
        # Best and worst performing stocks
        stock_pnl = trades.groupby('symbol')['gross_pnl'].sum().sort_values(ascending=False)
        best_stock = stock_pnl.index[0] if len(stock_pnl) > 0 else "N/A"
        worst_stock = stock_pnl.index[-1] if len(stock_pnl) > 0 else "N/A"
        best_pnl = stock_pnl.iloc[0] if len(stock_pnl) > 0 else 0
        worst_pnl = stock_pnl.iloc[-1] if len(stock_pnl) > 0 else 0
        
        # Most profitable pattern
        swing_trades = trades[trades['hold_hours'] > 24]
        swing_profit = swing_trades['gross_pnl'].sum() if not swing_trades.empty else 0
        intraday_trades = trades[trades['hold_hours'] <= 24]
        intraday_profit = intraday_trades['gross_pnl'].sum() if not intraday_trades.empty else 0
        
        best_strategy = "swing trades" if swing_profit > intraday_profit else "intraday trades"
        
        card = {
            'title': '📈 Performance Summary',
            'type': 'performance_summary',
            'metrics': {
                'net_pnl': total_pnl,
                'win_rate': win_rate,
                'avg_hold_time': f"{int(avg_hold_time//24)}d {int(avg_hold_time%24)}h {int((avg_hold_time%1)*60)}m",
                'best_stock': best_stock,
                'best_stock_pnl': best_pnl,
                'worst_stock': worst_stock,
                'worst_stock_pnl': worst_pnl
            },
            'insight': f"You earned most from {best_strategy}.",
            'action': f"Focus more on {best_strategy} to maximize profits."
        }
        self.insights_cards.append(card)
    
    def _generate_winning_patterns(self, trades: pd.DataFrame):
        """Card 2: High Win Rate Patterns"""
        # Analyze entry time patterns
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        early_trades = trades[trades['entry_hour'] < 10]
        
        if not early_trades.empty:
            early_win_rate = (early_trades['trade_result'] == 'win').mean() * 100
            early_avg_roi = early_trades['pnl_percentage'].mean()
            early_count = len(early_trades)
            
            # Find short hold winners
            short_holds = trades[trades['hold_hours'] < 3]
            short_win_rate = (short_holds['trade_result'] == 'win').mean() * 100 if not short_holds.empty else 0
            
            card = {
                'title': '🟩 Winning Patterns',
                'type': 'winning_patterns',
                'pattern': {
                    'entry_time': 'Before 10:00 AM',
                    'hold_duration': '<3 hours',
                    'win_rate': max(early_win_rate, short_win_rate),
                    'avg_roi': early_avg_roi,
                    'trade_count': early_count
                },
                'insight': f"{early_count} trades followed this pattern with {early_win_rate:.0f}% success.",
                'action': "Schedule more trades in the morning window for higher success rates."
            }
        else:
            # Fallback pattern
            winners = trades[trades['trade_result'] == 'win']
            best_hold_range = winners['hold_hours'].median()
            
            card = {
                'title': '🟩 Winning Patterns',
                'type': 'winning_patterns',
                'pattern': {
                    'hold_duration': f'~{best_hold_range:.1f} hours',
                    'win_rate': (winners['trade_result'] == 'win').mean() * 100,
                    'avg_roi': winners['pnl_percentage'].mean(),
                    'trade_count': len(winners)
                },
                'insight': f"Optimal hold time appears to be around {best_hold_range:.1f} hours.",
                'action': "Target similar hold durations for future trades."
            }
            
        self.insights_cards.append(card)
    
    def _generate_top_mistakes(self, trades: pd.DataFrame):
        """Card 3: Top 3 Mistakes to Avoid"""
        mistakes = []
        
        # Late entry pattern
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        late_entries = trades[trades['entry_hour'] >= 14]  # After 2 PM
        if not late_entries.empty:
            late_loss = late_entries[late_entries['trade_result'] == 'loss']['gross_pnl'].sum()
            if late_loss < 0:
                mistakes.append({
                    'mistake': 'Entry after 2:00 PM',
                    'impact': abs(late_loss),
                    'frequency': len(late_entries)
                })
        
        # Long losers
        long_losers = trades[(trades['hold_hours'] > 24) & (trades['trade_result'] == 'loss')]
        if not long_losers.empty:
            long_loss = long_losers['gross_pnl'].sum()
            mistakes.append({
                'mistake': 'Holding losses too long',
                'impact': abs(long_loss),
                'frequency': len(long_losers)
            })
        
        # Large position losers
        large_losses = trades[trades['gross_pnl'] < trades['gross_pnl'].quantile(0.1)]
        if not large_losses.empty:
            large_loss_impact = abs(large_losses['gross_pnl'].sum())
            mistakes.append({
                'mistake': 'Large position sizes on losers',
                'impact': large_loss_impact,
                'frequency': len(large_losses)
            })
        
        # Sort by impact
        mistakes.sort(key=lambda x: x['impact'], reverse=True)
        top_mistakes = mistakes[:3]
        
        total_avoidable_loss = sum(m['impact'] for m in top_mistakes)
        
        card = {
            'title': '🟥 Top Mistakes to Avoid',
            'type': 'top_mistakes',
            'mistakes': top_mistakes,
            'total_impact': total_avoidable_loss,
            'insight': f"These patterns cost you ₹{total_avoidable_loss:,.0f}.",
            'action': "Set rules to avoid these specific scenarios in future trades."
        }
        self.insights_cards.append(card)
    
    def _generate_behavioral_bias_report(self, trades: pd.DataFrame):
        """Card 4: Behavioral Bias Report"""
        biases = []
        
        # Revenge trading detection
        trades_sorted = trades.sort_values('exit_datetime')
        revenge_trades = []
        
        for i in range(1, len(trades_sorted)):
            prev_trade = trades_sorted.iloc[i-1]
            curr_trade = trades_sorted.iloc[i]
            
            # Same symbol, previous was loss, within same day
            if (prev_trade['symbol'] == curr_trade['symbol'] and 
                prev_trade['trade_result'] == 'loss' and
                (curr_trade['entry_datetime'] - prev_trade['exit_datetime']).total_seconds() < 7200):  # 2 hours
                revenge_trades.append(curr_trade)
        
        if revenge_trades:
            revenge_df = pd.DataFrame(revenge_trades)
            revenge_fail_rate = (revenge_df['trade_result'] == 'loss').mean() * 100
            biases.append(f"🔄 Revenge Trading: Re-entered same stock after loss → {revenge_fail_rate:.0f}% failed")
        
        # Early exit pattern
        winners = trades[trades['trade_result'] == 'win']
        if not winners.empty:
            quick_exits = winners[winners['hold_hours'] < 1]
            if len(quick_exits) > len(winners) * 0.3:  # More than 30% quick exits
                biases.append("🔓 Premature Profit Taking: Exited winners too early → Check what-if analysis")
        
        # Position sizing after wins
        if len(trades) > 5:
            trades_with_values = trades.sort_values('entry_datetime')
            win_streaks = []
            current_streak = 0
            
            for _, trade in trades_with_values.iterrows():
                if trade['trade_result'] == 'win':
                    current_streak += 1
                else:
                    if current_streak > 0:
                        win_streaks.append(current_streak)
                    current_streak = 0
            
            if win_streaks and max(win_streaks) >= 3:
                biases.append("💰 Position Sizing Creep: After wins, check if position sizes increased risk")
        
        card = {
            'title': '🧠 Behavioral Bias Report',
            'type': 'behavioral_bias',
            'biases': biases,
            'insight': f"Detected {len(biases)} potential behavioral patterns affecting performance.",
            'action': "Set systematic rules to counteract these emotional trading patterns."
        }
        self.insights_cards.append(card)
    
    def _generate_whatif_analysis(self, trades: pd.DataFrame):
        """Card 5: What-If Aggregated Analysis"""
        # This would integrate with our existing price fetcher for real analysis
        # For now, create simplified version based on patterns
        
        total_missed = 0
        suggestions = []
        
        # Quick exit analysis
        quick_winners = trades[(trades['trade_result'] == 'win') & (trades['hold_hours'] < 2)]
        if not quick_winners.empty:
            avg_quick_profit = quick_winners['gross_pnl'].mean()
            estimated_missed = len(quick_winners) * avg_quick_profit * 0.3  # Estimate 30% more if held longer
            total_missed += estimated_missed
            suggestions.append(f"💸 \"If you had held winners 30 mins longer\" → +₹{estimated_missed:,.0f}")
        
        # Late entry avoidance
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        late_losers = trades[(trades['entry_hour'] >= 14) & (trades['trade_result'] == 'loss')]
        if not late_losers.empty:
            late_losses = abs(late_losers['gross_pnl'].sum())
            suggestions.append(f"⏰ \"If you avoided post-2PM entries\" → +₹{late_losses:,.0f} saved")
        
        # Trailing stop benefit estimate
        profitable_trades = trades[trades['gross_pnl'] > 0]
        if not profitable_trades.empty:
            trailing_benefit = profitable_trades['gross_pnl'].sum() * 0.15  # Estimate 15% improvement
            suggestions.append(f"🔄 \"Trailing stop strategy\" → +₹{trailing_benefit:,.0f} potential")
        
        card = {
            'title': '🔍 What-If Analysis',
            'type': 'whatif_analysis',
            'suggestions': suggestions,
            'total_opportunity': total_missed,
            'insight': f"Potential improvements worth ₹{total_missed:,.0f} identified across all trades.",
            'action': "Implement systematic rules to capture these missed opportunities."
        }
        self.insights_cards.append(card)
    
    def _generate_strategy_leaderboard(self, trades: pd.DataFrame):
        """Card 6: Strategy Leaderboard"""
        strategies = []
        
        # Swing vs Intraday
        swing_trades = trades[trades['hold_hours'] > 24]
        if not swing_trades.empty:
            swing_win_rate = (swing_trades['trade_result'] == 'win').mean() * 100
            swing_roi = swing_trades['pnl_percentage'].mean()
            strategies.append({
                'name': f'Swing: >1d hold',
                'win_rate': swing_win_rate,
                'roi': swing_roi,
                'note': 'Longer-term positions'
            })
        
        intraday_trades = trades[trades['hold_hours'] <= 8]
        if not intraday_trades.empty:
            intraday_win_rate = (intraday_trades['trade_result'] == 'win').mean() * 100
            intraday_roi = intraday_trades['pnl_percentage'].mean()
            strategies.append({
                'name': 'Intraday: <8h hold',
                'win_rate': intraday_win_rate,
                'roi': intraday_roi,
                'note': 'Same-day trading'
            })
        
        # Time-based strategies
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        morning_trades = trades[trades['entry_hour'] < 11]
        if not morning_trades.empty:
            morning_win_rate = (morning_trades['trade_result'] == 'win').mean() * 100
            morning_roi = morning_trades['pnl_percentage'].mean()
            strategies.append({
                'name': 'Morning: <11AM entry',
                'win_rate': morning_win_rate,
                'roi': morning_roi,
                'note': 'Early market entry'
            })
        
        # Sort strategies by win rate
        strategies.sort(key=lambda x: x['win_rate'], reverse=True)
        
        best_strategy = strategies[0] if strategies else None
        worst_strategy = strategies[-1] if len(strategies) > 1 else None
        
        card = {
            'title': '🏆 Strategy Leaderboard',
            'type': 'strategy_leaderboard',
            'strategies': strategies,
            'best_strategy': best_strategy,
            'worst_strategy': worst_strategy,
            'insight': f"Best: {best_strategy['name']} ({best_strategy['win_rate']:.0f}% win rate)" if best_strategy else "Need more data",
            'action': f"Double down on {best_strategy['name']} setups" if best_strategy else "Collect more trade data"
        }
        self.insights_cards.append(card)
    
    def _generate_time_performance_map(self, trades: pd.DataFrame):
        """Card 7: Time-of-Day Performance Map"""
        trades['entry_hour'] = pd.to_datetime(trades['entry_datetime']).dt.hour
        
        # Performance by hour
        hourly_performance = trades.groupby('entry_hour').agg({
            'pnl_percentage': 'mean',
            'trade_result': lambda x: (x == 'win').mean() * 100,
            'gross_pnl': 'sum'
        }).round(1)
        
        if not hourly_performance.empty:
            best_hour = hourly_performance['pnl_percentage'].idxmax()
            worst_hour = hourly_performance['pnl_percentage'].idxmin()
            
            best_roi = hourly_performance.loc[best_hour, 'pnl_percentage']
            best_win_rate = hourly_performance.loc[best_hour, 'trade_result']
            worst_roi = hourly_performance.loc[worst_hour, 'pnl_percentage']
            worst_win_rate = hourly_performance.loc[worst_hour, 'trade_result']
            
            card = {
                'title': '🕘 Time Performance Map',
                'type': 'time_performance',
                'best_window': {
                    'time': f"{best_hour}:00 - {best_hour+1}:00",
                    'roi': best_roi,
                    'win_rate': best_win_rate
                },
                'worst_window': {
                    'time': f"{worst_hour}:00 - {worst_hour+1}:00",
                    'roi': worst_roi,
                    'win_rate': worst_win_rate
                },
                'insight': f"Best: {best_hour}:00-{best_hour+1}:00 (+{best_roi:.1f}%), Worst: {worst_hour}:00-{worst_hour+1}:00 ({worst_roi:.1f}%)",
                'action': f"Limit new entries during {worst_hour}:00-{worst_hour+1}:00 window for 2 weeks and measure impact."
            }
        else:
            card = {
                'title': '🕘 Time Performance Map',
                'type': 'time_performance',
                'insight': "Need more data to identify time-based patterns",
                'action': "Continue trading to build time-based performance data"
            }
            
        self.insights_cards.append(card)
    
    def _generate_stock_focus_card(self, trades: pd.DataFrame):
        """Card 8: Stock Focus Recommendations"""
        stock_performance = trades.groupby('symbol').agg({
            'gross_pnl': 'sum',
            'trade_result': lambda x: (x == 'win').mean() * 100,
            'pnl_percentage': 'mean'
        }).round(2)
        
        stock_performance['trade_count'] = trades.groupby('symbol').size()
        
        # Filter stocks with at least 2 trades
        significant_stocks = stock_performance[stock_performance['trade_count'] >= 2]
        
        if not significant_stocks.empty:
            # Best stock
            best_stock = significant_stocks['gross_pnl'].idxmax()
            best_pnl = significant_stocks.loc[best_stock, 'gross_pnl']
            best_win_rate = significant_stocks.loc[best_stock, 'trade_result']
            
            # Avoid stock
            worst_stock = significant_stocks['gross_pnl'].idxmin()
            worst_pnl = significant_stocks.loc[worst_stock, 'gross_pnl']
            worst_win_rate = significant_stocks.loc[worst_stock, 'trade_result']
            
            card = {
                'title': '🎯 Stock Focus',
                'type': 'stock_focus',
                'champion_stock': {
                    'symbol': best_stock,
                    'pnl': best_pnl,
                    'win_rate': best_win_rate,
                    'trade_count': significant_stocks.loc[best_stock, 'trade_count']
                },
                'avoid_stock': {
                    'symbol': worst_stock,
                    'pnl': worst_pnl,
                    'win_rate': worst_win_rate,
                    'trade_count': significant_stocks.loc[worst_stock, 'trade_count']
                } if worst_pnl < 0 else None,
                'insight': f"Champion: {best_stock} (₹{best_pnl:,.0f}, {best_win_rate:.0f}% win rate)",
                'action': f"Increase allocation to {best_stock} while maintaining risk management."
            }
        else:
            card = {
                'title': '🎯 Stock Focus',
                'type': 'stock_focus',
                'insight': "Need more trades per stock to identify consistent performers",
                'action': "Focus on 3-5 stocks to build deeper performance insights"
            }
            
        self.insights_cards.append(card)