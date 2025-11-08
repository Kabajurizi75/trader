# Browser Agent - Autonomous Market Data Scraping

## 🚀 Overview

The Browser Agent is an autonomous web scraping system that uses Selenium + ChromeDriver to collect real-time market data from various sources including CoinMarketCap and TradingView.

## ✨ Features

### MarketDataAgent Class
- **Headless Chrome**: Docker-compatible browser automation  
- **Multi-source Scraping**: CoinMarketCap + TradingView integration
- **Anti-detection**: User agent spoofing and automation hiding
- **Error Handling**: Comprehensive timeout, CAPTCHA, and selector fallbacks
- **Context Manager**: Automatic resource cleanup
- **Structured Output**: Consistent JSON responses with metadata

## 🎯 Quick Usage

### Basic Bitcoin Price Check
```python
from agent_browser.tools.market_data_agent import get_bitcoin_price

price_data = get_bitcoin_price()
print(f"Bitcoin: ${price_data['price']:,.2f}")
```

### Comprehensive Data Collection  
```python
from agent_browser.tools.market_data_agent import MarketDataAgent

with MarketDataAgent(headless=True) as agent:
    btc_data = agent.scrape_coinmarketcap_bitcoin()
    tv_data = agent.scrape_tradingview_data("BTCUSDT")
    comprehensive = agent.get_comprehensive_data(['BTC'])
```

### Task-based Approach
```python
from agent_browser.agent_core.planner import plan_tasks, execute_task_plan

tasks = plan_tasks("Get Bitcoin price and market sentiment")
results = execute_task_plan(tasks)
```

## 🛠️ Setup

### Local Development
```bash
# Install dependencies
pip install selenium webdriver-manager undetected-chromedriver

# Test installation
python test_market_agent.py
```

### Docker Setup
```bash
# Build and run
docker-compose up amiga-trader-api

# Run tests  
docker-compose --profile testing up browser-agent-test
```

## 📊 API Endpoints

- `GET /market-data/bitcoin` - Bitcoin data from CoinMarketCap
- `GET /market-data/tradingview/{symbol}` - TradingView data
- `POST /market-data/comprehensive` - Multi-source data
- `POST /agent/plan-tasks` - Plan tasks based on goal
- `POST /agent/execute-plan` - Plan and execute tasks

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_market_agent.py
```

Built with ❤️ for the Ameron ecosystem. 