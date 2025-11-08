"""
Portfolio Management System for Trading Agent
Handles portfolio tracking, risk management, and performance analysis
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class Position:
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    entry_date: datetime
    last_updated: datetime

@dataclass
class Trade:
    trade_id: str
    symbol: str
    side: TradeType
    quantity: float
    price: float
    value: float
    timestamp: datetime
    status: OrderStatus
    strategy: str
    fees: float = 0.0
    notes: str = ""
    binance_order_id: Optional[str] = None

@dataclass
class PortfolioSummary:
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    active_trades_count: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float

class PortfolioManager:
    def __init__(self, initial_balance: float = 10000.0, max_position_size: float = 0.1):
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.max_position_size = max_position_size  # 10% max per position
        
        # Storage
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.portfolio_history: List[Dict] = []
        
        # Risk management
        self.max_daily_loss = 0.05  # 5% max daily loss
        self.max_total_loss = 0.20  # 20% max total loss
        
        logger.info(f"Portfolio initialized with ${initial_balance:,.2f}")
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current market prices for symbols"""
        prices = {}
        
        # Try Binance API first
        try:
            import sys
            import os
            # Use helper to load local binance module
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            binance_helper_path = os.path.join(project_root, 'binance_helper.py')
            if os.path.exists(binance_helper_path):
                sys.path.insert(0, project_root)
                from binance_helper import load_binance_module
                local_binance = load_binance_module()
                get_market_price = local_binance.get_market_price
            else:
                # Fallback: direct import
                binance_api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot', 'api')
                binance_api_path = os.path.abspath(binance_api_path)
                if binance_api_path not in sys.path:
                    sys.path.insert(0, binance_api_path)
                
                import importlib.util
                binance_module_path = os.path.join(binance_api_path, 'binance.py')
                if os.path.exists(binance_module_path):
                    spec = importlib.util.spec_from_file_location("local_binance", binance_module_path)
                    local_binance = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(local_binance)
                    get_market_price = local_binance.get_market_price
                else:
                    raise ImportError("Local binance.py module not found")
            
            for symbol in symbols:
                # Convert symbol to Binance format (e.g., BTC -> BTCUSDT)
                binance_symbol = self._convert_to_binance_symbol(symbol)
                price = get_market_price(binance_symbol)
                if price:
                    prices[symbol] = price
                    continue
                
                # Fallback to market data agent if Binance fails
                try:
                    from agent_browser.tools.market_data_agent import MarketDataAgent
                    with MarketDataAgent() as agent:
                        if symbol == 'BTC':
                            data = agent.scrape_coinmarketcap_bitcoin()
                            if data.get('success') and data.get('price'):
                                prices[symbol] = data['price']
                        else:
                            data = agent.scrape_tradingview_data(f"{symbol}USDT")
                            if data.get('success') and data.get('price'):
                                prices[symbol] = data['price']
                except Exception as e2:
                    logger.warning(f"Market data agent failed for {symbol}: {e2}")
            
            return prices
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return {}
    
    def _convert_to_binance_symbol(self, symbol: str) -> str:
        """Convert symbol to Binance format"""
        # If already in Binance format, return as is
        if 'USDT' in symbol.upper() or 'BUSD' in symbol.upper():
            return symbol.upper()
        # Otherwise add USDT
        return f"{symbol.upper()}USDT"
    
    def execute_trade(self, symbol: str, side: TradeType, quantity: float, 
                     price: Optional[float] = None, strategy: str = "manual", 
                     use_binance: bool = True) -> Trade:
        """Execute a trade and update portfolio"""
        
        # Get current price if not provided
        if price is None:
            prices = self.get_current_prices([symbol])
            price = prices.get(symbol)
            if price is None:
                raise ValueError(f"Could not get price for {symbol}")
        
        # Calculate trade value
        trade_value = quantity * price
        fees = trade_value * 0.001  # 0.1% trading fee
        
        # Risk checks
        if side == TradeType.BUY:
            total_cost = trade_value + fees
            if total_cost > self.cash_balance:
                raise ValueError(f"Insufficient funds. Need ${total_cost:,.2f}, have ${self.cash_balance:,.2f}")
            
            # Position size check
            portfolio_value = self.get_portfolio_value()
            if trade_value > portfolio_value * self.max_position_size:
                raise ValueError(f"Trade exceeds max position size of {self.max_position_size*100}%")
        
        # Execute on Binance if enabled and API keys are available
        binance_order_id = None
        actual_price = price
        actual_quantity = quantity
        
        if use_binance:
            try:
                import sys
                import os
                # Use helper to load local binance module
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                binance_helper_path = os.path.join(project_root, 'binance_helper.py')
                if os.path.exists(binance_helper_path):
                    sys.path.insert(0, project_root)
                    from binance_helper import load_binance_module
                    local_binance = load_binance_module()
                    place_order = local_binance.place_order
                    get_binance_api = local_binance.get_binance_api
                else:
                    # Fallback: direct import
                    binance_api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'trading_bot', 'api')
                    binance_api_path = os.path.abspath(binance_api_path)
                    if binance_api_path not in sys.path:
                        sys.path.insert(0, binance_api_path)
                    
                    import importlib.util
                    binance_module_path = os.path.join(binance_api_path, 'binance.py')
                    if os.path.exists(binance_module_path):
                        spec = importlib.util.spec_from_file_location("local_binance", binance_module_path)
                        local_binance = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(local_binance)
                        place_order = local_binance.place_order
                        get_binance_api = local_binance.get_binance_api
                    else:
                        raise ImportError("Local binance.py module not found")
                
                binance_api = get_binance_api()
                if binance_api:
                    binance_symbol = self._convert_to_binance_symbol(symbol)
                    order_type = 'MARKET'  # Use market orders for immediate execution
                    
                    result = place_order(
                        symbol=binance_symbol,
                        side=side.value,
                        quantity=quantity,
                        order_type=order_type
                    )
                    
                    if result and result.get('status') == 'success':
                        binance_order_id = result.get('order_id')
                        # Update with actual execution price if available
                        if result.get('price'):
                            actual_price = float(result['price'])
                        if result.get('quantity'):
                            actual_quantity = float(result['quantity'])
                        logger.info(f"Binance order executed: {binance_order_id}")
                    else:
                        error_msg = result.get('message', 'Unknown error') if result else 'No response from Binance'
                        logger.warning(f"Binance order failed: {error_msg}. Continuing with simulated trade.")
                        use_binance = False
                else:
                    logger.warning("Binance API not configured. Executing simulated trade.")
                    use_binance = False
            except Exception as e:
                logger.warning(f"Binance execution failed: {e}. Continuing with simulated trade.")
            except ImportError:
                logger.warning("Binance module not available. Executing simulated trade.")
                use_binance = False
        
        # Recalculate with actual execution values
        trade_value = actual_quantity * actual_price
        fees = trade_value * 0.001
        
        # Create trade record
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            quantity=actual_quantity,
            price=actual_price,
            value=trade_value,
            timestamp=datetime.now(),
            status=OrderStatus.FILLED if use_binance else OrderStatus.FILLED,
            strategy=strategy,
            fees=fees,
            notes=f"Binance Order ID: {binance_order_id}" if binance_order_id else "Simulated trade"
        )
        
        # Update portfolio
        if side == TradeType.BUY:
            self._execute_buy(trade)
        else:
            self._execute_sell(trade)
        
        # Record trade
        self.trades.append(trade)
        self._update_portfolio_history()
        
        logger.info(f"Trade executed: {side.value} {actual_quantity} {symbol} @ ${actual_price:,.2f} {'(Binance)' if use_binance else '(Simulated)'}")
        return trade
    
    def _execute_buy(self, trade: Trade):
        """Execute buy order"""
        total_cost = trade.value + trade.fees
        self.cash_balance -= total_cost
        
        # Update or create position
        if trade.symbol in self.positions:
            position = self.positions[trade.symbol]
            total_quantity = position.quantity + trade.quantity
            total_cost_basis = (position.quantity * position.average_price) + trade.value
            new_avg_price = total_cost_basis / total_quantity
            
            position.quantity = total_quantity
            position.average_price = new_avg_price
        else:
            self.positions[trade.symbol] = Position(
                symbol=trade.symbol,
                quantity=trade.quantity,
                average_price=trade.price,
                current_price=trade.price,
                market_value=trade.value,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                entry_date=trade.timestamp,
                last_updated=trade.timestamp
            )
    
    def _execute_sell(self, trade: Trade):
        """Execute sell order"""
        if trade.symbol not in self.positions:
            raise ValueError(f"No position in {trade.symbol} to sell")
        
        position = self.positions[trade.symbol]
        if trade.quantity > position.quantity:
            raise ValueError(f"Insufficient position. Have {position.quantity}, trying to sell {trade.quantity}")
        
        # Calculate proceeds
        proceeds = trade.value - trade.fees
        self.cash_balance += proceeds
        
        # Update position
        position.quantity -= trade.quantity
        if position.quantity <= 0:
            del self.positions[trade.symbol]
        else:
            position.last_updated = trade.timestamp
    
    def update_positions(self):
        """Update all positions with current market prices"""
        if not self.positions:
            return
        
        symbols = list(self.positions.keys())
        current_prices = self.get_current_prices(symbols)
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = position.market_value - (position.quantity * position.average_price)
                position.unrealized_pnl_percent = (position.unrealized_pnl / (position.quantity * position.average_price)) * 100
                position.last_updated = datetime.now()
    
    def get_portfolio_value(self) -> float:
        """Get total portfolio value"""
        self.update_positions()
        invested_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash_balance + invested_value
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get comprehensive portfolio summary"""
        self.update_positions()
        
        # Basic values
        invested_value = sum(pos.market_value for pos in self.positions.values())
        total_value = self.cash_balance + invested_value
        total_pnl = total_value - self.initial_balance
        total_pnl_percent = (total_pnl / self.initial_balance) * 100
        
        # Performance metrics
        win_rate = self._calculate_win_rate()
        sharpe_ratio = self._calculate_sharpe_ratio()
        max_drawdown = self._calculate_max_drawdown()
        
        return PortfolioSummary(
            total_value=total_value,
            cash_balance=self.cash_balance,
            invested_value=invested_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            positions_count=len(self.positions),
            active_trades_count=len([t for t in self.trades if t.status == OrderStatus.FILLED]),
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown
        )
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from closed trades"""
        if not self.trades:
            return 0.0
        
        # For simplicity, consider all filled trades as wins if portfolio is positive
        filled_trades = [t for t in self.trades if t.status == OrderStatus.FILLED]
        if not filled_trades:
            return 0.0
        
        total_pnl = self.get_portfolio_value() - self.initial_balance
        return 100.0 if total_pnl > 0 else 0.0
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio (simplified)"""
        if len(self.portfolio_history) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(self.portfolio_history)):
            prev_value = self.portfolio_history[i-1]['total_value']
            curr_value = self.portfolio_history[i]['total_value']
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        # Simple Sharpe calculation (assuming risk-free rate = 0)
        avg_return = sum(returns) / len(returns)
        if len(returns) < 2:
            return 0.0
        
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        return (avg_return / std_dev) if std_dev > 0 else 0.0
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if len(self.portfolio_history) < 2:
            return 0.0
        
        values = [h['total_value'] for h in self.portfolio_history]
        peak = values[0]
        max_drawdown = 0.0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100  # Return as percentage
    
    def _update_portfolio_history(self):
        """Update portfolio history for performance tracking"""
        summary = self.get_portfolio_summary()
        self.portfolio_history.append({
            'timestamp': datetime.now().isoformat(),
            'total_value': summary.total_value,
            'cash_balance': summary.cash_balance,
            'invested_value': summary.invested_value,
            'total_pnl': summary.total_pnl,
            'positions_count': summary.positions_count
        })
        
        # Keep only last 30 days of history
        if len(self.portfolio_history) > 30:
            self.portfolio_history = self.portfolio_history[-30:]
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        total_value = self.get_portfolio_value()
        total_loss = (self.initial_balance - total_value) / self.initial_balance
        
        # Daily loss (simplified - would need actual daily tracking)
        daily_loss = 0.0  # Placeholder
        
        return {
            'total_loss_percent': total_loss * 100,
            'daily_loss_percent': daily_loss * 100,
            'max_total_loss_percent': self.max_total_loss * 100,
            'max_daily_loss_percent': self.max_daily_loss * 100,
            'risk_level': self._assess_risk_level(total_loss),
            'position_concentration': self._calculate_position_concentration()
        }
    
    def _assess_risk_level(self, total_loss: float) -> str:
        """Assess current risk level"""
        if total_loss < 0.05:
            return "LOW"
        elif total_loss < 0.15:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_position_concentration(self) -> Dict:
        """Calculate position concentration risk"""
        if not self.positions:
            return {'max_position_percent': 0.0, 'diversification_score': 100.0}
        
        total_invested = sum(pos.market_value for pos in self.positions.values())
        if total_invested == 0:
            return {'max_position_percent': 0.0, 'diversification_score': 100.0}
        
        position_percentages = [pos.market_value / total_invested for pos in self.positions.values()]
        max_position_percent = max(position_percentages) * 100
        
        # Simple diversification score (100 = perfectly diversified)
        diversification_score = 100 - max_position_percent
        
        return {
            'max_position_percent': max_position_percent,
            'diversification_score': diversification_score
        }
    
    def save_to_file(self, filename: str):
        """Save portfolio state to file"""
        data = {
            'initial_balance': self.initial_balance,
            'cash_balance': self.cash_balance,
            'positions': {k: asdict(v) for k, v in self.positions.items()},
            'trades': [asdict(t) for t in self.trades],
            'portfolio_history': self.portfolio_history,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Portfolio saved to {filename}")
    
    def load_from_file(self, filename: str):
        """Load portfolio state from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.initial_balance = data['initial_balance']
            self.cash_balance = data['cash_balance']
            self.portfolio_history = data.get('portfolio_history', [])
            
            # Reconstruct positions
            self.positions = {}
            for symbol, pos_data in data.get('positions', {}).items():
                pos_data['entry_date'] = datetime.fromisoformat(pos_data['entry_date'])
                pos_data['last_updated'] = datetime.fromisoformat(pos_data['last_updated'])
                self.positions[symbol] = Position(**pos_data)
            
            # Reconstruct trades
            self.trades = []
            for trade_data in data.get('trades', []):
                trade_data['timestamp'] = datetime.fromisoformat(trade_data['timestamp'])
                trade_data['side'] = TradeType(trade_data['side'])
                trade_data['status'] = OrderStatus(trade_data['status'])
                self.trades.append(Trade(**trade_data))
            
            logger.info(f"Portfolio loaded from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            raise 