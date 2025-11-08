#!/usr/bin/env python3
"""
Enhanced Multi-API Market Data Fetcher
Uses Alpha Vantage, Polygon.io, Binance, and yfinance fallback
"""

import sys
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, List
import json
import shutil

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class EnhancedMultiAPIFetcher:
    """Enhanced multi-API fetcher with multiple data sources"""
    
    def __init__(self):
        # API Keys
        self.alpha_vantage_key = "ARU0RNCVSD06VTEE"  # Your Alpha Vantage key
        self.polygon_key = "GwUppxyxL52Sa0nWQWaPT3KYycDo4_t2"  # Your Polygon key
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        
        # Create sessions for each API
        self.alpha_session = requests.Session()
        self.alpha_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.polygon_session = requests.Session()
        self.polygon_session.headers.update({
            'Authorization': f'Bearer {self.polygon_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        print(f"🔑 API Keys Status:")
        print(f"   Alpha Vantage: ✅ {self.alpha_vantage_key[:8]}...")
        print(f"   Polygon.io: ✅ {self.polygon_key[:8]}...")
        print(f"   Binance: {'✅' if self.binance_api_key else '❌'}")
        print(f"   yfinance: ✅ Version 0.2.65+ (fallback)")
    
    def clean_yfinance_cache(self):
        """Clean yfinance cache to avoid corruption issues"""
        try:
            cache_dir = os.path.expanduser("~/.cache/yfinance")
            if os.path.exists(cache_dir):
                print(f"🧹 Cleaning yfinance cache: {cache_dir}")
                shutil.rmtree(cache_dir)
                print("   ✅ Cache cleaned successfully")
            else:
                print("   ℹ️  No yfinance cache found")
        except Exception as e:
            print(f"   ⚠️  Cache cleaning failed: {e}")
    
    def fetch_alpha_vantage_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data from Alpha Vantage"""
        try:
            print(f"   📡 Alpha Vantage: Fetching {symbol}...")
            
            # Alpha Vantage endpoint
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "full" if period == "1y" else "compact"
            }
            
            response = self.alpha_session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Time Series (Daily)" in data:
                    # Parse the data
                    time_series = data["Time Series (Daily)"]
                    
                    # Convert to DataFrame
                    df_data = []
                    for date, values in time_series.items():
                        df_data.append({
                            'date': pd.to_datetime(date),
                            'open': float(values['1. open']),
                            'high': float(values['2. high']),
                            'low': float(values['3. low']),
                            'close': float(values['4. close']),
                            'volume': int(values['5. volume'])
                        })
                    
                    df = pd.DataFrame(df_data)
                    df = df.sort_values('date').reset_index(drop=True)
                    df = df.set_index('date')
                    
                    # Limit to requested period
                    if period == "1mo":
                        df = df.tail(30)
                    elif period == "3mo":
                        df = df.tail(90)
                    elif period == "6mo":
                        df = df.tail(180)
                    elif period == "1y":
                        df = df.tail(365)
                    
                    print(f"   ✅ Alpha Vantage: Fetched {len(df)} days of data")
                    return df
                else:
                    print(f"   ❌ Alpha Vantage: No time series data found")
                    if "Note" in data:
                        print(f"   📝 Note: {data['Note']}")
                    return None
            else:
                print(f"   ❌ Alpha Vantage: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Alpha Vantage error: {e}")
            return None
    
    def fetch_polygon_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data from Polygon.io"""
        try:
            print(f"   📡 Polygon.io: Fetching {symbol}...")
            
            # Calculate date range
            end_date = datetime.now()
            if period == "1mo":
                start_date = end_date - timedelta(days=30)
            elif period == "3mo":
                start_date = end_date - timedelta(days=90)
            elif period == "6mo":
                start_date = end_date - timedelta(days=180)
            else:  # 1y
                start_date = end_date - timedelta(days=365)
            
            # Polygon.io endpoint
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            response = self.polygon_session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("results"):
                    # Parse the data
                    results = data["results"]
                    
                    df_data = []
                    for result in results:
                        df_data.append({
                            'date': pd.to_datetime(result['t'], unit='ms'),
                            'open': result['o'],
                            'high': result['h'],
                            'low': result['l'],
                            'close': result['c'],
                            'volume': result['v']
                        })
                    
                    df = pd.DataFrame(df_data)
                    df = df.sort_values('date').reset_index(drop=True)
                    df = df.set_index('date')
                    
                    print(f"   ✅ Polygon.io: Fetched {len(df)} days of data")
                    return df
                else:
                    print(f"   ❌ Polygon.io: No results found")
                    return None
            else:
                print(f"   ❌ Polygon.io: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Polygon.io error: {e}")
            return None
    
    def fetch_yfinance_fallback(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data using yfinance as fallback (without session)"""
        try:
            print(f"   📡 yfinance: Fetching {symbol}...")
            
            import yfinance as yf
            
            # Use yfinance without session
            data = yf.download(symbol, period=period, progress=False)
            
            if data is not None and not data.empty:
                print(f"   ✅ yfinance: Fetched {len(data)} days of data")
                return data
            else:
                print(f"   ❌ yfinance: No data returned")
                return None
                
        except Exception as e:
            print(f"   ❌ yfinance error: {e}")
            return None
    
    def fetch_asset_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data for a single asset using multiple sources"""
        print(f"\n🔍 Fetching {symbol} data (period: {period})...")
        
        # Try Alpha Vantage first
        data = self.fetch_alpha_vantage_data(symbol, period)
        if data is not None:
            return data
        
        # Try Polygon.io second
        data = self.fetch_polygon_data(symbol, period)
        if data is not None:
            return data
        
        # Try yfinance as fallback
        data = self.fetch_yfinance_fallback(symbol, period)
        if data is not None:
            return data
        
        print(f"   ❌ All data sources failed for {symbol}")
        return None
    
    def fetch_multi_asset_data(self, symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple assets efficiently"""
        print(f"\n📊 Fetching Multi-Asset Data ({len(symbols)} symbols)...")
        
        result = {}
        
        for symbol in symbols:
            data = self.fetch_asset_data(symbol, period)
            if data is not None:
                result[symbol] = data
                print(f"   ✅ {symbol}: {data.shape}")
            else:
                print(f"   ❌ {symbol}: Failed to fetch data")
        
        return result
    
    def analyze_asset_data(self, data: pd.DataFrame, symbol: str):
        """Analyze asset data and provide insights"""
        if data is None or data.empty:
            print(f"❌ No data to analyze for {symbol}")
            return
        
        print(f"\n🔍 {symbol} Data Analysis:")
        print("=" * 50)
        
        # Basic info
        print(f"📊 Data Summary:")
        print(f"   Symbol: {symbol}")
        print(f"   Date Range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}")
        print(f"   Total Days: {len(data)}")
        
        # Price analysis
        if 'close' in data.columns:
            close_col = 'close'
        elif 'Close' in data.columns:
            close_col = 'Close'
        else:
            print("   ❌ No close price column found")
            return
        
        print(f"\n💰 Price Analysis:")
        print(f"   Current Price: ${data[close_col].iloc[-1]:.2f}")
        
        if 'high' in data.columns:
            print(f"   Period High: ${data['high'].max():.2f}")
        elif 'High' in data.columns:
            print(f"   Period High: ${data['High'].max():.2f}")
        
        if 'low' in data.columns:
            print(f"   Period Low: ${data['low'].min():.2f}")
        elif 'Low' in data.columns:
            print(f"   Period Low: ${data['Low'].min():.2f}")
        
        print(f"   Average Price: ${data[close_col].mean():.2f}")
        
        # Returns analysis
        if len(data) > 1:
            first_close = data[close_col].iloc[0]
            last_close = data[close_col].iloc[-1]
            total_return = ((last_close - first_close) / first_close) * 100
            print(f"   Total Return: {total_return:.2f}%")
            
            # Daily returns
            daily_returns = data[close_col].pct_change().dropna()
            avg_daily_return = daily_returns.mean() * 100
            print(f"   Average Daily Return: {avg_daily_return:.2f}%")
            
            # Volatility
            volatility = daily_returns.std() * (252 ** 0.5) * 100
            print(f"   Annualized Volatility: {volatility:.2f}%")
        
        # Volume analysis
        if 'volume' in data.columns:
            print(f"\n📊 Volume Analysis:")
            print(f"   Current Volume: {data['volume'].iloc[-1]:,}")
            print(f"   Average Volume: {data['volume'].mean():,.0f}")
            print(f"   Max Volume: {data['volume'].max():,}")
        elif 'Volume' in data.columns:
            print(f"\n📊 Volume Analysis:")
            print(f"   Current Volume: {data['Volume'].iloc[-1]:,}")
            print(f"   Average Volume: {data['Volume'].mean():,.0f}")
            print(f"   Max Volume: {data['Volume'].max():,}")

def main():
    """Main function to test enhanced multi-API fetcher"""
    print("🚀 Enhanced Multi-API Market Data Fetcher")
    print("=" * 60)
    
    # Create fetcher
    fetcher = EnhancedMultiAPIFetcher()
    
    # Test multi-asset fetching
    symbols = ["AAPL", "MSFT", "GOOG", "AMZN"]
    data = fetcher.fetch_multi_asset_data(symbols, "1mo")
    
    if data:
        print(f"\n📊 Successfully fetched data for {len(data)} symbols!")
        
        # Analyze each asset
        for symbol, symbol_data in data.items():
            fetcher.analyze_asset_data(symbol_data, symbol)
            
            # Show sample data
            print(f"\n📋 {symbol} Sample Data (First 3 rows):")
            print(symbol_data.head(3))
    else:
        print("❌ Failed to fetch any data")
        print("\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify API keys are correct")
        print("   3. Check API rate limits")
    
    print("\n" + "=" * 60)
    print("🏁 Enhanced multi-API testing completed!")

if __name__ == "__main__":
    main()
