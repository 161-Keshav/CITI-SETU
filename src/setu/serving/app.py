from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from time import perf_counter
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from setu.adapters import MockRail
from setu.audit import AuditLog
from setu.config import settings
from setu.explain import build_reasons
from setu.guardian import GuardianService, HoldState


class Channel(StrEnum):
    PAY = "pay"
    COLLECT = "collect"
    QR = "qr"


class ScoreRequest(BaseModel):
    payer_vpa: str = Field(min_length=4, max_length=80)
    payee_vpa: str = Field(min_length=4, max_length=80)
    amount_inr: float = Field(gt=0, le=500_000)
    channel: Channel
    timestamp: datetime
    lang: Literal["en", "hi", "ta", "te"] = "en"

    @field_validator("payer_vpa", "payee_vpa")
    @classmethod
    def vpa_has_handle(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("VPA must include a bank handle")
        return value


class GuardianEnrollment(BaseModel):
    payer_vpa: str
    guardian_name: str = Field(min_length=2, max_length=80)


class HoldDecision(BaseModel):
    token: str
    decision: Literal["approve", "reject"]


class PaymentRequest(ScoreRequest):
    pass


app = FastAPI(title="SETU-Shield API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    # Vite may bind either hostname during local development. Keep this explicit
    # rather than opening the API to arbitrary browser origins.
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
guardian = GuardianService(settings.secret, settings.hold_minutes)
audit = AuditLog()
rail = MockRail()
alerts: list[dict[str, object]] = []


def risk_policy(request: ScoreRequest) -> tuple[float, list[tuple[str, float]]]:
    flagged_payee = request.payee_vpa.lower().startswith(("quickcash", "mule", "scam"))
    first_time_large = request.amount_inr >= 10_000
    score = 0.08
    codes: list[tuple[str, float]] = []
    if request.channel == Channel.COLLECT:
        score += 0.32
        codes.append(("UNSOLICITED_COLLECT", 0.32))
    if first_time_large:
        score += 0.28
        codes.append(("FIRST_TIME_PAYEE_LARGE", 0.28))
    if flagged_payee:
        score += 0.4
        codes.insert(0, ("FAN_IN_BURST", 0.41))
        codes.append(("FAST_PASS_THROUGH", 0.24))
    return min(score, 0.98), codes or [("LINKED_TO_FLAGGED", 0.08)]


def score(request: ScoreRequest) -> dict[str, object]:
    started = perf_counter()
    if not settings.scorer_available:
        response = {"risk_score": None, "tier": "allow", "reasons": [], "guardian_required": False, "hold_id": None, "degraded": True}
    else:
        risk_score, codes = risk_policy(request)
        tier = "allow" if risk_score < 0.35 else "warn" if risk_score < 0.7 else "hold"
        reason_models = build_reasons(codes, request.lang)
        response = {
            "risk_score": round(risk_score, 2),
            "tier": tier,
            "reasons": [reason.__dict__ for reason in reason_models],
            "guardian_required": False,
            "hold_id": None,
            "degraded": False,
        }
        if tier == "hold" and request.payer_vpa in guardian.enrollments:
            hold, token = guardian.create(request.payer_vpa, request.payee_vpa, request.amount_inr, reason_models[0].text_localized)
            response.update({"guardian_required": True, "hold_id": hold.id, "guardian_link": f"/g/{token}"})
    response["model_version"] = settings.model_version
    response["latency_ms"] = round((perf_counter() - started) * 1000, 2)
    safe = {"tier": response["tier"], "model_version": settings.model_version, "reason_codes": [r["code"] for r in response["reasons"]]}
    audit.append("risk_scored", safe)
    if response["tier"] in {"warn", "hold"}:
        alerts.insert(0, {"id": f"a_{len(alerts) + 1}", "payee": request.payee_vpa, "tier": response["tier"], "reason_codes": safe["reason_codes"], "at": datetime.now().isoformat()})
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, bool]:
    return {"ready": True, "scorer_available": settings.scorer_available}


@app.post("/v1/risk/score")
def risk_score(request: ScoreRequest) -> dict[str, object]:
    return score(request)


@app.post("/v1/payments")
def payment(request: PaymentRequest) -> dict[str, object]:
    response = score(request)
    if response["tier"] == "hold":
        return {"status": "HELD", **response}
    if response["tier"] == "warn":
        return {"status": "REQUIRES_CONFIRMATION", **response}
    result = rail.initiate_collect(request.payer_vpa, request.payee_vpa, request.amount_inr) if request.channel == Channel.COLLECT else rail.initiate_pay(request.payer_vpa, request.payee_vpa, request.amount_inr)
    return {"status": result.status, "reference": result.reference, **response}


@app.post("/v1/guardian/enroll")
def enroll(request: GuardianEnrollment) -> dict[str, str]:
    guardian.enroll(request.payer_vpa, request.guardian_name)
    return {"status": "enrolled"}


@app.get("/v1/holds/{hold_id}")
def get_hold(hold_id: str) -> dict[str, object]:
    try:
        return guardian.get(hold_id).public()
    except KeyError as exc:
        raise HTTPException(404, "Hold not found") from exc


@app.get("/v1/guardian/{token}")
def guardian_preview(token: str) -> dict[str, object]:
    try:
        hold = guardian._decode(token)
        return {"hold": guardian.get(hold.id).public()}
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc


@app.post("/v1/holds/{hold_id}/decision")
def decide(hold_id: str, request: HoldDecision) -> dict[str, object]:
    try:
        hold = guardian.decision(hold_id, request.token, request.decision)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    audit.append("guardian_decision", {"hold_id": hold.id, "state": hold.state})
    return hold.public()


@app.post("/v1/holds/{hold_id}/cancel")
def cancel(hold_id: str) -> dict[str, object]:
    try:
        hold = guardian.cancel(hold_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    audit.append("hold_cancelled", {"hold_id": hold.id})
    return hold.public()


@app.get("/v1/ops/alerts")
def recent_alerts() -> dict[str, object]:
    return {"alerts": alerts[:25]}


@app.get("/v1/ops/graph")
def graph() -> dict[str, object]:
    return {"nodes": [{"id": "asha@bankA", "risk": 0.1}, {"id": "quickcash77@bankC", "risk": 0.91}, {"id": "mule-02@bankB", "risk": 0.82}, {"id": "sink@bankA", "risk": 0.66}], "edges": [{"source": "asha@bankA", "target": "quickcash77@bankC"}, {"source": "quickcash77@bankC", "target": "mule-02@bankB"}, {"source": "mule-02@bankB", "target": "sink@bankA"}]}


@app.get("/v1/model/info")
def model_info() -> dict[str, object]:
    return {"version": settings.model_version, "type": "deterministic demo policy", "data": "synthetic", "advisory": True}


@app.websocket("/ws/alerts")
async def alert_socket(socket: WebSocket) -> None:
    await socket.accept()
    await socket.send_json({"alerts": alerts[:25]})
    await socket.close()
