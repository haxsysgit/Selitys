# Selitys

selitys is a local developer onboarding and codebase explanation tool.

The name “selitys” is finnish for “explanation” or “clarification”.

selitys explains a backend codebase as if you just joined the team on day one.
It focuses on understanding systems, architecture, intent, and risk rather than rewriting or refactoring code.

This is a tooling project, not a framework, runtime, or AI chatbot.

---

## Core Purpose

Help developers answer questions like:
- What does this system actually do?
- Where does the real logic live?
- What should I read first?
- What parts are risky or fragile?
- How does a request flow end to end?
- Why does this weird file exist?

selitys behaves like a senior engineer onboarding a new teammate.

---

## Non-Goals

selitys explicitly does NOT:
- Modify or refactor code
- Generate production code
- Teach basic programming concepts
- Invent missing behavior
- Act as a generic “explain any code” chatbot

selitys is:
- Repo-specific
- Read-only
- Opinionated but careful
- Focused on clarity and confidence

---

## Target Users

- Backend engineers joining an unfamiliar codebase
- Solo developers returning to an old project
- Students learning real-world architecture
- Teams onboarding new hires
- Reviewers assessing system quality

---

## Operating Principles

1. Read before reasoning  
2. Infer carefully, never hallucinate  
3. Prefer “appears to” over certainty  
4. Highlight uncertainty explicitly  
5. Optimize for developer confidence  

---

## System Capabilities

selitys can:
- Inspect repository structure
- Identify entry points
- Detect architectural patterns
- Group files into subsystems
- Trace request lifecycles
- Identify coupling and risk
- Explain configuration and environment usage
- Answer repo-specific questions

selitys outputs structured explanations, not code.

---

## Incremental Build Philosophy

selitys must be built in small, stable steps.

Each step must:
- Produce working, reviewable output
- Avoid cascading complexity
- Build cleanly on previous steps
- Stop and wait for approval before continuing

The system must never attempt to build everything at once.

---

## High-Level Components

selitys is composed of logical layers, not technical ones:

1. Repository Scanner
2. Structure Interpreter
3. Architecture Explainer
4. Risk and Fragility Analyzer
5. Request Flow Narrator
6. Question Answering Layer
7. Markdown Exporter

Each layer can exist independently.

---

## Example Outputs

- selitys-overview.md
- selitys-architecture.md
- selitys-risk-map.md
- selitys-request-flow.md
- selitys-first-read.md

---

## Success Criteria

The project is successful if:
- A developer unfamiliar with the repo feels oriented in under 10 minutes
- The explanations feel accurate and grounded
- Risk areas are called out honestly
- The system feels like a human mentor, not documentation

---

## Future Extensions (Optional)

- CLI wrapper
- IDE integration
- Confidence scoring
- Comparison between two versions of a repo
- Onboarding checklist generation

These are explicitly out of scope for v1.

---