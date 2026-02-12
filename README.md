# Selitys

A CLI tool that explains backend codebases to developers. Point it at a repository and get structured explanations of the architecture, request flow, risks, and more — like a senior engineer onboarding a new teammate.

The name "selitys" is Finnish for "explanation".

---

## Installation

```bash
git clone https://github.com/yourusername/selitys.git
cd selitys
uv sync
```

To enable LLM-powered Q&A (optional):

```bash
uv sync --extra llm
cp .env.example .env
# Edit .env with your API key
```

---

## Quick Start

```bash
# Generate markdown docs for a codebase
selitys explain /path/to/repo -o ./output

# Ask a question about a codebase
selitys ask /path/to/repo "what frameworks are used?"

# Ask with LLM for richer answers
selitys ask /path/to/repo "explain the auth flow" --llm
```

---

## Commands

### `selitys explain`

Analyzes a repository and generates structured markdown documentation.

```bash
selitys explain /path/to/repo -o ./output
```

**Output files:**

| File | Description |
|------|-------------|
| `selitys-overview.md` | System purpose, tech stack, domain entities, API surface |
| `selitys-architecture.md` | Subsystems, patterns, coupling, Mermaid dependency graph, risk areas |
| `selitys-request-flow.md` | Step-by-step request walkthrough with code insights |
| `selitys-first-read.md` | Recommended reading order for new developers |
| `selitys-config.md` | Configuration files, environment variables, setup guide |

**Options:**

| Flag | Description |
|------|-------------|
| `-o, --output` | Output directory (default: `./selitys-output`) |
| `--json` | Also generate `selitys-analysis.json` for machine consumption |
| `--watch` | Re-run analysis automatically when source files change |
| `--include` | Only scan files matching these glob patterns |
| `--exclude` | Skip files matching these glob patterns |
| `--max-file-size` | Skip files larger than this (bytes, default: 2MB) |
| `--respect-gitignore` | Honor `.gitignore` rules (default: on) |

### `selitys ask`

Ask a question about a codebase and get an instant answer.

```bash
# Keyword-based (instant, no setup needed)
selitys ask /path/to/repo "what are the security risks?"

# LLM-powered (requires API key)
selitys ask /path/to/repo "how does authentication work?" --llm
```

Without `--llm`, questions are matched to topics using keyword analysis. Supported topics: purpose, frameworks, entry points, configuration, risks, architecture, request flow, languages, dependencies, entities, and file structure.

With `--llm`, your question and the full analysis context are sent to an LLM for a detailed, natural-language answer.

**LLM options:**

| Flag | Env var | Description |
|------|---------|-------------|
| `--api-key` | `SELITYS_API_KEY` | API key for the LLM provider |
| `--base-url` | `SELITYS_BASE_URL` | Base URL for an OpenAI-compatible API |
| `--model` | `SELITYS_MODEL` | Model name (e.g. `llama-3.3-70b-versatile`) |

See `.env.example` for provider-specific configuration.

### `selitys version`

Print the current version.

---

## Supported Languages & Frameworks

| Language | Frameworks |
|----------|------------|
| Python | FastAPI, Flask, Django, SQLAlchemy, Alembic, Pydantic, Celery, pytest |
| TypeScript / JavaScript | Express, Next.js, NestJS, React, Vue, Angular, Prisma, Sequelize |

Python support is the most mature. TypeScript/JavaScript detection covers frameworks, entry points, config files, and environment variables.

---

## Who It's For

- **New team members** joining an unfamiliar codebase
- **Solo developers** returning to an old project
- **Tech leads** onboarding new hires
- **Reviewers** assessing system quality before a code review

---

## Design Principles

- **Read-only** — never modifies the analyzed repository
- **Repo-specific** — tailored explanations, not generic advice
- **Evidence-first** — non-obvious claims include file references or uncertainty notes
- **Structured output** — deterministic markdown, not free-form prose
- **Lightweight** — no heavy dependencies; LLM support is optional

---

## JSON Schema

The JSON output shape is documented in `docs/selitys-analysis.schema.json`.

---

## License

MIT
