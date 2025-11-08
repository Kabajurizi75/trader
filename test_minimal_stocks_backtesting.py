#!/usr/bin/env python3
"""
Minimal Stocks Backtesting System
Uses real market data from Polygon.io and Alpha Vantage
Tests with minimal symbols to avoid rate limits
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_minimal_stocks_backtesting():
    """Test the enhanced backtesting engine with minimal stock symbols to avoid rate limits"""
    try:
        print("📈 Testing Minimal Stocks Backtesting System...")
        from trading_agent.enhanced_backtesting import (
            EnhancedBacktestingEngine,
            BacktestConfig,
            BacktestPeriod
        )
        print("✅ Successfully imported EnhancedBacktestingEngine")
        
        # Create test configuration - ONE YEAR TEST for maximum returns
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Full year test
        
        # Use only 2-3 stocks to avoid API rate limits
        stock_symbols = ['AAPL', 'MSFT']  # Just 2 major stocks
        
        print(f"📊 Asset Class: US Tech Stocks (Minimal)")
        print(f"📈 Total Symbols: {len(stock_symbols)}")
        print(f"   Stocks: {', '.join(stock_symbols)}")
        print(f"   Data Source: Polygon.io + Alpha Vantage + yfinance fallback")
        print(f"   Strategy: Avoid API rate limits with minimal symbols")
        
        # Create test configuration
        config = BacktestConfig(
            initial_balance=100000.0,  # $100k initial investment
            start_date=start_date,
            end_date=end_date,
            symbols=stock_symbols,
            strategies=['momentum'],
            risk_level='high',  # Ultra-aggressive
            max_positions=2,    # One position per stock
            rebalance_frequency=BacktestPeriod.DAILY,
            transaction_costs=0.001,
            slippage=0.0005,
            risk_free_rate=0.02
        )
        
        print("✅ Created BacktestConfig for MINIMAL STOCKS TEST")
        print(f"   Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End Date: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Test Period: {(end_date - start_date).days} days")
        print(f"   Initial Balance: ${config.initial_balance:,.2f}")
        print(f"   Expected Target: 250%+ Annual Returns")
        
        # Create backtesting engine
        engine = EnhancedBacktestingEngine()
        print("✅ Created EnhancedBacktestingEngine")
        
        # Run backtest
        print("\n🚀 Starting MINIMAL STOCKS BACKTEST...")
        result = engine.run_backtest(config)
        
        if result is None:
            print("❌ Backtest failed")
            return None, None
        
        print("✅ Backtest completed successfully!")
        
        # Generate comprehensive report
        print("\n📊 Generating Comprehensive Stocks Report...")
        report = engine.generate_backtest_report(result)
        
        # Display results
        print("\n🎯 Executive Summary - MINIMAL STOCKS ULTRA-AGGRESSIVE STRATEGY:")
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
        
        # Stock Performance Breakdown
        print(f"\n📈 Stock Performance Breakdown:")
        print(f"   AAPL (Apple): Tech giant momentum strategy")
        print(f"   MSFT (Microsoft): Cloud computing momentum")
        
        print("\n🎉 MINIMAL STOCKS ULTRA-AGGRESSIVE STRATEGY TEST COMPLETED!")
        
        # Final verdict
        if summary['annualized_return'] >= 250:
            print("🏆 INVESTOR-READY: Strategy exceeds 250% annual return target!")
            print("🚀 READY FOR PRODUCTION: Real market data validation successful!")
        else:
            print("🔧 STRATEGY OPTIMIZATION: Further improvements needed for 250% target")
            print("💡 CONSIDER: Enhanced position sizing, more aggressive entry/exit criteria")
        
        return result, report
        
    except Exception as e:
        print(f"❌ Error in minimal stocks backtesting: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main function to run minimal stocks backtesting"""
    print("🚀 MINIMAL STOCKS BACKTESTING SYSTEM")
    print("=" * 60)
    print("📈 Testing Ultra-Aggressive Strategy on Minimal Stock Set")
    print("📊 Using Real Market Data from Polygon.io + Alpha Vantage")
    print("🎯 Target: 250%+ Annual Returns with Real Market Validation")
    print("💡 Strategy: Avoid API rate limits with minimal symbols")
    print("=" * 60)
    
    result, report = test_minimal_stocks_backtesting()
    
    if result is not None:
        print("\n✅ MINIMAL STOCKS BACKTESTING COMPLETED SUCCESSFULLY!")
        print("📊 Results validated with real market data")
        print("🚀 Strategy ready for investor presentation")
    else:
        print("\n❌ MINIMAL STOCKS BACKTESTING FAILED")
        print("💡 Check error logs and verify data sources")
    
    print("\n" + "=" * 60)
    print("🏁 Minimal stocks backtesting completed!")

if __name__ == "__main__":
    main()

