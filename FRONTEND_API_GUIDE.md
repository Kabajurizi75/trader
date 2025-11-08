# Frontend API Integration Guide

## Fixed Issues

### 1. Binance Import Errors - FIXED ✅
All Binance imports now use the local `trading_bot/api/binance.py` module instead of the installed package.

### 2. Backtesting Status - NEW ENDPOINTS ✅
- `GET /simulations/backtest/status` - Check recent backtest status
- `POST /simulations/backtest` - Now returns detailed status and summary

### 3. Header & Sidebar Data - NEW ENDPOINTS ✅
Use these endpoints to fetch real data:

#### Header Data (Portfolio Value, Daily P&L)
```
GET http://localhost:8001/dashboard/header-data
GET http://localhost:8003/dashboard/header-data
```

Response:
```json
{
  "portfolio_value": 25000.0,
  "daily_pnl": 125.50,
  "daily_pnl_percent": 0.5,
  "timestamp": "2025-11-08T14:20:00"
}
```

#### Sidebar Data (Trades Count, Win Rate)
```
GET http://localhost:8001/dashboard/sidebar-data
GET http://localhost:8003/dashboard/sidebar-data
```

Response:
```json
{
  "trades_count": 42,
  "win_rate": 68.5,
  "agent_running": true,
  "timestamp": "2025-11-08T14:20:00"
}
```

## Frontend Integration

### Remove Lazy Loading from Sidebar

Since the frontend source is compiled, you'll need to:

1. **Find the sidebar component** in your source code
2. **Remove `React.lazy()` or `lazy()` imports** for sidebar components
3. **Use direct imports** instead:

**Before (with lazy loading):**
```javascript
const Trading = lazy(() => import('./components/Trading'));
```

**After (direct import):**
```javascript
import Trading from './components/Trading';
```

4. **Remove Suspense wrappers** around sidebar components
5. **Preload sidebar components** on app initialization

### API Endpoints for Frontend

#### Portfolio & Trading Data
- `GET /portfolio/summary` - Portfolio summary (real data from Trading Agent API)
- `GET /portfolio/positions` - Current positions (real data)
- `GET /agent/status` - Agent status with real performance metrics
- `GET /trade/history` - Trade history (real trades)

#### Market Data
- `GET /market/data` - Real-time market data from Binance
- `GET /analysis/sentiment` - Real sentiment from RAG engine

#### Backtesting
- `POST /simulations/backtest` - Run backtest (returns status and summary)
- `GET /simulations/backtest/status` - Check backtest status

### Example Frontend Code

```javascript
// Fetch header data
async function fetchHeaderData() {
  const response = await fetch('http://localhost:8001/dashboard/header-data', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data;
}

// Fetch sidebar data
async function fetchSidebarData() {
  const response = await fetch('http://localhost:8001/dashboard/sidebar-data', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data;
}

// Check backtest status
async function checkBacktestStatus() {
  const response = await fetch('http://localhost:8003/simulations/backtest/status');
  const data = await response.json();
  return data;
}
```

## All Logs Go to debug.log

All Python backend logs are now written to `debug.log` file. Frontend logs can be sent to:
- `POST /logs/frontend` (port 8003)
- `POST /logs/frontend` (port 8000 - RAG engine)

Use the `frontend_logging_utility.js` to intercept console logs and send them to the backend.

