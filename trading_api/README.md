# Trading API - Secure FastAPI Backend with OAuth2

## 🚀 Overview

A secure FastAPI backend with OAuth2 password bearer authentication for cryptocurrency trading operations. Features JWT token handling, role-based permissions, and comprehensive trading endpoints.

## ✨ Features

- **OAuth2 Authentication** with JWT tokens
- **Role-based Access Control** (trader, admin, viewer)
- **Trading System** with market/limit orders
- **Strategy Management** with CRUD operations
- **Comprehensive Input Validation**
- **CORS Support** for web applications

## 🎯 API Endpoints

### Authentication
- `POST /token` - Get access token
- `GET /users/me` - Get current user info

### Trading
- `POST /trade` - Execute trade order
- `GET /trade/history` - Get trade history

### Strategies
- `GET /strategies` - List strategies
- `POST /strategies` - Create strategy (admin)
- `PUT /strategies/{name}` - Update strategy (admin)
- `DELETE /strategies/{name}` - Delete strategy (admin)

### System
- `GET /health` - Health check
- `GET /` - API information

## 🔧 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn trading_api.main:app --host 0.0.0.0 --port 8001 --reload

# Test the API
python test_trading_api.py
```

## 👥 Test Users

| Username | Password | Role | Balance | Permissions |
|----------|----------|------|---------|-------------|
| `trader1` | `password123` | trader | $10,000 | read, trade |
| `admin` | `password123` | admin | $50,000 | read, trade, admin |
| `viewer` | `password123` | viewer | $0 | read |

## 📖 Documentation

Interactive API documentation: `http://localhost:8001/docs`

Built with FastAPI, OAuth2, and JWT authentication. 