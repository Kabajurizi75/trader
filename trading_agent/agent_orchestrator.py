"""
Trading Agent Orchestrator
Main coordination system for the autonomous trading agent
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from dataclasses import asdict

from .portfolio_manager import PortfolioManager, TradeType
from .strategy_engine import StrategyEngine, TradingSignal
from .simulation_engine import SimulationEngine

logger = logging.getLogger(__name__)

class TradingAgent:
    """Main trading agent that orchestrates all components"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        
        # Initialize components
        self.portfolio = PortfolioManager(
            initial_balance=self.config['initial_balance'],
            max_position_size=self.config['max_position_size']
        )
        
        self.strategy_engine = StrategyEngine()
        self.simulation_engine = SimulationEngine()
        
        # Agent state
        self.is_running = False
        self.last_update = None
        self.trade_count = 0
        self.performance_history = []
        
        # Configure strategies
        self._configure_strategies()
        
        logger.info("Trading Agent initialized")
    
    def _default_config(self) -> Dict:
        """Default configuration for the trading agent"""
        return {
            'initial_balance': 10000.0,
            'max_position_size': 0.1,  # 10% max per position
            'symbols': ['BTC', 'ETH'],
            'active_strategies': ['breakout', 'sentiment'],
            'update_interval_minutes': 15,
            'risk_management': {
                'max_daily_loss': 0.05,
                'max_total_loss': 0.20,
                'stop_loss_percent': 0.05,
                'take_profit_percent': 0.15
            },
            'auto_execute': False,  # Require manual approval by default
            'logging_level': 'INFO'
        }
    
    def _configure_strategies(self):
        """Configure and activate strategies based on config"""
        # Activate strategies from config
        self.strategy_engine.active_strategies = self.config['active_strategies']
        
        # Configure risk management parameters
        for strategy_id in self.strategy_engine.strategies:
            strategy = self.strategy_engine.strategies[strategy_id]
            if hasattr(strategy, 'params'):
                # Update strategy parameters with risk management settings
                risk_config = self.config['risk_management']
                strategy.params.update({
                    'stop_loss': risk_config.get('stop_loss_percent', 0.05),
                    'take_profit': risk_config.get('take_profit_percent', 0.15)
                })
    
    async def start_agent(self):
        """Start the autonomous trading agent"""
        if self.is_running:
            logger.warning("Agent is already running")
            return
        
        self.is_running = True
        logger.info("Starting autonomous trading agent")
        
        try:
            # Run initial cycle immediately
            await self._agent_cycle()
            
            # Then run on schedule
            while self.is_running:
                await asyncio.sleep(self.config['update_interval_minutes'] * 60)
                if self.is_running:  # Check again after sleep
                    await self._agent_cycle()
        
        except asyncio.CancelledError:
            logger.info("Agent cancelled")
            self.is_running = False
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.is_running = False
            raise
    
    async def stop_agent(self):
        """Stop the autonomous trading agent"""
        self.is_running = False
        logger.info("Trading agent stopped")
    
    async def _agent_cycle(self):
        """Single cycle of the trading agent"""
        try:
            logger.info("Starting agent cycle")
            
            # 1. Update portfolio with current prices
            self.portfolio.update_positions()
            
            # 2. Check risk management
            if not self._check_risk_limits():
                logger.warning("Risk limits exceeded, skipping trading")
                return
            
            # 3. Generate trading signals
            portfolio_data = asdict(self.portfolio.get_portfolio_summary())
            signals = self.strategy_engine.generate_signals(
                self.config['symbols'], 
                portfolio_data
            )
            
            # 4. Process signals
            if signals:
                await self._process_signals(signals)
            
            # 5. Update performance tracking
            self._update_performance_tracking()
            
            # 6. Log status
            self._log_agent_status()
            
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in agent cycle: {e}")
    
    def _check_risk_limits(self) -> bool:
        """Check if current portfolio is within risk limits"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        risk_config = self.config['risk_management']
        
        # Check total loss limit
        total_loss_percent = abs(portfolio_summary.total_pnl_percent)
        if portfolio_summary.total_pnl < 0 and total_loss_percent > risk_config['max_total_loss'] * 100:
            logger.error(f"Total loss limit exceeded: {total_loss_percent:.2f}%")
            return False
        
        # Check daily loss limit (simplified - would need proper daily tracking)
        # For now, just check if we're in a significant drawdown
        if total_loss_percent > risk_config['max_daily_loss'] * 100:
            logger.warning(f"Daily loss threshold reached: {total_loss_percent:.2f}%")
            return False
        
        return True
    
    async def _process_signals(self, signals: List[TradingSignal]):
        """Process trading signals and execute trades"""
        logger.info(f"Processing {len(signals)} trading signals")
        
        # Sort signals by confidence
        signals.sort(key=lambda s: s.confidence, reverse=True)
        
        for signal in signals:
            try:
                # Check if we should execute this signal
                if await self._should_execute_signal(signal):
                    await self._execute_signal(signal)
                else:
                    logger.info(f"Signal skipped: {signal.strategy} - {signal.reasoning}")
            
            except Exception as e:
                logger.error(f"Error processing signal: {e}")
    
    async def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """Determine if a signal should be executed"""
        
        # Check confidence threshold
        min_confidence = 0.6  # Minimum 60% confidence
        if signal.confidence < min_confidence:
            return False
        
        # Check position limits
        portfolio_summary = self.portfolio.get_portfolio_summary()
        if signal.signal.value == 'buy':
            # Check if we have enough cash
            required_amount = signal.quantity * signal.price
            if required_amount > self.portfolio.cash_balance:
                return False
            
            # Check position size limits
            position_value = signal.quantity * signal.price
            portfolio_value = portfolio_summary.total_value
            position_percent = position_value / portfolio_value
            
            if position_percent > self.config['max_position_size']:
                return False
        
        elif signal.signal.value == 'sell':
            # Check if we have the position to sell
            if signal.symbol not in self.portfolio.positions:
                return False
            
            position = self.portfolio.positions[signal.symbol]
            if signal.quantity > position.quantity:
                return False
        
        # Additional checks can be added here (market conditions, etc.)
        
        return True
    
    async def _execute_signal(self, signal: TradingSignal):
        """Execute a trading signal"""
        try:
            # Check if we should execute (auto_execute or manual approval)
            should_execute = self.config.get('auto_execute', False)
            
            if should_execute:
                # Execute automatically with Binance integration
                try:
                    trade = self.portfolio.execute_trade(
                        symbol=signal.symbol,
                        side=TradeType(signal.signal.value),
                        quantity=signal.quantity,
                        price=signal.price,
                        strategy=signal.strategy,
                        use_binance=True  # Enable Binance execution
                    )
                    
                    self.trade_count += 1
                    logger.info(f"Trade executed: {trade.trade_id}")
                    
                    # Store trade for analysis
                    self._record_trade_analysis(trade, signal)
                except ValueError as ve:
                    # Handle validation errors (insufficient funds, etc.)
                    logger.warning(f"Trade validation failed: {ve}")
                    self._record_pending_trade(signal)
                except Exception as te:
                    logger.error(f"Trade execution error: {te}")
                    # Still record as pending for manual review
                    self._record_pending_trade(signal)
            else:
                # Log for manual review
                logger.info(f"Trade signal (manual review required): {signal.signal.value} {signal.quantity} {signal.symbol} @ ${signal.price:.2f}")
                self._record_pending_trade(signal)
        
        except Exception as e:
            logger.error(f"Failed to execute signal: {e}")
    
    def _record_trade_analysis(self, trade, signal: TradingSignal):
        """Record trade analysis for performance tracking"""
        analysis = {
            'trade_id': trade.trade_id,
            'signal_confidence': signal.confidence,
            'signal_reasoning': signal.reasoning,
            'strategy': signal.strategy,
            'execution_time': datetime.now().isoformat(),
            'market_conditions': self._get_current_market_conditions()
        }
        
        # Store analysis (could be saved to database)
        if not hasattr(self, 'trade_analyses'):
            self.trade_analyses = []
        self.trade_analyses.append(analysis)
    
    def _record_pending_trade(self, signal: TradingSignal):
        """Record pending trade for manual review"""
        pending_trade = {
            'signal': asdict(signal),
            'created_at': datetime.now().isoformat(),
            'status': 'pending_review'
        }
        
        if not hasattr(self, 'pending_trades'):
            self.pending_trades = []
        self.pending_trades.append(pending_trade)
    
    def _get_current_market_conditions(self) -> Dict:
        """Get current market conditions for analysis"""
        try:
            # Get market data
            market_data = {}
            for symbol in self.config['symbols']:
                data = self.strategy_engine.get_market_data(symbol)
                if data:
                    market_data[symbol] = {
                        'price': data.price,
                        'change_percent': data.change_percent,
                        'volume': data.volume
                    }
            
            # Get sentiment (if available)
            try:
                import requests
                response = requests.get("http://localhost:8000/sentiment", timeout=5)
                sentiment = response.json() if response.status_code == 200 else None
            except:
                sentiment = None
            
            return {
                'market_data': market_data,
                'sentiment': sentiment,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.warning(f"Could not get market conditions: {e}")
            return {}
    
    def _update_performance_tracking(self):
        """Update performance tracking data"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        performance_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'total_value': portfolio_summary.total_value,
            'total_pnl': portfolio_summary.total_pnl,
            'total_pnl_percent': portfolio_summary.total_pnl_percent,
            'positions_count': portfolio_summary.positions_count,
            'trade_count': self.trade_count,
            'cash_balance': portfolio_summary.cash_balance,
            'invested_value': portfolio_summary.invested_value
        }
        
        self.performance_history.append(performance_snapshot)
        
        # Keep only last 100 snapshots
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    def _log_agent_status(self):
        """Log current agent status"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        logger.info(f"Agent Status - Portfolio: ${portfolio_summary.total_value:,.2f} "
                   f"({portfolio_summary.total_pnl_percent:+.2f}%), "
                   f"Positions: {portfolio_summary.positions_count}, "
                   f"Trades: {self.trade_count}")
    
    # Public API methods
    
    def get_agent_status(self) -> Dict:
        """Get comprehensive agent status"""
        portfolio_summary = self.portfolio.get_portfolio_summary()
        strategy_performance = self.strategy_engine.get_strategy_performance()
        
        return {
            'agent_info': {
                'is_running': self.is_running,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'trade_count': self.trade_count,
                'uptime_hours': (datetime.now() - (self.last_update or datetime.now())).total_seconds() / 3600
            },
            'portfolio': asdict(portfolio_summary),
            'strategies': strategy_performance,
            'config': self.config,
            'recent_performance': self.performance_history[-10:] if self.performance_history else []
        }
    
    def get_pending_trades(self) -> List[Dict]:
        """Get trades pending manual review"""
        return getattr(self, 'pending_trades', [])
    
    def approve_pending_trade(self, trade_index: int) -> bool:
        """Approve a pending trade for execution"""
        try:
            pending_trades = getattr(self, 'pending_trades', [])
            if 0 <= trade_index < len(pending_trades):
                pending_trade = pending_trades[trade_index]
                signal_data = pending_trade['signal']
                
                # Recreate signal object
                signal = TradingSignal(**signal_data)
                
                # Execute the trade
                trade = self.portfolio.execute_trade(
                    symbol=signal.symbol,
                    side=TradeType(signal.signal),
                    quantity=signal.quantity,
                    price=signal.price,
                    strategy=signal.strategy
                )
                
                # Remove from pending
                pending_trades.pop(trade_index)
                self.trade_count += 1
                
                logger.info(f"Pending trade approved and executed: {trade.trade_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error approving pending trade: {e}")
            return False
    
    def reject_pending_trade(self, trade_index: int) -> bool:
        """Reject a pending trade"""
        try:
            pending_trades = getattr(self, 'pending_trades', [])
            if 0 <= trade_index < len(pending_trades):
                rejected_trade = pending_trades.pop(trade_index)
                logger.info(f"Pending trade rejected: {rejected_trade['signal']['symbol']}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error rejecting pending trade: {e}")
            return False
    
    def update_config(self, new_config: Dict):
        """Update agent configuration"""
        self.config.update(new_config)
        self._configure_strategies()
        logger.info("Agent configuration updated")
    
    def save_state(self, filename: str):
        """Save agent state to file"""
        state = {
            'config': self.config,
            'trade_count': self.trade_count,
            'performance_history': self.performance_history,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'pending_trades': getattr(self, 'pending_trades', []),
            'trade_analyses': getattr(self, 'trade_analyses', []),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        # Also save portfolio state
        portfolio_filename = filename.replace('.json', '_portfolio.json')
        self.portfolio.save_to_file(portfolio_filename)
        
        logger.info(f"Agent state saved to {filename}")
    
    def load_state(self, filename: str):
        """Load agent state from file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            self.config = state.get('config', self._default_config())
            self.trade_count = state.get('trade_count', 0)
            self.performance_history = state.get('performance_history', [])
            
            if state.get('last_update'):
                self.last_update = datetime.fromisoformat(state['last_update'])
            
            # Load optional data
            self.pending_trades = state.get('pending_trades', [])
            self.trade_analyses = state.get('trade_analyses', [])
            
            # Load portfolio state
            portfolio_filename = filename.replace('.json', '_portfolio.json')
            self.portfolio.load_from_file(portfolio_filename)
            
            # Reconfigure strategies
            self._configure_strategies()
            
            logger.info(f"Agent state loaded from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading agent state: {e}")
            raise

