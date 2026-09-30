# API guide

Run `make api`, then use the OpenAPI UI at `http://localhost:8000/docs`.

```powershell
curl -X POST http://localhost:8000/v1/risk/score -H "Content-Type: application/json" -d '{"payer_vpa":"asha@bankA","payee_vpa":"quickcash77@bankC","amount_inr":24500,"channel":"collect","timestamp":"2026-09-30T12:00:00+05:30","lang":"ta"}'
```

The response has an advisory tier (`allow`, `warn`, or `hold`), up to two reason codes, and, for an enrolled payer with a hold, a signed guardian route. `/v1/payments` wraps the same score in the deterministic mock rail. `/healthz`, `/readyz`, `/v1/ops/alerts`, `/v1/ops/graph`, and `/v1/model/info` support the demo interfaces.

