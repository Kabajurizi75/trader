"""
Simulation Engine for Trading Agent
Provides backtesting, paper trading, and investor demonstration capabilities
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import random
import numpy as np
from enum import Enum

from .portfolio_manager import PortfolioManager, TradeType
from .strategy_engine import StrategyEngine, TradingSignal, MarketData

logger = logging.getLogger(__name__)

class SimulationType(Enum):
    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    LIVE_DEMO = "live_demo"

@dataclass
class SimulationConfig:
    simulation_type: SimulationType
    initial_balance: float
    duration_days: int
    symbols: List[str]
    strategies: List[str]
    risk_level: str = "medium"
    max_positions: int = 5
    rebalance_frequency: str = "daily"  # daily, weekly, monthly

@dataclass
class SimulationResult:
    config: SimulationConfig
    start_date: datetime
    end_date: datetime
    initial_value: float
    final_value: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    average_trade_return: float
    volatility: float
    daily_returns: List[float]
    trade_history: List[Dict]
    portfolio_history: List[Dict]

class MarketSimulator:
    """Simulates market conditions for backtesting"""
    
    def __init__(self):
        self.price_history = {}
        self.current_prices = {}
    
    def generate_price_data(self, symbol: str, days: int, initial_price: float = 50000.0) -> List[Dict]:
        """Generate realistic price data for simulation"""
        prices = []
        current_price = initial_price
        
        for i in range(days):
            # Generate realistic price movement (simplified random walk with trend)
            daily_return = np.random.normal(0.001, 0.03)  # 0.1% daily return, 3% volatility
            
            # Add some trend and momentum
            if i > 0:
                prev_return = prices[-1]['change_percent'] / 100
                momentum = prev_return * 0.1  # 10% momentum effect
                daily_return += momentum
            
            # Apply return
            new_price = current_price * (1 + daily_return)
            change_percent = (new_price - current_price) / current_price * 100
            
            # Generate volume (simplified)
            base_volume = "1.2B"
            volume_multiplier = 1 + abs(daily_return) * 2  # Higher volume on big moves
            
            price_data = {
                'symbol': symbol,
                'price': new_price,
                'change_percent': change_percent,
                'volume': f"{1.2 * volume_multiplier:.1f}B",
                'timestamp': datetime.now() - timedelta(days=days-i),
                'source': 'simulation'
            }
            
            prices.append(price_data)
            current_price = new_price
        
        self.price_history[symbol] = prices
        self.current_prices[symbol] = current_price
        return prices
    
    def get_price_at_date(self, symbol: str, date: datetime) -> Optional[Dict]:
        """Get price data for a specific date"""
        if symbol not in self.price_history:
            return None
        
        # Find closest price data to the requested date
        prices = self.price_history[symbol]
        closest_price = min(prices, key=lambda p: abs((p['timestamp'] - date).total_seconds()))
        return closest_price

class SimulationEngine:
    """Main simulation engine for backtesting and demonstrations"""
    
    def __init__(self):
        self.market_simulator = MarketSimulator()
        self.active_simulations = {}
        self.completed_simulations = []
    
    def create_demo_simulation(self, investor_profile: str = "balanced") -> SimulationConfig:
        """Create a demonstration simulation based on investor profile"""
        
        profiles = {
            "conservative": {
                "initial_balance": 10000.0,
                "duration_days": 30,
                "symbols": ["BTC"],
                "strategies": ["dca"],
                "risk_level": "low",
                "max_positions": 2
            },
            "balanced": {
                "initial_balance": 25000.0,
                "duration_days": 60,
                "symbols": ["BTC", "ETH"],
                "strategies": ["breakout", "sentiment"],
                "risk_level": "medium",
                "max_positions": 3
            },
            "aggressive": {
                "initial_balance": 50000.0,
                "duration_days": 90,
                "symbols": ["BTC", "ETH", "ADA"],
                "strategies": ["ai_powered", "breakout"],
                "risk_level": "high",
                "max_positions": 5
            }
        }
        
        profile_config = profiles.get(investor_profile, profiles["balanced"])
        
        return SimulationConfig(
            simulation_type=SimulationType.LIVE_DEMO,
            **profile_config
        )
    
    def run_backtest(self, config: SimulationConfig) -> SimulationResult:
        """Run a comprehensive backtest simulation"""
        logger.info(f"Starting backtest simulation: {config.duration_days} days")
        
        # Initialize components
        portfolio = PortfolioManager(config.initial_balance)
        strategy_engine = StrategyEngine()
        
        # Activate requested strategies
        strategy_engine.active_strategies = config.strategies
        
        # Generate market data for all symbols
        for symbol in config.symbols:
            self.market_simulator.generate_price_data(symbol, config.duration_days)
        
        # Track simulation data
        trade_history = []
        portfolio_history = []
        daily_returns = []
        
        start_date = datetime.now() - timedelta(days=config.duration_days)
        
        # Run simulation day by day
        for day in range(config.duration_days):
            current_date = start_date + timedelta(days=day)
            
            # Get market data for this day
            daily_market_data = {}
            for symbol in config.symbols:
                price_data = self.market_simulator.get_price_at_date(symbol, current_date)
                if price_data:
                    daily_market_data[symbol] = MarketData(**price_data)
            
            # Generate trading signals
            portfolio_data = asdict(portfolio.get_portfolio_summary())
            
            for symbol, market_data in daily_market_data.items():
                # Generate signals for this symbol
                signals = []
                for strategy_id in config.strategies:
                    strategy = strategy_engine.strategies.get(strategy_id)
                    if strategy:
                        signal = strategy.generate_signal(market_data, portfolio_data)
                        if signal:
                            signals.append(signal)
                
                # Execute best signal
                if signals:
                    best_signal = max(signals, key=lambda s: s.confidence)
                    
                    try:
                        if best_signal.signal == best_signal.signal.BUY and portfolio.cash_balance > best_signal.quantity * best_signal.price:
                            trade = portfolio.execute_trade(
                                symbol=best_signal.symbol,
                                side=TradeType.BUY,
                                quantity=best_signal.quantity,
                                price=best_signal.price,
                                strategy=best_signal.strategy
                            )
                            trade_history.append(asdict(trade))
                        
                        elif best_signal.signal == best_signal.signal.SELL and symbol in portfolio.positions:
                            position = portfolio.positions[symbol]
                            sell_quantity = min(best_signal.quantity, position.quantity)
                            
                            trade = portfolio.execute_trade(
                                symbol=best_signal.symbol,
                                side=TradeType.SELL,
                                quantity=sell_quantity,
                                price=best_signal.price,
                                strategy=best_signal.strategy
                            )
                            trade_history.append(asdict(trade))
                    
                    except Exception as e:
                        logger.warning(f"Could not execute trade: {e}")
            
            # Record daily portfolio value
            portfolio_summary = portfolio.get_portfolio_summary()
            portfolio_history.append({
                'date': current_date.isoformat(),
                'total_value': portfolio_summary.total_value,
                'cash_balance': portfolio_summary.cash_balance,
                'invested_value': portfolio_summary.invested_value,
                'positions': len(portfolio.positions)
            })
            
            # Calculate daily return
            if day > 0:
                prev_value = portfolio_history[day-1]['total_value']
                curr_value = portfolio_summary.total_value
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
        
        # Calculate final metrics
        final_summary = portfolio.get_portfolio_summary()
        total_return = final_summary.total_value - config.initial_balance
        total_return_percent = (total_return / config.initial_balance) * 100
        
        # Calculate additional metrics
        profitable_trades = len([t for t in trade_history if t['side'] == 'sell'])  # Simplified
        win_rate = (profitable_trades / len(trade_history) * 100) if trade_history else 0
        
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0  # Annualized
        sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)) if daily_returns and np.std(daily_returns) > 0 else 0
        
        # Max drawdown calculation
        portfolio_values = [p['total_value'] for p in portfolio_history]
        max_drawdown = self._calculate_max_drawdown(portfolio_values)
        
        result = SimulationResult(
            config=config,
            start_date=start_date,
            end_date=datetime.now(),
            initial_value=config.initial_balance,
            final_value=final_summary.total_value,
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=len(trade_history),
            profitable_trades=profitable_trades,
            average_trade_return=total_return_percent / len(trade_history) if trade_history else 0,
            volatility=volatility,
            daily_returns=daily_returns,
            trade_history=trade_history,
            portfolio_history=portfolio_history
        )
        
        self.completed_simulations.append(result)
        logger.info(f"Backtest completed. Return: {total_return_percent:.2f}%")
        
        return result
    
    def run_live_demo(self, config: SimulationConfig) -> str:
        """Start a live demonstration simulation"""
        demo_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize portfolio and strategy engine
        portfolio = PortfolioManager(config.initial_balance)
        strategy_engine = StrategyEngine()
        strategy_engine.active_strategies = config.strategies
        
        # Store active simulation
        self.active_simulations[demo_id] = {
            'config': config,
            'portfolio': portfolio,
            'strategy_engine': strategy_engine,
            'start_time': datetime.now(),
            'trade_count': 0,
            'last_update': datetime.now()
        }
        
        logger.info(f"Live demo started: {demo_id}")
        return demo_id
    
    def update_live_demo(self, demo_id: str) -> Dict:
        """Update a live demonstration with current market data"""
        if demo_id not in self.active_simulations:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo = self.active_simulations[demo_id]
        portfolio = demo['portfolio']
        strategy_engine = demo['strategy_engine']
        config = demo['config']
        
        # Get current market data and generate signals
        portfolio_data = asdict(portfolio.get_portfolio_summary())
        signals = strategy_engine.generate_signals(config.symbols, portfolio_data)
        
        # Execute signals (for demo purposes, execute automatically)
        executed_trades = []
        for signal in signals:
            try:
                if signal.signal.value == 'buy' and portfolio.cash_balance > signal.quantity * signal.price:
                    trade = portfolio.execute_trade(
                        symbol=signal.symbol,
                        side=TradeType.BUY,
                        quantity=signal.quantity,
                        price=signal.price,
                        strategy=signal.strategy
                    )
                    executed_trades.append(asdict(trade))
                    demo['trade_count'] += 1
                
                elif signal.signal.value == 'sell' and signal.symbol in portfolio.positions:
                    position = portfolio.positions[signal.symbol]
                    sell_quantity = min(signal.quantity, position.quantity)
                    
                    trade = portfolio.execute_trade(
                        symbol=signal.symbol,
                        side=TradeType.SELL,
                        quantity=sell_quantity,
                        price=signal.price,
                        strategy=signal.strategy
                    )
                    executed_trades.append(asdict(trade))
            
            except Exception as e:
                logger.warning(f"Demo trade execution failed: {e}")
        
        demo['last_update'] = datetime.now()
        
        # Return demo status
        portfolio_summary = portfolio.get_portfolio_summary()
        return {
            'demo_id': demo_id,
            'status': 'active',
            'runtime_hours': (datetime.now() - demo['start_time']).total_seconds() / 3600,
            'portfolio_summary': asdict(portfolio_summary),
            'recent_trades': executed_trades,
            'total_trades': demo['trade_count'],
            'active_strategies': strategy_engine.active_strategies,
            'current_signals': [asdict(s) for s in signals],
            'last_update': demo['last_update'].isoformat()
        }
    
    def get_demo_status(self, demo_id: str) -> Dict:
        """Get current status of a live demo"""
        if demo_id not in self.active_simulations:
            raise ValueError(f"Demo {demo_id} not found")
        
        return self.update_live_demo(demo_id)
    
    def stop_demo(self, demo_id: str) -> SimulationResult:
        """Stop a live demo and generate final results"""
        if demo_id not in self.active_simulations:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo = self.active_simulations[demo_id]
        portfolio = demo['portfolio']
        config = demo['config']
        
        # Generate final result
        portfolio_summary = portfolio.get_portfolio_summary()
        total_return = portfolio_summary.total_value - config.initial_balance
        total_return_percent = (total_return / config.initial_balance) * 100
        
        result = SimulationResult(
            config=config,
            start_date=demo['start_time'],
            end_date=datetime.now(),
            initial_value=config.initial_balance,
            final_value=portfolio_summary.total_value,
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=0.0,  # Would need historical tracking
            sharpe_ratio=0.0,  # Would need historical tracking
            win_rate=portfolio_summary.win_rate,
            total_trades=demo['trade_count'],
            profitable_trades=demo['trade_count'],  # Simplified
            average_trade_return=total_return_percent / demo['trade_count'] if demo['trade_count'] > 0 else 0,
            volatility=0.0,  # Would need historical tracking
            daily_returns=[],
            trade_history=[asdict(t) for t in portfolio.trades],
            portfolio_history=portfolio.portfolio_history
        )
        
        # Remove from active simulations
        del self.active_simulations[demo_id]
        self.completed_simulations.append(result)
        
        logger.info(f"Demo {demo_id} stopped. Final return: {total_return_percent:.2f}%")
        return result
    
    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """Calculate maximum drawdown from a series of portfolio values"""
        if len(values) < 2:
            return 0.0
        
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100  # Return as percentage
    
    def generate_investor_report(self, result: SimulationResult) -> Dict:
        """Generate a comprehensive investor report"""
        config = result.config
        
        # Performance summary
        performance_summary = {
            'total_return_percent': result.total_return_percent,
            'total_return_amount': result.total_return,
            'annualized_return': result.total_return_percent * (365 / config.duration_days),
            'max_drawdown': result.max_drawdown,
            'sharpe_ratio': result.sharpe_ratio,
            'volatility': result.volatility,
            'win_rate': result.win_rate
        }
        
        # Risk assessment
        risk_assessment = {
            'risk_level': config.risk_level,
            'risk_score': self._calculate_risk_score(result),
            'risk_adjusted_return': result.total_return_percent / max(result.volatility, 1),
            'maximum_loss': result.max_drawdown,
            'recovery_time_estimate': self._estimate_recovery_time(result)
        }
        
        # Strategy performance
        strategy_performance = self._analyze_strategy_performance(result)
        
        # Market conditions analysis
        market_analysis = {
            'simulation_period': f"{result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}",
            'market_conditions': 'simulated',  # Would analyze actual market conditions
            'symbols_traded': config.symbols,
            'total_trades': result.total_trades,
            'trading_frequency': result.total_trades / config.duration_days
        }
        
        return {
            'executive_summary': {
                'investment_amount': result.initial_value,
                'final_value': result.final_value,
                'total_return': result.total_return,
                'return_percentage': result.total_return_percent,
                'simulation_period_days': config.duration_days,
                'recommendation': self._generate_recommendation(result)
            },
            'performance_summary': performance_summary,
            'risk_assessment': risk_assessment,
            'strategy_performance': strategy_performance,
            'market_analysis': market_analysis,
            'detailed_metrics': {
                'daily_returns': result.daily_returns,
                'portfolio_history': result.portfolio_history[-30:],  # Last 30 days
                'recent_trades': result.trade_history[-10:]  # Last 10 trades
            }
        }
    
    def _calculate_risk_score(self, result: SimulationResult) -> int:
        """Calculate risk score from 1-10 (10 = highest risk)"""
        score = 5  # Base score
        
        # Adjust based on volatility
        if result.volatility > 0.3:
            score += 2
        elif result.volatility > 0.2:
            score += 1
        
        # Adjust based on max drawdown
        if result.max_drawdown > 20:
            score += 2
        elif result.max_drawdown > 10:
            score += 1
        
        # Adjust based on Sharpe ratio
        if result.sharpe_ratio < 0.5:
            score += 1
        elif result.sharpe_ratio > 1.5:
            score -= 1
        
        return min(max(score, 1), 10)
    
    def _estimate_recovery_time(self, result: SimulationResult) -> str:
        """Estimate time to recover from maximum drawdown"""
        if result.max_drawdown < 5:
            return "1-2 weeks"
        elif result.max_drawdown < 15:
            return "1-2 months"
        elif result.max_drawdown < 30:
            return "3-6 months"
        else:
            return "6+ months"
    
    def _analyze_strategy_performance(self, result: SimulationResult) -> Dict:
        """Analyze performance of individual strategies"""
        strategy_stats = {}
        
        for trade in result.trade_history:
            strategy = trade.get('strategy', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'trades': 0,
                    'total_value': 0,
                    'profitable_trades': 0
                }
            
            strategy_stats[strategy]['trades'] += 1
            strategy_stats[strategy]['total_value'] += trade.get('value', 0)
            
            # Simplified profit calculation
            if trade.get('side') == 'sell':
                strategy_stats[strategy]['profitable_trades'] += 1
        
        # Calculate performance metrics for each strategy
        for strategy, stats in strategy_stats.items():
            if stats['trades'] > 0:
                stats['avg_trade_value'] = stats['total_value'] / stats['trades']
                stats['win_rate'] = (stats['profitable_trades'] / stats['trades']) * 100
            else:
                stats['avg_trade_value'] = 0
                stats['win_rate'] = 0
        
        return strategy_stats
    
    def _generate_recommendation(self, result: SimulationResult) -> str:
        """Generate investment recommendation based on results"""
        if result.total_return_percent > 20 and result.max_drawdown < 15:
            return "STRONG BUY - Excellent risk-adjusted returns"
        elif result.total_return_percent > 10 and result.max_drawdown < 20:
            return "BUY - Good performance with manageable risk"
        elif result.total_return_percent > 0 and result.max_drawdown < 25:
            return "HOLD - Positive returns but monitor risk"
        elif result.total_return_percent > -5:
            return "CAUTION - Consider reducing position size"
        else:
            return "AVOID - High risk with poor returns"
    
    def save_simulation_results(self, filename: str):
        """Save all simulation results to file"""
        data = {
            'completed_simulations': [asdict(sim) for sim in self.completed_simulations],
            'active_simulations_count': len(self.active_simulations),
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Simulation results saved to {filename}") 