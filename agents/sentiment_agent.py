# NOTE: This agent's prompt has also been updated to accept a `risk_profile`.
# A risk-averse investor might interpret neutral or slightly negative news
# more cautiously than a risk-neutral one.

import json
import os
from langchain_core.prompts import ChatPromptTemplate
from infra.groq_client import groq_chat_client
from agents.schemas import SentimentOutput

SYSTEM_PROMPT = """You are a Sentiment Analyst Agent advising a {risk_profile} investor.
Your task is to analyze the sentiment of the provided financial news.

- For a 'risk-averse' investor, be cautious. Ambiguous or slightly negative news should lean towards a SELL recommendation. Overwhelmingly positive news is required for a BUY.
- For a 'risk-neutral' investor, provide a balanced assessment. Weigh the positive and negative news to determine the likely market reaction.

Based on the news, provide your analysis.
Respond with a JSON object that strictly follows this schema:
{{
  "sentiment_score": 0.0,
  "recommendation": "BUY or SELL",
  "confidence": 0.0,
  "rationale": "Justification for your recommendation based on the news and risk profile."
}}"""

class SentimentAgent:
    def __init__(self, max_news_items: int = 10):
        self.max_items = max_news_items
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Analyze the sentiment of the following news for ticker {ticker}:\n\n{news_context}")
        ])
        self.chain = self.prompt | groq_chat_client.with_structured_output(SentimentOutput, method = "json_mode")

    def get_news(self, ticker: str) -> str:
        """Loads news from a local JSON file (for PoC)."""
        news_path = f"data/news/{ticker}.json"
        if not os.path.exists(news_path):
            os.makedirs(os.path.dirname(news_path), exist_ok=True)
            dummy_news = [
                {"title": f"{ticker} Reports Record Earnings", "summary": "Shares surged after the company beat expectations."},
                {"title": f"Regulatory Concerns Loom Over {ticker}", "summary": "Investors are cautious amid potential government action."}
            ]
            with open(news_path, 'w') as f:
                json.dump(dummy_news, f)

        with open(news_path, 'r') as f:
            news_items = json.load(f)
        
        snippets = [f"Title: {item['title']}\nSummary: {item['summary']}" for item in news_items[:self.max_items]]
        return "\n---\n".join(snippets)

    def run(self, state: dict, debate_context: str = None) -> dict:
        """Executes the sentiment analysis."""
        ticker = state['ticker']
        risk_profile = state['risk_profile']
        
        if debate_context:
            news_context = debate_context
        else:
            news_context = self.get_news(ticker)
        
        if not news_context:
            return SentimentOutput(
                recommendation='SELL', 
                confidence=0.1,
                rationale="No news available for analysis."
            ).dict()
            
        output = self.chain.invoke({
            "risk_profile": risk_profile,
            "ticker": ticker, 
            "news_context": news_context
        })
            
        return output.dict()