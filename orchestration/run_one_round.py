# NOTE: This is the final version of the orchestrator. It now calculates a
# suggested portfolio weight in the finalization step, translating the
# agents' consensus score into an actionable investment size.

import argparse
import json
import datetime
import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain_core.prompts import ChatPromptTemplate
from infra.groq_client import groq_chat_client

# Import agent classes and the new PortfolioOutput schema
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent
from agents.valuation_agent import ValuationAgent
from agents.schemas import PortfolioOutput

# Define the state for the graph
class AgentState(TypedDict):
    ticker: str
    risk_profile: str
    turn_count: int
    max_turns: int
    fundamental_analysis: dict
    sentiment_analysis: dict
    valuation_analysis: dict
    collaborative_report: str
    debate_history: List[str]
    final_consensus: PortfolioOutput # Using the new schema for the final output
    
    


# Instantiate agents
fundamental_agent = FundamentalAgent()
sentiment_agent = SentimentAgent()
valuation_agent = ValuationAgent()

### Agent and Report Generation Nodes ###
def run_fundamental_agent(state: AgentState) -> dict:
    analysis = fundamental_agent.run(state)
    return {"fundamental_analysis": analysis, "debate_history": [f"Turn 1 (Fundamental): {analysis['rationale']} -> {analysis['recommendation']}"]}

def run_sentiment_agent(state: AgentState) -> dict:
    analysis = sentiment_agent.run(state)
    return {"sentiment_analysis": analysis, "debate_history": state['debate_history'] + [f"Turn 1 (Sentiment): {analysis['rationale']} -> {analysis['recommendation']}"]}

def run_valuation_agent(state: AgentState) -> dict:
    analysis = valuation_agent.run(state)
    return {"valuation_analysis": analysis, "debate_history": state['debate_history'] + [f"Turn 1 (Valuation): {analysis['rationale']} -> {analysis['recommendation']}"]}

def generate_collaborative_report(state: AgentState) -> dict:
    report_prompt = ChatPromptTemplate.from_template(
"""You are a senior investment strategist. Synthesize the following analyses from your junior agents into a single, comprehensive stock analysis report for {ticker}. The report should be well-structured with sections for 'Positive Indicators', 'Concerns', and a final 'Investment Conclusion'.

**Fundamental Analysis (for a {risk_profile} investor):** {fundamental_analysis}
**Sentiment Analysis (for a {risk_profile} investor):** {sentiment_analysis}
**Valuation Analysis (for a {risk_profile} investor):** {valuation_analysis}

Generate the final report based on this information."""
    )
    chain = report_prompt | groq_chat_client
    report = chain.invoke({
        "ticker": state['ticker'], "risk_profile": state['risk_profile'],
        "fundamental_analysis": state['fundamental_analysis']['rationale'],
        "sentiment_analysis": state['sentiment_analysis']['rationale'],
        "valuation_analysis": state['valuation_analysis']['rationale']
    }).content
    return {"collaborative_report": report}

def run_debate_step(state: AgentState) -> dict:
    turn = state['turn_count'] + 1
    debate_context = f"--- Initial Collaborative Report ---\n{state['collaborative_report']}\n\n--- Previous Analyses ---\nFundamental: {state['fundamental_analysis']['recommendation']}\nSentiment: {state['sentiment_analysis']['recommendation']}\nValuation: {state['valuation_analysis']['recommendation']}\n--- Your Task ---\nReview the report and your peers' stances. Re-state your recommendation and provide an updated rationale."
    f_analysis = fundamental_agent.run(state, debate_context)
    s_analysis = sentiment_agent.run(state, debate_context)
    v_analysis = valuation_agent.run(state, debate_context)
    history_update = [ f"Turn {turn} (Fundamental): {f_analysis['rationale']} -> {f_analysis['recommendation']}", f"Turn {turn} (Sentiment): {s_analysis['rationale']} -> {s_analysis['recommendation']}", f"Turn {turn} (Valuation): {v_analysis['rationale']} -> {v_analysis['recommendation']}"]
    return {"turn_count": turn, "fundamental_analysis": f_analysis, "sentiment_analysis": s_analysis, "valuation_analysis": v_analysis, "debate_history": state['debate_history'] + history_update}

def check_for_consensus(state: AgentState) -> str:
    recs = [state[key]['recommendation'] for key in ['fundamental_analysis', 'sentiment_analysis', 'valuation_analysis']]
    if len(set(recs)) == 1: return "consensus_reached"
    if state['turn_count'] >= state['max_turns']: return "max_turns_reached"
    return "continue_debate"

