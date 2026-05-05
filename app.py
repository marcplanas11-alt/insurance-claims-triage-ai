import json
from typing import TypedDict, Optional, List, Dict, Any

import anthropic
import pandas as pd
import streamlit as st
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------
# Streamlit setup
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="AI Claims Triage Workflow",
    page_icon="🧾",
    layout="wide",
)

st.title("🧾 AI Claims Triage Workflow")
st.caption(
    "Claude + LangGraph claims triage with validation, routing, human review, and audit trail."
)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Anthropic API Key", type="password")

    model_name = st.text_input(
        "Claude model",
        value="claude-haiku-4-5-20251001",
        help="Use the model available in your Anthropic account.",
    )

    confidence_threshold = st.slider(
        "Human review threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.70,
        step=0.05,
    )

    st.markdown("---")
    st.markdown("### Workflow")
    st.markdown(
        """
        1. **decision_node** — Claude recommends APPROVE / REJECT / ESCALATE  
        2. **validation_node** — Python validates output  
        3. **conditional edge** — routes based on risk  
        4. **routing_node** — auto-processes safe claims  
        5. **human_review_node** — escalates sensitive claims  
        """
    )


# ---------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------

class ClaimState(TypedDict):
    claim_id: str
    claim_text: str

    decision: Optional[str]
    confidence: Optional[float]
    decision_reason: Optional[str]

    is_valid: Optional[bool]
    validation_errors: Optional[List[str]]

    routing: Optional[str]
    final_status: Optional[str]

    human_review_required: bool
    human_review_reason: Optional[str]
    human_reviewer: Optional[str]
    human_review_status: Optional[str]

    audit_log: List[Dict[str, Any]]


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def safe_json_parse(raw_text: str) -> dict:
    cleaned = raw_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    elif cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "").strip()

    return json.loads(cleaned)


def create_initial_state(claim_id: str, claim_text: str) -> ClaimState:
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,

        "decision": None,
        "confidence": None,
        "decision_reason": None,

        "is_valid": None,
        "validation_errors": None,

        "routing": None,
        "final_status": None,

        "human_review_required": False,
        "human_review_reason": None,
        "human_reviewer": None,
        "human_review_status": None,

        "audit_log": [],
    }


# ---------------------------------------------------------------------
# Claude decision agent
# ---------------------------------------------------------------------

