from __future__ import annotations


def _scenario(client, payment_type: str, key: str) -> dict:
    scenarios = client.get("/api/demo/scenarios").json()
    return scenarios[payment_type][key]


def test_safe_traditional_scenario_is_high_trust(client):
    payload = _scenario(client, "traditional", "safe")
    response = client.post("/api/risk/traditional", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_category"] == "high_trust"
    assert body["risk_level"] == "low"
    assert body["recommendation"] == "continue"
    assert body["trust_score"] >= 80
    assert body["model_name"] == "LightGBM"
    assert len(body["factors"]) >= 1


def test_suspicious_traditional_scenario_is_flagged(client):
    payload = _scenario(client, "traditional", "suspicious")
    response = client.post("/api/risk/traditional", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_category"] in ("high_risk", "critical_risk")
    assert body["risk_level"] == "high"
    assert body["recommendation"] == "cancel"
    assert body["trust_score"] < 40
    assert any("device" in f["message_en"].lower() or "cvv" in f["message_en"].lower()
               or "location" in f["message_en"].lower() or "amount" in f["message_en"].lower()
               for f in body["factors"])


def test_assessment_is_persisted_and_retrievable(client):
    payload = _scenario(client, "traditional", "suspicious")
    created = client.post("/api/risk/traditional", json=payload).json()

    fetched = client.get(f"/api/risk/traditional/{created['assessment_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["trust_score"] == created["trust_score"]

    explanation = client.get(f"/api/risk/traditional/{created['assessment_id']}/explanation")
    assert explanation.status_code == 200
    assert len(explanation.json()["risk_factors"]) > 0


def test_unknown_assessment_returns_structured_404(client):
    response = client.get("/api/risk/traditional/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "ASSESSMENT_NOT_FOUND"
    assert "correlation_id" in body["error"]


def test_web3_suspicious_scenario_is_high_risk(client):
    payload = _scenario(client, "web3", "suspicious")
    response = client.post("/api/risk/web3", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "high"
    assert body["recommendation"] == "cancel"


def test_health_and_ready_endpoints(client):
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["traditional_model"]["model_name"] == "LightGBM"

    ready = client.get("/ready").json()
    assert ready["database"] == "ok"
