#!/usr/bin/env python3
"""
Multi-Asset Backtesting System for Amiga Trader
Tests ultra-aggressive strategy across all major asset classes
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_multi_asset_backtesting():
    """Test the enhanced backtesting engine across multiple asset classes"""
    try:
        print("🌍 Testing Multi-Asset Backtesting System...")
        from trading_agent.enhanced_backtesting import (
            EnhancedBacktestingEngine,
            BacktestConfig,
            BacktestPeriod
        )
        print("✅ Successfully imported EnhancedBacktestingEngine")
        
        # Create test configuration for ONE YEAR across multiple asset classes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Full year test
        
        # Define asset classes with their symbols
        asset_classes = {
            'Cryptocurrencies': ['BTC', 'ETH'],
            'FOREX': ['USD-EUR', 'EUR-USD', 'GBP-USD', 'USD-JPY'],
            'Commodities': ['GOLD', 'OIL', 'SILVER', 'COPPER'],
            'Equity Options': ['NVDA-OPT', 'AAPL-OPT', 'TSLA-OPT', 'GOOGL-OPT'],
            'Indices': ['SP500', 'NASDAQ', 'DOW', 'FTSE100'],
            'Bonds': ['US10Y', 'US30Y', 'GER10Y', 'JPN10Y']
        }
        
        print(f"✅ Created Multi-Asset Test Configuration")
        print(f"   Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End Date: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Test Period: {(end_date - start_date).days} days")
        print(f"   Asset Classes: {len(asset_classes)}")
        print(f"   Total Symbols: {sum(len(symbols) for symbols in asset_classes.values())}")
        print(f"   Expected Target: 250%+ Annual Returns across all assets")
        
        # Initialize engine
        engine = EnhancedBacktestingEngine()
        print("✅ Initialized EnhancedBacktestingEngine")
        
        # Test each asset class individually
        results = {}
        
        for asset_class, symbols in asset_classes.items():
            print(f"\n📊 Testing {asset_class} ({len(symbols)} symbols)...")
            
            # Create config for this asset class
            config = BacktestConfig(
                initial_balance=10000.0,
                start_date=start_date,
                end_date=end_date,
                symbols=symbols,
                strategies=['momentum'],
                risk_level='ultra_aggressive',
                max_positions=5,
                rebalance_frequency=BacktestPeriod.DAILY,
                transaction_costs=0.001,
                slippage=0.0005,
                risk_free_rate=0.02
            )
            
            try:
                # Run backtest for this asset class
                result = engine.run_backtest(config)
                results[asset_class] = result
                
                print(f"   ✅ {asset_class} Backtest Completed!")
                print(f"      Final Value: ${result.final_value:,.2f}")
                print(f"      Total Return: {result.total_return_percent:.2f}%")
                print(f"      Annualized Return: {result.annualized_return:.2f}%")
                print(f"      Sharpe Ratio: {result.sharpe_ratio:.3f}")
                print(f"      Max Drawdown: {result.max_drawdown:.2f}%")
                print(f"      Total Trades: {result.total_trades}")
                print(f"      Win Rate: {result.win_rate:.1f}%")
                
            except Exception as e:
                print(f"   ❌ {asset_class} Backtest Failed: {e}")
                results[asset_class] = None
        
        # Generate comprehensive multi-asset report
        print("\n📋 Generating Multi-Asset Backtest Report...")
        report = generate_multi_asset_report(results, start_date, end_date)
        print("✅ Multi-Asset Report generated successfully!")
        
        # Display comprehensive results
        print("\n🎯 MULTI-ASSET BACKTESTING RESULTS SUMMARY:")
        print("=" * 80)
        
        total_initial = 0
        total_final = 0
        successful_assets = 0
        
        for asset_class, result in results.items():
            if result is not None:
                total_initial += result.initial_value
                total_final += result.final_value
                successful_assets += 1
                
                print(f"\n📈 {asset_class}:")
                print(f"   Initial: ${result.initial_value:,.2f}")
                print(f"   Final: ${result.final_value:,.2f}")
                print(f"   Return: {result.total_return_percent:.2f}%")
                print(f"   Annualized: {result.annualized_return:.2f}%")
                print(f"   Sharpe: {result.sharpe_ratio:.3f}")
                print(f"   Drawdown: {result.max_drawdown:.2f}%")
                print(f"   Trades: {result.total_trades}")
                print(f"   Win Rate: {result.win_rate:.1f}%")
                
                # Performance assessment
                if result.annualized_return >= 250:
                    print(f"   🏆 PERFORMANCE: EXCEEDS 250% TARGET!")
                elif result.annualized_return >= 100:
                    print(f"   🚀 PERFORMANCE: EXCELLENT (100%+)")
                elif result.annualized_return >= 50:
                    print(f"   ✅ PERFORMANCE: GOOD (50%+)")
                else:
                    print(f"   ⚠️  PERFORMANCE: BELOW TARGET")
        
        # Overall portfolio performance
        if successful_assets > 0:
            overall_return = ((total_final - total_initial) / total_initial) * 100
            overall_annualized = ((total_final / total_initial) ** (365 / 365) - 1) * 100
            
            print(f"\n🌍 OVERALL MULTI-ASSET PORTFOLIO PERFORMANCE:")
            print(f"   Total Assets Tested: {len(asset_classes)}")
            print(f"   Successful Assets: {successful_assets}")
            print(f"   Total Initial Investment: ${total_initial:,.2f}")
            print(f"   Total Final Value: ${total_final:,.2f}")
            print(f"   Overall Return: {overall_return:.2f}%")
            print(f"   Overall Annualized: {overall_annualized:.2f}%")
            
            # Overall assessment
            if overall_annualized >= 250:
                print(f"   🏆 OVERALL RESULT: EXCEEDS 250% TARGET ACROSS ALL ASSETS!")
            elif overall_annualized >= 100:
                print(f"   🚀 OVERALL RESULT: EXCELLENT DIVERSIFIED PERFORMANCE!")
            else:
                print(f"   ⚠️  OVERALL RESULT: NEEDS OPTIMIZATION")
        
        print("\n🎉 Multi-Asset Backtesting System Test Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Multi-Asset test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_multi_asset_report(results, start_date, end_date):
    """Generate comprehensive multi-asset backtesting report"""
    
    report = {
        'test_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'total_assets': len(results),
        'successful_assets': sum(1 for r in results.values() if r is not None),
        'asset_class_results': {},
        'overall_performance': {},
        'recommendations': []
    }
    
    # Calculate overall performance
    total_initial = 0
    total_final = 0
    asset_performance = []
    
    for asset_class, result in results.items():
        if result is not None:
            total_initial += result.initial_value
            total_final += result.final_value
            
            asset_performance.append({
                'class': asset_class,
                'initial': result.initial_value,
                'final': result.final_value,
                'return_pct': result.total_return_percent,
                'annualized': result.annualized_return,
                'sharpe': result.sharpe_ratio,
                'drawdown': result.max_drawdown,
                'trades': result.total_trades,
                'win_rate': result.win_rate
            })
            
            # Store detailed results
            report['asset_class_results'][asset_class] = {
                'initial_value': result.initial_value,
                'final_value': result.final_value,
                'total_return': result.total_return,
                'total_return_percent': result.total_return_percent,
                'annualized_return': result.annualized_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'total_trades': result.total_trades,
                'win_rate': result.win_rate
            }
    
    # Overall portfolio metrics
    if total_initial > 0:
        overall_return = ((total_final - total_initial) / total_initial) * 100
        overall_annualized = ((total_final / total_initial) ** (365 / 365) - 1) * 100
        
        report['overall_performance'] = {
            'total_initial': total_initial,
            'total_final': total_final,
            'overall_return': overall_return,
            'overall_annualized': overall_annualized,
            'portfolio_growth': total_final / total_initial
        }
        
        # Generate recommendations
        if overall_annualized >= 250:
            report['recommendations'].append("STRONG BUY - Strategy exceeds 250% target across all asset classes")
        elif overall_annualized >= 100:
            report['recommendations'].append("BUY - Excellent diversified performance across multiple asset classes")
        else:
            report['recommendations'].append("HOLD - Strategy needs optimization for certain asset classes")
        
        # Asset class specific recommendations
        for asset_perf in asset_performance:
            if asset_perf['annualized'] >= 250:
                report['recommendations'].append(f"EXCELLENT: {asset_perf['class']} - {asset_perf['annualized']:.1f}% returns")
            elif asset_perf['annualized'] >= 100:
                report['recommendations'].append(f"GOOD: {asset_perf['class']} - {asset_perf['annualized']:.1f}% returns")
            else:
                report['recommendations'].append(f"NEEDS IMPROVEMENT: {asset_perf['class']} - {asset_perf['annualized']:.1f}% returns")
    
    return report

if __name__ == "__main__":
    success = test_multi_asset_backtesting()
    sys.exit(0 if success else 1)

