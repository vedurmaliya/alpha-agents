import argparse
import yfinance as yf
import pandas as pd
import os

def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetches historical stock prices using yfinance."""
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch and save historical stock price data.")
    parser.add_argument('--ticker', required=True, help="Stock ticker symbol (e.g., AAPL).")
    parser.add_argument('--start', default='2023-01-01', help="Start date in YYYY-MM-DD format.")
    parser.add_argument('--end', default='2024-06-30', help="End date in YYYY-MM-DD format.")
    args = parser.parse_args()

    data_dir = 'data/prices'
    os.makedirs(data_dir, exist_ok=True)
    
    df = fetch_price_data(args.ticker, args.start, args.end)
    output_path = f'{data_dir}/{args.ticker}.parquet'
    df.to_parquet(output_path)
    print(f'Saved price data to: {output_path}')