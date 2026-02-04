from flask import Flask, jsonify, request
from backend.services.market import get_market
from backend.services.risk import get_risk
from backend.services.logistics import get_logistics

app = Flask(__name__)

# MVP용 entity registry (나중에 DB/CSV로 교체)
ENTITIES = {
    "PORT_BUSAN": {"type": "port", "name": "Busan Port", "country": "KR", "lat": 35.10, "lng": 129.04},
    "PORT_SINGAPORE": {"type": "port", "name": "Singapore Port", "country": "SG", "lat": 1.26, "lng": 103.84},
    "VESSEL_001": {"type": "vessel", "name": "MY CARGO 001", "country": "PA", "lat": 20.5, "lng": 120.2},
}

def build_defaults() -> dict:
    return {
        "qty": 100.0,
        "unit_price_usd": 15000.0,
        "freight_usd": 2500.0,
        "duty_rate": 0.03,
        "insurance_usd": 120.0,
        "fx_usdkrw": 1320.0,
    }

@app.get("/api/insight")
def insight():
    entity_id = request.args.get("entity_id", "").strip()
    entity = ENTITIES.get(entity_id)
    if not entity:
        return jsonify({"error": "unknown entity_id", "entity_id": entity_id}), 404

    payload = {
        "entity": {"id": entity_id, **entity},
        "market": get_market(entity.get("country", "US")),
        "risk": get_risk(entity_id),
        "logistics": get_logistics(entity),
        "defaults": build_defaults(),
    }
    return jsonify(payload)

@app.get("/api/entities")
def list_entities():
    # Streamlit이 지도에 찍을 엔티티 목록
    out = [{"id": k, **v} for k, v in ENTITIES.items()]
    return jsonify(out)

if __name__ == "__main__":
    # Windows에서 import 경로 문제 생기면:
    #   python -m backend.app  (형태로 실행하는 방식도 가능)
    app.run(host="0.0.0.0", port=8000, debug=True)
