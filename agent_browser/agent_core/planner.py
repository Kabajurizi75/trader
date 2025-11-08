from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def plan_tasks(goal: str) -> List[Dict]:
    """
    Enhanced task planner that creates structured task plans based on goals
    """
    goal_lower = goal.lower()
    tasks = []
    
    # Market data collection tasks
    if any(keyword in goal_lower for keyword in ["price", "bitcoin", "btc", "crypto", "market"]):
        tasks.extend([
            {
                "action": "scrape_coinmarketcap",
                "priority": 1,
                "description": "Get current Bitcoin price and market data from CoinMarketCap",
                "expected_output": "price, volume, market_cap"
            },
            {
                "action": "scrape_tradingview", 
                "priority": 2,
                "description": "Get trading data and charts from TradingView",
                "expected_output": "price, change_percent, volume"
            }
        ])
    
    # News analysis tasks
    if any(keyword in goal_lower for keyword in ["news", "sentiment", "analysis", "summary"]):
        tasks.extend([
            {
                "action": "analyze_sentiment",
                "priority": 2,
                "description": "Analyze market sentiment from recent news",
                "expected_output": "sentiment, confidence, analysis"
            },
            {
                "action": "summarize_news",
                "priority": 3,
                "description": "Summarize recent market news",
                "expected_output": "summary, key_topics"
            }
        ])
    
    # Trading strategy tasks
    if any(keyword in goal_lower for keyword in ["trade", "buy", "sell", "strategy"]):
        tasks.extend([
            {
                "action": "check_trading_signals",
                "priority": 1,
                "description": "Check current trading signals and indicators",
                "expected_output": "signals, recommendations"
            },
            {
                "action": "analyze_market_conditions",
                "priority": 2,
                "description": "Analyze current market conditions for trading",
                "expected_output": "market_state, risk_level"
            }
        ])
    
    # Default fallback
    if not tasks:
        tasks.append({
            "action": "general_market_overview",
            "priority": 1,
            "description": "Get general market overview and current status",
            "expected_output": "market_summary"
        })
    
    # Sort by priority
    tasks.sort(key=lambda x: x['priority'])
    
    logger.info(f"Planned {len(tasks)} tasks for goal: {goal}")
    return tasks

def execute_task_plan(tasks: List[Dict]) -> Dict:
    """
    Execute a planned list of tasks using available tools
    """
    results = {
        'goal_completed': False,
        'tasks_executed': 0,
        'task_results': [],
        'errors': []
    }
    
    try:
        from ..tools.market_data_agent import MarketDataAgent
        
        with MarketDataAgent() as agent:
            for task in tasks:
                try:
                    task_result = _execute_single_task(task, agent)
                    results['task_results'].append(task_result)
                    results['tasks_executed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error executing task {task['action']}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        
        results['goal_completed'] = len(results['errors']) == 0
        
    except Exception as e:
        results['errors'].append(f"Failed to initialize MarketDataAgent: {str(e)}")
        logger.error(f"Critical error in task execution: {e}")
    
    return results

def _execute_single_task(task: Dict, agent) -> Dict:
    """
    Execute a single task using the appropriate method
    """
    action = task['action']
    
    if action == "scrape_coinmarketcap":
        return agent.scrape_coinmarketcap_bitcoin()
    elif action == "scrape_tradingview":
        return agent.scrape_tradingview_data("BTCUSDT")
    elif action == "general_market_overview":
        return agent.get_comprehensive_data(['BTC'])
    else:
        # For tasks that require RAG pipeline integration
        return {
            'action': action,
            'status': 'not_implemented',
            'message': f'Task {action} requires RAG pipeline integration'
        }
