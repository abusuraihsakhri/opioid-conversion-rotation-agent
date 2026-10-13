# Opioid Conversion Rotation Agent

Educational opioid exposure calculations, legacy rotation examples, and research-oriented Python audit workflows. **Not validated as a clinical decision-support system.**

## Browser application

The static MME reference interface is at [`web/index.html`](web/index.html), with a root [`index.html`](index.html) entry point for static hosting. Open `web/index.html` in a browser or serve the directory locally. No JavaScript framework, Python runtime, internet access, or API is required for the calculator itself.

Features:
- Estimated total daily oral morphine milligram equivalents (MME) for morphine, oxycodone, hydromorphone, hydrocodone, codeine, and tramadol.
- Transdermal fentanyl exposure estimates using **mcg/hour**, not mg/day.
- Add/remove multiple regimens, review individual MME contributions, and reset the total.
- Explicitly excludes methadone and injectable opioids from the browser calculator.

**Clinical limitation:** MME factors are estimates for exposure comparison and risk assessment, **not equianalgesic conversion ratios**. Do not derive a new opioid prescription, cross-tolerance reduction, methadone initiation dose, transdermal fentanyl patch strength, or taper plan from an MME total. In particular, the CDC 2022 guideline excludes pain management related to sickle cell disease, cancer-related pain treatment, palliative care, and end-of-life care from its recommendations.

**Source:** [CDC Clinical Practice Guideline for Prescribing Opioids for Pain (2022)](https://www.cdc.gov/mmwr/volumes/71/rr/rr7103a1.htm), Table of MME factors and its cautions.

## Python tools

The repository contains multiple independent, partially overlapping interfaces:

- `opioid_rotate.py` is the legacy research CLI and library, including `calculate_mme()`, `convert_opioid()`, `convert_to_methadone()`, `convert_to_fentanyl_patch()`, and `generate_taper_schedule()`. Conversion and taper outputs are illustrative and **are not prescribing instructions**; non-linear/complex drugs must be handled with specialist guidance. Generic `convert_opioid()` rejects methadone and fentanyl.
- `opioid_conversion_rotation_agent/` implements a separate generic numeric-threshold audit, batch CLI, and optional FastAPI service. Its `primary_metric` and `secondary_metric` are **not** opioid-equivalent doses.
- `agents/` contains an additional research audit/supervisor implementation with a keyed, in-memory HMAC audit chain. Its mock LLM adapter does not perform real model inference.

Install from a local checkout with Python 3.10+:

```sh
python -m pip install -e ".[test,api]"
python -m pytest -q
node --check web/app.js
node --test tests/web-mme.test.cjs
```

Run the research CLI:

```sh
python opioid_rotate.py mme --opioid oxycodone_po --dose 10 --times 3
python opioid_rotate.py list
python cli.py audit --case-id SAMPLE-001
python cli.py serve --host 127.0.0.1 --port 8000
```

The optional API exposes `GET /health`, `POST /api/audit`, and `POST /api/chat` for the **generic numeric audit**. It is not the browser calculator's backend. Do not expose this API directly to the public internet without authentication, request-size limits, appropriate network controls, and a clinical/privacy review.

## Docker

```sh
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The key is supplied externally; do not commit production secrets. The compose example binds port 8000 on the host, so restrict network exposure in any deployment.

## Privacy and safety

The browser MME calculator does not request patient identifiers, make network API calls, or write to persistent browser storage. Entered regimens remain in the current page's memory and disappear when it is closed or refreshed. The Python APIs and CLI can accept free text and identifiers and have **not** been independently verified for PHI de-identification or clinical suitability; use synthetic or appropriately de-identified inputs only. The HMAC audit trail is process-local, not persistent or externally anchored.

Clinical use requires professional review, validated institution-specific protocols, correct formulation/route, drug labeling, and appropriate safeguards. No result here should be interpreted as individual risk classification or a prescription.

## Technology, compatibility and license

- Python 3.10–3.12 (test matrix), standard library, Pydantic 2; FastAPI/Uvicorn optional.
- Browser: modern JavaScript-capable Chrome, Firefox, Safari, or Edge. The static calculator works without a backend; automated tests use Node.js 22.
- CI: Python tests, browser calculation tests, syntax checks, and dependency consistency.
- License: [MIT](LICENSE).
