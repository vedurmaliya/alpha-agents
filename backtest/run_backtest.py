# NOTE: This is the main script for the back-testing engine. It simulates the
# process of building and tracking a portfolio based on the agents' decisions
# on a specific historical date.
from dotenv import load_dotenv
load_dotenv()
import argparse
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

# Important: We import the compiled LangGraph app from the orchestration script
from orchestration.run_one_round import app

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculates the annualized Sharpe ratio."""
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())

def run_backtest(tickers: list, rebalance_date: str, end_date: str, risk_profile: str):
    """
    Runs a back-test for a given list of tickers and date range.
    """
    print(f"--- Starting Back-test ---")
    print(f"Universe: {tickers}")
    print(f"Rebalance Date: {rebalance_date}, End Date: {end_date}\n")
    
    portfolio = {}
    
    # 1. Run Agent Analysis for each stock in the universe
    for ticker in tickers:
        print(f"Analyzing {ticker} for {rebalance_date}...")
        initial_state = {
            "ticker": ticker,
            "risk_profile": risk_profile,
            "turn_count": 1,
            "max_turns": 3
        }
        # Note: For a true historical back-test, you would need to ensure your
        # data sources (news, filings, prices) are snapshot to the rebalance_date.
        # This PoC uses current data for analysis but simulates portfolio tracking.
        final_state = app.invoke(initial_state)
        
        recommendation = final_state.get('final_consensus', {})
        if recommendation.get('recommendation') == 'BUY':
            weight = recommendation.get('suggested_weight', 0.0)
            if weight > 0:
                portfolio[ticker] = weight
                print(f"  -> Decision: BUY, Suggested Weight: {weight:.2%}")
            else:
                print(f"  -> Decision: BUY, but weight is 0. Skipping.")
        else:
            print(f"  -> Decision: SELL or Hold. Excluding from portfolio.")

    if not portfolio:
        print("\nNo stocks were recommended for purchase. Back-test cannot proceed.")
        return

    # 2. Normalize weights so they sum to 1
    total_weight = sum(portfolio.values())
    normalized_portfolio = {ticker: weight / total_weight for ticker, weight in portfolio.items()}
    
    print("\n--- Final Portfolio ---")
    for ticker, weight in normalized_portfolio.items():
        print(f"{ticker}: {weight:.2%}")
        
    # 3. Fetch historical data for portfolio and benchmark (S&P 500)
    
    portfolio_tickers = list(normalized_portfolio.keys())
    all_tickers = portfolio_tickers + ['SPY']
    price_data = yf.download(all_tickers, start=rebalance_date, end=end_date)
    price_data = price_data.loc[:, "Adj Close"]
    
    # 4. Calculate Portfolio Returns
    returns = price_data.pct_change().dropna()
    portfolio_returns = pd.Series(0.0, index=returns.index)
    
    for ticker, weight in normalized_portfolio.items():
        portfolio_returns += returns[ticker] * weight
        
    # 5. Calculate Benchmark Returns
    benchmark_returns = returns['SPY']
    
    # 6. Calculate Performance Metrics
    cumulative_portfolio_returns = (1 + portfolio_returns).cumprod() - 1
    cumulative_benchmark_returns = (1 + benchmark_returns).cumprod() - 1
    
    portfolio_sharpe = calculate_sharpe_ratio(portfolio_returns)
    benchmark_sharpe = calculate_sharpe_ratio(benchmark_returns)
    
    print("\n--- Performance Results ---")
    print(f"Final Portfolio Return: {cumulative_portfolio_returns.iloc[-1]:.2%}")
    print(f"Final Benchmark Return: {cumulative_benchmark_returns.iloc[-1]:.2%}")
    print(f"Portfolio Sharpe Ratio: {portfolio_sharpe:.2f}")
    print(f"Benchmark Sharpe Ratio: {benchmark_sharpe:.2f}")

    # 7. Plot and Save Results
    plt.figure(figsize=(12, 6))
    plt.plot(cumulative_portfolio_returns.index, cumulative_portfolio_returns, label='Agent Portfolio')
    plt.plot(cumulative_benchmark_returns.index, cumulative_benchmark_returns, label='S&P 500 (SPY)')
    plt.title(f'Portfolio Performance ({rebalance_date} to {end_date})')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)
    
    os.makedirs('runs', exist_ok=True)
    chart_path = f"runs/backtest_{rebalance_date}_{risk_profile}.png"
    plt.savefig(chart_path)
    print(f"\nPerformance chart saved to: {chart_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a back-test of the AlphaAgents system.")
    parser.add_argument('--tickers', nargs='+', default=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META'], help="Space-separated list of stock tickers.")
    parser.add_argument('--start', default='2024-01-01', help="Portfolio rebalance date (YYYY-MM-DD).")
    parser.add_argument('--end', default=datetime.now().strftime('%Y-%m-%d'), help="End date for the back-test (YYYY-MM-DD).")
    parser.add_argument('--risk', default='risk-neutral', choices=['risk-averse', 'risk-neutral'], help="Investor risk profile.")
    
    args = parser.parse_args()
    
    run_backtest(tickers=args.tickers, rebalance_date=args.start, end_date=args.end, risk_profile=args.risk)