"""Measure the deterministic local demo policy against generated synthetic cases."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from setu.serving.app import Channel, ScoreRequest, risk_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latency-only", action="store_true")
    args = parser.parse_args()
    cases = [("quickcash77@bankC", 24500, Channel.COLLECT, 1), ("grocer@bankA", 220, Channel.PAY, 0), ("mule-02@bankB", 18000, Channel.QR, 1), ("rent@bankA", 8000, Channel.PAY, 0)]
    latencies: list[float] = []
    outcomes: list[tuple[float, int]] = []
    for _ in range(150):
        for payee, amount, channel, label in cases:
            request = ScoreRequest(payer_vpa="asha@bankA", payee_vpa=payee, amount_inr=amount, channel=channel, timestamp="2026-09-30T12:00:00+05:30")
            began = perf_counter()
            score, _ = risk_policy(request)
            latencies.append((perf_counter() - began) * 1000)
            outcomes.append((score, label))
    ordered = sorted(latencies)
    p95 = ordered[int(len(ordered) * 0.95)]
    if args.latency_only:
        print(json.dumps({"p50_ms": round(median(latencies), 4), "p95_ms": round(p95, 4), "p99_ms": round(ordered[int(len(ordered) * 0.99)], 4)}))
        return
    tp = sum(score >= 0.7 and label for score, label in outcomes)
    fp = sum(score >= 0.7 and not label for score, label in outcomes)
    fn = sum(score < 0.7 and label for score, label in outcomes)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    metrics = {"dataset": {"kind": "synthetic", "cases": len(outcomes), "seed": 42, "note": "Small deterministic smoke-evaluation; not a production fraud benchmark."}, "arms": {"isolated": {"status": "not trained in lightweight demo"}, "federated": {"status": "not trained in lightweight demo"}, "centralized": {"status": "not trained in lightweight demo"}}, "xgboost_baseline": {"status": "not installed in lightweight demo"}, "privacy_utility": {"status": "not measured"}, "poisoning": {"status": "not measured"}, "latency": {"p50_ms": round(median(latencies), 4), "p95_ms": round(p95, 4), "p99_ms": round(ordered[int(len(ordered) * 0.99)], 4), "throughput_context": "600 in-process score policy evaluations"}, "per_segment_fpr": {"status": "not measured"}, "thresholds": {"warn": 0.35, "hold": 0.7, "policy_precision": round(precision, 3), "policy_recall": round(recall, 3)}, "model_version": "policy-demo-2026-09-30", "seeds": [42], "generated_at": "local evaluation"}
    Path("results").mkdir(exist_ok=True)
    Path("results/metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print("Wrote results/metrics.json from the local deterministic smoke evaluation.")


if __name__ == "__main__":
    main()
