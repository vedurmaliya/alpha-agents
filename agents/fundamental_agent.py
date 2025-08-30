# NOTE: This agent's prompt has been updated to accept a `risk_profile`.
# This allows the LLM to tailor its analysis and recommendation based on
# whether it's advising a 'risk-averse' or 'risk-neutral' investor.

from langchain_core.prompts import ChatPromptTemplate
from infra.groq_client import groq_chat_client
from agents.schemas import FundamentalOutput
from scripts.ingest_documents import collection

SYSTEM_PROMPT = """You are a Fundamental Analyst Agent advising a {risk_profile} investor.
Your task is to analyze the provided snippets from a company's financial filings.

- For a 'risk-averse' investor, be highly critical. Emphasize risks, weak financials, or ambiguous statements. Only recommend BUY if the fundamentals are exceptionally strong.
- For a 'risk-neutral' investor, take a more balanced view, weighing growth potential against risks.

Based *only* on the information in the snippets, provide your analysis.
Respond with a JSON object that strictly follows this schema:
{{
  "company_overview": "Brief summary of the company based on the text.",
  "key_risks": ["List of key risks identified."],
  "financial_health_summary": "A summary of the company's financial health.",
  "recommendation": "BUY or SELL",
  "confidence": 0.0,
  "rationale": "Justification for your recommendation based on the snippets and the investor's risk profile."
}}"""

class FundamentalAgent:
    def __init__(self, retriever_k: int = 5):
        self.k = retriever_k
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Analyze the following context for ticker {ticker}:\n\n{context}")
        ])
        self.chain = self.prompt | groq_chat_client.with_structured_output(FundamentalOutput, method = "json_mode")

    def retrieve_context(self, ticker: str, query: str) -> str:
        """Retrieves relevant document chunks from ChromaDB."""
        results = collection.query(query_texts=[query], n_results=self.k, where={"ticker": ticker})
        return "\n---\n".join(results['documents'][0])

    def run(self, state: dict, debate_context: str = None) -> dict:
        """Executes the fundamental analysis."""
        ticker = state['ticker']
        risk_profile = state['risk_profile']
        
        # In a debate, the context is added to the prompt
        if debate_context:
            context = debate_context
        else:
            query = f"Provide a summary of financial health, growth, and key risks for {ticker}."
            context = self.retrieve_context(ticker, query)
        
        if not context:
            return FundamentalOutput(
                recommendation='SELL', 
                confidence=0.1,
                rationale=f"No financial filings found for ticker {ticker} in the database."
            ).dict()
        
        output = self.chain.invoke({
            "risk_profile": risk_profile,
            "ticker": ticker,
            "context": context
        })

        return output.dict()