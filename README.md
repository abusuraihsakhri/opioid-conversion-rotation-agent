# Opioid Conversion Rotation Agent

> **Domain:** Clinical Pharmacology & Precision Pharmacotherapy  
> **Reference Guidelines & Standards:** `CPIC Guidelines & FDA Table of Pharmacogenomic Biomarkers`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Opioid Conversion Rotation Agent** is an advanced analytical and computational platform implementing Equianalgesic Rotation & Cross-Tolerance Safety Reducer.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_mme()`**: Calculate total daily Morphine Milligram Equivalents (MME).

Args:
    opioid_doses: List of dicts with keys:
        - opioid: str (e.g., "morphine_po", "oxycodone_po")
        - dose_mg: float (dose per administration)
        - doses_per_day: int (number of administrations per day)
        OR
        - dose_mcg_per_hr: float (for fentanyl patch)
    
Returns:
    Dictionary with MME calculation
- **`convert_opioid()`**: Convert from one opioid to another with equianalgesic dosing.

Args:
    source_opioid: Source opioid name (e.g., "morphine_po")
    source_dose_mg: Source dose per administration in mg
    source_doses_per_day: Number of source doses per day
    target_opioid: Target opioid name
    cross_tolerance_reduction: Reduction for incomplete cross-tolerance (0.25-0.50)
    doses_per_day_target: Target number of doses per day
    
Returns:
    Dictionary with conversion details
- **`convert_to_methadone()`**: Convert total daily MME to methadone dose.

Methadone conversion is complex and non-linear.
The ratio increases with higher MME doses.

Args:
    total_daily_mme: Total daily morphine milligram equivalents
    cross_tolerance_reduction: Cross-tolerance reduction (default 50% for methadone)
    
Returns:
    Dictionary with methadone conversion
- **`generate_taper_schedule()`**: Generate a gradual opioid tapering schedule.

CDC recommends:
- Reduce by 10% per month for patients on opioids >1 year
- Reduce by 10% per week for patients on opioids <1 year
- Slower tapers (5-10% monthly) for patients on high doses

Args:
    current_daily_mme: Current total daily MME
    target_daily_mme: Target daily MME (0 for complete taper)
    reduction_percent: Percentage to reduce at each step
    interval_days: Days between reductions
    min_step_mme: Minimum reduction per step in MME
    
Returns:
    Dictionary with tapering schedule
- **`convert_to_fentanyl_patch()`**: Convert total daily MME to fentanyl transdermal patch dose.

Approximate: 1 mcg/hr fentanyl patch ≈ 2.4 MME/day
(varies by source, 2.0-3.0 range)

Args:
    total_daily_mme: Total daily morphine milligram equivalents
    cross_tolerance_reduction: Cross-tolerance reduction
    
Returns:
    Dictionary with fentanyl patch conversion

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate total daily Morphine Milligram Equivalents (MME).
  risk = "VERY_HIGH"
  risk = "HIGH"
  risk = "MODERATE"
  risk = "LOW"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t opioid-conversion-rotation-agent .
docker run -p 8000:8000 opioid-conversion-rotation-agent
```
