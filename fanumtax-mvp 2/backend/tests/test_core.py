import math
from fastapi.testclient import TestClient
from app import engine as E
from app.main import app

def test_zero_income_never_repays(): assert E.days_to_repay(5000, 0) == math.inf
def test_days_formula(): assert abs(E.days_to_repay(5000, 800) - 5000 / (96 - 5000 * .24 / 365)) < 1e-9
def test_low_income_rejected(): assert E.evaluate(5000, {"p10": 50, "p50": 100, "p90": 150})["status"] == "Not eligible"
def test_adjusted_amount():
    d = E.evaluate(20000, {"p10": 600, "p50": 800, "p90": 1000})
    assert d["status"] == "Eligible with adjusted amount" and d["max_safe_amount"] < 20000
def test_low_income_lower_repayment():
    assert E.simulate(5000, E.scenario("slow"))[0]["repayment"] < E.simulate(5000, E.scenario("normal"))[0]["repayment"]
def test_api_flow():
    c = TestClient(app); f = c.post("/api/evaluate", json={"name": "Ramesh", "amount": 5000}).json()["forecast"]
    assert f["p10"] <= f["p50"] <= f["p90"]
    assert c.post("/api/reforecast").json()["week"] == 1
    assert c.post("/api/evaluate", json={"name": "x", "amount": -1}).status_code == 422
