"""selitys API — FastAPI backend wrapping the existing analysis modules."""

from __future__ import annotations

import sys
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
    version="3.0.0",
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


def _run_scan_and_analysis(req: AnalyzeRequest | AskRequest):
    """Scan + analyze a repo. Returns (structure, analysis)."""
    repo = Path(req.repo_path).resolve()
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
    )


# ── Routes ──────────────────────────────────────────────────────


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
    return {"status": "ok", "version": "3.0.0"}
