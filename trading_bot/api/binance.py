import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import json
from datetime import datetime

class BinanceAPI:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.base_url = "https://api.binance.com"

        if not self.api_key or not self.secret_key:
            raise ValueError("BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables must be set")

    def _get_signature(self, params):
        """Generate HMAC SHA256 signature"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _send_request(self, method, endpoint, params=None, signed=False):
        """Send HTTP request to Binance API"""
        url = f"{self.base_url}{endpoint}"

        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        if signed and params:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._get_signature(params)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, params=params)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def get_account_info(self):
        """Get account information including balances"""
        endpoint = "/api/v3/account"
        return self._send_request('GET', endpoint, {}, signed=True)

    def get_symbol_price(self, symbol):
        """Get current price for a symbol"""
        endpoint = "/api/v3/ticker/price"
        params = {'symbol': symbol.upper()}
        return self._send_request('GET', endpoint, params)

    def get_24hr_ticker(self, symbol):
        """Get 24hr ticker data"""
        endpoint = "/api/v3/ticker/24hr"
        params = {'symbol': symbol.upper()}
        return self._send_request('GET', endpoint, params)

    def place_order(self, symbol, side, order_type, quantity, price=None):
        """Place a new order"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(quantity)
        }

        if order_type.upper() == 'LIMIT' and price:
            params['price'] = str(price)
            params['timeInForce'] = 'GTC'

        return self._send_request('POST', endpoint, params, signed=True)

    def get_open_orders(self, symbol=None):
        """Get open orders"""
        endpoint = "/api/v3/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        return self._send_request('GET', endpoint, params, signed=True)

    def cancel_order(self, symbol, order_id):
        """Cancel an order"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol.upper(),
            'orderId': str(order_id)
        }
        return self._send_request('DELETE', endpoint, params, signed=True)

    def get_all_orders(self, symbol, limit=500):
        """Get all orders for a symbol"""
        endpoint = "/api/v3/allOrders"
        params = {
            'symbol': symbol.upper(),
            'limit': limit
        }
        return self._send_request('GET', endpoint, params, signed=True)

    def get_exchange_info(self):
        """Get exchange information"""
        endpoint = "/api/v3/exchangeInfo"
        return self._send_request('GET', endpoint)

    def get_klines(self, symbol, interval='1d', limit=100):
        """Get kline/candlestick data"""
        endpoint = "/api/v3/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        return self._send_request('GET', endpoint, params)

# Global instance
binance_api = None

def get_binance_api():
    """Get or create Binance API instance"""
    global binance_api
    if binance_api is None:
        try:
            binance_api = BinanceAPI()
        except ValueError as e:
            print(f"Failed to initialize Binance API: {e}")
            return None
    return binance_api

def place_order(symbol, side, quantity, order_type='MARKET', price=None):
    """Place an order using Binance API"""
    api = get_binance_api()
    if not api:
        return {"status": "error", "message": "Binance API not configured"}

    try:
        result = api.place_order(symbol, side, order_type, quantity, price)
        if result:
            return {
                "status": "success",
                "order_id": result.get('orderId'),
                "symbol": result.get('symbol'),
                "side": result.get('side'),
                "quantity": result.get('origQty'),
                "price": result.get('price'),
                "status": result.get('status'),
                "timestamp": datetime.fromtimestamp(result.get('transactTime', 0) / 1000) if result.get('transactTime') else datetime.now()
            }
        else:
            return {"status": "error", "message": "Failed to place order"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_account_balance():
    """Get account balance"""
    api = get_binance_api()
    if not api:
        return {"status": "error", "message": "Binance API not configured"}

    try:
        account_info = api.get_account_info()
        if account_info:
            balances = {}
            for balance in account_info.get('balances', []):
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                if free > 0 or locked > 0:
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
            return {"status": "success", "balances": balances}
        else:
            return {"status": "error", "message": "Failed to get account info"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_market_price(symbol):
    """Get current market price"""
    api = get_binance_api()
    if not api:
        return None

    try:
        price_info = api.get_symbol_price(symbol)
        if price_info:
            return float(price_info.get('price', 0))
        return None
    except Exception as e:
        print(f"Failed to get market price for {symbol}: {e}")
        return None

def get_24hr_stats(symbol):
    """Get 24hr statistics"""
    api = get_binance_api()
    if not api:
        return None

    try:
        stats = api.get_24hr_ticker(symbol)
        if stats:
            return {
                'symbol': stats.get('symbol'),
                'price': float(stats.get('lastPrice', 0)),
                'change': float(stats.get('priceChange', 0)),
                'changePercent': float(stats.get('priceChangePercent', 0)),
                'volume': stats.get('volume'),
                'high': float(stats.get('highPrice', 0)),
                'low': float(stats.get('lowPrice', 0))
            }
        return None
    except Exception as e:
        print(f"Failed to get 24hr stats for {symbol}: {e}")
        return None
