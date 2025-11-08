"""
Strategy Engine for Trading Agent
Implements various trading strategies with AI-powered decision making
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class StrategyType(Enum):
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    SENTIMENT_BASED = "sentiment_based"
    AI_POWERED = "ai_powered"
    DCA = "dollar_cost_averaging"

@dataclass
class TradingSignal:
    symbol: str
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    price: float
    quantity: float
    strategy: str
    reasoning: str
    timestamp: datetime
    risk_level: str = "medium"

@dataclass
class MarketData:
    symbol: str
    price: float
    change_percent: float
    volume: str
    timestamp: datetime
    source: str

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, params: Dict):
        self.name = name
        self.params = params
        self.active = True
        self.performance_history = []
    
    @abstractmethod
    def generate_signal(self, market_data: MarketData, portfolio_data: Dict) -> Optional[TradingSignal]:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    def get_risk_level(self) -> str:
        """Get risk level of the strategy"""
        pass

class BreakoutStrategy(BaseStrategy):
    """Breakout trading strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'breakout_threshold': 0.02,  # 2% price movement
            'volume_threshold': 1.5,     # 1.5x average volume
            'stop_loss': 0.05,           # 5% stop loss
            'take_profit': 0.10,         # 10% take profit
            'lookback_period': 24        # 24 hours lookback
        }
        if params:
            default_params.update(params)
        
        super().__init__("Breakout Strategy", default_params)
    
    def generate_signal(self, market_data: MarketData, portfolio_data: Dict) -> Optional[TradingSignal]:
        """Generate breakout signal"""
        try:
            # Simple breakout logic based on price change
            price_change = abs(market_data.change_percent)
            
            if price_change >= self.params['breakout_threshold'] * 100:
                signal_type = SignalType.BUY if market_data.change_percent > 0 else SignalType.SELL
                confidence = min(price_change / 5.0, 1.0)  # Scale confidence
                
                # Calculate position size (risk management)
                portfolio_value = portfolio_data.get('total_value', 10000)
                risk_amount = portfolio_value * 0.02  # Risk 2% of portfolio
                quantity = risk_amount / market_data.price
                
                return TradingSignal(
                    symbol=market_data.symbol,
                    signal=signal_type,
                    confidence=confidence,
                    price=market_data.price,
                    quantity=quantity,
                    strategy=self.name,
                    reasoning=f"Price breakout detected: {market_data.change_percent:.2f}% change",
                    timestamp=datetime.now(),
                    risk_level=self.get_risk_level()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in breakout strategy: {e}")
            return None
    
    def get_risk_level(self) -> str:
        return "medium"

class SentimentBasedStrategy(BaseStrategy):
    """AI-powered sentiment-based trading strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'sentiment_threshold': 0.6,   # Minimum sentiment confidence
            'news_lookback_hours': 24,    # Hours of news to analyze
            'position_size_factor': 0.03  # 3% of portfolio per trade
        }
        if params:
            default_params.update(params)
        
        super().__init__("Sentiment-Based Strategy", default_params)
    
    def generate_signal(self, market_data: MarketData, portfolio_data: Dict) -> Optional[TradingSignal]:
        """Generate signal based on market sentiment"""
        try:
            # Get sentiment analysis from RAG engine
            sentiment_data = self._get_market_sentiment()
            
            if not sentiment_data:
                return None
            
            # Extract sentiment and confidence
            sentiment = sentiment_data.get('sentiment', 'neutral').lower()
            confidence_text = sentiment_data.get('confidence', 'low').lower()
            
            # Convert confidence to numeric
            confidence_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
            confidence = confidence_map.get(confidence_text, 0.5)
            
            if confidence < self.params['sentiment_threshold']:
                return None
            
            # Generate signal based on sentiment
            if sentiment == 'positive':
                signal_type = SignalType.BUY
            elif sentiment == 'negative':
                signal_type = SignalType.SELL
            else:
                return None
            
            # Calculate position size
            portfolio_value = portfolio_data.get('total_value', 10000)
            risk_amount = portfolio_value * self.params['position_size_factor']
            quantity = risk_amount / market_data.price
            
            return TradingSignal(
                symbol=market_data.symbol,
                signal=signal_type,
                confidence=confidence,
                price=market_data.price,
                quantity=quantity,
                strategy=self.name,
                reasoning=f"Market sentiment: {sentiment} (confidence: {confidence_text})",
                timestamp=datetime.now(),
                risk_level=self.get_risk_level()
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment strategy: {e}")
            return None
    
    def _get_market_sentiment(self) -> Optional[Dict]:
        """Get market sentiment from RAG engine"""
        try:
            import requests
            response = requests.get("http://localhost:8000/sentiment", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch sentiment data: {e}")
        return None
    
    def get_risk_level(self) -> str:
        return "high"

class DCAStrategy(BaseStrategy):
    """Dollar Cost Averaging strategy"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'investment_amount': 100.0,   # Fixed amount per trade
            'frequency_hours': 24,        # Trade frequency
            'max_price_deviation': 0.05   # Don't buy if price is >5% above average
        }
        if params:
            default_params.update(params)
        
        super().__init__("Dollar Cost Averaging", default_params)
        self.last_trade_time = None
    
    def generate_signal(self, market_data: MarketData, portfolio_data: Dict) -> Optional[TradingSignal]:
        """Generate DCA signal"""
        try:
            # Check if enough time has passed since last trade
            if self.last_trade_time:
                time_diff = datetime.now() - self.last_trade_time
                if time_diff.total_seconds() < self.params['frequency_hours'] * 3600:
                    return None
            
            # Simple DCA - always buy if conditions are met
            investment_amount = self.params['investment_amount']
            quantity = investment_amount / market_data.price
            
            # Update last trade time
            self.last_trade_time = datetime.now()
            
            return TradingSignal(
                symbol=market_data.symbol,
                signal=SignalType.BUY,
                confidence=0.8,  # DCA has consistent confidence
                price=market_data.price,
                quantity=quantity,
                strategy=self.name,
                reasoning=f"DCA scheduled purchase: ${investment_amount}",
                timestamp=datetime.now(),
                risk_level=self.get_risk_level()
            )
            
        except Exception as e:
            logger.error(f"Error in DCA strategy: {e}")
            return None
    
    def get_risk_level(self) -> str:
        return "low"

