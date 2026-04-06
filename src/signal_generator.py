import src.config as config

def calculate_trade_levels(entry: float, atr: float, lowest_20: float, highest_20: float) -> tuple:
    """
    Calculates Stop Loss and Target using ATR, recent swing structure, and Fibonacci levels.
    Returns: (stop_loss, target, risk_reward)
    """
    # 1. Base Stop Loss (ATR and Swing Low)
    sl_atr = entry - (config.ATR_MULTIPLIER * atr)
    base_sl = max(sl_atr, lowest_20 - (0.5 * atr))
    
    # 2. Fibonacci levels calculation (Retracement from Swing Low to Swing High)
    swing_range = highest_20 - lowest_20
    if swing_range <= 0 or entry >= highest_20: 
        # If entry is higher than the recent high (breakout), use extensions
        fib_ext_1618 = lowest_20 + (swing_range * 1.618)
        fib_ext_2618 = lowest_20 + (swing_range * 2.618)
        
        stop_loss = round(base_sl, 2)
        risk = entry - stop_loss
        if risk <= 0: return None, None, None
        
        # Calculate standard target
        std_target = entry + (config.RISK_REWARD_MIN * risk)
        
        # Determine closest fib extension that gives at least RISK_REWARD_MIN
        if fib_ext_1618 >= std_target:
            target = fib_ext_1618
        elif fib_ext_2618 >= std_target:
            target = fib_ext_2618
        else:
            target = std_target
    else:
        # We are inside the range (pullback). Use retracement logic
        fib_ret_0382 = highest_20 - (swing_range * 0.382)
        fib_ret_0500 = highest_20 - (swing_range * 0.500)
        fib_ret_0618 = highest_20 - (swing_range * 0.618)
        fib_ret_0786 = highest_20 - (swing_range * 0.786)
        
        # Stop loss logic: Find a fib level below the entry
        fib_sl_candidates = [f for f in [fib_ret_0382, fib_ret_0500, fib_ret_0618, fib_ret_0786, lowest_20] if f < entry]
        
        if fib_sl_candidates:
            best_fib_support = fib_sl_candidates[0]
            fib_sl = best_fib_support - (0.5 * atr)
            stop_loss = round(max(base_sl, fib_sl), 2)
        else:
            stop_loss = round(base_sl, 2)
            
        risk = entry - stop_loss
        if risk <= 0: return None, None, None
        
        # Target: prior high or 1.618 extension ensures adequate risk/reward
        std_target = entry + (config.RISK_REWARD_MIN * risk)
        
        if highest_20 >= std_target:
            target = highest_20
        else:
            fib_ext_1618 = lowest_20 + (swing_range * 1.618)
            if fib_ext_1618 >= std_target:
                target = fib_ext_1618
            else:
                target = std_target

    risk_reward = round((target - entry) / risk, 2)
    return stop_loss, round(target, 2), risk_reward


def generate_trade_signal(ticker: str, tech_score: int, tech_reasons: list, stats: dict, sentiment_data: dict) -> dict:
    """
    Combines technical and sentiment analysis to generate a final trade setup.
    """
    entry = stats['close']
    atr = stats['atr']
    lowest_20 = stats['lowest_20']
    highest_20 = stats['highest_20']
    
    stop_loss, target, risk_reward = calculate_trade_levels(entry, atr, lowest_20, highest_20)
    if stop_loss is None:
        return None  # Invalid setup
    
    # Calculate Confidence Score
    normalized_tech = min((tech_score / 100.0) * 70.0, 70.0)
    
    sent_val = sentiment_data['score'] # -1.0 to 1.0
    normalized_sent = 15.0 + (sent_val * 15.0)
    
    confidence = round(normalized_tech + normalized_sent)
    
    # Add sentiment reasoning and signal adjustments
    reasons = tech_reasons.copy()
    reasons.append("Applied Fibonacci levels for SL & Target optimization")
    if sentiment_data['label'] == 'Positive':
        reasons.append(f"Positive news sentiment (Score: {sent_val:.2f})")
    elif sentiment_data['label'] == 'Negative':
        reasons.append(f"Negative news sentiment (Score: {sent_val:.2f})")
        confidence -= 10
    else:
        reasons.append(f"Neutral news sentiment (Score: {sent_val:.2f})")

    signal = {
        "symbol": ticker,
        "entry": round(entry, 2),
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": risk_reward,
        "confidence": confidence,
        "sentiment": sentiment_data['label'],
        "reasoning": reasons
    }
    
    return signal
