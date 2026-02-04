# selitys AI Build Prompt

This document defines the exact instructions for building selitys incrementally using an AI coding assistant.

The human will not write code.
The human will review, approve, or request fixes.
The AI must proceed carefully and in small steps.

---

## Project Identity

Project name: selitys  
Meaning: explanation or clarification

selitys is a local, read-only developer tooling project that explains a backend codebase as if the reader just joined the team on day one.

selitys focuses on understanding systems, not changing them.

---

## Core Objective

Build a CLI tool that:
- Reads a local backend repository
- Analyzes structure and relationships
- Produces structured markdown explanations
- Helps a developer understand architecture, request flow, and risk

selitys must feel like a senior engineer onboarding a teammate.

---

## Absolute Constraints

These constraints are mandatory and must never be violated.

- Do not refactor or modify the analyzed repository
- Do not generate production application code
- Do not invent system behavior
- Do not overbuild features
- Do not move to the next step without explicit approval
- Do not bundle all features into one implementation
- Do not use em dashes in any output
- Do not use commit prefixes like feat, chore, fix, refactor

If anything is unclear, state uncertainty explicitly.

---

## Human Role

The human will:
- Review outputs
- Approve or reject steps
- Ask for fixes
- Decide when to proceed

The human will not:
- Write code
- Debug large codebases
- Review massive diffs

Optimize for minimal review effort.

---

## Development Environment

- Language: Python
- Dependency management: uv
- Interface: CLI only
- Outputs: Markdown files

Use uv consistently for:
- Dependency declaration
- Virtual environment setup
- Reproducibility

Do not introduce unnecessary dependencies.

---

## Incremental Build Rule

selitys must be built in small, stable layers.

Each step must:
- Be independently reviewable
- Produce tangible value
- Avoid speculative abstractions
- Build directly on the previous step

After each step:
- Stop
- Ask for approval
- Wait for explicit instruction to continue

Never assume future steps are approved.

---

## Commit Rules

Commits are required occasionally, not constantly.

Commit messages must:
- Be plain sentences
- Describe what changed or why
- Avoid prefixes like feat, chore, refactor
- Avoid emojis

Examples:
- "Add initial repository scanning logic"
- "Introduce structured markdown output for overview"
- "Tighten request flow inference logic"

Do not squash everything into one commit.

---

## Step Order and Responsibilities

### Step 1: Repository Understanding Only

Do not write code yet.

Produce a written analysis that includes:
1. What the system appears to do
2. Primary entry points
3. Core subsystems
4. Where business logic likely lives
5. How configuration and environment variables are used
6. Which files a new developer should read first
7. Which areas appear risky or tightly coupled

Use cautious language.
Do not assume correctness.

Stop after this step and wait for approval.

---

### Step 2: Explanation Schema Definition

Still no code.

Define:
- The exact markdown structure selitys will generate
- Required sections for each output file
- Naming conventions
- What information is mandatory vs optional

The schema must be simple and deterministic.

Stop and wait for approval.

---

### Step 3: Minimal Core Engine

Now begin coding.

Responsibilities:
- Traverse the local repository
- Read files safely
- Build a minimal internal representation
- No CLI flags yet
- No exports yet
- No plugins

Focus on correctness and clarity.

After implementation:
- Commit once
- Stop and wait for approval

---

### Step 4: Overview Markdown Generation

Responsibilities:
- Generate selitys-overview.md
- Follow the approved schema exactly
- Ensure deterministic ordering
- Avoid conversational tone

After implementation:
- Commit once
- Stop and wait for approval

---

### Step 5: Architecture and Risk Explanation

Responsibilities:
- Group files into subsystems
- Infer dependency direction where possible
- Highlight coupling and fragility
- Explicitly mark uncertain inferences

Do not attempt diagrams.
Text only.

After implementation:
- Commit once
- Stop and wait for approval

---

### Step 6: Request Flow Explanation

Responsibilities:
- Explain one typical request path
- Start from entry point to response
- Mention configuration and persistence touchpoints
- Avoid edge cases and branching logic

This is a narrative explanation, not a trace log.

After implementation:
- Commit once
- Stop and wait for approval

---

### Step 7: First-Read Guide

Responsibilities:
- Generate selitys-first-read.md
- List files in recommended reading order
- Explain why each file matters
- Explain what can be skipped initially

This must feel practical and opinionated but careful.

After implementation:
- Commit once
- Stop and wait for approval

---

## Definition of Done for v1

selitys v1 is complete when:
- Four markdown files are generated consistently
- Output structure is deterministic
- The explanations feel accurate and grounded
- A new backend developer feels oriented quickly
- No UI or web server exists
- No remote repository support exists

Once v1 is complete:
- Stop development
- Tag the release
- Do not add features immediately

---

## Quality Bar

Prefer:
- Clear reasoning over cleverness
- Explicit uncertainty over false confidence
- Small steps over fast progress
- Stable outputs over flexibility

selitys is judged on trustworthiness, not novelty.

---

## Final Instruction

Follow this document strictly.
Build selitys patiently.
Stop after each step.
Wait for approval.
