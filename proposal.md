# SETU-Shield — Hackathon Submission Text

**Proposal Title**
SETU-Shield: Federated Learning for Cross-Bank Mule-Account Detection and Guardian-Assisted UPI Payments

**Problem Understanding**
Most UPI fraud no longer involves a hacked account. The victim is talked into approving a collect request or scanning a QR code, and within minutes the money moves through mule accounts spread across several banks. Each bank sees only the hop that touches its own customers, so no one sees the ring, and banks cannot pool raw customer data because of privacy rules. Meanwhile the users most at risk, such as elderly and first-time digital users, get the same generic "Are you sure?" popup as everyone else and tap through it.

**Solution Description**
SETU-Shield adds three things around a UPI payment. First, banks train one shared mule-detection model with federated learning, so only model updates travel and customer data stays put. Second, before money moves, the payee is scored and the user sees a plain-language reason (for example, "this account received money from 40 new people in two hours") in English, Hindi, Tamil or Telugu. Third, for users who opt in, a high-risk payment is held and a trusted family member gets a signed, single-use link to approve or reject it. It is designed as an advisory layer beside existing bank fraud systems: if it is unavailable, payments continue.

**Implementation Approach**
We built a seeded simulator of three banks, each seeing a different mix of mule typologies (collector fan-in, layering, fan-out cash-out, new-account bursts). A small neural model is trained three ways on identical data budgets: each bank alone, federated with weighted FedAvg, and pooled as a ceiling. Results are averaged over five seeds on a global test set. The prototype API (FastAPI) applies risk tiers, generates localized reason codes, runs the guardian hold flow with HMAC-signed single-use tokens, writes a hash-chained audit log, and calls a payment rail through an adapter (mock rail by default; designed to swap in a sandbox rail). Two React dashboards show the payer and bank-operations views. The federated model is validated offline; wiring it into the serving path is the next step.

**Technology Stack**
Python, FastAPI, scikit-learn and NumPy (federated experiment), Pydantic, React + TypeScript + Vite, Docker Compose, GitHub Actions, pytest. Designed to add Flower, Opacus, ONNX Runtime and Redis for production-style serving, and Bhashini for translation and voice.

**Expected Impact**
On our synthetic benchmark the federated model reached PR-AUC 0.915 (±0.012) versus 0.872 (±0.011) for banks working alone, and matched the pooled-data ceiling of 0.915. At a 1% false-positive rate it caught 88.5% of mules versus 83.8% for isolated banks. These numbers show the mechanism, not real-world performance, because the data is simulated and the banks' typology mix is an assumption we state openly. For banks, the approach means earlier mule detection without sharing raw data; for users, warnings they can understand and a family member as a second pair of eyes; for financial inclusion, a safety net that makes first-time and elderly users more comfortable adopting digital payments.

**GitHub Repository URL:** {{GITHUB_URL}}
**Pitch Deck URL:** {{DECK_URL}}
