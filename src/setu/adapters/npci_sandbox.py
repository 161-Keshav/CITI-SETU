from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class PaymentResult:
    reference: str
    status: str


class PaymentRail(ABC):
    @abstractmethod
    def validate_vpa(self, vpa: str) -> bool: ...

    @abstractmethod
    def initiate_pay(self, payer_vpa: str, payee_vpa: str, amount_inr: float) -> PaymentResult: ...

    @abstractmethod
    def initiate_collect(self, payer_vpa: str, payee_vpa: str, amount_inr: float) -> PaymentResult: ...

    @abstractmethod
    def get_status(self, reference: str) -> str: ...


class MockRail(PaymentRail):
    def __init__(self) -> None:
        self.statuses: dict[str, str] = {}

    def validate_vpa(self, vpa: str) -> bool:
        return "@" in vpa and len(vpa) > 3

    def _send(self, kind: str, payer_vpa: str, payee_vpa: str, amount_inr: float) -> PaymentResult:
        reference = "mock_" + hashlib.sha256(f"{kind}:{payer_vpa}:{payee_vpa}:{amount_inr}".encode()).hexdigest()[:12]
        self.statuses[reference] = "SUCCESS"
        return PaymentResult(reference, "SUCCESS")

    def initiate_pay(self, payer_vpa: str, payee_vpa: str, amount_inr: float) -> PaymentResult:
        return self._send("pay", payer_vpa, payee_vpa, amount_inr)

    def initiate_collect(self, payer_vpa: str, payee_vpa: str, amount_inr: float) -> PaymentResult:
        return self._send("collect", payer_vpa, payee_vpa, amount_inr)

    def get_status(self, reference: str) -> str:
        return self.statuses.get(reference, "UNKNOWN")
