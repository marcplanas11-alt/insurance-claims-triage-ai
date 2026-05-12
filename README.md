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

The workflow is a state machine:
### Components

- **`ClaimState`** — structured claim file that evolves across the workflow
- **`decision_node`** — Claude evaluates the claim and returns structured JSON
- **`validation_node`** — enforces output integrity and validates required fields
- **`routing_node`** — applies deterministic business rules
- **`human_review_node`** — escalates sensitive or uncertain claims

---

## 🔹 Flow Logic

All claims pass through validation before any routing decision.

Human review is triggered when:

- Decision confidence (model-reported) falls below **0.7**
- Validation layer detects missing or malformed fields
- Decision category is in the sensitive list (`REJECT`, `FRAUD_FLAG`, 
  high-amount claims)
- Specific keywords are detected in the claim narrative (e.g. *intentional*, 
  *deliberate*)

---

## 🔹 Governance & Controls

The system enforces multiple control layers:

- **Structured JSON outputs** — no free-text decisions
- **Confidence thresholds** for decision reliability (≥0.7 for auto-routing)
- **Validation layer** before any operational routing
- **Human-in-the-loop** for uncertain or high-risk cases
- **Audit trail** capturing input, decision, confidence score, validation 
  status, and routing outcome for every claim

This architecture is designed to align with the operational principles of 
**DORA Art. 28** (ICT third-party risk) and **EU AI Act high-risk system 
requirements** (Arts. 9–15: risk management, data governance, transparency, 
human oversight, accuracy and robustness).

Production deployment in a regulated environment would require formal 
conformity assessment, documented risk management system, encrypted 
persistent audit storage with retention policies, and post-market 
monitoring — none of which are implemented here.

---

## 🔹 Test Cases

The workflow is validated using three Pytest scenarios:

| # | Scenario | Expected Result | Path |
|---|---|---|---|
| 1 | Low-risk claim (clean facts, low amount) | `AUTO_PAY`, confidence > 0.8 | decision → validation → routing |
| 2 | Unclear claim (ambiguous narrative) | `MANUAL_REVIEW`, validation flags missing context | decision → validation → human_review |
| 3 | Intentional damage signal | `REJECT` routed to `HUMAN_REVIEW` (no auto-rejection) | decision → validation → human_review |

Run the test suite:

```bash
pytest -v
```

---

## 🔹 Insurance Relevance

This workflow mirrors real-world claims operations patterns:

- **FNOL triage** and initial classification
- **Straight-through processing** for low-risk, low-ambiguity claims
- **Controlled escalation** to claims adjusters for sensitive cases
- **Auditability** for regulatory and internal governance review

The system demonstrates how AI can **augment, not replace**, claims 
decision-making.

---

## ⚙️ Model Selection

| Node | Implementation | Reason |
|---|---|---|
| Decision | Claude Sonnet | Probabilistic reasoning for nuanced claim assessment |
| Validation | Deterministic Python | No LLM — auditability and predictability |
| Routing | Deterministic Python | No LLM — business rules must be inspectable |
| Human review | Deterministic Python | No LLM — routing logic only |

**Single-LLM-node approach by design.** The architecture deliberately limits 
LLM use to the one node where probabilistic reasoning adds value. All other 
nodes are deterministic for auditability and predictability.

---

## ⚙️ How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# 3a. Run the test suite
pytest -v

# 3b. Or launch the Streamlit interface
streamlit run app.py
```

The Streamlit app opens at `http://localhost:8501`. Upload a claim narrative 
or use the built-in sample, then click **Run Triage** to see the full 
state-machine trace.

---

## 🧪 Evaluation Methodology (current state)

Current evaluation is **functional testing only** — the three Pytest 
scenarios above verify expected state transitions and routing.

**What is not yet measured:**

- Decision accuracy against a human-reviewer baseline
- False positive rate (claims routed to human review that didn't need it)
- False negative rate (claims auto-processed that should have been escalated)
- Latency per claim
- Cost per claim

**Planned evaluation framework:**

- Golden dataset of ~30 synthetic claims with hand-annotated expected routes
- LLM-as-judge scoring on three dimensions: routing correctness, confidence 
  calibration, audit-trail completeness
- Pairwise comparison of prompt versions to detect regressions
- Integration with `agent-evaluation-dashboard` for observability

---

## ⚠️ Limitations and Scope

- Synthetic claims data only — no validation against real claim files
- No formal evaluation framework yet (planned, see above)
- Confidence scoring relies on **model-reported confidence**, which is 
  known to be poorly calibrated for LLMs; production deployment would 
  require external confidence calibration
- Single-language (English); not tested on French or Spanish claim narratives
- No prompt versioning or A/B testing infrastructure
- Audit trail is in-memory only; production deployment would require 
  encrypted persistent storage with retention policies aligned with 
  regulatory minimums
- No fine-tuning on insurance-specific corpora — relies entirely on 
  Claude's base model plus prompt engineering
- Decision rules are hard-coded; a real deployment would need a rules 
  management layer reviewable by underwriting/claims leadership
- Streamlit interface is for demonstration; not a production-grade UI

---

## 🚀 Next Steps

- Build the golden dataset + LLM-as-judge evaluation framework described above
- Add prompt versioning and regression testing
- Externalise decision rules into a reviewable configuration layer
- Implement encrypted persistent audit storage
- Test multilingual claim narratives (French, Spanish)
- Integrate cost and latency monitoring per claim

---

## 🔗 Related Projects in This Portfolio

- [`reinsurance-contract-crew`](https://github.com/intlinsure/reinsurance-contract-crew) 
  — upstream multi-agent contract review workflow
- [`agent-evaluation-dashboard`](https://github.com/intlinsure/agent-evaluation-dashboard) 
  — observability dashboard for this triage system
- [`bordereaux-intake-n8n-mcp`](https://github.com/intlinsure/bordereaux-intake-n8n-mcp) 
  — adjacent claims-data ingestion workflow
- [`ba-process-models`](https://github.com/intlinsure/ba-process-models) 
  — BPMN AS-IS / TO-BE for the claims triage process
- [`insurance-ai-governance-pack`](https://github.com/intlinsure/insurance-ai-governance-pack) 
  — DORA / EU AI Act documentation patterns

---

## 👤 Context

Built by Marc Planas — operations background across MGA reinsurance, 
delegated authority workflows, and claims operations (Accelerant, Sompo, 
Zurich, Confide). Python (intermediate), Anthropic Skilljar certified. 
The architectural choices reflect ~10 years of seeing where manual claims 
triage breaks down: inconsistent decisions, missing audit context, and 
unclear escalation criteria.

---

## 🔒 Data Disclosure

All claims data used in this project is **synthetic and generated for 
demonstration purposes**. No real client data, proprietary documents, or 
confidential information is included.

---

## 🏷️ Tags

`ai` · `llm` · `anthropic` · `claude-api` · `langgraph` · `state-machine` · 
`insurance` · `claims` · `agentic-ai` · `hitl` · `dora` · `eu-ai-act` · 
`audit-trail` · `python` · `streamlit` · `pytest`
