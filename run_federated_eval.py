"""Three-arm experiment: isolated vs federated (FedAvg) vs centralized.

Synthetic data only. Each bank sees a different mix of fraud typologies
(non-IID), which is the assumption the federated benefit rests on.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from time import perf_counter

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, roc_curve
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=ConvergenceWarning)
TYPES = ["collector_fan_in", "layering", "fan_out_cashout", "new_account_burst"]
BANK_MIX = {  # share of each bank's mules by typology (non-IID)
    "A": [0.70, 0.10, 0.10, 0.10],
    "B": [0.10, 0.70, 0.10, 0.10],
    "C": [0.10, 0.10, 0.40, 0.40],
}


def _legit(r, n):
    hops = np.where(r.random(n) < 0.93, 5, r.integers(2, 5, n))
    return np.c_[np.log1p(r.poisson(3, n)), np.log(r.lognormal(6.4, 1.0, n)), np.log(r.lognormal(6.8, 1.0, n)),
                 np.log1p(r.poisson(3, n)), r.beta(4, 3, n) , r.beta(2, 8, n), r.beta(2, 5, n), hops, r.normal(0, 1, n)]


def _mule(r, typ, n):
    x = _legit(r, n)
    if typ == 0:
        x[:, 0] = np.log1p(r.poisson(35, n)); x[:, 1] = np.log(r.lognormal(4.8, .7, n))
    elif typ == 1:
        x[:, 1] = np.log(r.lognormal(2.1, .6, n)); x[:, 4] = r.beta(30, 1.2, n); x[:, 3] = np.log1p(r.poisson(1.5, n))
    elif typ == 2:
        x[:, 3] = np.log1p(r.poisson(30, n)); x[:, 5] = r.beta(5, 5, n); x[:, 1] = np.log(r.lognormal(3.4, .7, n))
    else:
        x[:, 2] = np.log(r.lognormal(1.4, .6, n)); x[:, 0] = np.log1p(r.poisson(15, n)); x[:, 5] = r.beta(4, 6, n)
    x[:, 7] = np.where(r.random(n) < 0.65, r.integers(1, 4, n), 5)
    evasive = r.random(n) < 0.25  # 25% of mules mimic normal behaviour on some features
    x[evasive, :3] = _legit(r, evasive.sum())[:, :3]
    return x


def make(r, n, mix, mule_rate=0.03):
    k = int(n * mule_rate)
    t = r.choice(4, k, p=mix)
    X = np.vstack([_legit(r, n - k)] + [_mule(r, i, int((t == i).sum())) for i in range(4)])
    y = np.r_[np.zeros(n - k), np.ones(k)]
    typ = np.r_[np.full(n - k, -1), np.concatenate([np.full(int((t == i).sum()), i) for i in range(4)])]
    p = r.permutation(n)
    return X[p], y[p], typ[p]


def new_model(seed):
    return MLPClassifier((24, 12), learning_rate_init=0.01, random_state=seed, batch_size=128)


def fit(m, X, y, epochs, w=3):
    Xb = np.vstack([X] + [X[y == 1]] * w); yb = np.r_[y, np.ones(int(y.sum()) * w)]
    for _ in range(epochs):
        m.partial_fit(Xb, yb, classes=[0, 1])
    return m


def fedavg(banks, rounds, seed):
    g = new_model(seed); fit(g, banks[0][0][:64], banks[0][1][:64], 1)
    for _ in range(rounds):
        outs, sizes = [], []
        for X, y in banks:
            c = new_model(seed); fit(c, X[:64], y[:64], 1)
            c.coefs_ = [w.copy() for w in g.coefs_]; c.intercepts_ = [b.copy() for b in g.intercepts_]
            fit(c, X, y, 1); outs.append(c); sizes.append(len(y))
        s = np.array(sizes) / sum(sizes)
        g.coefs_ = [sum(m.coefs_[i] * w for m, w in zip(outs, s)) for i in range(len(g.coefs_))]
        g.intercepts_ = [sum(m.intercepts_[i] * w for m, w in zip(outs, s)) for i in range(len(g.intercepts_))]
    return g


def score(m, sc, X):
    return m.predict_proba(sc.transform(X))[:, 1]


def evaluate(s, y, typ, thr):
    fpr, tpr, _ = roc_curve(y, s)
    rings, hit = 0, 0
    for t in range(4):
        idx = np.where(typ == t)[0]
        for i in range(0, len(idx) - 4, 5):
            rings += 1; hit += bool((s[idx[i:i + 5]] >= thr).any())
    return {"pr_auc": average_precision_score(y, s), "recall_at_1pct_fpr": float(np.interp(0.01, fpr, tpr)),
            "ring_detection_pct": 100 * hit / rings}


def run(seed):
    r = np.random.default_rng(seed)
    raw = {b: make(r, 12000, mix) for b, mix in BANK_MIX.items()}
    Xv, yv, _ = make(r, 20000, [.25] * 4, 0.04)
    Xt, yt, tt = make(r, 20000, [.25] * 4, 0.04)
    sc = StandardScaler().fit(np.vstack([v[0] for v in raw.values()]))  # shared feature scaling constants
    banks = [(sc.transform(X), y) for X, y, _ in raw.values()]
    def thr(m):  # threshold at 1% FPR on a global validation set
        s = score(m, sc, Xv); return np.quantile(s[yv == 0], 0.99)
    res = {}
    iso = [fit(new_model(seed), X, y, 30) for X, y in banks]
    res["isolated"] = [evaluate(score(m, sc, Xt), yt, tt, thr(m)) for m in iso]
    fed = fedavg(banks, 30, seed)
    res["federated"] = [evaluate(score(fed, sc, Xt), yt, tt, thr(fed))]
    cen = fit(new_model(seed), np.vstack([b[0] for b in banks]), np.r_[tuple(b[1] for b in banks)], 30)
    res["centralized"] = [evaluate(score(cen, sc, Xt), yt, tt, thr(cen))]
    x1 = sc.transform(Xt[:1]); lat = []
    for _ in range(500):
        t0 = perf_counter(); fed.predict_proba(x1); lat.append((perf_counter() - t0) * 1000)
    return {k: {m: float(np.mean([d[m] for d in v])) for m in v[0]} for k, v in res.items()}, lat


if __name__ == "__main__":
    seeds = [11, 22, 33, 44, 55]; runs, lats = [], []
    for s in seeds:
        a, l = run(s); runs.append(a); lats += l; print(s, {k: round(v["pr_auc"], 3) for k, v in a.items()})
    arms = {k: {m: {"mean": round(float(np.mean([r[k][m] for r in runs])), 3), "std": round(float(np.std([r[k][m] for r in runs])), 3)}
                for m in runs[0][k]} for k in runs[0]}
    out = {"dataset": {"kind": "synthetic", "banks": 3, "samples_per_bank": 12000, "mule_rate_train": 0.03,
                       "note": "Non-IID typology mix per bank; global balanced test set. Not a real-world benchmark."},
           "arms": arms, "seeds": seeds,
           "latency": {"scope": "single-sample MLP inference only, not end-to-end API", "p50_ms": round(float(np.percentile(lats, 50)), 3),
                       "p95_ms": round(float(np.percentile(lats, 95)), 3), "p99_ms": round(float(np.percentile(lats, 99)), 3)},
           "privacy_utility": {"status": "not measured"}, "poisoning": {"status": "not measured"},
           "model_version": "fedavg-mlp-24-12-r30"}
    Path("results").mkdir(exist_ok=True)
    Path("results/metrics.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["arms"], indent=1)); print(out["latency"])