def calculate_suggested_weight(final_rec: str, scores: dict) -> float:
    """Calculates a portfolio weight based on the final recommendation and score."""
    if final_rec == 'SELL':
        return 0.0
    
    # Normalize the BUY score to a weight (e.g., 0.0 to 0.1 for 0% to 10%)
    total_score = sum(scores.values())
    buy_score_normalized = scores.get('BUY', 0.0) / total_score if total_score > 0 else 0.0
    
    # Scale to a max of 10% weight. A score of 1.0 (max possible) = 10% weight.
    suggested_weight = round(buy_score_normalized * 0.1, 4)
    return suggested_weight

def finalize_consensus(state: AgentState) -> dict:
    final_rec = state['fundamental_analysis']['recommendation']
    rationale = f"Consensus reached after {state['turn_count']} turn(s). All agents agree on a recommendation of {final_rec}."
    # In consensus, confidence is high. We use a proxy score.
    scores = {'BUY': 1.0, 'SELL': 0.0} if final_rec == 'BUY' else {'BUY': 0.0, 'SELL': 1.0}
    weight = calculate_suggested_weight(final_rec, scores)
    
    return {"final_consensus": PortfolioOutput(recommendation=final_rec, rationale=rationale, scores=scores, suggested_weight=weight).dict()}

def finalize_no_consensus(state: AgentState) -> dict:
    weights = {'fundamental': 0.5, 'sentiment': 0.2, 'valuation': 0.3}
    scores = {'BUY': 0.0, 'SELL': 0.0}
    analyses = {'fundamental': state['fundamental_analysis'], 'sentiment': state['sentiment_analysis'], 'valuation': state['valuation_analysis']}
    for name, analysis in analyses.items(): scores[analysis['recommendation']] += analysis['confidence'] * weights[name]
    
    final_rec = 'BUY' if scores['BUY'] > scores['SELL'] else 'SELL'
    rationale = f"No consensus after {state['max_turns']} turns. Final decision by weighted vote."
    weight = calculate_suggested_weight(final_rec, scores)
    
    return {"final_consensus": PortfolioOutput(recommendation=final_rec, rationale=rationale, scores=scores, suggested_weight=weight).dict()}

# Build and compile the graph
workflow = StateGraph(AgentState)
# ... [add_node and add_edge calls are the same as the previous version] ...
workflow.add_node("fundamental_agent", run_fundamental_agent)
workflow.add_node("sentiment_agent", run_sentiment_agent)
workflow.add_node("valuation_agent", run_valuation_agent)
workflow.add_node("generate_report", generate_collaborative_report)
workflow.add_node("debate_step", run_debate_step)
workflow.add_node("finalize_consensus", finalize_consensus)
workflow.add_node("finalize_no_consensus", finalize_no_consensus)
workflow.set_entry_point("fundamental_agent")
workflow.add_edge("fundamental_agent", "sentiment_agent")
workflow.add_edge("sentiment_agent", "valuation_agent")
workflow.add_edge("valuation_agent", "generate_report")
workflow.add_conditional_edges("generate_report", check_for_consensus, {"consensus_reached": "finalize_consensus", "continue_debate": "debate_step", "max_turns_reached": "finalize_no_consensus"})
workflow.add_conditional_edges("debate_step", check_for_consensus, {"consensus_reached": "finalize_consensus", "continue_debate": "debate_step", "max_turns_reached": "finalize_no_consensus"})
workflow.add_edge("finalize_consensus", END)
workflow.add_edge("finalize_no_consensus", END)
app = workflow.compile()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a multi-agent stock analysis with debate.")
    parser.add_argument('--ticker', required=True, help="Stock ticker symbol (e.g., AAPL).")
    parser.add_argument('--risk', default='risk-neutral', choices=['risk-averse', 'risk-neutral'], help="Investor risk profile.")
    args = parser.parse_args()

    initial_state = {"ticker": args.ticker, "risk_profile": args.risk, "turn_count": 1, "max_turns": 3}
    
    print(f"Running analysis for {args.ticker} with a {args.risk} profile...")
    final_state = app.invoke(initial_state)
    
    os.makedirs('runs', exist_ok=True)
    fname = f"runs/{args.ticker}_{args.risk}_{datetime.date.today()}.json"
    with open(fname, 'w') as f: json.dump(final_state, f, indent=2)
    
    print("\n--- Collaborative Report ---")
    print(final_state.get('collaborative_report', 'Not generated.'))
        
    print("\n--- Final Recommendation ---")
    print(json.dumps(final_state.get('final_consensus', {}), indent=2))
    print(f"\nFull run state saved to: {fname}")