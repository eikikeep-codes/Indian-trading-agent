import yfinance as yf
import pandas as pd
from typing import Dict
from tqdm import tqdm

def fetch_data_for_tickers(tickers: list, lookback_days: int) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for a list of tickers.
    
    Args:
        tickers: List of ticker strings (e.g., ['RELIANCE.NS'])
        lookback_days: Number of calendar days to look back
        
    Returns:
        Dictionary mapping ticker format string to a DataFrame of its data.
    """
    if not tickers:
        return {}
        
    print(f"Fetching data for {len(tickers)} tickers over the last {lookback_days} days...")
    
    # We download in batch for efficiency
    # group_by='ticker' returns a hierarchal dataframe if more than 1 ticker
    try:
        data = yf.download(tickers, period=f"{lookback_days}d", group_by='ticker', threads=True, progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

    ticker_data_map = {}
    
    if len(tickers) == 1:
        # If single ticker, columns are Open, High, Low, Close, Adj Close, Volume
        ticker = tickers[0]
        df = data.dropna()
        if not df.empty:
            ticker_data_map[ticker] = df
    else:
        # Multiple tickers parsing
        for ticker in tickers:
            if ticker in data.columns.levels[0]:
                df = data[ticker].dropna()
                # Ensure we have required columns
                if not df.empty and 'Close' in df.columns.levels[0] if isinstance(df.columns, pd.MultiIndex) else 'Close' in df.columns:
                    # Depending on yfinance version, columns could still be a multi-index after selecting ticker.
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1) # Or whatever level
                    ticker_data_map[ticker] = df
                    
    # Double check for 1.1.0 new format (yfinance latest format changes):
    # If the above fails, let's just do a sequential fetch with tqdm if dataframe parsing is messy
    # But usually, it's safer to download 1 by 1 for robustness against missing stocks
    
    return ticker_data_map

def fetch_data_sequential(tickers: list, lookback_days: int) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data sequentially to avoid MultiIndex issues and handle missing data cleanly.
    """
    ticker_data_map = {}
    print(f"Fetching data for {len(tickers)} tickers sequentially...")
    
    for ticker in tqdm(tickers):
        try:
            # We want roughly 'lookback_days' trading days. Setting period='1y' or 'max' or specific
            # Using 'y' or 'mo' or 'd'
            # yfinance periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            period_str = "1y"
            if lookback_days <= 100:
                period_str = "6mo"
            elif lookback_days <= 300:
                period_str = "1y"
            elif lookback_days <= 700:
                period_str = "2y"
            elif lookback_days > 700:
                period_str = "5y"

            tkr = yf.Ticker(ticker)
            df = tkr.history(period=period_str)
            
            if not df.empty and len(df) > 20: # Ensure enough data length
                # Keep only what we need
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                ticker_data_map[ticker] = df
        except Exception as e:
            # Silently skip errors on individual fetching
            pass
            
    return ticker_data_map
