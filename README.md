# TrustTrace Prototype

TrustTrace is an **explainable AI fraud-prevention layer embedded inside existing banking and payment journeys**. It demonstrates two integrations:

1. A traditional bank-payment flow, scored by a **real trained LightGBM model** with **real SHAP explanations**, persisted to PostgreSQL.
2. A Web3 wallet-approval flow, currently scored by a transparent rule engine (see [What's deferred](#whats-deferred) — the trained Web3 model exists but isn't wired in yet).

Both flows return an understandable decision before authorization, in English and Arabic.

## What's real here

Unlike a typical hackathon demo, the traditional-payment path is a genuine trained-model integration, not hand-coded if/else rules:

- **Model**: the actual LightGBM classifier from `TrustTrace_AI` (ROC-AUC 0.999 on held-out test data), loaded once at startup from `app/ml/traditional/artifacts/`.
- **Feature parity**: inference uses the exact 31-feature schema, category vocabularies, and numeric/categorical split captured in the training-time support bundle (`trusttrace_lightgbm_support.joblib`) — see `app/ml/traditional/service.py`. This is what prevents training-serving skew.
- **Calibration**: raw LightGBM output is passed through the trained Platt-scaling calibrator before being compared to the decision threshold (0.7913).
- **Explanations**: `shap.TreeExplainer` runs against the real booster for every assessment; the top contributors are mapped to plain-language English/Arabic sentences (`app/services/explanation_service.py`) and to structured analyst detail (feature, value, SHAP value, direction, rank).
- **Trust Score / decision separation**: `trust_score_service.py` turns `fraud_probability` into a 0–100 Trust Score and a 5-tier risk category; `decision_engine.py` turns the risk category into a recommended action — both driven by `app/config/decision_thresholds.json`, not hard-coded in the inference path, so an institution could override them later.
- **Persistence**: every assessment writes real rows to Postgres (`transactions`, `fraud_assessments`, `assessment_explanations`, `audit_logs`) via Alembic-managed tables — see `alembic/versions/`.
- **JOFS-backed, not just JOFS-adjacent**: the assessment pipeline actually calls JOFS (`app/integrations/open_finance/provider.py`) to resolve the account, balance, beneficiary and transaction history *before* building the model features — it doesn't just display JOFS data next to an unrelated score. See [JOFS-to-model pipeline](#jofs-to-model-pipeline) below.
- **Tests**: `tests/` includes unit tests for feature derivation, trust score bands, and the decision engine, plus integration tests that hit the live API + Postgres and assert on real model output, plus a dedicated `tests/test_jofs_pipeline.py` proving the pipeline is live (same feature vector for prediction+SHAP, different inputs produce different vectors, JOFS-not-found fails clearly instead of faking a score, explanations tied to the right assessment id, no score math in frontend JS).

## Documented assumptions

The traditional model's *training* notebook/code was not provided to this integration — only the trained artifacts (`TrustTrace_AI.zip`) were. Two things were inferred rather than confirmed:

- `log_transaction_amount` is computed as `log1p(transaction_amount)` — the standard, monotonic, zero-safe choice. This feature ranks 25th/31 by mean |SHAP|, so it has limited effect either way.
- The bin edges for `transaction_amount_bin`, `geo_velocity_bin`, `geo_distance_km`, and `session_duration_bin` (e.g. what counts as "fast" vs "impossible" travel speed) are a documented heuristic in `app/services/feature_service.py`, not the original training cut points. These are all low-importance categorical features.

Everything else — feature order, category vocabularies, the calibrator, the threshold — comes directly from the training-time support bundle, with no guessing involved.

## What a real integration would supply vs. what this demo defaults

The model expects payment-gateway/device/session telemetry (CVV match, 3-D Secure result, tokenization method, IP type, device-fingerprint match, geo-velocity, etc.) that a real card network or device-intelligence vendor would supply. This prototype accepts all of it as an optional `signals` object on the request (`TransactionSignals` in `app/schemas.py`) with neutral defaults, so:

- A minimal request (just amount/merchant/domain, like the original prototype) still works, using defaults.
- The demo scenarios (`app/data/demo_scenarios.py`) send a full, realistic `signals` payload so "safe" and "suspicious" genuinely score differently through the real model.
- A production integration would populate `signals` from the real gateway/device pipeline instead of relying on defaults.

`avg_amount_deviation_sigma`, `merchant_category_vs_history`, and `account_age_days` are **not** taken from the client at all — they're computed server-side from real Postgres transaction history (`app/services/feature_service.py::TransactionHistory`).

## JOFS-to-model pipeline

`assessment_service.assess_traditional()` (now `async`) does this at request time, for every traditional assessment:

```text
JOFS: get_account (required)          -> 404 JOFS_ACCOUNT_NOT_FOUND if unresolvable, no score produced
JOFS: get_balance (optional)          -> business context + funds display, not a model feature
JOFS: get_beneficiary (optional)      -> display + beneficiary_verified in the response
JOFS: get_transactions (optional)     -> merged with Postgres history (deduped by external_transaction_id
                                          stored in Transaction.metadata_json) into avg_amount_deviation_sigma
JOFS: confirm_available_funds (opt.)  -> funds_available in the response, not a model feature
        -> app/services/jofs_normalization.py (shape-agnostic: handles both the mock and the
           inferred Berlin-Group-style live shape)
        -> feature_service.build_traditional_features()  (unchanged formulas)
        -> TraditionalFraudModelService.validate_feature_contract()  (new: exact 31-feature check)
        -> .predict() and .explain()  (called with the identical features dict -- proven in tests)
        -> trust_score_service -> decision_engine  (unchanged, config-driven)
        -> explanation_service  (SHAP factors -> EN/AR)
        -> Postgres persistence + provenance metadata (jofs_mode, account_source, missing_data,
           defaulted_signals, ...) in Transaction.metadata_json and AuditLog.details
        -> RiskAssessment response (includes account_balance, funds_available, beneficiary_verified,
           and a full `provenance` object -- never secrets/credentials)
```

**Important honesty note**: JOFS is an *account-information* (open-banking) API. It has no concept of card-payment-gateway telemetry. 11 of the 31 trained features — `cvv_match_status`, `three_ds_auth_result`, `tokenization_used`, `card_present_cnp`, `ip_address_type`, `device_fingerprint_match`, `network_carrier_type`, `session_duration_sec`, `geo_velocity_kmh`, `geo_distance_km`, `cards_on_device_30d`, `order_shipping_speed` — have no JOFS source and continue to come from the request's `signals` object (gateway/device layer), exactly as before. Only `avg_amount_deviation_sigma` (partially), `merchant_category_vs_history` (partially, JOFS has no merchant-category taxonomy so only the local Postgres side contributes to the category-match count), and account context (`account_age_days` fallback, balance, beneficiary identity) are genuinely enriched by JOFS.

The adapter's `JOFS_MODE=live` branch is written against the Berlin-Group/NextGenPSD2-style field names inferred from the sandbox docs (`transactionAmount.amount`, `availableBalance.balanceAmount`, ...) but **has not been exercised against a real JOFS endpoint** — this sandbox's network doesn't reach the live JOFS host. Everything above has been proven end-to-end against `JOFS_MODE=mock`, which runs through the exact same code path (`JOFSAdapter` is the single interface both modes implement) — so the wiring is real, but the live sandbox's actual field names should be spot-checked against `app/services/jofs_normalization.py` before going live.

## What's deferred

This iteration deliberately scoped to *one real, fully-tested end-to-end flow* rather than the full platform. Not built (yet):

- Wiring the trained Web3 Random Forest model + its SHAP bundle (`web3_fraud_project.zip`) into the Web3 tab — it still uses the original rule engine.
- Next.js/TypeScript frontend, institutional dashboard, multi-tenant institutions/consents/feedback tables.
- Verifying `JOFS_MODE=live` against a real JOFS sandbox endpoint (needs real credentials + network access this environment doesn't have; the mock and live paths share identical code, see above).
- IBAN/identity confirmation is not called from the assessment flow (it needs identity fields — `uid_type`/`uid_value` — the current request/UI doesn't collect; the standalone `/api/jofs/iban-confirmation` endpoint still exists for that separately).
- Blockchain RPC integration, auth/RBAC, rate limiting, and deployment configs (Vercel/Render/managed Postgres).

## Project structure

```text
app/
├── main.py                       FastAPI app, startup wiring, static hosting
├── schemas.py                    Pydantic request/response models
├── core/                         Settings, decision-threshold config loader, error envelope
├── config/decision_thresholds.json
├── db/                           SQLAlchemy engine/session, declarative base, demo seed
├── models/orm.py                 SQLAlchemy ORM tables
├── ml/
│   ├── interfaces.py             FraudModelService/PredictionResult/ExplanationResult
│   └── traditional/
│       ├── service.py            Real LightGBM + calibrator + SHAP inference
│       └── artifacts/            Trained model files (from TrustTrace_AI.zip)
├── services/
│   ├── feature_service.py        Builds the 31 model features (request + DB history)
│   ├── explanation_service.py    SHAP -> plain-language EN/AR explanations
│   ├── trust_score_service.py    fraud_probability -> Trust Score -> risk_category
│   ├── decision_engine.py        risk_category -> recommended_action (config-driven)
│   ├── assessment_service.py     Orchestrates the full traditional flow + persistence
│   ├── audit_service.py
│   └── web3_rules_service.py     Existing rule-based Web3 engine (unchanged logic)
├── integrations/open_finance/provider.py   JOFS adapter (mock/live)
├── api/routes/                   health, jofs, assessments
├── data/demo_scenarios.py        Full-signal demo payloads for the frontend
└── static/                       Existing vanilla-JS frontend (unchanged)
alembic/versions/                 Database migrations
tests/                            Unit + integration tests
```

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set your local Postgres password
createdb trusttrace
alembic upgrade head
./start.sh              # or: python -m uvicorn app.main:app --reload
```

Demo data (a backdated account with baseline transaction history, so the "safe" vs "suspicious" scenarios differ meaningfully on the very first run) seeds automatically on first startup. To seed manually: `python -m app.db.seed`.

Open `http://127.0.0.1:8000`. API docs at `http://127.0.0.1:8000/docs`.

## Run tests

```bash
python -m pytest -q
```

Integration tests hit the real API and the Postgres database configured in `.env` — no mocking of the model or the database (JOFS itself runs in mock mode by default, so no live network call happens). They also write real rows to the shared demo account (`ACC-1001`), which shifts `avg_amount_deviation_sigma` for later runs since it's a genuine historical average. **Before a live demo, re-seed clean data:**

```bash
psql "$DATABASE_URL" -c "TRUNCATE assessment_explanations, audit_logs, fraud_assessments, transactions, devices, accounts, merchants, customers, model_registry RESTART IDENTITY CASCADE;"
python -m app.db.seed
```

## API

### `POST /api/risk/traditional`

```json
{
  "account_id": "ACC-1001",
  "beneficiary_id": "BEN-777",
  "amount": 2450,
  "currency": "JOD",
  "merchant": "Fast Visa Approval",
  "domain": "visa-fast-approval.example",
  "device_id": "UNKNOWN-DEVICE-771",
  "location": "Unknown",
  "rapid_attempts": 4,
  "signals": {
    "cvv_match_status": "cvv2_mismatch",
    "three_ds_auth_result": "challenge_fail",
    "ip_address_type": "vpn",
    "device_fingerprint_match": "new_device"
  }
}
```

Returns trust score, risk category, recommended action, and ranked SHAP-based risk/protective factors in English and Arabic. See `/docs` for the full schema, and `GET /api/risk/traditional/{assessment_id}` / `.../explanation` to retrieve a persisted assessment.

### `POST /api/risk/web3`

Unchanged from the original prototype — see `app/services/web3_rules_service.py`.

## JOFS integration

Defaults to `JOFS_MODE=mock`. When sandbox credentials are available, set `JOFS_MODE=live` plus the relevant `JOFS_*_BASE_URL` variables and verify each endpoint against the sandbox's "Try API" interface before trusting it — this integration has not been exercised against a live JOFS endpoint. JOFS calls happen only from the backend; never place API keys in frontend JavaScript.

## Prototype honesty

- The traditional risk assessment is a real trained model with real SHAP explanations — but it is still a **risk assessment, not proof of fraud**. The institution or user makes the final decision.
- Payment-gateway telemetry (CVV match, 3DS result, etc.) is demo-supplied unless a real gateway integration populates `signals`.
- The Web3 flow still uses transparent demonstration rules, not the trained Web3 model.
- JOFS account data is mocked until credentials are configured.
- No real card details, passwords, CVVs, or banking credentials are stored.
