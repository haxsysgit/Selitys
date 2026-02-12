# Selitys

A tool that explains backend codebases to developers. Point it at a local repo or a GitHub URL and get structured explanations of the architecture, request flow, risks, and more — like a senior engineer onboarding a new teammate.

Available as a **CLI**, a **web UI**, or both via **Docker**.

The name "selitys" is Finnish for "explanation".

---

## Install

### Option 1: pip (CLI only)

```bash
pip install selitys
```

### Option 2: Docker (web UI + API)

```bash
git clone https://github.com/haxhimitsu/selitys.git
cd selitys
cp .env.example .env  # optional: add LLM API key
docker compose up
```

Open **http://localhost:8000** — paste a local path or GitHub URL and go.

### Option 3: From source

```bash
git clone https://github.com/haxhimitsu/selitys.git
cd selitys
pip install -e ".[backend]"

# Start the web UI
cd frontend && npm install && npm run dev &
uvicorn backend.app:app --reload
```

---

## Quick Start

### CLI

```bash
# Generate markdown docs
selitys explain /path/to/repo -o ./output

# Ask a question (instant, keyword-based)
selitys ask /path/to/repo "what frameworks are used?"

# Ask with LLM for richer answers
selitys ask /path/to/repo "explain the auth flow" --llm
```

### Web UI

Paste any of these into the input field:

```
/path/to/local/repo
https://github.com/encode/httpx
https://github.com/tiangolo/fastapi
```

Public GitHub repos are cloned automatically with `git clone --depth 1`.

---

## What You Get

| Page | What it shows |
|------|---------------|
| **Overview** | Purpose, tech stack, metrics, domain entities, API surface, risks |
| **Architecture** | Subsystems with file trees, patterns, frameworks, language breakdown |
| **Request Flow** | Step-by-step request walkthrough with interactive timeline |
| **First Read** | Recommended reading order for new developers |
| **Config** | Config files, environment variables, entry points |
| **Ask** | Q&A — keyword-based or LLM-powered |

The CLI generates the same data as markdown files:

| File | Description |
|------|-------------|
| `selitys-overview.md` | System purpose, tech stack, domain entities, API surface |
| `selitys-architecture.md` | Subsystems, patterns, dependency graph, risk areas |
| `selitys-request-flow.md` | Step-by-step request walkthrough |
| `selitys-first-read.md` | Recommended reading order |
| `selitys-config.md` | Configuration files, environment variables |

---

## CLI Options

### `selitys explain`

```bash
selitys explain /path/to/repo -o ./output
```

| Flag | Description |
|------|-------------|
| `-o, --output` | Output directory (default: `./selitys-output`) |
| `--json` | Also generate `selitys-analysis.json` |
| `--watch` | Re-run on file changes |
| `--include` | Glob patterns to include |
| `--exclude` | Glob patterns to exclude |
| `--max-file-size` | Skip files larger than this (default: 2MB) |

### `selitys ask`

```bash
selitys ask /path/to/repo "how does auth work?" --llm
```

| Flag | Env var | Description |
|------|---------|-------------|
| `--llm` | — | Use LLM instead of keyword matching |
| `--api-key` | `SELITYS_API_KEY` | API key for the LLM provider |
| `--base-url` | `SELITYS_BASE_URL` | OpenAI-compatible API base URL |
| `--model` | `SELITYS_MODEL` | Model name (e.g. `llama-3.3-70b-versatile`) |

---

## Supported Languages

| Language | Frameworks |
|----------|------------|
| Python | FastAPI, Flask, Django, SQLAlchemy, Alembic, Pydantic, Celery, pytest |
| TypeScript / JavaScript | Express, Next.js, NestJS, React, Vue, Angular, Prisma, Sequelize |

Python support is the most mature.

---

## Who It's For

- **New team members** joining an unfamiliar codebase
- **Solo developers** returning to an old project
- **Tech leads** onboarding new hires
- **Reviewers** assessing system quality

---

## Design Principles

- **Read-only** — never modifies the analyzed repository
- **Repo-specific** — tailored explanations, not generic advice
- **Evidence-first** — claims include file references
- **Lightweight** — no heavy deps; LLM is optional

---

## License

MIT
