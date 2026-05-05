import json
from datetime import datetime

import anthropic
import streamlit as st


st.set_page_config(
    page_title="AI-Powered Insurance Claims Triage v2",
    page_icon="🧾",
    layout="wide",
)

st.title("🧾 AI-Powered Insurance Claims Triage v2")
st.caption(
    "Stateful agentic workflow: intake → policy analysis → decision → validation → escalation rules → audit trail"
)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Anthropic API Key", type="password")
    confidence_threshold = st.slider(
        "Human review threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.70,
        step=0.05,
        help="Claims below this final confidence are escalated for human review.",
    )
    st.markdown("---")
    st.markdown("### Agentic Workflow")
    st.markdown(
        """
        1. **Intake Agent** extracts claim facts  
        2. **Policy Agent** checks coverage  
        3. **Decision Agent** recommends approve / escalate / reject  
        4. **Validation Agent** challenges the decision  
        5. **Escalation Router** applies deterministic rules
        """
    )


# ── Inputs ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    claim_text = st.text_area("Paste claim text", height=220)
with col2:
    policy_text = st.text_area("Paste policy text", height=220)

sample_col1, sample_col2 = st.columns([1, 4])
with sample_col1:
    load_sample = st.button("Load sample case")

if load_sample:
    st.session_state["claim_text"] = (
        "The insured reports water damage to the kitchen caused by a burst pipe. "
        "Estimated repair cost is £8,500. The incident occurred 18 days ago. "
        "The insured has provided photos but no plumber invoice yet."
    )
    st.session_state["policy_text"] = (
        "The policy covers sudden and accidental escape of water from fixed domestic installations. "
        "Claims must be notified as soon as reasonably practicable. Gradual damage, wear and tear, "
        "and pre-existing damage are excluded. The insurer may request invoices, photos, and repair reports."
    )
    st.rerun()

if "claim_text" in st.session_state and not claim_text:
    claim_text = st.session_state["claim_text"]
if "policy_text" in st.session_state and not policy_text:
    policy_text = st.session_state["policy_text"]


# ── Helpers ────────────────────────────────────────────────────────────────
def get_client(key):
    return anthropic.Anthropic(api_key=key)


def call_claude(client, prompt, max_tokens=900):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def add_audit(state, step, note):
    state["audit_trail"].append(
        {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "step": step,
            "note": note,
        }
    )
    return state


def new_state(claim, policy):
    return {
        "claim_text": claim,
        "policy_text": policy,
        "intake": None,
        "coverage_analysis": None,
        "decision": None,
        "confidence": None,
        "risk_flags": [],
        "validation": None,
        "human_review_required": False,
        "final_route": None,
        "audit_trail": [],
    }


def intake_agent(client, state):
    prompt = f"""
You are an insurance claims intake analyst.

Extract the key facts from the claim.

Return structured markdown with:
- Claim type
- Cause of loss
- Estimated loss
- Missing information
- Initial risk flags

Claim:
{state['claim_text']}
"""
    state["intake"] = call_claude(client, prompt, max_tokens=700)
    add_audit(state, "Intake Agent", "Claim facts extracted and initial risk indicators identified.")
    return state


def policy_agent(client, state):
    prompt = f"""
You are an insurance coverage analyst.

Based on the intake analysis and policy wording, assess coverage.

INTAKE:
{state['intake']}

POLICY WORDING:
{state['policy_text']}

Return structured markdown with:
- Coverage position
- Relevant policy wording
- Exclusions or conditions
- Ambiguities
- Missing documentation
- Coverage confidence from 0.00 to 1.00
"""
    state["coverage_analysis"] = call_claude(client, prompt, max_tokens=900)
    add_audit(state, "Policy Agent", "Coverage position, exclusions, ambiguities and missing documentation reviewed.")
    return state


def decision_agent(client, state):
    prompt = f"""
You are a claims decision agent.

Use the claim intake and policy analysis to recommend a decision.

Choose exactly one decision:
- APPROVE
- ESCALATE
- REJECT

Return ONLY valid JSON with this schema:
{{
  "decision": "APPROVE | ESCALATE | REJECT",
  "confidence": 0.0,
  "risk_flags": ["coverage_unclear", "missing_documentation", "late_notification", "high_value", "fraud_indicator"],
  "decision_summary": "brief summary",
  "policy_basis": "policy basis for decision",
  "uncertainty": "what remains uncertain",
  "human_review_recommended": true
}}

INTAKE:
{state['intake']}

COVERAGE ANALYSIS:
{state['coverage_analysis']}
"""
    raw = call_claude(client, prompt, max_tokens=900)
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        decision = {
            "decision": "ESCALATE",
            "confidence": 0.50,
            "risk_flags": ["invalid_json_output"],
            "decision_summary": raw,
            "policy_basis": "The model did not return valid JSON.",
            "uncertainty": "Output parsing failed; human review required.",
            "human_review_recommended": True,
        }

    state["decision"] = decision
    state["confidence"] = float(decision.get("confidence", 0.50))
    state["risk_flags"] = list(set(decision.get("risk_flags", [])))
    add_audit(state, "Decision Agent", f"Decision generated: {decision.get('decision', 'UNKNOWN')}.")
    return state


