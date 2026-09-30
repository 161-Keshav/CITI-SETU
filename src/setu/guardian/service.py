from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
import base64
import hashlib
import hmac
import json
import secrets


class HoldState(StrEnum):
    PENDING_GUARDIAN = "PENDING_GUARDIAN"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"


@dataclass
class Hold:
    id: str
    payer_vpa: str
    guardian_name: str
    payee_vpa: str
    amount_inr: float
    reason: str
    expires_at: datetime
    state: HoldState = HoldState.PENDING_GUARDIAN
    nonce: str = ""
    token_used: bool = False

    def public(self) -> dict[str, object]:
        data = asdict(self)
        data["expires_at"] = self.expires_at.isoformat()
        return data


class GuardianService:
    def __init__(self, secret: str, hold_minutes: int = 10) -> None:
        self.secret = secret.encode()
        self.hold_minutes = hold_minutes
        self.holds: dict[str, Hold] = {}
        self.enrollments: dict[str, str] = {"asha@bankA": "Arun"}

    def enroll(self, payer_vpa: str, guardian_name: str) -> None:
        self.enrollments[payer_vpa] = guardian_name

    def create(self, payer_vpa: str, payee_vpa: str, amount_inr: float, reason: str) -> tuple[Hold, str]:
        hold = Hold(
            id=f"h_{secrets.token_urlsafe(9)}",
            payer_vpa=payer_vpa,
            guardian_name=self.enrollments[payer_vpa],
            payee_vpa=payee_vpa,
            amount_inr=amount_inr,
            reason=reason,
            expires_at=datetime.now(UTC) + timedelta(minutes=self.hold_minutes),
            nonce=secrets.token_urlsafe(12),
        )
        self.holds[hold.id] = hold
        return hold, self._token(hold)

    def _token(self, hold: Hold) -> str:
        payload = json.dumps({"id": hold.id, "nonce": hold.nonce}, separators=(",", ":")).encode()
        signature = hmac.new(self.secret, payload, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(payload + b"." + signature).decode().rstrip("=")

    def _decode(self, token: str) -> Hold:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        payload, signature = raw.rsplit(b".", 1)
        expected = hmac.new(self.secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid guardian link")
        data = json.loads(payload)
        hold = self.holds.get(data["id"])
        if hold is None or hold.nonce != data["nonce"]:
            raise ValueError("Guardian link is not valid")
        return hold

    def get(self, hold_id: str) -> Hold:
        hold = self.holds[hold_id]
        if hold.state == HoldState.PENDING_GUARDIAN and datetime.now(UTC) >= hold.expires_at:
            hold.state = HoldState.EXPIRED
            hold.state = HoldState.CANCELLED
        return hold

    def decision(self, hold_id: str, token: str, decision: str) -> Hold:
        hold = self._decode(token)
        if hold.id != hold_id or hold.token_used or self.get(hold_id).state != HoldState.PENDING_GUARDIAN:
            raise ValueError("This guardian link has expired or was already used")
        if decision not in {"approve", "reject"}:
            raise ValueError("Decision must be approve or reject")
        hold.token_used = True
        hold.state = HoldState.APPROVED if decision == "approve" else HoldState.REJECTED
        hold.state = HoldState.RELEASED if decision == "approve" else HoldState.CANCELLED
        return hold

    def cancel(self, hold_id: str) -> Hold:
        hold = self.get(hold_id)
        if hold.state != HoldState.PENDING_GUARDIAN:
            raise ValueError("Only a pending hold can be cancelled")
        hold.state = HoldState.CANCELLED
        return hold

