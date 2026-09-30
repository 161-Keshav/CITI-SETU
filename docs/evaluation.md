# Evaluation protocol

The checked-in `results/metrics.json` is produced by `make eval`. It measures a small, deterministic synthetic smoke set and records policy precision, recall, and in-process latency. It explicitly does **not** report a federation result, privacy-utility curve, poisoning experiment, per-segment false-positive rate, or held-out-ring result.

The full experiment must generate a seeded multi-bank graph, split by time and unseen rings, train isolated, federated, and centralized arms across at least three seeds, and report mean plus standard deviation. Until that exists, this demo should be described as a product-flow prototype rather than an evidence-backed fraud model.

