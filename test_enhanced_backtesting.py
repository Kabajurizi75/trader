#!/usr/bin/env python3
"""
Test script for Enhanced Backtesting Engine
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_backtesting():
    """Test the enhanced backtesting engine"""
    try:
        print("🧪 Testing Enhanced Backtesting Engine - ONE YEAR ULTRA-AGGRESSIVE STRATEGY...")
        
        # Import the enhanced backtesting engine
        from trading_agent.enhanced_backtesting import (
            EnhancedBacktestingEngine, 
            BacktestConfig, 
            BacktestPeriod
        )
        
        print("✅ Successfully imported EnhancedBacktestingEngine")
        
        # Create test configuration - ONE YEAR TEST for maximum returns
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Full year test
        
        config = BacktestConfig(
            initial_balance=10000.0,
            start_date=start_date,
            end_date=end_date,
            symbols=['BTC', 'ETH'],
            strategies=['momentum'],
            risk_level='medium',
            max_positions=3,
            rebalance_frequency=BacktestPeriod.DAILY,
            transaction_costs=0.001,
            slippage=0.0005,
            risk_free_rate=0.02
        )
        
        print("✅ Created BacktestConfig for ONE YEAR TEST")
        print(f"   Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End Date: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Test Period: {(end_date - start_date).days} days")
        print(f"   Symbols: {config.symbols}")
        print(f"   Strategies: {config.strategies}")
        print(f"   Expected Target: 250%+ Annual Returns")
        
        # Initialize engine
        engine = EnhancedBacktestingEngine()
        print("✅ Initialized EnhancedBacktestingEngine")
        
        # Test data provider
        print("\n📊 Testing Historical Data Provider...")
        data_provider = engine.data_provider
        
        for symbol in config.symbols:
            print(f"   Fetching data for {symbol}...")
            data = data_provider.get_historical_data(symbol, start_date, end_date)
            
            if data is not None and not data.empty:
                print(f"   ✅ {symbol}: {len(data)} days of data")
                print(f"      Columns: {list(data.columns)}")
                print(f"      Date range: {data['date'].min()} to {data['date'].max()}")
                print(f"      Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
            else:
                print(f"   ❌ {symbol}: No data returned")
        
        # Run backtest
        print("\n🚀 Running Enhanced Backtest...")
        result = engine.run_backtest(config)
        
        print("✅ Backtest completed successfully!")
        print(f"   Initial Value: ${result.initial_value:,.2f}")
        print(f"   Final Value: ${result.final_value:,.2f}")
        print(f"   Total Return: {result.total_return_percent:.2f}%")
        print(f"   Annualized Return: {result.annualized_return:.2f}%")
        print(f"   Max Drawdown: {result.max_drawdown:.2f}%")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Win Rate: {result.win_rate:.1f}%")
        
        # Test VaR calculations
        print("\n📈 Risk Metrics:")
        print(f"   VaR 95%: {result.var_95:.2f}%")
        print(f"   VaR 99%: {result.var_99:.2f}%")
        print(f"   CVaR 95%: {result.cvar_95:.2f}%")
        print(f"   CVaR 99%: {result.cvar_99:.2f}%")
        print(f"   Volatility: {result.volatility:.2f}%")
        
        # Generate report
        print("\n📋 Generating Backtest Report...")
        report = engine.generate_backtest_report(result)
        print("✅ Report generated successfully!")
        
        print("\n🎯 Executive Summary - ONE YEAR ULTRA-AGGRESSIVE STRATEGY:")
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
        
        print("\n🎉 ONE YEAR ULTRA-AGGRESSIVE STRATEGY TEST COMPLETED!")
        
        # Final verdict
        if summary['annualized_return'] >= 250:
            print("🏆 INVESTOR-READY: Strategy exceeds 250% annual return target!")
        else:
            print("🔧 STRATEGY OPTIMIZATION: Further improvements needed for 250% target")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_backtesting()
    sys.exit(0 if success else 1) 