def decision_agent_claude(client, claim_text: str, model: str) -> dict:
    prompt = f"""
You are an insurance claims triage assistant.

Analyze the claim text and return ONLY valid JSON.

Allowed decisions:
- APPROVE
- REJECT
- ESCALATE

Rules:

- APPROVE low-risk, common claims with clear damage descriptions
  (e.g. minor vehicle damage, water damage, small incidents)
  even if full policy details are not provided.

- REJECT only if there is clear indication the claim is invalid.

- ESCALATE when:
  - claim is unclear
  - high-value or complex
  - potential coverage ambiguity
  - possible fraud signals

- Claims with REJECT decisions must still require human review before final denial.
- Do not invent facts.
- Do not assume coverage beyond reasonable common cases.
- Return JSON only.

Claim text:
{claim_text}

Required JSON format:
{{
  "decision": "APPROVE | REJECT | ESCALATE",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    response = client.messages.create(
        model=model,
        max_tokens=300,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    raw_text = response.content[0].text
    return safe_json_parse(raw_text)


# ---------------------------------------------------------------------
# LangGraph nodes
# ---------------------------------------------------------------------

def decision_node(state: ClaimState) -> ClaimState:
    client = st.session_state["anthropic_client"]
    model = st.session_state["model_name"]
    threshold = st.session_state["confidence_threshold"]

    try:
        result = decision_agent_claude(client, state["claim_text"], model)

        decision = result.get("decision", "ESCALATE")
        confidence = float(result.get("confidence", 0.0))
        reason = result.get("reason", "No reason provided")

    except Exception as e:
        decision = "ESCALATE"
        confidence = 0.0
        reason = f"Claude decision failed: {str(e)}"

    state["decision"] = decision
    state["confidence"] = confidence
    state["decision_reason"] = reason

    state["human_review_required"] = (
        decision == "ESCALATE"
        or decision == "REJECT"
        or confidence < threshold
    )

    state["audit_log"].append({
        "step": "decision_node",
        "agent": "claude",
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "human_review_required": state["human_review_required"],
    })

    return state


def validation_node(state: ClaimState) -> ClaimState:
    errors = []

    if state["decision"] not in ["APPROVE", "REJECT", "ESCALATE"]:
        errors.append("Invalid decision value")

    if state["confidence"] is None:
        errors.append("Missing confidence score")

    elif state["confidence"] < 0 or state["confidence"] > 1:
        errors.append("Confidence must be between 0 and 1")

    if not state["decision_reason"]:
        errors.append("Missing decision reason")

    state["is_valid"] = len(errors) == 0
    state["validation_errors"] = errors

    if not state["is_valid"]:
        state["human_review_required"] = True

    state["audit_log"].append({
        "step": "validation_node",
        "is_valid": state["is_valid"],
        "errors": errors,
    })

    return state


def routing_node(state: ClaimState) -> ClaimState:
    if not state["is_valid"]:
        routing = "MANUAL_REVIEW"
        final_status = "Escalated due to validation failure"
        state["human_review_required"] = True

    elif state["decision"] == "APPROVE" and state["confidence"] >= st.session_state["confidence_threshold"]:
        routing = "AUTO_PAY"
        final_status = "Approved for automatic payment"

    else:
        routing = "MANUAL_REVIEW"
        final_status = "Escalated due to uncertainty"
        state["human_review_required"] = True

    state["routing"] = routing
    state["final_status"] = final_status

    state["audit_log"].append({
        "step": "routing_node",
        "routing": routing,
        "final_status": final_status,
        "human_review_required": state["human_review_required"],
    })

    return state


def human_review_node(state: ClaimState) -> ClaimState:
    review_reason = state.get("decision_reason", "Manual review required")

    state["human_review_reason"] = review_reason
    state["human_reviewer"] = "claims_adjuster"
    state["human_review_status"] = "PENDING"
    state["routing"] = "MANUAL_REVIEW"
    state["final_status"] = "Pending human claims review"

    state["audit_log"].append({
        "step": "human_review_node",
        "review_required": True,
        "review_reason": review_reason,
        "assigned_to": "claims_adjuster",
        "status": "PENDING",
    })

    return state


def decide_next_step(state: ClaimState) -> str:
    if state["human_review_required"]:
        return "human_review"

    return "routing"


# ---------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------

def build_claims_graph():
    workflow = StateGraph(ClaimState)

    workflow.add_node("decision", decision_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("routing", routing_node)
    workflow.add_node("human_review", human_review_node)

    workflow.add_edge(START, "decision")
    workflow.add_edge("decision", "validation")

    workflow.add_conditional_edges(
        "validation",
        decide_next_step,
        {
            "human_review": "human_review",
            "routing": "routing",
        },
    )

    workflow.add_edge("human_review", END)
    workflow.add_edge("routing", END)

    return workflow.compile()


# ---------------------------------------------------------------------
# Input UI
# ---------------------------------------------------------------------

claim_id = st.text_input("Claim ID", value="CLAIM_DEMO_001")

claim_text = st.text_area(
    "Paste claim text",
    height=180,
    value="Minor scratch on insured vehicle reported with full details",
)

col1, col2, col3 = st.columns(3)

with col1:
    sample_auto = st.button("Load AUTO_PAY sample")

with col2:
    sample_manual = st.button("Load MANUAL_REVIEW sample")

with col3:
    sample_reject = st.button("Load REJECT_REVIEW sample")

if sample_auto:
    claim_id = "TEST_AUTO_PAY_001"
    claim_text = "Minor scratch on insured vehicle reported with full details"

if sample_manual:
    claim_id = "TEST_MANUAL_REVIEW_001"
    claim_text = "Customer reports unusual situation with unclear details"

if sample_reject:
    claim_id = "TEST_REJECT_REVIEW_001"
    claim_text = "I intentionally broke my window to test the system."


# ---------------------------------------------------------------------
# Run workflow
# ---------------------------------------------------------------------

run = st.button("▶ Run Claims Workflow", type="primary")

if run:
    if not api_key:
        st.error("Enter your Anthropic API key.")
    elif not claim_text.strip():
        st.error("Enter claim text.")
    else:
        try:
            st.session_state["anthropic_client"] = anthropic.Anthropic(api_key=api_key)
            st.session_state["model_name"] = model_name
            st.session_state["confidence_threshold"] = confidence_threshold

            claims_graph = build_claims_graph()
            initial_state = create_initial_state(claim_id, claim_text)

            final_state = claims_graph.invoke(initial_state)
            st.session_state["final_state"] = final_state

            st.success("Workflow completed.")

        except anthropic.AuthenticationError:
            st.error("Invalid Anthropic API key.")
        except Exception as e:
            st.error(f"Workflow failed: {e}")


# ---------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------

final_state = st.session_state.get("final_state")

if final_state:
    st.divider()

    st.subheader("Final Decision")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric("Decision", final_state["decision"])

    with metric2:
        st.metric("Confidence", f"{final_state['confidence']:.2f}")

    with metric3:
        st.metric("Routing", final_state["routing"])

    with metric4:
        st.metric("Human Review", str(final_state["human_review_required"]))

    if final_state["human_review_required"]:
        st.warning("Human review required before final claim action.")
    else:
        st.success("Claim eligible for automated processing.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Claim State", "Validation", "Human Review", "Audit Trail"]
    )

    with tab1:
        st.json({
            "claim_id": final_state["claim_id"],
            "claim_text": final_state["claim_text"],
            "decision": final_state["decision"],
            "confidence": final_state["confidence"],
            "decision_reason": final_state["decision_reason"],
            "routing": final_state["routing"],
            "final_status": final_state["final_status"],
        })

    with tab2:
        st.json({
            "is_valid": final_state["is_valid"],
            "validation_errors": final_state["validation_errors"],
        })

    with tab3:
        st.json({
            "human_review_required": final_state["human_review_required"],
            "human_review_reason": final_state["human_review_reason"],
            "human_reviewer": final_state["human_reviewer"],
            "human_review_status": final_state["human_review_status"],
        })

    with tab4:
        audit_df = pd.DataFrame(final_state["audit_log"])
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇ Download audit trail CSV",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name="claims_triage_audit_trail.csv",
            mime="text/csv",
        )
