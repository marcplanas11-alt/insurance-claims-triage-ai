# AI Claims Triage Workflow — LangGraph + Claude

Governed AI-assisted claims triage workflow built with Streamlit, LangGraph, Python validation logic and Claude.

> **Positioning:** this is a portfolio prototype. It does not approve, reject or pay claims in production. It demonstrates how probabilistic model reasoning can be wrapped in deterministic validation, routing controls, audit logging and human review.

---

## Executive Summary

Claims triage requires fast first-pass assessment, but regulated insurance workflows cannot rely on an LLM as a standalone decision-maker. This project separates reasoning from control:

```text
Claim text
   ↓
Claude decision node
   ↓
Python validation node
   ↓
Conditional routing
   ↓                 ↓
Auto-process path     Human review path
   ↓                 ↓
Audit trail           Audit trail
```

The LLM proposes `APPROVE`, `REJECT` or `ESCALATE` with a confidence score. Python then validates the output and applies hard governance rules. Rejections, escalations, invalid outputs and low-confidence cases are routed to human review.

---

## Main Files

| File / Folder | Purpose |
|---|---|
| `app.py` | Streamlit app, LangGraph workflow, Claude call, validation, routing and audit display |
| `requirements.txt` | Python dependencies |
| `tests/test_app.py` | Unit tests for state creation, JSON parsing, validation and routing |
| `notebooks/claims_langgraph_step_by_step.ipynb` | Learning notebook / step-by-step workflow exploration |

---

## Governance Controls

The workflow enforces:

- structured JSON output from the model;
- allowed decisions only: `APPROVE`, `REJECT`, `ESCALATE`;
- confidence threshold;
- Python validation before routing;
- no automatic rejection;
- human review for rejected, escalated or low-confidence cases;
- audit log generated at each node;
- CSV export of the audit trail.

---

## Full Setup and Execution Guide

### 1. Clone the repository

```bash
git clone https://github.com/marcplanas11-alt/insurance-claims-triage-ai.git
cd insurance-claims-triage-ai
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Dependencies:

| Package | Use |
|---|---|
| `streamlit` | Browser app |
| `anthropic` | Claude API client |
| `langgraph` | State-machine workflow orchestration |
| `langchain`, `langchain-core` | Supporting LangGraph ecosystem packages |
| `pandas` | Audit table and CSV export |

---

## Run the Streamlit App

```bash
streamlit run app.py
```

Expected output:

```text
Local URL: http://localhost:8501
```

In the browser:

1. Enter the API key in the sidebar.
2. Keep or change the Claude model name.
3. Adjust the confidence threshold.
4. Load one of the sample claims or paste a custom claim.
5. Click **Run Claims Workflow**.
6. Review the final decision, routing, validation output, human review fields and audit trail.

---

## Run Tests

```bash
python -m pytest tests/test_app.py
```

---

## Complete Command Formula

### Windows CMD

```bash
git clone https://github.com/marcplanas11-alt/insurance-claims-triage-ai.git
cd insurance-claims-triage-ai
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### Windows PowerShell

```bash
git clone https://github.com/marcplanas11-alt/insurance-claims-triage-ai.git
cd insurance-claims-triage-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
git clone https://github.com/marcplanas11-alt/insurance-claims-triage-ai.git
cd insurance-claims-triage-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

---

## Troubleshooting

### Invalid key error

Check the value entered in the Streamlit sidebar and run the workflow again.

### Model not available

Change the model name in the sidebar to a model available in your account.

### `streamlit` is not recognized

```bash
python -m streamlit run app.py
```

### Tests import the Streamlit app

The test suite imports `app.py`, so Streamlit may initialise during test collection. For a future production refactor, move pure workflow functions into a separate module such as `src/workflow.py` and keep `app.py` as UI-only.

---

## Cleanup Notes

- The previous README was incomplete and stopped after an unfinished code block.
- Test logic should live in `tests/`, not inside `app.py`.
- Keep real claim data out of the repository; use synthetic examples only.

---

## Author

Built by Marc Planas Callico — Insurance Operations, Business Analysis and AI-enabled transformation.
