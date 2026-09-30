"""A transparent demo payload for the collector-mule payment scenario."""
import json

print(json.dumps({"scenario": "collector fan-in", "payer": "asha@bankA", "payee": "quickcash77@bankC", "amount_inr": 24500, "channel": "collect", "expected_tier": "hold", "note": "Synthetic demo scenario; no live bank traffic."}, indent=2))

