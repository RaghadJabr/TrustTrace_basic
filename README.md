# TrustTrace Hackathon Prototype

TrustTrace is an **explainable AI fraud-prevention layer embedded inside existing banking and payment journeys**. The prototype demonstrates two integrations:

1. A traditional bank-payment flow using JOFS-style account, balance and beneficiary context.
2. A Web3 wallet-approval flow using blockchain, wallet, contract and token-permission context.

Both flows use the same risk engine and return an understandable decision before authorization.

## What is included

- Partner-bank payment interface
- Traditional safe and suspicious scenarios
- Web3 safe and suspicious approval scenarios
- Shared risk engine with configurable weighted rules
- English and Arabic interface with RTL support
- Explainable risk factors and a 0–100 risk score
- Mock JOFS adapter with a live-integration mode
- FastAPI API documentation at `/docs`
- Automated risk-engine tests

## Project structure

```text
trusttrace-prototype/
├── app/
│   ├── data/demo_data.json
│   ├── static/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   ├── jofs_adapter.py
│   ├── main.py
│   ├── models.py
│   └── risk_engine.py
├── tests/test_risk_engine.py
├── .env.example
├── requirements.txt
├── start.bat
└── start.sh
```

## Run on Windows

1. Install Python 3.11 or newer.
2. Open PowerShell or Command Prompt in this folder.
3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Copy `.env.example` to `.env`.
6. Start the server:

```powershell
start.bat
```

7. Open `http://127.0.0.1:8000`.

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
./start.sh
```

## Demo sequence

### Traditional suspicious flow

1. Open **Bank payment**.
2. Select **Fake e-visa merchant — suspicious**.
3. Click **Confirm payment**.
4. TrustTrace runs before authorization.
5. Show the risk score, risk factors and recommendation to cancel.

### Traditional safe flow

Select **Trusted retailer — safe** and repeat.

### Web3 suspicious flow

1. Open **Web3 approval**.
2. Select **Malicious approval — suspicious**.
3. Click **Approve transaction**.
4. Show the unlimited-token approval and suspicious-network explanation.

### Arabic flow

Use the language button in the top-right. The layout switches to RTL and the risk explanations use Arabic.

## JOFS integration

The supplied sandbox document shows resources such as Accounts, Balances, Beneficiaries and Branches, but the exact base URL, authentication and response structure must be taken from the activated developer portal.

The prototype therefore defaults to:

```env
JOFS_MODE=mock
```

When credentials are available:

```env
JOFS_MODE=live
JOFS_BASE_URL=https://your-jofs-sandbox-base-url
JOFS_API_KEY=your-token
```

Then update the response mapping in `app/jofs_adapter.py` after testing each endpoint in the portal's **Try API** interface.

Important: JOFS data should be called only from the backend. Do not place API keys in the browser JavaScript.

## Prototype honesty

- The risk weights are transparent demonstration rules, not validated bank fraud thresholds.
- JOFS account data is mocked until credentials are configured.
- Device, location, behaviour, merchant and fraud-intelligence signals are simulated.
- The first bank pilot should run in advisory mode; the bank remains responsible for authorization.
- No real card details, passwords, CVVs or banking credentials are stored.

## API examples

### Traditional assessment

`POST /api/risk/traditional`

```json
{
  "account_id": "ACC-1001",
  "beneficiary_id": "BEN-777",
  "amount": 650,
  "currency": "JOD",
  "merchant": "Fast Visa Approval",
  "domain": "visa-fast-approval.example",
  "device_id": "UNKNOWN-DEVICE",
  "location": "Unknown",
  "rapid_attempts": 4
}
```

### Web3 assessment

`POST /api/risk/web3`

```json
{
  "wallet_address": "0xLEEN000000000000000000000000000000000001",
  "contract_address": "0xBAD0000000000000000000000000000000000777",
  "network": "ethereum",
  "action": "token_approval",
  "token_symbol": "USDT",
  "approval_limit": "unlimited",
  "wallet_scam_reports": 5,
  "suspicious_network": true
}
```

## Next technical tasks

1. Activate the JOFS account and capture the exact API schemas.
2. Replace mock account, balance and beneficiary calls with live sandbox calls.
3. Add request/response logging with sensitive-field redaction.
4. Add an audit table for assessments.
5. Calibrate fraud weights with bank-domain feedback.
6. Add a real domain-reputation source and live blockchain RPC only after the core demo is stable.
