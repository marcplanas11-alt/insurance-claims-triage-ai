import app


def test_create_initial_state_has_required_fields():
    state = app.create_initial_state("C1", "Minor scratch on vehicle")

    assert state["claim_id"] == "C1"
    assert state["claim_text"] == "Minor scratch on vehicle"
    assert state["decision"] is None
    assert state["confidence"] is None
    assert state["human_review_required"] is False
    assert state["human_review_reason"] is None
    assert state["human_reviewer"] is None
    assert state["human_review_status"] is None
    assert state["audit_log"] == []


def test_safe_json_parse_plain_json():
    raw = '{"decision": "APPROVE", "confidence": 0.85, "reason": "clear low-risk claim"}'
    parsed = app.safe_json_parse(raw)

    assert parsed["decision"] == "APPROVE"
    assert parsed["confidence"] == 0.85


def test_safe_json_parse_markdown_json():
    raw = """```json
{
  "decision": "ESCALATE",
  "confidence": 0.5,
  "reason": "unclear claim"
}
```"""
    parsed = app.safe_json_parse(raw)

    assert parsed["decision"] == "ESCALATE"
    assert parsed["confidence"] == 0.5


def test_validation_node_accepts_valid_decision():
    state = app.create_initial_state("C2", "Minor scratch")
    state["decision"] = "APPROVE"
    state["confidence"] = 0.85
    state["decision_reason"] = "Low-risk claim"

    result = app.validation_node(state)

    assert result["is_valid"] is True
    assert result["validation_errors"] == []
    assert result["audit_log"][-1]["step"] == "validation_node"


def test_validation_node_rejects_invalid_decision_value():
    state = app.create_initial_state("C3", "Minor scratch")
    state["decision"] = "MAYBE"
    state["confidence"] = 0.85
    state["decision_reason"] = "Invalid decision test"

    result = app.validation_node(state)

    assert result["is_valid"] is False
    assert "Invalid decision value" in result["validation_errors"]
    assert result["human_review_required"] is True


def test_human_review_node_sets_review_fields():
    state = app.create_initial_state("C4", "Unclear claim")
    state["decision_reason"] = "Claim details unclear"
    state["human_review_required"] = True

    result = app.human_review_node(state)

    assert result["routing"] == "MANUAL_REVIEW"
    assert result["final_status"] == "Pending human claims review"
    assert result["human_review_reason"] == "Claim details unclear"
    assert result["human_reviewer"] == "claims_adjuster"
    assert result["human_review_status"] == "PENDING"
    assert result["audit_log"][-1]["step"] == "human_review_node"


def test_decide_next_step_routes_to_human_review():
    state = app.create_initial_state("C5", "Unclear claim")
    state["human_review_required"] = True

    assert app.decide_next_step(state) == "human_review"


def test_decide_next_step_routes_to_routing():
    state = app.create_initial_state("C6", "Clear low-risk claim")
    state["human_review_required"] = False

    assert app.decide_next_step(state) == "routing"
