#!/usr/bin/env python3
"""
Simple yfinance AAPL Data Fetcher
Test script to fetch Apple stock data
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

def test_yfinance_aapl():
    """Test yfinance data fetching for AAPL stock"""
    try:
        print("🍎 Testing yfinance AAPL Data Fetching...")
        
        # Try to import yfinance
        try:
            import yfinance as yf
            print("✅ yfinance imported successfully")
        except ImportError:
            print("❌ yfinance not installed. Installing...")
            os.system("pip install yfinance")
            import yfinance as yf
            print("✅ yfinance installed and imported")
        
        # Set date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Create ticker object for AAPL
        ticker = yf.Ticker("AAPL")
        print("📊 AAPL ticker object created")
        
        # Try different methods to get data
        print("\n🔄 Attempting to fetch data...")
        
        # Method 1: Direct history fetch
        try:
            print("📈 Method 1: Direct history fetch...")
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if data is not None and not data.empty:
                print(f"✅ Success! Fetched {len(data)} days of data")
                print(f"📊 Data shape: {data.shape}")
                print(f"📅 Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
                
                # Display first few rows
                print("\n📋 First 5 rows of data:")
                print(data.head())
                
                # Display last few rows
                print("\n📋 Last 5 rows of data:")
                print(data.tail())
                
                # Basic statistics
                print("\n📊 Basic Statistics:")
                print(f"   Open: ${data['Open'].iloc[-1]:.2f}")
                print(f"   High: ${data['High'].iloc[-1]:.2f}")
                print(f"   Low: ${data['Low'].iloc[-1]:.2f}")
                print(f"   Close: ${data['Close'].iloc[-1]:.2f}")
                print(f"   Volume: {data['Volume'].iloc[-1]:,}")
                
                # Calculate returns
                if len(data) > 1:
                    first_close = data['Close'].iloc[0]
                    last_close = data['Close'].iloc[-1]
                    total_return = ((last_close - first_close) / first_close) * 100
                    print(f"\n📈 30-Day Return: {total_return:.2f}%")
                
                return data
            else:
                print("❌ No data returned from direct fetch")
                
        except Exception as e1:
            print(f"❌ Method 1 failed: {e1}")
            
            # Method 2: Try with different interval
            try:
                print("\n📈 Method 2: Trying with 5d interval...")
                data = ticker.history(start=start_date, end=end_date, interval='5d')
                
                if data is not None and not data.empty:
                    print(f"✅ Success with 5d interval! Fetched {len(data)} periods")
                    print(data.head())
                    return data
                else:
                    print("❌ No data returned from 5d interval")
                    
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                
                # Method 3: Try with weekly interval
                try:
                    print("\n📈 Method 3: Trying with weekly interval...")
                    data = ticker.history(start=start_date, end=end_date, interval='1wk')
                    
                    if data is not None and not data.empty:
                        print(f"✅ Success with weekly interval! Fetched {len(data)} weeks")
                        print(data.head())
                        return data
                    else:
                        print("❌ No data returned from weekly interval")
                        
                except Exception as e3:
                    print(f"❌ Method 3 failed: {e3}")
                    
                    # Method 4: Try getting info
                    try:
                        print("\n📈 Method 4: Trying to get ticker info...")
                        info = ticker.info
                        print(f"✅ Got ticker info: {info.get('longName', 'Unknown')}")
                        print(f"   Sector: {info.get('sector', 'Unknown')}")
                        print(f"   Industry: {info.get('industry', 'Unknown')}")
                        print(f"   Market Cap: ${info.get('marketCap', 0):,}")
                        
                    except Exception as e4:
                        print(f"❌ Method 4 failed: {e4}")
        
        print("\n❌ All methods failed to fetch data")
        print("🔍 This suggests yfinance API issues")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def analyze_aapl_data(data):
    """Analyze the fetched AAPL data"""
    if data is None or data.empty:
        print("❌ No data to analyze")
        return
    
    print("\n🔍 AAPL Data Analysis:")
    print("=" * 50)
    
    # Price analysis
    print(f"💰 Price Analysis:")
    print(f"   Current Price: ${data['Close'].iloc[-1]:.2f}")
    print(f"   30-Day High: ${data['High'].max():.2f}")
    print(f"   30-Day Low: ${data['Low'].min():.2f}")
    print(f"   Average Price: ${data['Close'].mean():.2f}")
    
    # Volume analysis
    print(f"\n📊 Volume Analysis:")
    print(f"   Current Volume: {data['Volume'].iloc[-1]:,}")
    print(f"   Average Volume: {data['Volume'].mean():,.0f}")
    print(f"   Max Volume: {data['Volume'].max():,}")
    
    # Volatility analysis
    print(f"\n📈 Volatility Analysis:")
    daily_returns = data['Close'].pct_change().dropna()
    volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized
    print(f"   Daily Volatility: {daily_returns.std() * 100:.2f}%")
    print(f"   Annualized Volatility: {volatility:.2f}%")
    
    # Trend analysis
    print(f"\n📊 Trend Analysis:")
    if len(data) > 5:
        recent_trend = ((data['Close'].iloc[-1] - data['Close'].iloc[-5]) / data['Close'].iloc[-5]) * 100
        print(f"   5-Day Trend: {recent_trend:.2f}%")
    
    if len(data) > 10:
        medium_trend = ((data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10]) * 100
        print(f"   10-Day Trend: {medium_trend:.2f}%")
    
    # Moving averages
    print(f"\n📊 Moving Averages:")
    if len(data) >= 5:
        ma_5 = data['Close'].rolling(5).mean().iloc[-1]
        print(f"   5-Day MA: ${ma_5:.2f}")
    
    if len(data) >= 10:
        ma_10 = data['Close'].rolling(10).mean().iloc[-1]
        print(f"   10-Day MA: ${ma_10:.2f}")
    
    current_price = data['Close'].iloc[-1]
    if len(data) >= 5:
        ma_5 = data['Close'].rolling(5).mean().iloc[-1]
        if current_price > ma_5:
            print(f"   📈 Price above 5-day MA (Bullish)")
        else:
            print(f"   📉 Price below 5-day MA (Bearish)")

if __name__ == "__main__":
    print("🚀 Starting AAPL Data Fetch Test...")
    print("=" * 60)
    
    # Fetch data
    aapl_data = test_yfinance_aapl()
    
    # Analyze data if successful
    if aapl_data is not None:
        analyze_aapl_data(aapl_data)
        print("\n✅ AAPL data fetch and analysis completed successfully!")
    else:
        print("\n❌ Failed to fetch AAPL data")
        print("💡 This may indicate yfinance API issues or network problems")
    
    print("\n" + "=" * 60)
    print("�� Test completed!")

