# 🧠 AI Claims Triage Workflow (LangGraph + Claude)

A governed AI-assisted claims triage workflow built on a state-machine 
architecture, designed to support insurance claims operations while 
maintaining auditability, control, and human oversight.

---

## 🔹 Overview

This system combines:

- **Claude (Anthropic)** for probabilistic decision-making
- **Python** for deterministic validation and control logic
- **LangGraph** for state-machine orchestration

The objective is to demonstrate how AI can support claims operations while 
maintaining the auditability, control, and human oversight that regulated 
insurance workflows require.

---

## 🔹 Key Insight

LLMs provide reasoning, but cannot be trusted as standalone decision systems.

Control must be enforced through:

- **Deterministic validation**
- **Explicit routing rules**
- **Human oversight**

This architecture deliberately separates probabilistic AI reasoning from 
operational decision control. The LLM is used in only one node by design — 
all other nodes are deterministic Python for auditability and predictability.

---

## 🔹 Architecture
### Components

| Component | Type | Role |
|---|---|---|
| `ClaimState` | TypedDict | Structured claim file that evolves across every node |
| `decision_node` | Claude API | Evaluates claim, returns structured JSON with decision + confidence |
| `validation_node` | Python | Validates output integrity and required field presence |
| `routing_node` | Python | Applies deterministic business rules for clean claims |
| `human_review_node` | Python | Escalates sensitive or uncertain claims |

---

## 🔹 Flow Logic

All claims pass through validation before any routing decision.

Human review is triggered when any of these conditions are met:

- Decision is `REJECT` — no auto-rejection; all rejections require human sign-off
- Decision is `ESCALATE` — ambiguous, unclear, or complex claims
- Model-reported confidence falls below **0.7** (configurable in the UI)
- Validation layer detects missing or malformed fields

Claims reaching `routing_node` are only those where decision is `APPROVE` 
and confidence ≥ 0.7.

---

## 🔹 Governance & Controls

The system enforces multiple control layers:

- **Structured JSON outputs** — no free-text decisions; Claude must return 
  `APPROVE`, `REJECT`, or `ESCALATE` with a numeric confidence score
- **Confidence threshold** — default 0.7, adjustable via the Streamlit sidebar
- **Validation layer** — Python checks output integrity before any routing
- **Human-in-the-loop** — all rejections and escalations require human review; 
  no claim is ever auto-rejected
- **Audit trail** — every node appends to `audit_log`, capturing step name, 
  decision, confidence, validation status, and routing outcome; exportable as CSV

This architecture is designed to align with the operational principles of 
**DORA Art. 28** (ICT third-party risk) and **EU AI Act high-risk system 
requirements** (Arts. 9–15: risk management, data governance, transparency, 
human oversight, accuracy and robustness).

Production deployment in a regulated environment would require formal 
conformity assessment, documented risk management system, encrypted persistent 
audit storage with retention policies, and post-market monitoring — none of 
which are implemented here.

---

## 🔹 Test Cases

Three scenarios are validated in the test suite and notebook:

| # | Scenario | Claim input | Expected decision | Expected routing | Human review |
|---|---|---|---|---|---|
| 1 | Low-risk, clear claim | "Minor scratch on insured vehicle reported with full details" | `APPROVE`, confidence ≥ 0.8 | `AUTO_PAY` | No |
| 2 | Unclear, ambiguous claim | "Customer reports unusual situation with unclear details" | `ESCALATE` | `MANUAL_REVIEW` | Yes |
| 3 | Intentional damage | "I intentionally broke my window to test the system." | `REJECT` | `MANUAL_REVIEW` | Yes |

All three scenarios are verified via the notebook (`notebooks/claims_langgraph_step_by_step.ipynb`) 
with real Claude API outputs.

Unit tests covering state initialisation, JSON parsing, validation logic, 
routing logic, and human review escalation are in `tests/test_app.py`:

```bash
