# NOTE: This agent is now LLM-based. It first calculates quantitative metrics
# and then feeds them to an LLM with a specific risk-profile prompt to get a
# nuanced recommendation, rather than using a hard-coded rule.

import pandas as pd
import numpy as np
import os
from langchain_core.prompts import ChatPromptTemplate
from infra.groq_client import groq_chat_client
from agents.schemas import ValuationOutput

# agents/valuation_agent.py

SYSTEM_PROMPT = """You are a meticulous Valuation Analyst advising a {risk_profile} investor.
Your task is to interpret the provided quantitative metrics and decide whether to BUY or SELL a stock.

- For a 'risk-averse' investor, prioritize capital preservation. Recommend BUY only on stocks with strong positive returns AND low volatility. High volatility is a major red flag.
- For a 'risk-neutral' investor, focus on balanced growth. You can tolerate moderate volatility if the returns are compelling.

Based *only* on the metrics below, provide your recommendation.
Respond with a JSON object that strictly follows this schema:
{{
  "metrics": {{"annualized_return": 0.0, "annualized_volatility": 0.0}},
  "recommendation": "BUY or SELL",
  "confidence": 0.0,
  "rationale": "Justification for your recommendation based on the metrics and risk profile."
}}"""

class ValuationAgent:
    def __init__(self, price_data_folder: str = 'data/prices'):
        self.price_folder = price_data_folder
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Analyze the following metrics for ticker {ticker}:\n\nAnnualized Return: {annualized_return:.2f}\nAnnualized Volatility: {annualized_volatility:.2f}")
        ])
        self.chain = self.prompt | groq_chat_client.with_structured_output(ValuationOutput, method = "json_mode")

    def load_price_data(self, ticker: str) -> pd.DataFrame | None:
        """Loads price data from a Parquet file."""
        path = f'{self.price_folder}/{ticker}.parquet'
        if not os.path.exists(path):
            return None
        return pd.read_parquet(path)

    def compute_metrics(self, df: pd.DataFrame) -> dict:
        """Computes annualized return and volatility."""
        daily_returns = df['Close'].pct_change().dropna()
        if daily_returns.empty:
            return {'annualized_return': 0.0, 'annualized_volatility': 0.0}
        
        cumulative_return = (1 + daily_returns).prod() - 1
        num_trading_days = len(daily_returns)
        annualized_return = ((1 + cumulative_return) ** (252 / num_trading_days)) - 1 if num_trading_days > 0 else 0
        annualized_volatility = daily_returns.std() * np.sqrt(252)
        
        return {
            'annualized_return': float(annualized_return),
            'annualized_volatility': float(annualized_volatility)
        }

    def run(self, state: dict, debate_context: str = None) -> dict:
        """Executes the valuation analysis."""
        ticker = state['ticker']
        risk_profile = state['risk_profile']
        df = self.load_price_data(ticker)
        
        if df is None or df.empty:
            return ValuationOutput(
                recommendation='SELL', 
                confidence=0.1,
                rationale='No historical price data available.'
            ).dict()

        metrics = self.compute_metrics(df)
        
        # If in a debate, the context is added to the prompt
        if debate_context:
            human_prompt = f"Previous Debate Context:\n{debate_context}\n\nAnalyze the following metrics for ticker {ticker}:\n\nAnnualized Return: {metrics['annualized_return']:.2f}\nAnnualized Volatility: {metrics['annualized_volatility']:.2f}"
            output = self.chain.invoke({
                "risk_profile": risk_profile,
                "ticker": ticker,
                "annualized_return": metrics['annualized_return'],
                "annualized_volatility": metrics['annualized_volatility'],
                # This part of the prompt isn't directly used by the chain template but shows how you'd inject context
                "context": human_prompt 
            })
        else:
             output = self.chain.invoke({
                "risk_profile": risk_profile,
                "ticker": ticker,
                "annualized_return": metrics['annualized_return'],
                "annualized_volatility": metrics['annualized_volatility']
            })

        return output.dict()