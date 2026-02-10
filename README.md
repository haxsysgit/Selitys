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

# Include JSON output
selitys explain /path/to/your/backend -o ./output --json

# Check version
selitys version
```

This generates five markdown files in the output directory:

| File | Description |
|------|-------------|
| `selitys-overview.md` | System purpose, tech stack, domain entities, API endpoints |
| `selitys-architecture.md` | Subsystems, patterns, coupling, risk areas |
| `selitys-request-flow.md` | Step-by-step request walkthrough with code insights |
| `selitys-first-read.md` | Recommended reading order for new developers |
| `selitys-config.md` | Configuration files and environment variables |

Optional:
- `selitys-analysis.json` when `--json` is used

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
- **Evidence-first**: Non-obvious statements include evidence references or uncertainty notes

---

## Supported Frameworks

selitys works best with Python backend projects using:

- FastAPI / Flask / Django
- SQLAlchemy
- Alembic
- Pydantic

JS and TS support is available but less mature than Python.

---

## Spec

The current spec lives in `selitys-v2-spec.md`.

---

## License

MIT
