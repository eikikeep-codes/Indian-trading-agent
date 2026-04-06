import pandas as pd
from typing import Tuple, List, Dict
import src.config as config

def evaluate_strategy(df: pd.DataFrame) -> Tuple[bool, int, List[str], Dict]:
    """
    Evaluates the swing trading strategy on the latest candle in the dataframe.
    
    Returns:
        is_qualified (bool): Whether it passes minimum criteria to be considered
        score (int): Technical score (0 to 100)
        reasons (List[str]): List of human-readable reasons
        stats (Dict): Dictionary containing key levels (entry, close, atr, etc.)
    """
    if df.empty or len(df) < 50:
        return False, 0, [], {}
        
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    reasons = []
    score = 0
    
    # Check 1: Trend Filter
    trend_bullish = last_row['Close'] > last_row['EMA_fast'] and last_row['EMA_fast'] > last_row['EMA_slow']
    if trend_bullish:
        score += 30
        reasons.append("Price is above 20 EMA and 50 EMA (Bullish Trend)")
        
    # Check 2: Momentum (RSI & MACD)
    rsi = last_row['RSI']
    momentum_rsi = config.RSI_LOWER_BOUND <= rsi <= config.RSI_UPPER_BOUND
    if momentum_rsi:
        score += 15
        reasons.append(f"RSI is at {rsi:.2f} (Within optimal 50-70 range)")
        
    macd_bullish = last_row['MACD_line'] > last_row['MACD_signal']
    if macd_bullish:
        score += 15
        reasons.append("MACD is above signal line (Bullish Momentum)")
        
    # Check 3: Breakout / Structure
    # Breakout: close above the 20-day high from yesterday
    breakout = last_row['Close'] > prev_row['Highest_20']
    
    # Pullback: close is above EMA20, but low touched or went below EMA20 recently 
    pullback = last_row['Close'] > last_row['EMA_fast'] and (last_row['Low'] <= last_row['EMA_fast'] or prev_row['Low'] <= prev_row['EMA_fast'])
    
    structure_passed = False
    if breakout:
        score += 20
        reasons.append("Recent breakout above 20-day resistance")
        structure_passed = True
    elif pullback:
        score += 15
        reasons.append("Bullish pullback to 20 EMA support")
        structure_passed = True

    # Check 4: Volume Confirmation
    vol_confirmation = last_row['Volume'] > (config.VOLUME_MULTIPLIER * last_row['Volume_Avg'])
    if vol_confirmation:
        score += 20
        reasons.append(f"High volume confirmation ({last_row['Volume'] / last_row['Volume_Avg']:.1f}x average)")
        
    # Check 5: Volatility / ATR constraints (avoid anomalies)
    atr = last_row['ATR']
    price = last_row['Close']
    atr_pct = (atr / price) * 100
    if 1.0 <= atr_pct <= 8.0:
        # reasonable volatility for swing trading
        pass
    else:
        # Penalize if extremely illiquid/volatile or dead
        score -= 10
        reasons.append(f"Warning: Volatility (ATR %) is {atr_pct:.2f}% which is outside ideal range.")

    is_qualified = score >= 50 and trend_bullish and structure_passed
    
    stats = {
        'close': last_row['Close'],
        'atr': last_row['ATR'],
        'lowest_20': last_row['Lowest_20'],
        'highest_20': last_row['Highest_20'],
        'ema_20': last_row['EMA_fast']
    }
    
    return is_qualified, score, reasons, stats
