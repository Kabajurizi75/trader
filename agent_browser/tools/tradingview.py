def scrape_tradingview(symbol: str):
    """
    Legacy wrapper for the new MarketDataAgent
    """
    try:
        from .market_data_agent import MarketDataAgent
        
        with MarketDataAgent() as agent:
            return agent.scrape_tradingview_data(symbol)
    except Exception as e:
        return {
            'symbol': symbol,
            'error': str(e),
            'source': 'tradingview_legacy',
            'success': False
        }
