import argparse
import json
from tabulate import tabulate

import src.config as config
from src.data_loader import fetch_data_sequential
from src.indicators import compute_indicators
from src.strategy import evaluate_strategy
from src.sentiment import fetch_sentiment_for_ticker
from src.signal_generator import generate_trade_signal
from src.backtester import run_backtest

def run_daily_scan():
    tickers = config.NIFTY_50_TICKERS
    data_map = fetch_data_sequential(tickers, lookback_days=config.DATA_LOOKBACK_DAYS)
    
    signals = []
    
    print("\nEvaluating strategy and fetching sentiment...")
    for ticker, df in data_map.items():
        df_ind = compute_indicators(df, 
                                    ema_fast=config.EMA_FAST,
                                    ema_slow=config.EMA_SLOW,
                                    rsi_period=config.RSI_PERIOD,
                                    volume_avg_period=config.VOLUME_AVG_PERIOD,
                                    atr_period=config.ATR_PERIOD)
                                    
        is_qualified, tech_score, tech_reasons, stats = evaluate_strategy(df_ind)
        
        if is_qualified:
            # Fetch sentiment only for qualified stocks to save time/requests
            sentiment_data = fetch_sentiment_for_ticker(ticker)
            
            signal = generate_trade_signal(ticker, tech_score, tech_reasons, stats, sentiment_data)
            if signal:
                signals.append(signal)
            
    # Sort by confidence score descending
    signals.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Save JSON
    with open('swing_signals.json', 'w') as f:
        json.dump(signals, f, indent=4)
        
    print(f"\nSaved {len(signals)} signals to swing_signals.json")
        
    if not signals:
        print("No qualified setups found today.")
        return
        
    # Print CLI Table
    table_data = []
    for s in signals:
        table_data.append([
            s['symbol'],
            s['entry'],
            s['stop_loss'],
            s['target'],
            s['risk_reward'],
            s['confidence'],
            s['sentiment']
        ])
        
    headers = ["Symbol", "Entry", "Stop Loss", "Target", "R:R", "Confidence", "Sentiment"]
    print("\n--- ACTIONABLE SWING TRADE SIGNALS ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    print("\nTop Signal Reasoning:")
    top_signal = signals[0]
    print(f"[{top_signal['symbol']}]")
    for r in top_signal['reasoning']:
        print(f" - {r}")


def main():
    parser = argparse.ArgumentParser(description="Indian Swing Trading Agent")
    parser.add_argument("--scan", action="store_true", help="Run daily market scan")
    parser.add_argument("--backtest", action="store_true", help="Run historical backtest")
    
    args = parser.parse_args()
    
    if args.backtest:
        # For backtest, we need at least 1-2 years of data
        data_map = fetch_data_sequential(config.NIFTY_50_TICKERS, lookback_days=400)
        stats = run_backtest(data_map)
        print("\n--- BACKTEST RESULTS ---")
        for k, v in stats.items():
            print(f"{k.capitalize()}: {v}")
            
    elif args.scan:
        run_daily_scan()
        
    else:
        print("Please specify an action. Use --scan or --backtest.")
        
if __name__ == "__main__":
    main()
