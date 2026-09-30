from fastapi.testclient import TestClient

from setu.serving.app import app


client = TestClient(app)


def test_scam_scenario_creates_guardian_hold() -> None:
    response = client.post("/v1/risk/score", json={"payer_vpa": "asha@bankA", "payee_vpa": "quickcash77@bankC", "amount_inr": 24500, "channel": "collect", "timestamp": "2026-09-30T12:00:00+05:30", "lang": "ta"})
    body = response.json()
    assert response.status_code == 200
    assert body["tier"] == "hold"
    assert body["guardian_required"] is True
    assert body["reasons"]


def test_legitimate_small_payment_is_allowed() -> None:
    response = client.post("/v1/risk/score", json={"payer_vpa": "asha@bankA", "payee_vpa": "grocer@bankA", "amount_inr": 220, "channel": "pay", "timestamp": "2026-09-30T12:00:00+05:30", "lang": "en"})
    assert response.json()["tier"] == "allow"

