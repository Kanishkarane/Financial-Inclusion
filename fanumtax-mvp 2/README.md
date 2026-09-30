# FANUMTAX

**Credit that moves with your income.**

FanumTax is a hackathon prototype for informal workers (street vendors, gig workers) who have steady UPI activity but no bureau credit history. Instead of a fixed EMI, repayment is a **capped percentage of each day's UPI inflow**, and affordability is judged on a **conservative income forecast (P10)**, not the average.

> **Prototype only.** FanumTax does not provide regulated lending or financial advice. All data is synthetic. No real UPI, bank, or credential access exists anywhere in the code.

![FanumTax landing page](./docs/screenshots/01-landing.png)

---

## Contents

1. [Problem and core idea](#1-problem-and-core-idea)
2. [What is implemented, and what is not](#2-what-is-implemented-and-what-is-not)
3. [Product walkthrough](#3-product-walkthrough)
4. [How it works](#4-how-it-works)
5. [API](#5-api)
6. [Synthetic data](#6-synthetic-data)
7. [Run locally](#7-run-locally)
8. [Tests](#8-tests)
9. [Project structure](#9-project-structure)
10. [Design notes](#10-design-notes)
11. [Known limitations and observed behaviour](#11-known-limitations-and-observed-behaviour)
12. [Assumptions needing verification](#12-assumptions-needing-verification)
13. [Roadmap](#13-roadmap)

---

## 1. Problem and core idea

Informal workers may move substantial money through UPI yet be classed "No Hit" by traditional lenders. Even with credit, a fixed EMI mismatches irregular daily income: one slow week can turn an affordable loan into a missed payment.

Our position is **not** "an alternative credit score". It is:

> **Match the repayment to the income.**

Two engines do the work:

| Engine | What it does |
|---|---|
| **1. Income forecasting** | LightGBM quantile models predict daily income as a range (P10 / P50 / P90). A conformal adjustment widens the range using held-out data. **P10 is used for affordability.** |
| **2. Flexible repayment** | Each day, 12% of inflow goes to repayment, with 24% APR simple interest and a 90-day maximum. Slow day means a smaller payment; strong day means a larger one. |

Flexible repayment reduces pressure on slow days. **It does not eliminate default risk.**

---

## 2. What is implemented, and what is not

### Implemented

- Synthetic UPI transaction generation
- Transaction analytics
- Income forecasting
- P10 / P50 / P90 forecasts
- Conservative affordability assessment
- Flexible repayment calculation
- Loan evaluation
- Trust Score
- SHAP-based model explanation
- Payer-payee transaction graph
- Suspicious transaction indicators
- Fairness audit using Fairlearn
- Weekly re-forecasting
- FastAPI backend
- React frontend
- Automated tests
- Docker configuration

### Not implemented

- Real UPI/bank integration
- Real loan disbursement
- Real e-mandates
- Production credit bureau integration
- Production fraud detection
- Production lending decisions
- Real customer data

All data used by the prototype is synthetic.

---

# 3. Product walkthrough

## 3.1 Landing page

FanumTax introduces the core idea:

> **Credit that moves with your income.**

![FanumTax landing page](./docs/screenshots/01-landing.png)

---

## 3.2 Borrower onboarding

The user can enter borrower information or load the Ramesh demonstration profile.

![FanumTax onboarding](./docs/screenshots/02-onboarding.png)

---

## 3.3 Transaction analysis

The system analyzes synthetic UPI activity and calculates income and transaction characteristics.

![Transaction analysis](./docs/screenshots/03-transaction-analysis.png)

---

## 3.4 Conservative income forecast

FanumTax forecasts income as a range instead of relying on a single average.

![Income forecast](./docs/screenshots/04-income-forecast.png)

The key values are:

- **P10:** Conservative income estimate
- **P50:** Expected estimate
- **P90:** Higher-income estimate

The P10 estimate is used for affordability calculations.

---

## 3.5 FanumTax Trust Score

The prototype provides an internal risk/affordability indicator based on transaction and income characteristics.

![FanumTax Trust Score](./docs/screenshots/05-trust-score.png)

This is **not a replacement for an official credit bureau score**.

---

## 3.6 Loan evaluation

For the demonstration loan:

- Principal: ₹5,000
- Interest: approximately 24% APR
- Repayment: 12% of daily eligible inflow
- Maximum repayment period: 90 days

![Loan evaluation](./docs/screenshots/06-loan-evaluation.png)

The system evaluates affordability using the conservative income forecast rather than simply using average income.

---

## 3.7 Flexible repayment

This is the core FanumTax concept.

![Flexible repayment](./docs/screenshots/07-flexible-repayment.png)

For example:

| Daily UPI inflow | 12% repayment |
|---:|---:|
| ₹300 | ₹36 |
| ₹800 | ₹96 |
| ₹1,200 | ₹144 |

A slow-income day therefore produces a smaller repayment rather than forcing the borrower to meet a fixed EMI.

---

## 3.8 Weekly reforecast

FanumTax can simulate a new week of transaction activity and update the forecast.

![Weekly reforecast](./docs/screenshots/08-reforecast.png)

The system recalculates:

- P10 forecast
- P50 forecast
- repayment capacity
- Trust Score
- repayment projection

---

## 3.9 Payer-payee risk graph

NetworkX is used to represent transaction relationships and identify suspicious patterns.

![Payer-payee risk graph](./docs/screenshots/09-risk-graph.png)

The graph is an MVP screening mechanism and **does not constitute definitive fraud detection**.

---

## 3.10 Fairness audit

The prototype includes a Fairlearn-based fairness audit using synthetic demonstration data.

![Fairness audit](./docs/screenshots/10-fairness-audit.png)

The audit is intended for monitoring and analysis rather than proving that the system is bias-free.

---

## 4. How it works

### Income forecasting

```text
Synthetic UPI transactions
          ↓
Daily income aggregation
          ↓
Feature engineering
          ↓
LightGBM quantile models
          ↓
P10 / P50 / P90
          ↓
Conformal adjustment
          ↓
Conservative P10 affordability estimate
