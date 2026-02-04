from datetime import datetime, timedelta
import random

def get_logistics(entity: dict) -> dict:
    """
    MVP: Mock logistics.
    Later: AIS / Port data / visibility APIs.
    """
    now = datetime.utcnow()
    eta = now + timedelta(hours=random.randint(24, 120))
    return {
        "status": random.choice(["Under Way", "Anchored", "In Port", "Delayed"]),
        "speed_kn": round(random.uniform(8, 18), 1),
        "eta_utc": eta.strftime("%Y-%m-%d %H:%M"),
    }
