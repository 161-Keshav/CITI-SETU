"""Validate generated evaluation output before a human renders publishing artifacts."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    metrics = Path("results/metrics.json")
    if not metrics.exists():
        raise SystemExit("results/metrics.json is missing. Run `make eval` first.")
    payload = json.loads(metrics.read_text(encoding="utf-8"))
    Path("docs/pitch/assets").mkdir(parents=True, exist_ok=True)
    Path("docs/pitch/assets/metrics-summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Validated metrics and staged docs/pitch/assets/metrics-summary.json. Publishing prose retains explicit 'not measured' fields until full training is run.")


if __name__ == "__main__":
    main()

