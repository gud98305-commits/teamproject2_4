import random

def get_risk(entity_id: str) -> dict:
    """
    MVP: Mock risk scoring + top news.
    Later: RSS/News API + keyword scoring + LLM summary.
    """
    samples = [
        {"tag": "strike", "severity": 0.78, "headline": "Port labor negotiations stalled; slowdown risk rising."},
        {"tag": "weather", "severity": 0.55, "headline": "Adverse weather window may disrupt schedules."},
        {"tag": "geopolitics", "severity": 0.62, "headline": "Regulatory uncertainty could affect export flows."},
        {"tag": "congestion", "severity": 0.66, "headline": "Terminal congestion reported; dwell time increasing."},
    ]
    top = random.sample(samples, k=2)
    score = round(sum(x["severity"] for x in top) / len(top), 2)
    return {"risk_score": score, "top_news": top}