def validation_agent(client, state):
    prompt = f"""
You are a claims QA validation agent.

Challenge the proposed decision. Look for unsupported conclusions, ambiguity, missing documents,
late notification, coverage uncertainty, and cases that require human review.

Return ONLY valid JSON with this schema:
{{
  "validation_status": "PASS | REVIEW_REQUIRED | FAIL",
  "issues": ["issue 1", "issue 2"],
  "additional_risk_flags": ["coverage_unclear", "missing_documentation", "late_notification", "high_value", "inconsistent_reasoning"],
  "confidence_adjustment": -0.15,
  "human_review_required": true,
  "reason": "brief reason"
}}

CLAIM:
{state['claim_text']}

POLICY:
{state['policy_text']}

INTAKE:
{state['intake']}

COVERAGE ANALYSIS:
{state['coverage_analysis']}

PROPOSED DECISION:
{json.dumps(state['decision'], indent=2)}
"""
    raw = call_claude(client, prompt, max_tokens=900)
    try:
        validation = json.loads(raw)
    except json.JSONDecodeError:
        validation = {
            "validation_status": "REVIEW_REQUIRED",
            "issues": ["Validation agent did not return valid JSON."],
            "additional_risk_flags": ["invalid_validation_output"],
            "confidence_adjustment": -0.20,
            "human_review_required": True,
            "reason": raw,
        }

    state["validation"] = validation
    adjustment = float(validation.get("confidence_adjustment", 0.0))
    state["confidence"] = max(0.0, min(1.0, state["confidence"] + adjustment))

    additional_flags = validation.get("additional_risk_flags", [])
    state["risk_flags"] = sorted(list(set(state["risk_flags"] + additional_flags)))

    if validation.get("human_review_required") is True:
        state["human_review_required"] = True

    add_audit(
        state,
        "Validation Agent",
        f"Validation status: {validation.get('validation_status', 'UNKNOWN')}; confidence adjusted by {adjustment:+.2f}.",
    )
    return state


def apply_escalation_rules(state, threshold):
    flags = set(state.get("risk_flags", []))
    reasons = []

    if state["confidence"] < threshold:
        state["human_review_required"] = True
        reasons.append(f"Final confidence {state['confidence']:.2f} below threshold {threshold:.2f}.")

    if "coverage_unclear" in flags:
        state["human_review_required"] = True
        reasons.append("Coverage unclear flag present.")

    if "missing_documentation" in flags:
        state["human_review_required"] = True
        reasons.append("Missing documentation flag present.")

    if "fraud_indicator" in flags:
        state["human_review_required"] = True
        reasons.append("Fraud indicator flag present.")

    if state["human_review_required"]:
        state["final_route"] = "HUMAN_REVIEW"
    else:
        state["final_route"] = "AUTO_PROCESS"

    add_audit(
        state,
        "Escalation Router",
        " | ".join(reasons) if reasons else "No deterministic escalation rule triggered.",
    )
    return state


# ── Run workflow ───────────────────────────────────────────────────────────
run = st.button("▶ Run Agentic Claims Workflow", type="primary")

if run:
    if not api_key:
        st.error("Enter your Anthropic API key.")
    elif not claim_text.strip() or not policy_text.strip():
        st.error("Provide both claim text and policy text.")
    else:
        try:
            client = get_client(api_key)
            state = new_state(claim_text, policy_text)
            add_audit(state, "Workflow Started", "State object created.")

            progress = st.progress(0, text="Starting workflow...")

            with st.spinner("Running Intake Agent..."):
                state = intake_agent(client, state)
                progress.progress(20, text="Intake complete")

            with st.spinner("Running Policy Agent..."):
                state = policy_agent(client, state)
                progress.progress(40, text="Policy analysis complete")

            with st.spinner("Running Decision Agent..."):
                state = decision_agent(client, state)
                progress.progress(60, text="Decision complete")

            with st.spinner("Running Validation Agent..."):
                state = validation_agent(client, state)
                progress.progress(80, text="Validation complete")

            state = apply_escalation_rules(state, confidence_threshold)
            progress.progress(100, text="Workflow complete")
            add_audit(state, "Workflow Completed", f"Final route: {state['final_route']}.")

            st.session_state["last_state"] = state
            st.success("Workflow completed.")

        except anthropic.AuthenticationError:
            st.error("Invalid Anthropic API key.")
        except Exception as e:
            st.error(f"Workflow failed: {e}")


# ── Results ────────────────────────────────────────────────────────────────
state = st.session_state.get("last_state")

if state:
    st.divider()

    metric1, metric2, metric3, metric4 = st.columns(4)
    with metric1:
        st.metric("Decision", state["decision"].get("decision", "UNKNOWN"))
    with metric2:
        st.metric("Final confidence", f"{state['confidence']:.2f}")
    with metric3:
        st.metric("Final route", state["final_route"])
    with metric4:
        st.metric("Risk flags", len(state["risk_flags"]))

    if state["final_route"] == "HUMAN_REVIEW":
        st.warning("Human review required before final settlement action.")
    else:
        st.success("No escalation rule triggered. Claim can proceed to auto-processing subject to business controls.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Intake", "Policy", "Decision", "Validation", "Final Routing", "Audit Trail"]
    )

    with tab1:
        st.markdown(state["intake"])

    with tab2:
        st.markdown(state["coverage_analysis"])

    with tab3:
        st.json(state["decision"])

    with tab4:
        st.json(state["validation"])

    with tab5:
        st.markdown("### Final Routing Decision")
        st.write(f"**Route:** {state['final_route']}")
        st.write(f"**Human review required:** {state['human_review_required']}")
        st.write(f"**Final confidence:** {state['confidence']:.2f}")
        st.markdown("### Risk Flags")
        if state["risk_flags"]:
            for flag in state["risk_flags"]:
                st.markdown(f"- `{flag}`")
        else:
            st.write("No risk flags.")

    with tab6:
        st.markdown("### Audit Trail")
        audit_df = pd.DataFrame(state["audit_trail"])
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇ Download audit trail CSV",
            data=audit_df.to_csv(index=False).encode("utf-8"),
            file_name="claims_triage_audit_trail.csv",
            mime="text/csv",
        )
