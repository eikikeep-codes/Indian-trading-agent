import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

def compute_indicators(df: pd.DataFrame, 
                       ema_fast: int = 20, 
                       ema_slow: int = 50, 
                       rsi_period: int = 14, 
                       volume_avg_period: int = 20,
                       atr_period: int = 14) -> pd.DataFrame:
    """
    Computes technical indicators and appends them as new columns.
    Uses the 'ta' library.
    """
    if df.empty or len(df) < max(ema_fast, ema_slow, rsi_period, volume_avg_period, atr_period):
        return pd.DataFrame()
        
    df = df.copy()

    # EMA
    df['EMA_fast'] = EMAIndicator(close=df['Close'], window=ema_fast, fillna=False).ema_indicator()
    df['EMA_slow'] = EMAIndicator(close=df['Close'], window=ema_slow, fillna=False).ema_indicator()

    # RSI
    df['RSI'] = RSIIndicator(close=df['Close'], window=rsi_period, fillna=False).rsi()

    # MACD
    macd = MACD(close=df['Close'], fillna=False)
    df['MACD_line'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()

    # ATR
    atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=atr_period, fillna=False)
    df['ATR'] = atr.average_true_range()

    # Volume Average
    df['Volume_Avg'] = df['Volume'].rolling(window=volume_avg_period).mean()

    # Support / Resistance (Basic recent n-day high/low)
    # We will compute 20-day high and 20-day low for structural breakouts
    df['Highest_20'] = df['High'].rolling(window=20).max()
    df['Lowest_20'] = df['Low'].rolling(window=20).min()

    # Ensure no overly huge inf or missing at the end
    # We'll forward fill the indicators if necessary, but typically recent rows have valid values.
    
    return df
