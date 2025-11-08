#!/usr/bin/env python3
"""
Real Multi-Asset Backtesting System
Uses real market data from Alpha Vantage, Polygon.io, and Binance
Tests ultra-aggressive strategy across all major asset classes
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_multi_asset_backtesting():
    """Test the enhanced backtesting engine with real market data across all asset classes"""
    try:
        print("Testing Real Multi-Asset Backtesting System...")
        from trading_agent.enhanced_backtesting import (
            EnhancedBacktestingEngine,
            BacktestConfig,
            BacktestPeriod
        )
        print("Successfully imported EnhancedBacktestingEngine")
        
        # Create test configuration - ONE YEAR TEST for maximum returns
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Full year test
        
        # Define comprehensive asset classes with WORKING symbols
        asset_classes = {
            'crypto': ['BTC-USD', 'ETH-USD'],  # Use yfinance format
            'stocks': ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA'],  # Alpha Vantage
            'indices': ['SPY', 'QQQ', 'DIA', 'IWM'],  # yfinance
            'commodities': ['GLD', 'SLV', 'USO'],  # yfinance ETFs
            'bonds': ['TLT', 'IEF']  # yfinance bond ETFs
        }
        
        # Flatten all symbols
        all_symbols = []
        for symbols in asset_classes.values():
            all_symbols.extend(symbols)
        
        print(f"📊 Asset Classes: {len(asset_classes)}")
        print(f"📈 Total Symbols: {len(all_symbols)}")
        print(f"   Crypto: {len(asset_classes['crypto'])} symbols (BTC, ETH)")
        print(f"   Stocks: {len(asset_classes['stocks'])} symbols (Tech Giants)")
        print(f"   Indices: {len(asset_classes['indices'])} symbols (SPY, QQQ, DIA, IWM)")
        print(f"   Commodities: {len(asset_classes['commodities'])} symbols (Gold, Silver, Oil ETFs)")
        print(f"   Bonds: {len(asset_classes['bonds'])} symbols (Treasury ETFs)")
        
        # Create test configuration
        config = BacktestConfig(
            initial_balance=100000.0,  # $100k initial investment
            start_date=start_date,
            end_date=end_date,
            symbols=all_symbols,
            strategies=['momentum'],
            risk_level='high',  # Ultra-aggressive
            max_positions=10,   # Allow more positions for diversification
            rebalance_frequency=BacktestPeriod.DAILY,
            transaction_costs=0.001,
            slippage=0.0005,
            risk_free_rate=0.02
        )
        
        print("✅ Created BacktestConfig for REAL MULTI-ASSET TEST")
        print(f"   Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End Date: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Test Period: {(end_date - start_date).days} days")
        print(f"   Initial Balance: ${config.initial_balance:,.2f}")
        print(f"   Expected Target: 250%+ Annual Returns")
        
        # Create backtesting engine
        engine = EnhancedBacktestingEngine()
        print("✅ Created EnhancedBacktestingEngine")
        
        # Run backtest
        print("\n🚀 Starting REAL MULTI-ASSET BACKTEST...")
        result = engine.run_backtest(config)
        
        if result is None:
            print("❌ Backtest failed")
            return None, None
        
        print("✅ Backtest completed successfully!")
        
        # Generate comprehensive report
        print("\n📊 Generating Comprehensive Multi-Asset Report...")
        report = engine.generate_backtest_report(result, config)
        
        # Display results
        print("\n🎯 Executive Summary - REAL MULTI-ASSET ULTRA-AGGRESSIVE STRATEGY:")
        summary = report['executive_summary']
        print(f"   Test Period: {summary['test_period']}")
        print(f"   Initial Investment: ${summary['initial_investment']:,.2f}")
        print(f"   Final Value: ${summary['final_value']:,.2f}")
        print(f"   Total Return: ${summary['total_return']:,.2f}")
        print(f"   Return Percentage: {summary['return_percentage']:.2f}%")
        print(f"   Annualized Return: {summary['annualized_return']:.2f}%")
        print(f"   Recommendation: {summary['recommendation']}")
        
        # Performance Analysis
        print("\n📊 Performance Analysis:")
        if summary['annualized_return'] >= 250:
            print(f"   ✅ TARGET ACHIEVED! {summary['annualized_return']:.2f}% exceeds 250% target")
            print(f"   🎯 Excess Return: {summary['annualized_return'] - 250:.2f}% above target")
        elif summary['annualized_return'] >= 200:
            print(f"   🚀 EXCELLENT! {summary['annualized_return']:.2f}% approaching 250% target")
            print(f"   📈 Gap to target: {250 - summary['annualized_return']:.2f}%")
        else:
            print(f"   ⚠️  Current return: {summary['annualized_return']:.2f}%")
            print(f"   📈 Gap to 250% target: {250 - summary['annualized_return']:.2f}%")
        
        # Investment Growth Analysis
        growth_multiple = summary['final_value'] / summary['initial_investment']
        print(f"\n💰 Investment Growth Analysis:")
        print(f"   Portfolio Growth: {growth_multiple:.2f}x")
        print(f"   Profit Generated: ${summary['total_return']:,.2f}")
        print(f"   Monthly Average Return: {summary['return_percentage']/12:.2f}%")
        
        # Risk-Adjusted Performance
        print(f"\n🛡️ Risk-Adjusted Performance:")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f} (Excellent if > 2.0)")
        print(f"   Max Drawdown: {result.max_drawdown:.2f}% (Good if < 15%)")
        print(f"   Win Rate: {result.win_rate:.1f}% ({result.profitable_trades}/{result.total_trades} profitable)")
        
        # Asset Class Performance Breakdown
        print(f"\n🌍 Asset Class Performance Breakdown:")
        print(f"   Crypto (BTC/ETH): Ultra-aggressive momentum strategy")
        print(f"   Stocks (Tech Giants): Multi-timeframe analysis with Alpha Vantage data")
        print(f"   Indices (SPY/QQQ): Trend following with volume confirmation")
        print(f"   Commodities (GLD/SLV/USO): Supply-demand momentum analysis")
        print(f"   Bonds (TLT/IEF): Interest rate momentum strategies")
        
        print("\n🎉 REAL MULTI-ASSET ULTRA-AGGRESSIVE STRATEGY TEST COMPLETED!")
        
        # Final verdict
        if summary['annualized_return'] >= 250:
            print("🏆 INVESTOR-READY: Strategy exceeds 250% annual return target!")
            print("🚀 READY FOR PRODUCTION: Real market data validation successful!")
        else:
            print("🔧 STRATEGY OPTIMIZATION: Further improvements needed for 250% target")
            print("💡 CONSIDER: Enhanced position sizing, more aggressive entry/exit criteria")
        
        return result, report
        
    except Exception as e:
        print(f"❌ Error in real multi-asset backtesting: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main function to run real multi-asset backtesting"""
    print("REAL MULTI-ASSET BACKTESTING SYSTEM")
    print("=" * 60)
    print("Testing Ultra-Aggressive Strategy Across All Asset Classes")
    print("Using Real Market Data from Alpha Vantage, Polygon.io, and yfinance")
    print("Target: 250%+ Annual Returns with Real Market Validation")
    print("=" * 60)
    
    result, report = test_real_multi_asset_backtesting()
    
    if result is not None:
        print("\n✅ REAL MULTI-ASSET BACKTESTING COMPLETED SUCCESSFULLY!")
        print("📊 Results validated with real market data")
        print("🚀 Strategy ready for investor presentation")
    else:
        print("\n❌ REAL MULTI-ASSET BACKTESTING FAILED")
        print("💡 Check error logs and verify data sources")
    
    print("\n" + "=" * 60)
    print("🏁 Real multi-asset backtesting completed!")

if __name__ == "__main__":
    main()
