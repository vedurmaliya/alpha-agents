# NOTE: This file is updated to include a `PortfolioOutput` schema.
# This schema will structure the final output, including the new `suggested_weight`.

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class AgentOutput(BaseModel):
    recommendation: Literal['BUY', 'SELL'] = Field(description="The final investment recommendation, either BUY or SELL.")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence in the recommendation, from 0.0 to 1.0.")
    rationale: str = Field(description="A brief justification for the recommendation.")
    extra: Dict[str, Any] = Field({}, description="Additional data or metadata from the agent's analysis.")

class FundamentalOutput(AgentOutput):
    company_overview: str = ""
    key_risks: List[str] = []
    financial_health_summary: str = ""

class SentimentOutput(AgentOutput):
    sentiment_score: float = Field(0.0, ge=-1.0, le=1.0, description="Overall sentiment score from -1.0 (very negative) to 1.0 (very positive).")

class ValuationOutput(AgentOutput):
    metrics: Dict[str, float] = Field({}, description="Key valuation metrics like annualized volatility and return.")

class PortfolioOutput(BaseModel):
    recommendation: Literal['BUY', 'SELL']
    rationale: str
    scores: Dict[str, float]
    suggested_weight: float = Field(0.0, ge=0.0, le=0.1, description="Suggested portfolio weight, from 0.0 (0%) to 0.1 (10%).")