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
