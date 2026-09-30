# Judge Q&A

**Is the data real?** No. Every account and transaction in this repository is synthetic. The purpose of this slice is to prove the intervention and integration boundaries, not to claim real-world detection quality.

**Why federated learning?** Banks may be unable or unwilling to pool raw customer graphs. The proposed next phase compares isolated, federated, and pooled training honestly; the current demo does not claim that result yet.

**Could a false positive hurt someone?** Yes. The design uses a tiered response and only creates a guardian hold for opted-in users. The service fails open on an outage.

**Is it integrated with NPCI?** No. The default rail is an offline deterministic mock. The adapter is a seam for a future documented sandbox integration.

