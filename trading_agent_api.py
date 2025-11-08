"""
Trading Agent API - Main API for the autonomous trading system
Combines all components: RAG, Trading, Portfolio Management, Strategies, and Simulations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
import asyncio
import json
import sys
import os

# Configure logging to debug.log
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logging_config import setup_logging
setup_logging('debug.log', logging.INFO)

# Import trading agent components
from trading_agent.agent_orchestrator import TradingAgent, create_trading_agent
from trading_agent.portfolio_manager import PortfolioManager
from trading_agent.strategy_engine import StrategyEngine
from trading_agent.simulation_engine import SimulationEngine, SimulationConfig, SimulationType

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ameron - Complete Trading Agent System",
    description="Autonomous AI-powered trading agent with RAG, portfolio management, and simulations",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global trading agent instance
trading_agent: Optional[TradingAgent] = None
simulation_engine = SimulationEngine()

# Pydantic models
class AgentConfig(BaseModel):
    profile: str = "balanced"  # conservative, balanced, aggressive
    initial_balance: float = 25000.0
    auto_execute: bool = False
    symbols: List[str] = ["BTC", "ETH"]
    strategies: List[str] = ["breakout", "sentiment"]

class LogEntry(BaseModel):
    level: str  # DEBUG, INFO, WARN, ERROR
    message: str
    category: Optional[str] = None
    metadata: Optional[Dict] = None

class TradeRequest(BaseModel):
    symbol: str
    side: str  # buy/sell
    quantity: float
    strategy: str = "manual"

class SimulationRequest(BaseModel):
    initial_balance: float = 10000.0
    duration_days: int = 60
    symbols: List[str] = ["BTC"]
    strategies: List[str] = ["breakout"]
    investor_profile: str = "balanced"

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the trading agent on startup"""
    global trading_agent
    logger.info("Starting Amiga Trading Agent System")
    
    # Initialize with default balanced profile
    trading_agent = create_trading_agent("balanced")
    logger.info("Trading agent initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global trading_agent
    if trading_agent and trading_agent.is_running:
        await trading_agent.stop_agent()
    logger.info("Trading agent system shutdown")

# Root and health endpoints
@app.get("/")
async def root():
    """API information and capabilities"""
    return {
        "name": "Ameron - Complete Trading Agent System",
        "version": "2.0.0",
        "description": "Autonomous AI-powered trading with RAG intelligence",
        "capabilities": [
            "Autonomous trading with multiple strategies",
            "AI-powered market analysis using RAG",
            "Real-time portfolio management",
            "Comprehensive backtesting and simulations",
            "Risk management and performance tracking",
            "Investor demonstrations and reporting"
        ],
        "endpoints": {
            "agent_control": "/agent/",
            "portfolio": "/portfolio/",
            "strategies": "/strategies/",
            "simulations": "/simulations/",
            "market_analysis": "/market/",
            "investor_demos": "/demo/"
        },
        "documentation": "/docs",
        "agent_status": "active" if trading_agent and trading_agent.is_running else "stopped"
    }

@app.get("/health")
async def health_check():
    """Comprehensive system health check"""
    global trading_agent
    
    # Check trading agent
    agent_status = "unknown"
    if trading_agent:
        agent_status = "running" if trading_agent.is_running else "stopped"
    
    # Check RAG engine
    rag_status = "unknown"
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        rag_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        rag_status = "unavailable"
    
    # Check trading API
    trading_api_status = "unknown"
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=5)
        trading_api_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        trading_api_status = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "trading_agent": agent_status,
            "rag_engine": rag_status,
            "trading_api": trading_api_status,
            "simulation_engine": "available",
            "portfolio_manager": "available"
        },
        "active_simulations": len(simulation_engine.active_simulations),
        "completed_simulations": len(simulation_engine.completed_simulations)
    }

