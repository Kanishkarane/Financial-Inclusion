# FANUMTAX (hackathon MVP, core slice)
Credit whose repayment follows irregular income. Prototype only; not regulated lending or financial advice. All data synthetic.

## Run
    cd backend && pip install -r requirements.txt
    uvicorn app.main:app --port 8000      # open http://localhost:8000
    python -m pytest                      # tests

## Implemented
- Synthetic UPI daily-inflow generator (seeded, weekly seasonality, slow periods): `backend/app/engine.py`
- LightGBM quantile forecast (P10/P50/P90) + split-conformal (CQR) adjustment, hand-written (not MAPIE)
- Flexible repayment: 12% of daily inflow, 24% APR simple interest, 90-day cap, closed-form duration
- Decision from P10: Eligible / Eligible with adjusted amount / Needs review / Not eligible
- Repayment simulator (normal/slow/strong) and weekly reforecast (appends a simulated week, retrains)
- Frontend served by FastAPI, every button calls the API

## NOT yet built
Trust Score, SHAP, LLM explanation layer, NetworkX risk graph, Fairlearn audit, MLflow, SQLite, Docker, onboarding upload, React/Tailwind build.

## Assumptions and limits
Forecast uses ~100 synthetic days, so intervals are MVP estimates with no coverage guarantee. RBI rules on variable daily e-mandates, competitor offers and market rates are unverified and need legal/market review. State is in memory for one demo user.
