"""Generate a tiny, deterministic synthetic UPI snapshot for the local demo."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    root = Path("data")
    root.mkdir(exist_ok=True)
    rows = []
    for bank in "abc":
        bank_dir = root / f"bank_{bank}"
        bank_dir.mkdir(exist_ok=True)
        for index in range(20):
            rows.append({"account_id": f"{bank}_{index:03}", "bank": bank.upper(), "age_days": random.randint(4, 1800), "is_mule": int(bank == "c" and index < 2)})
        with (bank_dir / "accounts.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([row for row in rows if row["bank"] == bank.upper()])
    print(f"Generated {len(rows)} synthetic accounts with seed {args.seed}.")


if __name__ == "__main__":
    main()

