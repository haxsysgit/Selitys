"""selitys API — FastAPI backend wrapping the existing analysis modules."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root so SELITYS_API_KEY etc. are available
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# Ensure the src/ package is importable when running from the backend/ dir
sys.path.insert(0, str(_project_root / "src"))

from selitys import __version__  # noqa: E402
from selitys.core.analyzer import Analyzer  # noqa: E402
from selitys.core.qa import QuestionAnswerer  # noqa: E402
from selitys.core.scanner import RepoScanner  # noqa: E402

from backend.models import (  # noqa: E402
    AnalysisResponse,
    AnalyzeRequest,
    ApiEndpointOut,
    AskKeywordResponse,
    AskLLMResponse,
    AskRequest,
    DependencyEdgeOut,
    DependencyGraphOut,
    DependencyLayerOut,
    DependencyNodeOut,
    EntryPointOut,
    ErrorResponse,
    FrameworkOut,
    RequestFlowOut,
    RequestFlowStepOut,
    RiskAreaOut,
    SubsystemOut,
)

app = FastAPI(
    title="selitys API",
    description="Analyze backend codebases and ask questions about them",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory cache ─────────────────────────────────────────────
# Maps analysis_id → (RepoStructure, AnalysisResult)
_cache: dict[str, tuple] = {}


# ── Helpers ─────────────────────────────────────────────────────


# Maps GitHub URL → local temp path so we don't re-clone
_clone_cache: dict[str, str] = {}

_GH_PATTERN = re.compile(
    r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$"
)


def _resolve_repo_path(raw_path: str, github_token: str | None = None) -> Path:
    """Resolve a local path or GitHub URL to a local directory.

    For private repos, pass a GitHub personal access token via *github_token*
    or set the ``GITHUB_TOKEN`` environment variable.
    """
    match = _GH_PATTERN.match(raw_path.strip())
    if match:
        if raw_path in _clone_cache:
            p = Path(_clone_cache[raw_path])
            if p.is_dir():
                return p

        owner, repo_name = match.group(1), match.group(2)
        token = github_token or os.environ.get("GITHUB_TOKEN")

        # Build clone URL — inject token for private repos
        clone_url = raw_path.strip()
        if token:
            clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo_name}.git"

        tmp = Path(tempfile.mkdtemp(prefix=f"selitys-{owner}-{repo_name}-"))
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(tmp / repo_name)],
                check=True, capture_output=True, text=True, timeout=120,
            )
        except subprocess.CalledProcessError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            detail = e.stderr.strip()
            # Don't leak token in error messages
            if token:
                detail = detail.replace(token, "***")
            raise HTTPException(status_code=400, detail=f"Failed to clone repo: {detail}")
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmp, ignore_errors=True)
            raise HTTPException(status_code=408, detail="Clone timed out (120s). Repo may be too large.")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="git is not installed on this system.")

        cloned = tmp / repo_name
        _clone_cache[raw_path] = str(cloned)
        return cloned

    repo = Path(raw_path).resolve()
    if not repo.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a valid directory: {raw_path}")
    return repo


def _run_scan_and_analysis(req: AnalyzeRequest | AskRequest):
    """Scan + analyze a repo. Returns (structure, analysis)."""
    repo = _resolve_repo_path(req.repo_path, getattr(req, "github_token", None))
    if not repo.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a valid directory: {req.repo_path}")

    max_size = None if req.max_file_size <= 0 else req.max_file_size
    scanner = RepoScanner(
        repo,
        max_file_size_bytes=max_size,
        respect_gitignore=req.respect_gitignore,
        include_patterns=getattr(req, "include_patterns", None),
        exclude_patterns=getattr(req, "exclude_patterns", None),
    )
    structure = scanner.scan()
    analyzer = Analyzer(structure)
    analysis = analyzer.analyze()
    return structure, analysis


def _analysis_to_response(structure, analysis) -> AnalysisResponse:
    """Convert internal dataclasses to the API response model."""
    return AnalysisResponse(
        repo_name=analysis.repo_name,
        likely_purpose=analysis.likely_purpose,
        detailed_purpose=analysis.detailed_purpose,
        total_files=structure.total_files,
        total_lines=structure.total_lines,
        languages=structure.languages_detected,
        domain_entities=analysis.domain_entities,
        api_endpoints=[
            ApiEndpointOut(method=m, path=p, description=d)
            for m, p, d in analysis.api_endpoints
        ],
        frameworks=[
            FrameworkOut(name=fw.name, category=fw.category, confidence=fw.confidence)
            for fw in analysis.frameworks
        ],
        entry_points=[
            EntryPointOut(path=ep.path, description=ep.description)
            for ep in analysis.entry_points
        ],
        subsystems=[
            SubsystemOut(
                name=s.name, directory=s.directory,
                description=s.description, key_files=s.key_files,
            )
            for s in analysis.subsystems
        ],
        risk_areas=[
            RiskAreaOut(
                location=r.location, risk_type=r.risk_type,
                description=r.description, severity=r.severity,
            )
            for r in analysis.risk_areas
        ],
        patterns_detected=analysis.patterns_detected,
        request_flow=(
            RequestFlowOut(
                name=analysis.request_flow.name,
                description=analysis.request_flow.description,
                steps=[
                    RequestFlowStepOut(
                        order=s.order, location=s.location,
                        description=s.description, file_path=s.file_path,
                    )
                    for s in analysis.request_flow.steps
                ],
                touchpoints=analysis.request_flow.touchpoints,
            )
            if analysis.request_flow
            else None
        ),
        first_read_files=[
            {"path": path, "reason": reason, "priority": prio}
            for path, reason, prio in analysis.first_read_files
        ],
        skip_files=[
            {"path": path, "reason": reason}
            for path, reason in analysis.skip_files
        ],
        config_files=analysis.config.config_files,
        env_vars=analysis.config.env_vars,
        dependency_graph=DependencyGraphOut(
            nodes=[
                DependencyNodeOut(
                    path=n.path, label=n.label, node_type=n.node_type,
                    subsystem=n.subsystem, imports_count=n.imports_count,
                    imported_by_count=n.imported_by_count,
                )
                for n in analysis.dependency_graph.nodes
            ],
            edges=[
                DependencyEdgeOut(
                    source=e.source, target=e.target,
                    import_name=e.import_name, edge_type=e.edge_type,
                )
                for e in analysis.dependency_graph.edges
            ],
            layers=[
                DependencyLayerOut(name=l["name"], files=l["files"], type=l["type"])
                for l in analysis.dependency_graph.layers
            ],
        ),
    )


# ── Routes ──────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    """Health check for Render / uptime monitors."""
    return {"status": "ok", "version": __version__}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest):
    """Analyze a repository and return structured results."""
    structure, analysis = _run_scan_and_analysis(req)

    # Cache for subsequent /ask calls
    analysis_id = str(uuid.uuid4())
    _cache[req.repo_path] = (structure, analysis)

    resp = _analysis_to_response(structure, analysis)
    return resp


@app.post("/api/ask", response_model=AskKeywordResponse | AskLLMResponse)
async def ask(req: AskRequest):
    """Ask a question about a codebase."""
    # Use cached analysis if available, otherwise run fresh
    if req.repo_path in _cache:
        structure, analysis = _cache[req.repo_path]
    else:
        structure, analysis = _run_scan_and_analysis(req)
        _cache[req.repo_path] = (structure, analysis)

    if req.use_llm:
        try:
            from selitys.core.qa_llm import ask_llm
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="LLM Q&A requires httpx. Install with: pip install httpx",
            )

        try:
            response = ask_llm(
                structure,
                analysis,
                req.question,
                api_key=req.api_key,
                base_url=req.base_url,
                model=req.model,
            )
        except SystemExit:
            raise HTTPException(
                status_code=400,
                detail="LLM call failed. Check API key (SELITYS_API_KEY) and provider config.",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return AskLLMResponse(question=req.question, answer=response)

    # Keyword-based
    qa = QuestionAnswerer(structure, analysis)
    answer = qa.ask(req.question)
    return AskKeywordResponse(
        question=answer.question,
        summary=answer.summary,
        details=answer.details,
        related_files=answer.related_files,
        confidence=answer.confidence,
    )


@app.get("/api/results/{repo_path:path}", response_model=AnalysisResponse)
async def get_results(repo_path: str):
    """Retrieve cached analysis results for a repo path."""
    # Try with and without leading slash
    key = repo_path if repo_path in _cache else f"/{repo_path}"
    if key not in _cache:
        raise HTTPException(status_code=404, detail="No cached analysis for this repo. Run /api/analyze first.")

    structure, analysis = _cache[key]
    return _analysis_to_response(structure, analysis)


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok", "version": __version__}


# ── Static frontend serving (production) ─────────────────────────
_frontend_dist = _project_root / "frontend" / "dist"
if _frontend_dist.is_dir():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the Vue SPA — try static file first, fallback to index.html."""
        file = _frontend_dist / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(_frontend_dist / "index.html")

    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="assets")
