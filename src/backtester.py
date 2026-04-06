import pandas as pd
from typing import Dict
from tqdm import tqdm
import src.config as config
import src.indicators as indicators
from src.strategy import evaluate_strategy
from src.signal_generator import calculate_trade_levels

def run_backtest(ticker_data_map: Dict[str, pd.DataFrame]) -> dict:
    """
    Runs a historical backtest of the technical strategy over the provided data.
    Assumes data is at least 1 year long.
    """
    trades = []
    
    print("Running Backtest on Technical Strategy...")
    for ticker, df in tqdm(ticker_data_map.items()):
        # Compute indicators for the whole dataframe
        df_ind = indicators.compute_indicators(df, 
                                               ema_fast=config.EMA_FAST,
                                               ema_slow=config.EMA_SLOW,
                                               rsi_period=config.RSI_PERIOD,
                                               volume_avg_period=config.VOLUME_AVG_PERIOD,
                                               atr_period=config.ATR_PERIOD)
                                               
        if df_ind.empty or len(df_ind) < 60:
            continue
            
        in_trade = False
        entry_price = 0
        stop_loss = 0
        target = 0
        
        # We start checking from day 50 onwards to have valid indicators
        for i in range(50, len(df_ind) - 1):
            current_date = df_ind.index[i]
            current_slice = df_ind.iloc[:i+1]
            
            if not in_trade:
                # Check for signal
                is_qualified, score, _, stats = evaluate_strategy(current_slice)
                
                if is_qualified:
                    # Enter trade at next day open
                    next_day = df_ind.iloc[i+1]
                    entry_price = next_day['Open']
                    
                    stop_loss, target, _ = calculate_trade_levels(entry_price, stats['atr'], stats['lowest_20'], stats['highest_20'])
                    if stop_loss is not None:
                        in_trade = True
            else:
                # We are in a trade, check if target or stop loss hit today
                day_data = df_ind.iloc[i]
                high = day_data['High']
                low = day_data['Low']
                
                if low <= stop_loss:
                    # Stopped out
                    trades.append({
                        "ticker": ticker,
                        "entry": entry_price,
                        "exit": stop_loss,
                        "profit_pct": ((stop_loss - entry_price) / entry_price) * 100,
                        "outcome": "LOSS"
                    })
                    in_trade = False
                elif high >= target:
                    # Target hit
                    trades.append({
                        "ticker": ticker,
                        "entry": entry_price,
                        "exit": target,
                        "profit_pct": ((target - entry_price) / entry_price) * 100,
                        "outcome": "WIN"
                    })
                    in_trade = False
                    
    # Compile Stats
    if not trades:
        return {"total_trades": 0, "win_rate": 0.0, "avg_return": 0.0, "max_drawdown": 0.0}
        
    wins = [t for t in trades if t['outcome'] == 'WIN']
    win_rate = len(wins) / len(trades) * 100
    
    avg_return = sum([t['profit_pct'] for t in trades]) / len(trades)
    
    # Simple max drawdown estimate (sum of consecutive losses)
    # A proper portfolio level drawdown needs equity curve, 
    # but here we just compute max consecutive loss sum for simplicity.
    max_dd = 0
    current_dd = 0
    for t in trades:
        if t['profit_pct'] < 0:
            current_dd += t['profit_pct']
            max_dd = min(max_dd, current_dd)
        else:
            current_dd = 0 # reset on wins for a crude measure

    return {
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 2),
        "max_drawdown": round(max_dd, 2)
    }
