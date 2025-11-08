def should_buy(price_history):
    if price_history[-1] > max(price_history[:-1]):
        return True
    return False
