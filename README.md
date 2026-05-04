# AI Claims Triage Workflow (LangGraph + Claude)
🔹 Overview 

Replace your current overview with:

## Overview

This project implements a governed AI-assisted claims triage workflow using a state-machine architecture.

The system combines:
- Claude (Anthropic) for probabilistic decision-making
- Python for deterministic validation and control logic
- LangGraph for orchestration of workflow steps

The objective is to demonstrate how AI can support insurance claims operations while maintaining full auditability, control, and human oversight.
🔹 Architecture 
## Architecture

The workflow is designed as a state machine:

Claim State → Decision Node → Validation Node → Routing / Human Review

### Components

- **ClaimState**: Structured claim file evolving across the workflow
- **decision_node**: Claude evaluates the claim and returns structured JSON
- **validation_node**: Ensures output integrity and enforces constraints
- **routing_node**: Applies deterministic business rules
- **human_review_node**: Escalates sensitive or uncertain claims

### Flow Logic

- All claims are validated before routing
- Human review is triggered for:
  - low confidence
  - unclear claims
  - sensitive decisions (e.g. rejection)
🔹 Governance & Controls (THIS IS YOUR EDGE)
## Governance & Controls

The system enforces multiple control layers:

- Structured JSON outputs (no free text decisions)
- Confidence thresholds for decision reliability
- Validation layer before any operational routing
- Human-in-the-loop for uncertain or high-risk cases
- Full audit trail capturing every decision step

This ensures compliance with regulated insurance environments (e.g. DORA, EU AI Act principles).
🔹 Test Cases (NEW SECTION)
## Test Cases

The workflow has been validated using three scenarios:

1. **Low-risk claim**
   - Result: AUTO_PAY
   - Path: decision → validation → routing

2. **Unclear claim**
   - Result: MANUAL_REVIEW
   - Path: decision → validation → human_review

3. **Intentional damage**
   - Result: REJECT → HUMAN_REVIEW
   - Path: decision → validation → human_review
🔹 Insurance Relevance (KEEP BUT UPGRADE)
## Insurance Relevance

This workflow mirrors real-world claims operations:

- FNOL triage and classification
- Straight-through processing for low-risk claims
- Controlled escalation to claims adjusters
- Auditability for regulatory and internal governance

The system demonstrates how AI can augment, not replace, claims decision-making.
🔹 Key Insight (VERY IMPORTANT)
## Key Insight

LLMs provide reasoning, but cannot be trusted as standalone decision systems.

Control must be enforced through:
- deterministic validation
- explicit routing rules
- human oversight

This architecture separates probabilistic AI reasoning from operational decision control.