# Convenience function for creating a trading agent
def create_trading_agent(profile: str = "balanced") -> TradingAgent:
    """Create a trading agent with predefined profile"""
    
    profiles = {
        "conservative": {
            'initial_balance': 10000.0,
            'max_position_size': 0.05,  # 5% max per position
            'symbols': ['BTC'],
            'active_strategies': ['dca'],
            'update_interval_minutes': 60,  # Less frequent updates
            'auto_execute': True,
            'risk_management': {
                'max_daily_loss': 0.02,  # 2% max daily loss
                'max_total_loss': 0.10,  # 10% max total loss
                'stop_loss_percent': 0.03,
                'take_profit_percent': 0.08
            }
        },
        "balanced": {
            'initial_balance': 25000.0,
            'max_position_size': 0.08,  # 8% max per position
            'symbols': ['BTC', 'ETH'],
            'active_strategies': ['breakout', 'sentiment'],
            'update_interval_minutes': 30,
            'auto_execute': False,  # Manual review
            'risk_management': {
                'max_daily_loss': 0.03,  # 3% max daily loss
                'max_total_loss': 0.15,  # 15% max total loss
                'stop_loss_percent': 0.05,
                'take_profit_percent': 0.12
            }
        },
        "aggressive": {
            'initial_balance': 50000.0,
            'max_position_size': 0.15,  # 15% max per position
            'symbols': ['BTC', 'ETH', 'ADA'],
            'active_strategies': ['ai_powered', 'breakout', 'sentiment'],
            'update_interval_minutes': 15,  # Frequent updates
            'auto_execute': True,
            'risk_management': {
                'max_daily_loss': 0.05,  # 5% max daily loss
                'max_total_loss': 0.25,  # 25% max total loss
                'stop_loss_percent': 0.08,
                'take_profit_percent': 0.20
            }
        }
    }
    
    config = profiles.get(profile, profiles["balanced"])
    return TradingAgent(config) 