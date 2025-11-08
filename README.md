# Ameron - Autonomous AI Trading System

A comprehensive, production-ready AI-powered trading system featuring RAG (Retrieval-Augmented Generation), autonomous browser agents, and real-time market analysis.

## 🚀 Overview

Ameron is a sophisticated trading platform that combines multiple AI technologies to create an autonomous trading system:

- **RAG Engine**: Real-time market news analysis and sentiment detection
- **Trading Agent**: Autonomous trading with risk management
- **Browser Agent**: Web scraping and market data collection
- **Frontend**: Modern React/TypeScript dashboard
- **API Layer**: Secure REST APIs with OAuth2 authentication

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Engine    │    │   Trading API   │    │ Trading Agent   │
│   (Port 8000)   │    │   (Port 8001)   │    │   (Port 8003)   │
│                 │    │                 │    │                 │
│ • AI Analysis   │◄──►│ • OAuth2 Auth   │◄──►│ • Orchestration │
│ • Market Data   │    │ • Secure Trades │    │ • Simulations   │
│ • Sentiment     │    │ • Portfolio API │    │ • Strategies    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Agent Browser   │
                    │                 │
                    │ • Web Scraping  │
                    │ • Market News   │
                    │ • Data Mining   │
                    └─────────────────┘
```

## 📋 Features

### Core Components

- **🤖 AI-Powered Analysis**: RAG pipeline for real-time market news analysis
- **📊 Autonomous Trading**: Self-executing trading strategies with risk management
- **🌐 Web Scraping**: Browser automation for market data collection
- **🔐 Secure APIs**: OAuth2 authentication and role-based access control
- **📱 Modern Frontend**: React/TypeScript dashboard with real-time updates
- **📈 Portfolio Management**: Comprehensive position tracking and P&L analysis
- **🎯 Strategy Engine**: Multiple trading strategies with backtesting
- **🔄 Real-time Data**: Live market data integration

### Trading Features

- **Risk Management**: Stop-loss, position limits, portfolio optimization
- **Multi-Strategy Support**: Breakout, sentiment, and custom strategies
- **Simulation Engine**: Backtesting and paper trading capabilities
- **Market Sentiment Analysis**: AI-powered sentiment detection
- **Portfolio Analytics**: Performance tracking and reporting

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**: Core application logic
- **FastAPI**: High-performance API framework
- **OpenAI GPT**: LLM for analysis and decision making
- **Pinecone**: Vector database for RAG
- **Selenium**: Browser automation
- **SQLAlchemy**: Database ORM (planned)

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: State management
- **Recharts**: Data visualization
- **Vite**: Fast build tool

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration
- **OAuth2**: Authentication
- **WebSocket**: Real-time communication

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API Key
- Pinecone API Key (optional)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd amiga-trader
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone Configuration (optional)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=financial-news

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Trading Configuration
BINANCE_API_KEY=your_binance_api_key_here
```

### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start RAG Engine
uvicorn rag_engine.api_service:app --reload --port 8000

# Start Trading API
uvicorn trading_api.main:app --reload --port 8001

# Start Trading Agent
python trading_agent/agent_orchestrator.py
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Docker Deployment (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 API Documentation

### Service Endpoints

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| RAG Engine | 8000 | http://localhost:8000 | AI analysis and news processing |
| Trading API | 8001 | http://localhost:8001 | Secure trading operations |
| Frontend | 3000 | http://localhost:3000 | React dashboard |

### Key API Endpoints

#### RAG Engine (Port 8000)
- `POST /ingest` - Ingest financial news from RSS feeds
- `POST /query` - Query the RAG system
- `GET /sentiment` - Analyze market sentiment
- `GET /summary` - Summarize market news

#### Trading API (Port 8001)
- `POST /token` - OAuth2 authentication
- `POST /trade` - Execute trades
- `GET /trade/history` - Get trade history
- `GET /strategies` - List trading strategies

## 🎯 Usage Examples

### 1. Market Analysis

```python
# Query RAG system for market insights
import requests

response = requests.post("http://localhost:8000/query", 
    json={"question": "What is the latest Bitcoin news?"})
print(response.json())
```

### 2. Execute Trade

```python
# Authenticate and execute trade
import requests

# Login
auth_response = requests.post("http://localhost:8001/token", 
    data={"username": "trader1", "password": "password123"})
token = auth_response.json()["access_token"]

# Execute trade
headers = {"Authorization": f"Bearer {token}"}
trade_response = requests.post("http://localhost:8001/trade",
    json={
        "symbol": "BTC",
        "side": "buy",
        "quantity": 0.1,
        "order_type": "market"
    },
    headers=headers)
```

### 3. Start Trading Agent

```python
from trading_agent.agent_orchestrator import create_trading_agent

# Create and start agent
agent = create_trading_agent(profile="balanced")
await agent.start_agent()
```

## 🔧 Configuration

### Trading Agent Configuration

```python
config = {
    'initial_balance': 10000.0,
    'max_position_size': 0.1,  # 10% max per position
    'symbols': ['BTC', 'ETH'],
    'active_strategies': ['breakout', 'sentiment'],
    'risk_management': {
        'max_daily_loss': 0.05,
        'max_total_loss': 0.20,
        'stop_loss_percent': 0.05,
        'take_profit_percent': 0.15
    }
}
```

### RAG Pipeline Configuration

```python
# rag_engine/config.py
RAGConfig = {
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'OPENAI_MODEL': 'gpt-3.5-turbo',
    'CHUNK_SIZE': 1000,
    'CHUNK_OVERLAP': 200,
    'SIMILARITY_THRESHOLD': 0.7
}
```

## 📊 Project Structure

```
amiga-trader/
├── agent_browser/          # Browser automation
│   ├── agent_core/        # Core planning logic
│   └── tools/             # Web scraping tools
├── auth_service/          # Authentication service
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/        # Page components
│   │   ├── stores/       # State management
│   │   └── services/     # API services
├── rag_engine/           # RAG pipeline
│   ├── ingest/          # Data ingestion
│   ├── llm/             # LLM integration
│   └── vector_store/    # Vector database
├── trading_agent/       # Trading logic
│   ├── portfolio_manager.py
│   ├── strategy_engine.py
│   └── simulation_engine.py
├── trading_api/         # Trading API
└── trading_bot/         # Legacy trading bot
```

## 🧪 Testing

### Run Tests

```bash
# Test RAG pipeline
python test_rag.py

# Test trading system
python test_trading_api.py

# Test market agent
python test_market_agent.py

# Run system test
python test_system.py
```

### Demo Mode

```bash
# Start demo showcase
python demo_showcase.py

# Run investor demo
python start_investor_demo.py
```

## 🔒 Security

- **OAuth2 Authentication**: Secure token-based authentication
- **Role-Based Access**: Different permission levels (trader, admin, viewer)
- **API Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error responses

## 📈 Performance

- **Real-time Processing**: Sub-second response times
- **Scalable Architecture**: Microservices design
- **Caching**: Redis integration (planned)
- **Load Balancing**: Horizontal scaling support
- **Monitoring**: Health checks and metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check `SETUP.md` for detailed setup instructions
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join community discussions

## 🚀 Roadmap

- [ ] Real broker integration (Binance, Coinbase Pro)
- [ ] Advanced ML models for prediction
- [ ] Mobile app development
- [ ] Cloud deployment (AWS/GCP)
- [ ] Advanced risk management
- [ ] Social trading features

---

**Current Project Completion: 85%**

This system is production-ready for paper trading and simulation environments. Real money trading requires additional compliance and regulatory considerations.
