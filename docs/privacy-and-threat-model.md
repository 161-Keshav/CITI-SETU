# Privacy and threat model

The demo uses synthetic VPAs and records only minimum event metadata in its local hash-chained audit file. Application logs should hash identifiers; payment amounts and full VPAs do not belong in normal logs. The guardian URL carries only an opaque hold id and nonce inside an HMAC-signed token.

| Threat | Demo mitigation | Remaining gap |
|---|---|---|
| Spoofed guardian link | HMAC signature, expiry, single use | No production identity assurance |
| Replay | Used-token flag and terminal hold state | No distributed token store |
| Scorer outage | Fail-open advisory behaviour | Availability monitoring is minimal |
| Audit tampering | SHA-256 linked entries | Local file is not an external immutable store |
| Federated poisoning | Documented future work | No federation implementation in this slice |

The intended future design keeps raw transaction graphs inside each bank and shares model updates only. That reduces data movement but does not eliminate model-inversion, membership-inference, or malicious-client risks. Clipping, anomaly filtering, differential privacy, secure aggregation, and a formal DPDP/RBI/NPCI review are required before any pilot. This project has not made a compliance claim.

