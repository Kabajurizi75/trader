"""
Demo API for Trading Agent
Provides investor-facing endpoints for demonstrations and simulations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime
import asyncio
import json

from .portfolio_manager import PortfolioManager
from .strategy_engine import StrategyEngine
from .simulation_engine import SimulationEngine, SimulationConfig, SimulationType

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ameron - Investor Demo API",
    description="Interactive demonstrations and simulations for potential investors",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
simulation_engine = SimulationEngine()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            'market': [],
            'agent': [],
            'portfolio': []
        }
    
    async def connect(self, websocket: WebSocket, connection_type: str):
        await websocket.accept()
        if connection_type in self.active_connections:
            self.active_connections[connection_type].append(websocket)
            logger.info(f"New {connection_type} WebSocket connection")
    
    def disconnect(self, websocket: WebSocket, connection_type: str):
        if connection_type in self.active_connections:
            try:
                self.active_connections[connection_type].remove(websocket)
                logger.info(f"{connection_type} WebSocket connection closed")
            except ValueError:
                pass
    
    async def broadcast(self, message: Dict, connection_type: str):
        if connection_type in self.active_connections:
            for connection in self.active_connections[connection_type]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_type}: {e}")

manager = ConnectionManager()

# Helper functions for WebSocket data
async def get_current_market_data():
    """Get current market data for WebSocket updates"""
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
        # Return mock data for demo
        return {
            "market_data": {
                "BTC": {"price": 50000.0, "change_percent": 0.5, "volume": "1B", "timestamp": datetime.now().isoformat()},
                "ETH": {"price": 3000.0, "change_percent": -0.2, "volume": "500M", "timestamp": datetime.now().isoformat()}
            },
            "symbols_count": 2,
            "timestamp": datetime.now().isoformat()
        }

# WebSocket endpoints
@app.websocket("/market")
async def websocket_market(websocket: WebSocket):
    await manager.connect(websocket, "market")
    try:
        while True:
            # Send market data periodically
            market_data = await get_current_market_data()
            await websocket.send_text(json.dumps({
                "type": "market_data",
                "payload": market_data
            }))
            await asyncio.sleep(5)  # Send updates every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "market")
    except Exception as e:
        logger.error(f"Market WebSocket error: {e}")
        manager.disconnect(websocket, "market")

@app.websocket("/agent")
async def websocket_agent(websocket: WebSocket):
    await manager.connect(websocket, "agent")
    try:
        while True:
            # Send agent status updates
            agent_status = {
                "type": "agent_status",
                "payload": {
                    "status": "demo_mode",
                    "active_demos": len(simulation_engine.active_simulations),
                    "timestamp": datetime.now().isoformat()
                }
            }
            await websocket.send_text(json.dumps(agent_status))
            await asyncio.sleep(10)  # Send updates every 10 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agent")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
        manager.disconnect(websocket, "agent")

@app.websocket("/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    await manager.connect(websocket, "portfolio")
    try:
        while True:
            # Send portfolio updates
            portfolio_data = {
                "type": "portfolio_update",
                "payload": {
                    "total_value": 25000.0,  # Demo value
                    "daily_pnl": 0.0,
                    "positions": [],
                    "timestamp": datetime.now().isoformat()
                }
            }
            await websocket.send_text(json.dumps(portfolio_data))
            await asyncio.sleep(15)  # Send updates every 15 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "portfolio")
    except Exception as e:
        logger.error(f"Portfolio WebSocket error: {e}")
        manager.disconnect(websocket, "portfolio")

# Pydantic models
class InvestorProfile(BaseModel):
    risk_tolerance: str = "balanced"  # conservative, balanced, aggressive
    investment_amount: float = 25000.0
    investment_horizon: str = "medium"  # short, medium, long
    experience_level: str = "intermediate"  # beginner, intermediate, advanced
    preferred_assets: List[str] = ["BTC", "ETH"]

class SimulationRequest(BaseModel):
    investor_profile: InvestorProfile
    simulation_duration_days: int = 60
    strategies: List[str] = ["breakout", "sentiment"]
    include_ai_analysis: bool = True

class LiveDemoRequest(BaseModel):
    investor_profile: InvestorProfile
    demo_duration_minutes: int = 30
    auto_execute_trades: bool = True

class BacktestRequest(BaseModel):
    initial_balance: float = 10000.0
    duration_days: int = 90
    symbols: List[str] = ["BTC"]
    strategies: List[str] = ["breakout"]
    risk_level: str = "medium"

# API Endpoints

@app.get("/")
async def root():
    """API information and available endpoints"""
    return {
        "name": "Ameron - Investor Demo API",
        "version": "1.0.0",
        "description": "Interactive trading agent demonstrations for investors",
        "endpoints": {
            "demos": "/demo/",
            "simulations": "/simulation/",
            "backtests": "/backtest/",
            "strategies": "/strategies/",
            "market_data": "/market/"
        },
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_demos": len(simulation_engine.active_simulations),
        "completed_simulations": len(simulation_engine.completed_simulations)
    }

# Demo Endpoints

@app.post("/demo/start")
async def start_live_demo(request: LiveDemoRequest):
    """Start a live trading demonstration"""
    try:
        # Create simulation config based on investor profile
        config = _create_config_from_profile(
            request.investor_profile, 
            request.demo_duration_minutes // 1440 or 1  # Convert to days
        )
        config.simulation_type = SimulationType.LIVE_DEMO
        
        # Start the demo
        demo_id = simulation_engine.run_live_demo(config)
        
        return {
            "demo_id": demo_id,
            "status": "started",
            "config": config.__dict__,
            "estimated_duration_minutes": request.demo_duration_minutes,
            "message": "Live demo started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting live demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo/{demo_id}/status")
async def get_demo_status(demo_id: str):
    """Get current status of a live demo"""
    try:
        status = simulation_engine.get_demo_status(demo_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting demo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/demo/{demo_id}/update")
async def update_demo(demo_id: str):
    """Manually trigger demo update with current market data"""
    try:
        status = simulation_engine.update_live_demo(demo_id)
        return {
            "updated": True,
            "timestamp": datetime.now().isoformat(),
            "demo_status": status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/demo/{demo_id}/stop")
async def stop_demo(demo_id: str):
    """Stop a live demo and get final results"""
    try:
        result = simulation_engine.stop_demo(demo_id)
        investor_report = simulation_engine.generate_investor_report(result)
        
        return {
            "demo_stopped": True,
            "final_results": result.__dict__,
            "investor_report": investor_report,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo/active")
async def list_active_demos():
    """List all active demonstrations"""
    return {
        "active_demos": list(simulation_engine.active_simulations.keys()),
        "count": len(simulation_engine.active_simulations),
        "timestamp": datetime.now().isoformat()
    }

# Simulation Endpoints

@app.post("/simulation/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a comprehensive backtest simulation"""
    try:
        config = SimulationConfig(
            simulation_type=SimulationType.BACKTEST,
            initial_balance=request.initial_balance,
            duration_days=request.duration_days,
            symbols=request.symbols,
            strategies=request.strategies,
            risk_level=request.risk_level
        )
        
        # Run backtest
        result = simulation_engine.run_backtest(config)
        investor_report = simulation_engine.generate_investor_report(result)
        
        return {
            "backtest_completed": True,
            "simulation_results": result.__dict__,
            "investor_report": investor_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulation/quick-demo")
async def quick_demo_simulation(request: SimulationRequest):
    """Run a quick demonstration simulation based on investor profile"""
    try:
        # Create config from investor profile
        config = _create_config_from_profile(
            request.investor_profile,
            request.simulation_duration_days
        )
        config.strategies = request.strategies
        
        # Run simulation
        result = simulation_engine.run_backtest(config)
        investor_report = simulation_engine.generate_investor_report(result)
        
        return {
            "simulation_completed": True,
            "investor_profile": request.investor_profile.__dict__,
            "simulation_results": result.__dict__,
            "investor_report": investor_report,
            "ai_analysis_included": request.include_ai_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running quick demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulation/results")
async def get_simulation_results():
    """Get all completed simulation results"""
    return {
        "completed_simulations": len(simulation_engine.completed_simulations),
        "results": [sim.__dict__ for sim in simulation_engine.completed_simulations[-10:]],  # Last 10
        "timestamp": datetime.now().isoformat()
    }

# Strategy Endpoints

@app.get("/strategies/available")
async def get_available_strategies():
    """Get list of available trading strategies"""
    strategy_engine = StrategyEngine()
    performance = strategy_engine.get_strategy_performance()
    
    strategies = {
        "breakout": {
            "name": "Breakout Strategy",
            "description": "Trades on price breakouts above/below key levels",
            "risk_level": "medium",
            "best_for": "trending markets",
            "parameters": ["breakout_threshold", "stop_loss", "take_profit"]
        },
        "sentiment": {
            "name": "Sentiment-Based Strategy", 
            "description": "Uses AI to analyze market sentiment from news",
            "risk_level": "high",
            "best_for": "news-driven markets",
            "parameters": ["sentiment_threshold", "news_lookback_hours"]
        },
        "dca": {
            "name": "Dollar Cost Averaging",
            "description": "Systematic investment at regular intervals",
            "risk_level": "low",
            "best_for": "long-term investing",
            "parameters": ["investment_amount", "frequency_hours"]
        },
        "ai_powered": {
            "name": "AI-Powered Strategy",
            "description": "Advanced AI combining multiple data sources",
            "risk_level": "high",
            "best_for": "experienced investors",
            "parameters": ["ai_confidence_threshold", "max_position_size"]
        }
    }
    
    return {
        "available_strategies": strategies,
        "performance_data": performance,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/strategies/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str):
    """Get detailed performance data for a specific strategy"""
    strategy_engine = StrategyEngine()
    performance = strategy_engine.get_strategy_performance()
    
    if strategy_id not in performance:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
    
    return {
        "strategy_id": strategy_id,
        "performance": performance[strategy_id],
        "timestamp": datetime.now().isoformat()
    }

# Market Data Endpoints

@app.get("/market/current")
async def get_current_market_data_rest():
    """Get current market data for all supported symbols"""
    try:
        return await get_current_market_data()
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/analysis")
async def get_market_analysis():
    """Get AI-powered market analysis"""
    try:
        import requests
        
        # Get sentiment and news analysis from RAG engine
        analysis = {}
        
        try:
            sentiment_response = requests.get("http://localhost:8000/sentiment", timeout=10)
            if sentiment_response.status_code == 200:
                analysis['sentiment'] = sentiment_response.json()
        except:
            analysis['sentiment'] = {"error": "Sentiment analysis unavailable"}
        
        try:
            summary_response = requests.get("http://localhost:8000/summary", timeout=10)
            if summary_response.status_code == 200:
                analysis['news_summary'] = summary_response.json()
        except:
            analysis['news_summary'] = {"error": "News summary unavailable"}
        
        return {
            "market_analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "analysis_sources": ["sentiment", "news_summary"]
        }
        
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Investor Profile Endpoints

@app.post("/profile/recommend-strategies")
async def recommend_strategies(profile: InvestorProfile):
    """Recommend strategies based on investor profile"""
    recommendations = _get_strategy_recommendations(profile)
    
    return {
        "investor_profile": profile.__dict__,
        "recommended_strategies": recommendations,
        "explanation": _explain_recommendations(profile, recommendations),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/profile/risk-assessment")
async def assess_risk_profile(profile: InvestorProfile):
    """Assess risk profile and provide recommendations"""
    risk_score = _calculate_investor_risk_score(profile)
    
    return {
        "investor_profile": profile.__dict__,
        "risk_score": risk_score,
        "risk_level": _get_risk_level_from_score(risk_score),
        "recommendations": _get_risk_based_recommendations(risk_score),
        "timestamp": datetime.now().isoformat()
    }

# Helper Functions

def _create_config_from_profile(profile: InvestorProfile, duration_days: int) -> SimulationConfig:
    """Create simulation config from investor profile"""
    
    # Map risk tolerance to strategies
    strategy_mapping = {
        "conservative": ["dca"],
        "balanced": ["breakout", "sentiment"],
        "aggressive": ["ai_powered", "breakout"]
    }
    
    # Map experience level to risk settings
    risk_mapping = {
        "beginner": "low",
        "intermediate": "medium", 
        "advanced": "high"
    }
    
    return SimulationConfig(
        simulation_type=SimulationType.BACKTEST,
        initial_balance=profile.investment_amount,
        duration_days=duration_days,
        symbols=profile.preferred_assets,
        strategies=strategy_mapping.get(profile.risk_tolerance, ["breakout"]),
        risk_level=risk_mapping.get(profile.experience_level, "medium"),
        max_positions=3 if profile.risk_tolerance == "conservative" else 5
    )

def _get_strategy_recommendations(profile: InvestorProfile) -> List[Dict]:
    """Get strategy recommendations based on investor profile"""
    recommendations = []
    
    if profile.risk_tolerance == "conservative":
        recommendations.append({
            "strategy": "dca",
            "weight": 0.7,
            "reason": "Low risk, suitable for conservative investors"
        })
        recommendations.append({
            "strategy": "breakout",
            "weight": 0.3,
            "reason": "Moderate growth potential with controlled risk"
        })
    
    elif profile.risk_tolerance == "balanced":
        recommendations.append({
            "strategy": "breakout",
            "weight": 0.4,
            "reason": "Good balance of risk and return"
        })
        recommendations.append({
            "strategy": "sentiment",
            "weight": 0.4,
            "reason": "AI-powered insights for better timing"
        })
        recommendations.append({
            "strategy": "dca",
            "weight": 0.2,
            "reason": "Stability component"
        })
    
    else:  # aggressive
        recommendations.append({
            "strategy": "ai_powered",
            "weight": 0.5,
            "reason": "Maximum AI capabilities for high returns"
        })
        recommendations.append({
            "strategy": "breakout",
            "weight": 0.3,
            "reason": "Momentum trading for quick gains"
        })
        recommendations.append({
            "strategy": "sentiment",
            "weight": 0.2,
            "reason": "News-driven opportunities"
        })
    
    return recommendations

def _explain_recommendations(profile: InvestorProfile, recommendations: List[Dict]) -> str:
    """Explain strategy recommendations"""
    explanations = []
    
    for rec in recommendations:
        explanations.append(f"{rec['strategy']} ({rec['weight']*100:.0f}%): {rec['reason']}")
    
    base_explanation = f"Based on your {profile.risk_tolerance} risk tolerance and {profile.experience_level} experience level, we recommend: "
    
    return base_explanation + "; ".join(explanations)

def _calculate_investor_risk_score(profile: InvestorProfile) -> int:
    """Calculate risk score from 1-10 based on investor profile"""
    score = 5  # Base score
    
    # Risk tolerance
    if profile.risk_tolerance == "conservative":
        score -= 2
    elif profile.risk_tolerance == "aggressive":
        score += 3
    
    # Experience level
    if profile.experience_level == "beginner":
        score -= 1
    elif profile.experience_level == "advanced":
        score += 2
    
    # Investment horizon
    if profile.investment_horizon == "short":
        score += 1
    elif profile.investment_horizon == "long":
        score -= 1
    
    return min(max(score, 1), 10)

def _get_risk_level_from_score(score: int) -> str:
    """Convert risk score to risk level"""
    if score <= 3:
        return "LOW"
    elif score <= 6:
        return "MEDIUM"
    else:
        return "HIGH"

def _get_risk_based_recommendations(risk_score: int) -> List[str]:
    """Get recommendations based on risk score"""
    if risk_score <= 3:
        return [
            "Focus on Dollar Cost Averaging strategy",
            "Limit position sizes to 2-3% of portfolio",
            "Consider longer investment horizons",
            "Avoid high-volatility strategies"
        ]
    elif risk_score <= 6:
        return [
            "Balance between growth and stability",
            "Use breakout and sentiment strategies",
            "Position sizes up to 5% of portfolio",
            "Monitor risk metrics regularly"
        ]
    else:
        return [
            "Leverage AI-powered strategies for maximum returns",
            "Higher position sizes acceptable (up to 10%)",
            "Active trading with multiple strategies",
            "Accept higher volatility for growth potential"
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 