from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: str = "audit.jsonl") -> None:
        self.path = Path(path)

    def append(self, event: str, payload: dict[str, Any]) -> None:
        previous = "0" * 64
        if self.path.exists() and self.path.stat().st_size:
            previous = json.loads(self.path.read_text(encoding="utf-8").splitlines()[-1])["hash"]
        record = {"at": datetime.now(UTC).isoformat(), "event": event, "payload": payload, "previous_hash": previous}
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
        record["hash"] = hashlib.sha256(encoded).hexdigest()
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")

    def verify_chain(self) -> bool:
        previous = "0" * 64
        if not self.path.exists():
            return True
        for line in self.path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            supplied = record.pop("hash")
            if record["previous_hash"] != previous:
                return False
            encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(encoded).hexdigest() != supplied:
                return False
            previous = supplied
        return True

