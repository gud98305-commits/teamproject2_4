import random

def get_market(country_code: str) -> dict:
    """
    MVP: Mock market indicators.
    Later: replace with yfinance / paid APIs.
    """
    fx = {
        "USD/KRW": 1320 + random.randint(-15, 15),
        "USD/CNY": round(7.10 + random.uniform(-0.05, 0.05), 3),
        "USD/JPY": round(148 + random.uniform(-2, 2), 2),
    }

    commodities = {
        "Copper": round(3.8 + random.uniform(-0.1, 0.1), 3),
        "Aluminum": 2300 + random.randint(-50, 50),
        "Nickel": 16000 + random.randint(-300, 300),
    }

    freight = {
        "Container Index (mock)": 2100 + random.randint(-120, 120)
    }

    return {"country": country_code, "fx": fx, "commodities": commodities, "freight": freight}
