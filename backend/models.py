"""Pydantic models for the selitys API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request models ──────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the repository to analyze")
    max_file_size: int = Field(2_000_000, description="Skip files larger than this (bytes)")
    respect_gitignore: bool = Field(True, description="Respect .gitignore rules")
    include_patterns: list[str] | None = Field(None, description="Glob patterns to include")
    exclude_patterns: list[str] | None = Field(None, description="Glob patterns to exclude")


class AskRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the repository to query")
    question: str = Field(..., description="Question about the codebase")
    use_llm: bool = Field(False, description="Use LLM for richer answers")
    api_key: str | None = Field(None, description="API key for LLM provider")
    base_url: str | None = Field(None, description="Base URL for OpenAI-compatible API")
    model: str | None = Field(None, description="Model name to use")
    max_file_size: int = Field(2_000_000, description="Skip files larger than this (bytes)")
    respect_gitignore: bool = Field(True, description="Respect .gitignore rules")


# ── Response models ─────────────────────────────────────────────


class EntryPointOut(BaseModel):
    path: str
    description: str


class FrameworkOut(BaseModel):
    name: str
    category: str
    confidence: str = "high"


class RiskAreaOut(BaseModel):
    location: str
    risk_type: str
    description: str
    severity: str = "medium"


class ApiEndpointOut(BaseModel):
    method: str
    path: str
    description: str


class SubsystemOut(BaseModel):
    name: str
    directory: str
    description: str
    key_files: list[str] = []


class RequestFlowStepOut(BaseModel):
    order: int
    location: str
    description: str
    file_path: str | None = None


class RequestFlowOut(BaseModel):
    name: str
    description: str
    steps: list[RequestFlowStepOut] = []
    touchpoints: list[str] = []


class AnalysisResponse(BaseModel):
    repo_name: str
    likely_purpose: str
    detailed_purpose: str = ""
    total_files: int = 0
    total_lines: int = 0
    languages: dict[str, int] = {}
    domain_entities: list[str] = []
    api_endpoints: list[ApiEndpointOut] = []
    frameworks: list[FrameworkOut] = []
    entry_points: list[EntryPointOut] = []
    subsystems: list[SubsystemOut] = []
    risk_areas: list[RiskAreaOut] = []
    patterns_detected: list[str] = []
    request_flow: RequestFlowOut | None = None
    first_read_files: list[dict] = []
    skip_files: list[dict] = []
    config_files: list[str] = []
    env_vars: list[str] = []


class AskKeywordResponse(BaseModel):
    question: str
    summary: str
    details: list[str] = []
    related_files: list[str] = []
    confidence: str = "high"
    mode: str = "keyword"


class AskLLMResponse(BaseModel):
    question: str
    answer: str
    mode: str = "llm"


class ErrorResponse(BaseModel):
    detail: str
