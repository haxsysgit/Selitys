# Selitys

A local CLI tool that explains backend codebases to developers.

The name "selitys" is Finnish for "explanation" or "clarification".

---

## What It Does

selitys analyzes a local repository and generates structured markdown explanations that help you understand:

- What the system does and its domain entities
- How requests flow through the application
- What architectural patterns are used
- Which areas are risky or fragile
- What files to read first as a new developer

It behaves like a senior engineer onboarding a new teammate.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/selitys.git
cd selitys

# Install with uv
uv sync
```

---

## Usage

```bash
# Analyze a repository
selitys explain /path/to/your/backend -o ./output

# Check version
selitys version
```

This generates four markdown files in the output directory:

| File | Description |
|------|-------------|
| `selitys-overview.md` | System purpose, tech stack, domain entities, API endpoints |
| `selitys-architecture.md` | Subsystems, patterns, coupling, risk areas |
| `selitys-request-flow.md` | Step-by-step request walkthrough with code insights |
| `selitys-first-read.md` | Recommended reading order for new developers |

---

## Target Users

- Backend engineers joining an unfamiliar codebase
- Solo developers returning to an old project
- Teams onboarding new hires
- Reviewers assessing system quality

---

## Design Principles

- **Read-only**: Never modifies the analyzed repository
- **Repo-specific**: Tailored explanations, not generic advice
- **Opinionated but careful**: Uses cautious language for inferences
- **Structured output**: Deterministic markdown, not prose

---

## Supported Frameworks

selitys works best with Python backend projects using:

- FastAPI / Flask / Django
- SQLAlchemy
- Alembic
- Pydantic

Support for other languages and frameworks is planned.

---

## License

MIT