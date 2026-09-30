"""FanumTax core engines. Synthetic data -> LightGBM quantile forecast (+split-conformal
adjustment, implemented manually, not MAPIE) -> flexible repayment -> loan decision."""
import numpy as np, pandas as pd, lightgbm as lgb

RATE, APR, MAX_DAYS, MIN_LOAN = 0.12, 0.24, 90, 1000.0
DOW = np.array([.85, .8, .85, .9, 1.05, 1.3, 1.25])  # weekly seasonality (Mon..Sun)

def gen_days(n=120, seed=42, start="2026-06-01", base=800):
    """Synthetic daily UPI inflow for a tea stall: seasonality, noise, slow periods."""
    rng = np.random.default_rng(seed)
    d = pd.date_range(start, periods=n)
    v = base * DOW[d.dayofweek] * rng.lognormal(0, .22, n)
    for s in rng.choice(max(n - 8, 1), min(3, max(n // 30, 1)), replace=False):
        v[s:s + rng.integers(3, 6)] *= .55  # slow periods
    return pd.DataFrame({"date": d, "inflow": v.round(0), "n_txn": (v / 45 + rng.poisson(2, n)).round()})

def _feats(s):
    return pd.DataFrame({"lag1": s.shift(1), "lag7": s.shift(7), "m7": s.shift(1).rolling(7).mean(),
                         "sd7": s.shift(1).rolling(7).std(), "m14": s.shift(1).rolling(14).mean()})

def forecast(inflow, horizon=7, start_dow=0):
    """Daily P10/P50/P90 (conformal-adjusted), averaged over the next `horizon` days."""
    s = pd.Series(np.asarray(inflow, float))
    if len(s) < 40: raise ValueError("Need at least 40 days of history")
    X = _feats(s); X["dow"] = (start_dow + np.arange(len(s))) % 7
    ok = X.dropna().index; cal, tr = ok[-21:], ok[:-21]; mdl = {}
    for q in (.1, .5, .9):
        mdl[q] = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=120, learning_rate=.05,
                                   num_leaves=7, min_child_samples=8, verbose=-1, random_state=0).fit(X.loc[tr], s[tr])
    lo, hi = mdl[.1].predict(X.loc[cal]), mdl[.9].predict(X.loc[cal])
    score = np.maximum(lo - s[cal], s[cal] - hi)  # CQR nonconformity scores
    qhat = float(np.quantile(score, min(1, .8 * (1 + 1 / len(cal)))))
    hist, out = list(s), []
    for _ in range(horizon):
        x = _feats(pd.concat([pd.Series(hist), pd.Series([np.nan])], ignore_index=True)).iloc[[-1]].copy()
        x["dow"] = (start_dow + len(hist)) % 7
        p = {q: float(mdl[q].predict(x)[0]) for q in mdl}
        out.append((p[.1] - qhat, p[.5], p[.9] + qhat)); hist.append(p[.5])
    a = np.maximum(np.array(out).mean(0), 0)
    a[0] = min(a[0], a[1]); a[2] = max(a[2], a[1])
    return {"p10": round(a[0]), "p50": round(a[1]), "p90": round(a[2]), "conformal_qhat": round(qhat, 1),
            "note": "MVP estimate on ~100 synthetic days; no statistical coverage guarantee."}

def days_to_repay(principal, daily_income, rate=RATE, apr=APR):
    """Simple interest accrues daily: P(1+apr*d/365) = rate*I*d  =>  d = P/(rate*I - P*apr/365)."""
    den = rate * daily_income - principal * apr / 365
    return float("inf") if principal <= 0 or den <= 0 else principal / den

def evaluate(amount, fc):
    if amount <= 0: raise ValueError("Loan amount must be positive")
    d10, d50 = days_to_repay(amount, fc["p10"]), days_to_repay(amount, fc["p50"])
    max_safe = round(fc["p10"] * RATE * MAX_DAYS / (1 + APR * MAX_DAYS / 365))  # largest principal clearing in 90d at P10
    if d10 <= MAX_DAYS: status, why = "Eligible", f"At the conservative P10 income the loan clears in {d10:.0f} days, inside the {MAX_DAYS}-day cap."
    elif max_safe >= MIN_LOAN: status, why = "Eligible with adjusted amount", f"At P10 income the requested amount would not clear in {MAX_DAYS} days. The largest amount that does is Rs {max_safe}."
    elif d50 <= MAX_DAYS: status, why = "Needs review", "Clears only under the expected (P50) scenario, not the conservative one."
    else: status, why = "Not eligible", "Even expected income cannot repay this within the maximum period."
    r = lambda d: None if d == float("inf") else round(d)
    return {"status": status, "reason": why, "requested": amount, "p10_income": fc["p10"],
            "daily_repayment_at_p10": round(RATE * fc["p10"], 1), "days_at_p10": r(d10), "days_at_p50": r(d50),
            "max_days": MAX_DAYS, "max_safe_amount": max_safe,
            "total_due_at_p10_horizon": None if d10 == float("inf") else round(amount * (1 + APR * d10 / 365))}

def simulate(amount, incomes):
    """12% of each day's inflow goes to repayment until the total due is cleared."""
    rows, paid = [], 0.0
    for i, inc in enumerate(incomes[:MAX_DAYS], 1):
        due = amount * (1 + APR * i / 365); pay = min(RATE * inc, max(due - paid, 0)); paid += pay
        rows.append({"day": i, "income": round(inc), "repayment": round(pay, 1), "cumulative": round(paid, 1), "remaining": round(max(due - paid, 0), 1)})
        if due - paid <= 0.5: break
    return rows

def scenario(kind, n=90, seed=7):
    return list(gen_days(n, seed=seed)["inflow"] * {"normal": 1.0, "slow": .55, "strong": 1.4}[kind])
