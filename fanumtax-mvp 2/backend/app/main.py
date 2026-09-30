from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import engine as E

app = FastAPI(title="FanumTax MVP")
STATE = {}  # single-demo-user in-memory state

class Req(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    amount: float = Field(gt=0, le=50000)

def _summary(df):
    x = df["inflow"]
    return {"avg": round(x.mean()), "median": round(x.median()), "volatility_cv": round(x.std() / x.mean(), 2),
            "active_days": int((x > 0).sum()), "largest": round(x.max()), "avg_txn_per_day": round(df.n_txn.mean(), 1),
            "trend_pct": round((x[-14:].mean() / x[-28:-14].mean() - 1) * 100, 1)}

def _run(df, amount):
    fc = E.forecast(df["inflow"].values, start_dow=df["date"].iloc[0].dayofweek)
    return {"summary": _summary(df), "forecast": fc, "decision": E.evaluate(amount, fc),
            "history": [{"date": str(d.date()), "inflow": v} for d, v in zip(df["date"], df["inflow"])][-60:]}

@app.post("/api/evaluate")
def evaluate(r: Req):
    df = E.gen_days(); STATE.update(df=df, amount=r.amount, week=0)
    STATE["last"] = out = _run(df, r.amount); return out

@app.post("/api/reforecast")
def reforecast():
    if "df" not in STATE: raise HTTPException(400, "Run /api/evaluate first")
    prev = STATE["last"]; STATE["week"] += 1; w = STATE["week"]
    new = E.gen_days(7, seed=100 + w, start=str(STATE["df"]["date"].iloc[-1].date() + pd.Timedelta(days=1)))
    new["inflow"] = (new["inflow"] * [1.0, .6, 1.25][w % 3]).round()  # simulated week drifts each run
    STATE["df"] = pd.concat([STATE["df"], new], ignore_index=True)
    STATE["last"] = cur = _run(STATE["df"], STATE["amount"])
    return {"week": w, "previous": {"forecast": prev["forecast"], "decision": prev["decision"]}, "current": cur}

@app.get("/api/repayment/{kind}")
def repayment(kind: str):
    if kind not in ("normal", "slow", "strong"): raise HTTPException(404, "kind must be normal|slow|strong")
    if "df" not in STATE: raise HTTPException(400, "Run /api/evaluate first")
    return E.simulate(STATE["amount"], E.scenario(kind))

app.mount("/", StaticFiles(directory=Path(__file__).parents[2] / "frontend", html=True), name="ui")
