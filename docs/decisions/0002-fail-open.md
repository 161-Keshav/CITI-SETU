# ADR 0002: fail open when safety scoring is unavailable

SETU-Shield is advisory. If scoring infrastructure is unavailable, the API returns `allow` plus `degraded: true` instead of blocking payment. This prevents the safety layer from becoming a payment-availability dependency, while making the degraded state visible for operations follow-up.

