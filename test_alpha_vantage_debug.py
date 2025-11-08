#!/usr/bin/env python3
"""
Debug Alpha Vantage API Response
Test the actual API response to understand the data format
"""

import requests
import json
from datetime import datetime, timedelta

def test_alpha_vantage_api():
    """Test Alpha Vantage API directly"""
    print("🔍 Testing Alpha Vantage API Response...")
    
    # API Key
    api_key = "ARU0RNCVSD06VTEE"
    
    # Test with AAPL
    symbol = "AAPL"
    
    # Alpha Vantage endpoint
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact"  # Try compact first
    }
    
    print(f"📡 Fetching data for {symbol}...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📋 Response Keys: {list(data.keys())}")
            
            # Check for error messages
            if "Error Message" in data:
                print(f"❌ Error: {data['Error Message']}")
                return
            
            if "Note" in data:
                print(f"📝 Note: {data['Note']}")
            
            # Check for time series data
            if "Time Series (Daily)" in data:
                time_series = data["Time Series (Daily)"]
                print(f"✅ Time Series found with {len(time_series)} days")
                
                # Show first few entries
                print("\n📊 First 3 days of data:")
                for i, (date, values) in enumerate(time_series.items()):
                    if i >= 3:
                        break
                    print(f"   {date}: {values}")
            else:
                print("❌ No Time Series (Daily) found")
                print(f"Available keys: {list(data.keys())}")
                
                # Show full response for debugging
                print(f"\n🔍 Full Response:")
                print(json.dumps(data, indent=2))
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_alpha_vantage_intraday():
    """Test Alpha Vantage intraday function"""
    print("\n🔍 Testing Alpha Vantage Intraday Function...")
    
    api_key = "ARU0RNCVSD06VTEE"
    symbol = "AAPL"
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "60min",
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Intraday Response Keys: {list(data.keys())}")
            
            if "Time Series (60min)" in data:
                time_series = data["Time Series (60min)"]
                print(f"✅ Intraday Time Series found with {len(time_series)} entries")
            else:
                print("❌ No intraday time series found")
        else:
            print(f"❌ Intraday HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Intraday Error: {e}")

def main():
    """Main function"""
    print("🚀 Alpha Vantage API Debug Tool")
    print("=" * 50)
    
    test_alpha_vantage_api()
    test_alpha_vantage_intraday()
    
    print("\n" + "=" * 50)
    print("🏁 Debug completed!")

if __name__ == "__main__":
    main()