# Agent Control Endpoints
@app.post("/agent/create")
async def create_agent(config: AgentConfig):
    """Create and configure a new trading agent"""
    global trading_agent
    
    try:
        # Stop existing agent if running
        if trading_agent and trading_agent.is_running:
            await trading_agent.stop_agent()
        
        # Create new agent with specified profile
        trading_agent = create_trading_agent(config.profile)
        
        # Update configuration
        agent_config = {
            'initial_balance': config.initial_balance,
            'auto_execute': config.auto_execute,
            'symbols': config.symbols,
            'active_strategies': config.strategies
        }
        trading_agent.update_config(agent_config)
        
        return {
            "agent_created": True,
            "profile": config.profile,
            "config": agent_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/start")
async def start_agent(background_tasks: BackgroundTasks):
    """Start the autonomous trading agent"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured. Create an agent first.")
    
    if trading_agent.is_running:
        raise HTTPException(status_code=400, detail="Agent is already running")
    
    try:
        # Start agent in background task
        async def run_agent():
            try:
                await trading_agent.start_agent()
            except Exception as e:
                logger.error(f"Agent runtime error: {e}")
                trading_agent.is_running = False
        
        # Create and schedule the background task
        import asyncio
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_agent())
        background_tasks.add_task(lambda: None)  # Placeholder for FastAPI background tasks
        
        return {
            "agent_started": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Autonomous trading agent started",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/stop")
async def stop_agent():
    """Stop the autonomous trading agent"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    if not trading_agent.is_running:
        raise HTTPException(status_code=400, detail="Agent is not running")
    
    try:
        await trading_agent.stop_agent()
        
        return {
            "agent_stopped": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Trading agent stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status")
async def get_agent_status():
    """Get comprehensive agent status and performance"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        status = trading_agent.get_agent_status()
        return {
            "agent_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Portfolio Management Endpoints
@app.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get current portfolio summary"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        summary = trading_agent.portfolio.get_portfolio_summary()
        return {
            "portfolio_summary": summary.__dict__,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/positions")
async def get_positions():
    """Get current portfolio positions"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        # Update positions with current prices
        trading_agent.portfolio.update_positions()
        
        positions = {}
        for symbol, position in trading_agent.portfolio.positions.items():
            positions[symbol] = position.__dict__
        
        return {
            "positions": positions,
            "positions_count": len(positions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio/trades")
async def get_trade_history():
    """Get trade history"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        trades = [trade.__dict__ for trade in trading_agent.portfolio.trades]
        
        return {
            "trades": trades,
            "total_trades": len(trades),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/execute-trade")
async def execute_manual_trade(trade_request: TradeRequest):
    """Execute a manual trade"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        from trading_agent.portfolio_manager import TradeType
        
        # Execute trade with Binance integration enabled
        trade = trading_agent.portfolio.execute_trade(
            symbol=trade_request.symbol,
            side=TradeType(trade_request.side.lower()),
            quantity=trade_request.quantity,
            strategy=trade_request.strategy,
            use_binance=True  # Enable Binance execution
        )
        
        # Convert trade to dict for JSON serialization
        trade_dict = {
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "side": trade.side.value,
            "quantity": trade.quantity,
            "price": trade.price,
            "value": trade.value,
            "timestamp": trade.timestamp.isoformat(),
            "status": trade.status.value,
            "strategy": trade.strategy,
            "fees": trade.fees,
            "notes": trade.notes,
            "binance_order_id": getattr(trade, 'binance_order_id', None)
        }
        
        return {
            "trade_executed": True,
            "trade": trade_dict,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as ve:
        # Handle validation errors (insufficient funds, etc.)
        logger.error(f"Trade validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Strategy Management Endpoints
@app.get("/strategies/available")
async def get_available_strategies():
    """Get all available trading strategies"""
    try:
        strategy_engine = StrategyEngine()
        performance = strategy_engine.get_strategy_performance()
        
        strategies = {
            "breakout": {
                "name": "Breakout Strategy",
                "description": "Trades on price breakouts above/below key levels",
                "risk_level": "medium",
                "best_for": "trending markets"
            },
            "sentiment": {
                "name": "Sentiment-Based Strategy", 
                "description": "Uses AI to analyze market sentiment from news",
                "risk_level": "high",
                "best_for": "news-driven markets"
            },
            "dca": {
                "name": "Dollar Cost Averaging",
                "description": "Systematic investment at regular intervals",
                "risk_level": "low",
                "best_for": "long-term investing"
            },
            "ai_powered": {
                "name": "AI-Powered Strategy",
                "description": "Advanced AI combining multiple data sources",
                "risk_level": "high",
                "best_for": "experienced investors"
            }
        }
        
        return {
            "available_strategies": strategies,
            "performance_data": performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/signals")
async def get_current_signals():
    """Get current trading signals from all active strategies"""
    global trading_agent
    
    if not trading_agent:
        raise HTTPException(status_code=400, detail="No agent configured")
    
    try:
        from dataclasses import asdict
        
        # Get current portfolio data
        portfolio_data = asdict(trading_agent.portfolio.get_portfolio_summary())
        
        # Generate signals
        signals = trading_agent.strategy_engine.generate_signals(
            trading_agent.config['symbols'],
            portfolio_data
        )
        
        return {
            "signals": [asdict(signal) for signal in signals],
            "signals_count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Simulation Endpoints
@app.post("/simulations/backtest")
async def run_backtest_simulation(request: SimulationRequest):
    """Run a comprehensive backtest simulation with status tracking"""
    try:
        # Use enhanced backtesting engine for better results
        import sys
        import os
        # Try to import from trading_agent directory
        try:
            from trading_agent.enhanced_backtesting import EnhancedBacktestingEngine, BacktestConfig, BacktestPeriod
        except ImportError:
            # Fallback: import from root directory
            sys.path.insert(0, os.path.dirname(__file__))
            from enhanced_backtesting import EnhancedBacktestingEngine, BacktestConfig, BacktestPeriod
        
        from datetime import datetime, timedelta
        
        # Create backtest config
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.duration_days)
        
        backtest_config = BacktestConfig(
            initial_balance=request.initial_balance,
            start_date=start_date,
            end_date=end_date,
            symbols=request.symbols,
            strategies=request.strategies,
            risk_level=request.investor_profile,
            max_positions=5,
            rebalance_frequency=BacktestPeriod.DAILY
        )
        
        logger.info(f"Starting backtest: {request.symbols} for {request.duration_days} days")
        
        # Run enhanced backtest
        backtest_engine = EnhancedBacktestingEngine()
        result = backtest_engine.run_backtest(backtest_config)
        
        # Generate report
        report = backtest_engine.generate_backtest_report(result)
        
        logger.info(f"Backtest completed: {result.total_return_percent:.2f}% return, {result.total_trades} trades")
        
        return {
            "backtest_completed": True,
            "status": "success",
            "simulation_results": result.to_dict(),
            "investor_report": report,
            "summary": {
                "return_percent": result.total_return_percent,
                "total_trades": result.total_trades,
                "win_rate": result.win_rate,
                "max_drawdown": result.max_drawdown,
                "sharpe_ratio": result.sharpe_ratio
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.get("/simulations/backtest/status")
async def get_backtest_status():
    """Get status of recent backtests"""
    try:
        from trading_agent.enhanced_backtesting import EnhancedBacktestingEngine
        backtest_engine = EnhancedBacktestingEngine()
        
        recent_results = backtest_engine.backtest_results[-5:] if backtest_engine.backtest_results else []
        
        return {
            "recent_backtests": [
                {
                    "completed_at": datetime.now().isoformat(),  # Would need to track actual completion time
                    "return_percent": r.total_return_percent,
                    "total_trades": r.total_trades,
                    "status": "completed"
                }
                for r in recent_results
            ],
            "total_backtests": len(backtest_engine.backtest_results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting backtest status: {e}")
        return {
            "recent_backtests": [],
            "total_backtests": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/simulations/demo/start")
async def start_investor_demo(request: SimulationRequest):
    """Start a live investor demonstration"""
    try:
        # Create demo config
        config = simulation_engine.create_demo_simulation(request.investor_profile)
        config.initial_balance = request.initial_balance
        config.symbols = request.symbols
        config.strategies = request.strategies
        
        # Start demo
        demo_id = simulation_engine.run_live_demo(config)
        
        return {
            "demo_started": True,
            "demo_id": demo_id,
            "config": config.__dict__,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulations/demo/{demo_id}/status")
async def get_demo_status(demo_id: str):
    """Get status of a running demonstration"""
    try:
        status = simulation_engine.get_demo_status(demo_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting demo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Analysis Endpoints
@app.get("/market/current")
async def get_current_market_data():
    """Get current market data and analysis"""
    try:
        from agent_browser.tools.market_data_agent import MarketDataAgent
        
        symbols = ["BTC", "ETH"]
        market_data = {}
        
        with MarketDataAgent() as agent:
            for symbol in symbols:
                if symbol == "BTC":
                    data = agent.scrape_coinmarketcap_bitcoin()
                else:
                    data = agent.scrape_tradingview_data(f"{symbol}USDT")
                
                if data.get('success'):
                    market_data[symbol] = {
                        'price': data.get('price'),
                        'change_percent': data.get('change_percent', 0),
                        'volume': data.get('volume', 'N/A'),
                        'source': data.get('source'),
                        'timestamp': datetime.now().isoformat()
                    }
        
        return {
            "market_data": market_data,
            "symbols_count": len(market_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/analysis")
async def get_ai_market_analysis():
    """Get AI-powered market analysis from RAG engine"""
    try:
        import requests
        
        analysis = {}
        
        # Get sentiment analysis
        try:
            response = requests.get("http://localhost:8000/sentiment", timeout=10)
            if response.status_code == 200:
                analysis['sentiment'] = response.json()
        except:
            analysis['sentiment'] = {"error": "Sentiment analysis unavailable"}
        
        # Get news summary
        try:
            response = requests.get("http://localhost:8000/summary", timeout=10)
            if response.status_code == 200:
                analysis['news_summary'] = response.json()
        except:
            analysis['news_summary'] = {"error": "News summary unavailable"}
        
        return {
            "ai_analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "analysis_sources": ["sentiment", "news_summary", "rag_engine"]
        }
        
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Investor Dashboard Endpoint
@app.post("/logs/frontend")
async def log_frontend_message(log_entry: LogEntry):
    """Receive and log frontend messages to debug.log"""
    try:
        log_level = getattr(logging, log_entry.level.upper(), logging.INFO)
        log_message = log_entry.message
        
        if log_entry.category:
            log_message = f"[{log_entry.category}] {log_message}"
        
        if log_entry.metadata:
            log_message += f" | Metadata: {log_entry.metadata}"
        
        logger.log(log_level, log_message)
        
        return {
            "logged": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error logging frontend message: {e}")
        return {
            "logged": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/header-data")
async def get_header_data():
    """Get header data (portfolio value, daily P&L) for frontend"""
    global trading_agent
    
    try:
        if trading_agent:
            portfolio_summary = trading_agent.portfolio.get_portfolio_summary()
            return {
                "portfolio_value": portfolio_summary.total_value,
                "daily_pnl": 0,  # Would need daily tracking
                "daily_pnl_percent": 0,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "portfolio_value": 0,
                "daily_pnl": 0,
                "daily_pnl_percent": 0,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting header data: {e}")
        return {
            "portfolio_value": 0,
            "daily_pnl": 0,
            "daily_pnl_percent": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/sidebar-data")
async def get_sidebar_data():
    """Get sidebar data (trades count, win rate) for frontend"""
    global trading_agent
    
    try:
        if trading_agent:
            agent_status = trading_agent.get_agent_status()
            portfolio = agent_status.get('portfolio', {})
            agent_info = agent_status.get('agent_info', {})
            
            return {
                "trades_count": agent_info.get('trade_count', 0),
                "win_rate": portfolio.get('win_rate', 0),
                "agent_running": agent_info.get('is_running', False),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "trades_count": 0,
                "win_rate": 0,
                "agent_running": False,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting sidebar data: {e}")
        return {
            "trades_count": 0,
            "win_rate": 0,
            "agent_running": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/dashboard/investor")
async def get_investor_dashboard():
    """Get comprehensive investor dashboard data"""
    global trading_agent
    
    try:
        dashboard_data = {
            "system_status": {
                "agent_running": trading_agent.is_running if trading_agent else False,
                "last_update": trading_agent.last_update.isoformat() if trading_agent and trading_agent.last_update else None,
                "uptime_hours": 0
            },
            "portfolio_summary": None,
            "recent_performance": [],
            "active_strategies": [],
            "current_signals": [],
            "market_data": {},
            "ai_analysis": {},
            "risk_metrics": {}
        }
        
        if trading_agent:
            # Portfolio data
            portfolio_summary = trading_agent.portfolio.get_portfolio_summary()
            dashboard_data["portfolio_summary"] = portfolio_summary.__dict__
            
            # Performance history
            dashboard_data["recent_performance"] = trading_agent.performance_history[-10:]
            
            # Active strategies
            dashboard_data["active_strategies"] = trading_agent.strategy_engine.active_strategies
            
            # Risk metrics
            dashboard_data["risk_metrics"] = trading_agent.portfolio.get_risk_metrics()
        
        # Market data
        try:
            market_response = await get_current_market_data()
            dashboard_data["market_data"] = market_response["market_data"]
        except:
            pass
        
        # AI analysis
        try:
            analysis_response = await get_ai_market_analysis()
            dashboard_data["ai_analysis"] = analysis_response["ai_analysis"]
        except:
            pass
        
        return {
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 