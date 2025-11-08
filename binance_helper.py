"""
Helper module to load local Binance API module
Prevents import conflicts with installed binance package
"""

import os
import sys
import importlib.util

def load_binance_module():
    """Load the local binance.py module from trading_bot/api/"""
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    binance_api_path = os.path.join(current_dir, 'trading_bot', 'api')
    binance_module_path = os.path.join(binance_api_path, 'binance.py')
    
    if not os.path.exists(binance_module_path):
        # Try alternative path
        binance_api_path = os.path.join(current_dir, '..', 'trading_bot', 'api')
        binance_module_path = os.path.join(binance_api_path, 'binance.py')
        binance_api_path = os.path.abspath(binance_api_path)
    
    if not os.path.exists(binance_module_path):
        raise ImportError(f"Local binance.py module not found. Searched: {binance_module_path}")
    
    # Add to path if not already there
    if binance_api_path not in sys.path:
        sys.path.insert(0, binance_api_path)
    
    # Load module using importlib
    spec = importlib.util.spec_from_file_location("local_binance", binance_module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load binance module from {binance_module_path}")
    
    local_binance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(local_binance)
    
    return local_binance

# Convenience functions
def get_binance_functions():
    """Get all Binance functions from local module"""
    local_binance = load_binance_module()
    return {
        'get_market_price': local_binance.get_market_price,
        'get_24hr_stats': local_binance.get_24hr_stats,
        'place_order': local_binance.place_order,
        'get_binance_api': local_binance.get_binance_api,
        'get_account_balance': local_binance.get_account_balance
    }

