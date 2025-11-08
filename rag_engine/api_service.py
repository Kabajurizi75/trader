from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime

from .rag_pipeline import RAGPipeline
from .config import RAGConfig

# Configure logging to debug.log
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logging
setup_logging('debug.log', logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ameron RAG API",
    description="RAG API for Financial Market Analysis",
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

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict]
    timestamp: str
    processing_time: Optional[float] = None

class LogEntry(BaseModel):
    level: str  # DEBUG, INFO, WARN, ERROR
    message: str
    category: Optional[str] = None
    metadata: Optional[Dict] = None

class IngestResponse(BaseModel):
    success: bool
    message: str
    articles_processed: Optional[int] = None
    documents_stored: Optional[int] = None
    timestamp: str

class SentimentResponse(BaseModel):
    sentiment: str
    analysis: str
    confidence: str
    sources_count: int
    timestamp: str

class NewsSummaryResponse(BaseModel):
    summary: str
    key_topics: List[str]
    sources_count: int
    timeframe: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    pipeline_ready: bool
    vector_store_connected: bool
    llm_available: bool
    timestamp: str

class StatsResponse(BaseModel):
    vector_store_stats: Dict
    pipeline_config: Dict
    timestamp: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health"""
    try:
        stats = rag_pipeline.get_pipeline_stats()
        return HealthResponse(
            status="healthy",
            pipeline_ready=stats.get('vector_store', {}).get('error') is None,
            vector_store_connected=stats.get('vector_store', {}).get('error') is None,
            llm_available=stats.get('llm', {}).get('error') is None,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            pipeline_ready=False,
            vector_store_connected=False,
            llm_available=False,
            timestamp=datetime.now().isoformat()
        )

# Ingest financial news
@app.post("/ingest", response_model=IngestResponse)
async def ingest_news(background_tasks: BackgroundTasks):
    """Ingest financial news from RSS feeds"""
    try:
        start_time = datetime.now()
        
        # Run ingestion in background
        success = rag_pipeline.ingest_and_store()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            return IngestResponse(
                success=True,
                message="News ingested successfully",
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="Ingestion failed")
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query the RAG system
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system - Enhanced for clearer responses"""
    try:
        start_time = datetime.now()
        
        # Process query with enhanced context
        result = rag_pipeline.query(request.question, top_k=request.top_k)
        
        # Ensure answer is clear and comprehensive
        answer = result.get('answer', '')
        if not answer or len(answer) < 20:
            answer = "I couldn't find enough information to provide a comprehensive answer. Please try rephrasing your question or asking about a different topic."
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Query processed: '{request.question[:50]}...' - {len(answer)} chars - {processing_time:.2f}s")
        
        return QueryResponse(
            question=result.get('question', request.question),
            answer=answer,
            sources=result.get('sources', []),
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

# Analyze market sentiment
@app.get("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment():
    """Analyze market sentiment"""
    try:
        start_time = datetime.now()
        
        sentiment_result = rag_pipeline.analyze_market_sentiment()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SentimentResponse(
            sentiment=sentiment_result['sentiment'],
            analysis=sentiment_result['analysis'],
            confidence=sentiment_result['confidence'],
            sources_count=sentiment_result.get('sources_count', 0),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Summarize market news
@app.get("/summary", response_model=NewsSummaryResponse)
async def summarize_news(hours_back: int = 24):
    """Summarize market news"""
    try:
        start_time = datetime.now()
        
        summary_result = rag_pipeline.summarize_market_news(hours_back)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return NewsSummaryResponse(
            summary=summary_result['summary'],
            key_topics=summary_result['key_topics'],
            sources_count=summary_result['sources_count'],
            timeframe=summary_result['timeframe'],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"News summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get system statistics
@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics and configuration"""
    try:
        stats = rag_pipeline.get_pipeline_stats()
        
        return StatsResponse(
            vector_store_stats=stats.get('vector_store', {}),
            pipeline_config={
                'embedding_model': stats.get('embedding_model', ''),
                'llm_model': stats.get('llm_model', ''),
                'rss_feeds_count': stats.get('rss_feeds_count', 0),
                'chunk_size': stats.get('chunk_size', 0),
                'chunk_overlap': stats.get('chunk_overlap', 0)
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get available RSS feeds
@app.get("/feeds")
async def get_feeds():
    """Get list of configured RSS feeds"""
    try:
        config = RAGConfig()
        return {
            "feeds": config.RSS_FEEDS,
            "count": len(config.RSS_FEEDS),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Feeds retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Frontend logging endpoint
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

# Simple query endpoint (GET for easy testing)
@app.get("/ask")
async def ask_question(q: str):
    """Simple GET endpoint for questions - Enhanced for clearer responses"""
    try:
        result = rag_pipeline.query(q)
        answer = result.get('answer', '')
        
        # Ensure answer is clear
        if not answer or len(answer) < 20:
            answer = "I couldn't find enough information to provide a comprehensive answer. Please try rephrasing your question."
        
        logger.info(f"Simple query: '{q[:50]}...' - {len(answer)} chars")
        
        return {
            "question": q,
            "answer": answer,
            "sources_count": len(result.get('sources', [])),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Simple query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

# Market data scraping endpoints
@app.get("/market-data/bitcoin")
async def get_bitcoin_data():
    """Get Bitcoin market data from CoinMarketCap"""
    try:
        from agent_browser.tools.market_data_agent import MarketDataAgent
        
        with MarketDataAgent() as agent:
            result = agent.scrape_coinmarketcap_bitcoin()
            
        return {
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bitcoin data scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-data/tradingview/{symbol}")
async def get_tradingview_data(symbol: str):
    """Get trading data from TradingView"""
    try:
        from agent_browser.tools.market_data_agent import MarketDataAgent
        
        with MarketDataAgent() as agent:
            result = agent.scrape_tradingview_data(symbol)
            
        return {
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"TradingView data scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/market-data/comprehensive")
async def get_comprehensive_market_data(symbols: List[str] = ['BTC']):
    """Get comprehensive market data from multiple sources"""
    try:
        from agent_browser.tools.market_data_agent import MarketDataAgent
        
        with MarketDataAgent() as agent:
            result = agent.get_comprehensive_data(symbols)
            
        return result
        
    except Exception as e:
        logger.error(f"Comprehensive market data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/plan-tasks")
async def plan_agent_tasks(goal: str):
    """Plan tasks based on a goal using the agent planner"""
    try:
        from agent_browser.agent_core.planner import plan_tasks
        
        tasks = plan_tasks(goal)
        
        return {
            "goal": goal,
            "tasks": tasks,
            "task_count": len(tasks),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task planning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/execute-plan")
async def execute_agent_plan(goal: str):
    """Plan and execute tasks based on a goal"""
    try:
        from agent_browser.agent_core.planner import plan_tasks, execute_task_plan
        
        # Plan tasks
        tasks = plan_tasks(goal)
        
        # Execute tasks
        results = execute_task_plan(tasks)
        
        return {
            "goal": goal,
            "execution_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "message": "Ameron RAG API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest",
            "query": "/query",
            "sentiment": "/sentiment",
            "summary": "/summary",
            "stats": "/stats",
            "feeds": "/feeds",
            "ask": "/ask?q=your_question",
            "market_data": {
                "bitcoin": "/market-data/bitcoin",
                "tradingview": "/market-data/tradingview/{symbol}",
                "comprehensive": "/market-data/comprehensive"
            },
            "agent": {
                "plan_tasks": "/agent/plan-tasks",
                "execute_plan": "/agent/execute-plan"
            }
        },
        "docs": "/docs",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 