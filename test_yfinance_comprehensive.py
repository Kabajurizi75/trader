#!/usr/bin/env python3
"""
Comprehensive yfinance Testing Script
Tests multiple approaches to understand why it works in Colab but not locally
"""

import sys
import os
import platform
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def test_yfinance_comprehensive():
    """Test yfinance with multiple approaches and diagnostics"""
    print("🔍 Comprehensive yfinance Testing & Diagnostics")
    print("=" * 60)
    
    # System diagnostics
    print("🖥️  System Diagnostics:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Check network connectivity
    print("\n🌐 Network Diagnostics:")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"   Internet: ✅ Connected (Status: {response.status_code})")
    except Exception as e:
        print(f"   Internet: ❌ Failed ({e})")
    
    try:
        response = requests.get("https://finance.yahoo.com", timeout=5)
        print(f"   Yahoo Finance: ✅ Accessible (Status: {response.status_code})")
    except Exception as e:
        print(f"   Yahoo Finance: ❌ Failed ({e})")
    
    # Test yfinance installation
    print("\n📦 yfinance Installation Test:")
    try:
        import yfinance as yf
        print(f"   yfinance: ✅ Installed (Version: {yf.__version__})")
    except ImportError as e:
        print(f"   yfinance: ❌ Not installed ({e})")
        print("   Installing yfinance...")
        os.system("pip install yfinance --upgrade")
        try:
            import yfinance as yf
            print(f"   yfinance: ✅ Installed after upgrade (Version: {yf.__version__})")
        except ImportError as e2:
            print(f"   yfinance: ❌ Still failed after upgrade ({e2})")
            return
    
    # Test multiple yfinance approaches
    print("\n🧪 Testing Multiple yfinance Approaches:")
    
    # Approach 1: Basic download
    print("\n1️⃣ Approach 1: Basic yf.download()")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"   📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        data = yf.download("AAPL", start=start_date, end=end_date, progress=False)
        
        if data is not None and not data.empty:
            print(f"   ✅ Success! Fetched {len(data)} days of data")
            print(f"   📊 Data shape: {data.shape}")
            print(f"   📈 Last close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No data returned")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Approach 2: Ticker object
    print("\n2️⃣ Approach 2: Ticker object")
    try:
        ticker = yf.Ticker("AAPL")
        print(f"   📊 Ticker info: {ticker.info.get('longName', 'N/A')}")
        
        # Get history
        data = ticker.history(period="30d")
        
        if data is not None and not data.empty:
            print(f"   ✅ Success! Fetched {len(data)} days of data")
            print(f"   📊 Data shape: {data.shape}")
            print(f"   📈 Last close: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No data returned")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Approach 3: Different symbol format
    print("\n3️⃣ Approach 3: Different symbol formats")
    symbols_to_try = ["AAPL", "AAPL.US", "AAPL-USD", "AAPL:US"]
    
    for symbol in symbols_to_try:
        try:
            print(f"   🔍 Trying symbol: {symbol}")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data is not None and not data.empty:
                print(f"   ✅ Success with {symbol}! Fetched {len(data)} days")
                break
            else:
                print(f"   ❌ No data with {symbol}")
                
        except Exception as e:
            print(f"   ❌ Failed with {symbol}: {e}")
    
    # Approach 4: Different date formats
    print("\n4️⃣ Approach 4: Different date formats")
    try:
        # Use string dates
        data = yf.download("AAPL", start="2024-07-22", end="2024-08-22", progress=False)
        
        if data is not None and not data.empty:
            print(f"   ✅ Success with string dates! Fetched {len(data)} days")
        else:
            print("   ❌ No data with string dates")
            
    except Exception as e:
        print(f"   ❌ Failed with string dates: {e}")
    
    # Approach 5: Different intervals
    print("\n5️⃣ Approach 5: Different intervals")
    intervals_to_try = ["1d", "5d", "1wk", "1mo"]
    
    for interval in intervals_to_try:
        try:
            print(f"   🔍 Trying interval: {interval}")
            data = yf.download("AAPL", start=start_date, end=end_date, interval=interval, progress=False)
            
            if data is not None and not data.empty:
                print(f"   ✅ Success with {interval}! Fetched {len(data)} periods")
                break
            else:
                print(f"   ❌ No data with {interval}")
                
        except Exception as e:
            print(f"   ❌ Failed with {interval}: {e}")
    
    # Approach 6: Different periods
    print("\n6️⃣ Approach 6: Different periods")
    periods_to_try = ["5d", "1mo", "3mo", "6mo", "1y"]
    
    for period in periods_to_try:
        try:
            print(f"   🔍 Trying period: {period}")
            data = yf.download("AAPL", period=period, progress=False)
            
            if data is not None and not data.empty:
                print(f"   ✅ Success with {period}! Fetched {len(data)} periods")
                break
            else:
                print(f"   ❌ No data with {period}")
                
        except Exception as e:
            print(f"   ❌ Failed with {period}: {e}")
    
    # Approach 7: Test with different assets
    print("\n7️⃣ Approach 7: Test with different assets")
    assets_to_try = ["BTC-USD", "ETH-USD", "SPY", "QQQ"]
    
    for asset in assets_to_try:
        try:
            print(f"   🔍 Trying asset: {asset}")
            data = yf.download(asset, period="1mo", progress=False)
            
            if data is not None and not data.empty:
                print(f"   ✅ Success with {asset}! Fetched {len(data)} periods")
                break
            else:
                print(f"   ❌ No data with {asset}")
                
        except Exception as e:
            print(f"   ❌ Failed with {asset}: {e}")
    
    # Summary and recommendations
    print("\n" + "=" * 60)
    print("📋 Summary & Recommendations:")
    print("=" * 60)
    
    print("\n💡 If yfinance still doesn't work locally:")
    print("   1. Check your firewall/proxy settings")
    print("   2. Try using a VPN")
    print("   3. Check if your ISP blocks Yahoo Finance")
    print("   4. Try running from a different network")
    print("   5. Use Google Colab for development/testing")
    
    print("\n🚀 Alternative Solutions:")
    print("   1. Use Alpha Vantage API (free tier)")
    print("   2. Use Polygon.io API (free tier)")
    print("   3. Use Binance API for crypto")
    print("   4. Use simulated data for backtesting")
    
    print("\n🏁 Comprehensive testing completed!")

if __name__ == "__main__":
    test_yfinance_comprehensive()