class AIPoweredStrategy(BaseStrategy):
    """AI-powered strategy using RAG and market analysis"""
    
    def __init__(self, params: Dict = None):
        default_params = {
            'ai_confidence_threshold': 0.7,
            'max_position_size': 0.05,  # 5% of portfolio
            'use_technical_analysis': True,
            'use_sentiment_analysis': True,
            'use_news_analysis': True
        }
        if params:
            default_params.update(params)
        
        super().__init__("AI-Powered Strategy", default_params)
    
    def generate_signal(self, market_data: MarketData, portfolio_data: Dict) -> Optional[TradingSignal]:
        """Generate AI-powered trading signal"""
        try:
            # Gather multiple data sources
            analysis_data = self._gather_analysis_data(market_data)
            
            if not analysis_data:
                return None
            
            # Use AI to make trading decision
            ai_decision = self._make_ai_decision(analysis_data, market_data, portfolio_data)
            
            if ai_decision and ai_decision['confidence'] >= self.params['ai_confidence_threshold']:
                # Calculate position size
                portfolio_value = portfolio_data.get('total_value', 10000)
                max_investment = portfolio_value * self.params['max_position_size']
                quantity = max_investment / market_data.price
                
                return TradingSignal(
                    symbol=market_data.symbol,
                    signal=SignalType(ai_decision['signal']),
                    confidence=ai_decision['confidence'],
                    price=market_data.price,
                    quantity=quantity,
                    strategy=self.name,
                    reasoning=ai_decision['reasoning'],
                    timestamp=datetime.now(),
                    risk_level=self.get_risk_level()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in AI strategy: {e}")
            return None
    
    def _gather_analysis_data(self, market_data: MarketData) -> Dict:
        """Gather data from multiple sources for AI analysis"""
        analysis_data = {
            'market_data': market_data,
            'sentiment': None,
            'news_summary': None,
            'technical_indicators': None
        }
        
        try:
            import requests
            
            # Get sentiment analysis
            if self.params['use_sentiment_analysis']:
                try:
                    response = requests.get("http://localhost:8000/sentiment", timeout=5)
                    if response.status_code == 200:
                        analysis_data['sentiment'] = response.json()
                except:
                    pass
            
            # Get news summary
            if self.params['use_news_analysis']:
                try:
                    response = requests.get("http://localhost:8000/summary", timeout=5)
                    if response.status_code == 200:
                        analysis_data['news_summary'] = response.json()
                except:
                    pass
            
            # Add technical indicators (simplified)
            if self.params['use_technical_analysis']:
                analysis_data['technical_indicators'] = self._calculate_technical_indicators(market_data)
            
        except Exception as e:
            logger.warning(f"Error gathering analysis data: {e}")
        
        return analysis_data
    
    def _calculate_technical_indicators(self, market_data: MarketData) -> Dict:
        """Calculate basic technical indicators"""
        # Simplified technical analysis
        change_percent = market_data.change_percent
        
        return {
            'trend': 'bullish' if change_percent > 2 else 'bearish' if change_percent < -2 else 'neutral',
            'momentum': 'strong' if abs(change_percent) > 5 else 'weak',
            'volatility': 'high' if abs(change_percent) > 10 else 'normal'
        }
    
    def _make_ai_decision(self, analysis_data: Dict, market_data: MarketData, portfolio_data: Dict) -> Optional[Dict]:
        """Make AI-powered trading decision"""
        try:
            # Simple AI decision logic (can be enhanced with actual ML models)
            score = 0.0
            reasoning_parts = []
            
            # Sentiment analysis
            sentiment_data = analysis_data.get('sentiment')
            if sentiment_data:
                sentiment = sentiment_data.get('sentiment', 'neutral').lower()
                if sentiment == 'positive':
                    score += 0.3
                    reasoning_parts.append("Positive market sentiment")
                elif sentiment == 'negative':
                    score -= 0.3
                    reasoning_parts.append("Negative market sentiment")
            
            # Technical indicators
            tech_data = analysis_data.get('technical_indicators')
            if tech_data:
                if tech_data['trend'] == 'bullish':
                    score += 0.2
                    reasoning_parts.append("Bullish technical trend")
                elif tech_data['trend'] == 'bearish':
                    score -= 0.2
                    reasoning_parts.append("Bearish technical trend")
            
            # News analysis
            news_data = analysis_data.get('news_summary')
            if news_data and news_data.get('key_topics'):
                # Simple keyword analysis
                positive_keywords = ['growth', 'bull', 'rise', 'gain', 'positive']
                negative_keywords = ['crash', 'bear', 'fall', 'loss', 'negative']
                
                summary = news_data.get('summary', '').lower()
                pos_count = sum(1 for word in positive_keywords if word in summary)
                neg_count = sum(1 for word in negative_keywords if word in summary)
                
                if pos_count > neg_count:
                    score += 0.2
                    reasoning_parts.append("Positive news sentiment")
                elif neg_count > pos_count:
                    score -= 0.2
                    reasoning_parts.append("Negative news sentiment")
            
            # Market data analysis
            if market_data.change_percent > 5:
                score += 0.1
                reasoning_parts.append("Strong upward momentum")
            elif market_data.change_percent < -5:
                score -= 0.1
                reasoning_parts.append("Strong downward momentum")
            
            # Determine signal and confidence
            if score > 0.3:
                return {
                    'signal': 'buy',
                    'confidence': min(score, 1.0),
                    'reasoning': "AI Analysis: " + ", ".join(reasoning_parts)
                }
            elif score < -0.3:
                return {
                    'signal': 'sell',
                    'confidence': min(abs(score), 1.0),
                    'reasoning': "AI Analysis: " + ", ".join(reasoning_parts)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in AI decision making: {e}")
            return None
    
    def get_risk_level(self) -> str:
        return "high"

class StrategyEngine:
    """Main strategy engine that manages and executes trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategies: List[str] = []
        self.signal_history: List[TradingSignal] = []
        
        # Initialize default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize default trading strategies"""
        self.strategies['breakout'] = BreakoutStrategy()
        self.strategies['sentiment'] = SentimentBasedStrategy()
        self.strategies['dca'] = DCAStrategy()
        self.strategies['ai_powered'] = AIPoweredStrategy()
        
        # Activate some strategies by default
        self.active_strategies = ['breakout', 'sentiment']
    
    def add_strategy(self, strategy_id: str, strategy: BaseStrategy):
        """Add a new strategy"""
        self.strategies[strategy_id] = strategy
        logger.info(f"Strategy '{strategy_id}' added")
    
    def activate_strategy(self, strategy_id: str):
        """Activate a strategy"""
        if strategy_id in self.strategies and strategy_id not in self.active_strategies:
            self.active_strategies.append(strategy_id)
            logger.info(f"Strategy '{strategy_id}' activated")
    
    def deactivate_strategy(self, strategy_id: str):
        """Deactivate a strategy"""
        if strategy_id in self.active_strategies:
            self.active_strategies.remove(strategy_id)
            logger.info(f"Strategy '{strategy_id}' deactivated")
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get current market data for a symbol"""
        # Try Binance API first
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'trading_bot', 'api'))
            from binance import get_24hr_stats, get_market_price
            
            # Convert symbol to Binance format
            binance_symbol = symbol.upper()
            if not binance_symbol.endswith('USDT') and not binance_symbol.endswith('BUSD'):
                binance_symbol = f"{binance_symbol}USDT"
            
            # Get 24hr stats for better data
            stats = get_24hr_stats(binance_symbol)
            if stats:
                return MarketData(
                    symbol=symbol,
                    price=stats['price'],
                    change_percent=stats['changePercent'],
                    volume=str(stats.get('volume', 'N/A')),
                    timestamp=datetime.now(),
                    source='binance'
                )
            
            # Fallback to simple price
            price = get_market_price(binance_symbol)
            if price:
                return MarketData(
                    symbol=symbol,
                    price=price,
                    change_percent=0.0,
                    volume='N/A',
                    timestamp=datetime.now(),
                    source='binance'
                )
        except Exception as e:
            logger.warning(f"Binance API failed for {symbol}: {e}")
        
        # Fallback to market data agent
        try:
            from agent_browser.tools.market_data_agent import MarketDataAgent
            
            with MarketDataAgent() as agent:
                if symbol == 'BTC':
                    data = agent.scrape_coinmarketcap_bitcoin()
                else:
                    data = agent.scrape_tradingview_data(f"{symbol}USDT")
                
                if data.get('success') and data.get('price'):
                    return MarketData(
                        symbol=symbol,
                        price=data['price'],
                        change_percent=data.get('change_percent', 0.0),
                        volume=data.get('volume', 'N/A'),
                        timestamp=datetime.now(),
                        source=data.get('source', 'unknown')
                    )
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
        
        return None
    
    def generate_signals(self, symbols: List[str], portfolio_data: Dict) -> List[TradingSignal]:
        """Generate trading signals from all active strategies"""
        all_signals = []
        
        for symbol in symbols:
            market_data = self.get_market_data(symbol)
            if not market_data:
                continue
            
            for strategy_id in self.active_strategies:
                strategy = self.strategies.get(strategy_id)
                if strategy and strategy.active:
                    try:
                        signal = strategy.generate_signal(market_data, portfolio_data)
                        if signal:
                            all_signals.append(signal)
                            self.signal_history.append(signal)
                    except Exception as e:
                        logger.error(f"Error generating signal from {strategy_id}: {e}")
        
        # Keep only recent signal history
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
        
        return all_signals
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for all strategies"""
        performance = {}
        
        for strategy_id, strategy in self.strategies.items():
            # Get signals from this strategy
            strategy_signals = [s for s in self.signal_history if s.strategy == strategy.name]
            
            performance[strategy_id] = {
                'name': strategy.name,
                'active': strategy_id in self.active_strategies,
                'total_signals': len(strategy_signals),
                'recent_signals': len([s for s in strategy_signals if s.timestamp > datetime.now() - timedelta(days=7)]),
                'avg_confidence': np.mean([s.confidence for s in strategy_signals]) if strategy_signals else 0.0,
                'risk_level': strategy.get_risk_level(),
                'last_signal': strategy_signals[-1].timestamp.isoformat() if strategy_signals else None
            }
        
        return performance
    
    def get_consolidated_signal(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """Consolidate multiple signals into a single recommendation"""
        if not signals:
            return None
        
        # Group signals by symbol
        symbol_signals = {}
        for signal in signals:
            if signal.symbol not in symbol_signals:
                symbol_signals[signal.symbol] = []
            symbol_signals[signal.symbol].append(signal)
        
        # For now, return the signal with highest confidence
        # Could be enhanced with more sophisticated logic
        best_signal = max(signals, key=lambda s: s.confidence)
        return best_signal 