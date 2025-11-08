#!/usr/bin/env python3
"""
Multi-API Market Data Fetcher
Uses multiple data sources for reliable market data
"""

import sys
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, List
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class MultiAPIDataFetcher:
    """Fetches market data from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # API Keys from environment
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        
        print(f"🔑 API Keys Status:")
        print(f"   Binance: {'✅' if self.binance_api_key else '❌'}")
        print(f"   Alpha Vantage: {'✅' if self.alpha_vantage_key else '❌'}")
        print(f"   Polygon: {'✅' if self.polygon_key else '❌'}")
    
    def fetch_aapl_data(self) -> Optional[pd.DataFrame]:
        """Fetch AAPL data from multiple sources"""
        print("\n🍎 Fetching AAPL Data from Multiple Sources...")
        
        # Try yfinance first (same method as Colab)
        print("🔄 Trying yfinance (Colab method)...")
        data = self._fetch_yfinance_colab_method()
        if data is not None:
            return data
        
        # Try Binance (if you have the key)
        if self.binance_api_key:
            print("🔄 Trying Binance API...")
            data = self._fetch_binance_aapl()
            if data is not None:
                return data
        
        # Try Alpha Vantage (free tier)
        print("🔄 Trying Alpha Vantage API...")
        data = self._fetch_alpha_vantage_aapl()
        if data is not None:
            return data
        
        # Try Polygon.io (free tier)
        print("🔄 Trying Polygon.io API...")
        data = self._fetch_polygon_aapl()
        if data is not None:
            return data
        
        print("❌ All data sources failed")
        return None
    
    def _fetch_yfinance_colab_method(self) -> Optional[pd.DataFrame]:
        """Fetch AAPL data using the same method that works in Colab"""
        try:
            print("   📡 Fetching from yfinance (Colab method)...")
            
            # Import yfinance
            try:
                import yfinance as yf
                print("   ✅ yfinance imported successfully")
            except ImportError:
                print("   ❌ yfinance not installed. Installing...")
                os.system("pip install yfinance")
                import yfinance as yf
                print("   ✅ yfinance installed and imported")
            
            # Use the exact same method as Colab
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Last 1 year
            
            print(f"   📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Download data using the same method as Colab
            data = yf.download("AAPL", start=start_date, end=end_date, progress=False)
            
            if data is not None and not data.empty:
                # Reset index to make date a column
                data = data.reset_index()
                
                # Rename columns to match our expected format
                data = data.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Adj Close': 'close',  # Use adjusted close
                    'Volume': 'volume'
                })
                
                # Select only the columns we need
                data = data[['date', 'open', 'high', 'low', 'close', 'volume']]
                
                print(f"   ✅ yfinance (Colab method): Fetched {len(data)} days of data")
                return data
            else:
                print(f"   ❌ yfinance (Colab method): No data returned")
                return None
                
        except Exception as e:
            print(f"   ❌ yfinance (Colab method) error: {e}")
            return None
    
    def _fetch_binance_aapl(self) -> Optional[pd.DataFrame]:
        """Fetch AAPL data from Binance (if available)"""
        try:
            # Note: Binance primarily has crypto, but let's try
            print("   📊 Binance: Primarily for crypto, trying alternative...")
            return None
        except Exception as e:
            print(f"   ❌ Binance error: {e}")
            return None
    
    def _fetch_alpha_vantage_aapl(self) -> Optional[pd.DataFrame]:
        """Fetch AAPL data from Alpha Vantage"""
        try:
            if not self.alpha_vantage_key:
                print("   ⚠️  No Alpha Vantage API key - using free demo")
                # Use demo key for testing
                api_key = "demo"
            else:
                api_key = self.alpha_vantage_key
            
            # Alpha Vantage endpoint
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": "AAPL",
                "apikey": api_key,
                "outputsize": "compact"  # Last 100 days
            }
            
            print("   📡 Fetching from Alpha Vantage...")
            response = self.session.get(url, params=params, timeout=10)
            
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
    
    def _fetch_polygon_aapl(self) -> Optional[pd.DataFrame]:
        """Fetch AAPL data from Polygon.io"""
        try:
            if not self.polygon_key:
                print("   ⚠️  No Polygon API key - skipping")
                return None
            
            # Polygon.io endpoint
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            headers = {"Authorization": f"Bearer {self.polygon_key}"}
            
            print("   📡 Fetching from Polygon.io...")
            response = self.session.get(url, headers=headers, timeout=10)
            
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
    
    def analyze_data(self, data: pd.DataFrame, source: str):
        """Analyze the fetched data"""
        if data is None or data.empty:
            print("❌ No data to analyze")
            return
        
        print(f"\n🔍 AAPL Data Analysis (Source: {source}):")
        print("=" * 60)
        
        # Basic info
        print(f"📊 Data Summary:")
        print(f"   Source: {source}")
        print(f"   Date Range: {data['date'].min().strftime('%Y-%m-%d')} to {data['date'].max().strftime('%Y-%m-%d')}")
        print(f"   Total Days: {len(data)}")
        
        # Price analysis
        print(f"\n💰 Price Analysis:")
        print(f"   Current Price: ${data['close'].iloc[-1]:.2f}")
        print(f"   Period High: ${data['high'].max():.2f}")
        print(f"   Period Low: ${data['low'].min():.2f}")
        print(f"   Average Price: ${data['close'].mean():.2f}")
        
        # Volume analysis
        print(f"\n📊 Volume Analysis:")
        print(f"   Current Volume: {data['volume'].iloc[-1]:,}")
        print(f"   Average Volume: {data['volume'].mean():,.0f}")
        print(f"   Max Volume: {data['volume'].max():,}")
        
        # Returns analysis
        if len(data) > 1:
            print(f"\n📈 Returns Analysis:")
            first_close = data['close'].iloc[0]
            last_close = data['close'].iloc[-1]
            total_return = ((last_close - first_close) / first_close) * 100
            print(f"   Total Return: {total_return:.2f}%")
            
            # Daily returns
            daily_returns = data['close'].pct_change().dropna()
            avg_daily_return = daily_returns.mean() * 100
            print(f"   Average Daily Return: {avg_daily_return:.2f}%")
            
            # Volatility
            volatility = daily_returns.std() * (252 ** 0.5) * 100
            print(f"   Annualized Volatility: {volatility:.2f}%")
        
        # Trend analysis
        if len(data) > 5:
            print(f"\n📊 Trend Analysis:")
            recent_trend = ((data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]) * 100
            print(f"   5-Day Trend: {recent_trend:.2f}%")
            
            if len(data) > 10:
                medium_trend = ((data['close'].iloc[-1] - data['close'].iloc[-10]) / data['close'].iloc[-10]) * 100
                print(f"   10-Day Trend: {medium_trend:.2f}%")
        
        # Moving averages
        if len(data) >= 5:
            print(f"\n📊 Moving Averages:")
            ma_5 = data['close'].rolling(5).mean().iloc[-1]
            print(f"   5-Day MA: ${ma_5:.2f}")
            
            if len(data) >= 10:
                ma_10 = data['close'].rolling(10).mean().iloc[-1]
                print(f"   10-Day MA: ${ma_10:.2f}")
            
            current_price = data['close'].iloc[-1]
            if current_price > ma_5:
                print(f"   📈 Price above 5-day MA (Bullish)")
            else:
                print(f"   📉 Price below 5-day MA (Bearish)")

def main():
    """Main function to test data fetching"""
    print("🚀 Multi-API Market Data Fetcher")
    print("=" * 60)
    
    # Create fetcher
    fetcher = MultiAPIDataFetcher()
    
    # Fetch AAPL data
    aapl_data = fetcher.fetch_aapl_data()
    
    if aapl_data is not None:
        # Determine source
        source = "Multiple APIs"
        if len(aapl_data) > 0:
            print(f"\n✅ Successfully fetched AAPL data!")
            
            # Analyze the data
            fetcher.analyze_data(aapl_data, source)
            
            # Show sample data
            print(f"\n📋 Sample Data (First 5 rows):")
            print(aapl_data.head())
            
            print(f"\n📋 Sample Data (Last 5 rows):")
            print(aapl_data.tail())
            
        else:
            print("❌ Data fetched but empty")
    else:
        print("❌ Failed to fetch data from any source")
        print("\n💡 Recommendations:")
        print("   1. Get free Alpha Vantage API key: https://www.alphavantage.co/")
        print("   2. Get free Polygon.io API key: https://polygon.io/")
        print("   3. Check your Binance API key configuration")
    
    print("\n" + "=" * 60)
    print("🏁 Data fetching test completed!")

if __name__ == "__main__":
    main()
