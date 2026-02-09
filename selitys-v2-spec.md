# selitys v2 Specification

## Project Identity
Project name: selitys
Purpose: local, read-only developer tooling that explains backend codebases

## Core Objective
Produce deterministic, evidence-based onboarding documents from a local repository.

## Constraints
- Read-only, never modifies the analyzed repo
- No remote repository support
- No UI or web server in v2
- No diagrams in output
- No em dashes in output
- Never invent system behavior
- Every non-obvious statement must cite evidence or be marked uncertain

## v2 Focus
- Deeper analysis for Python and JavaScript/TypeScript
- Cleaner architecture for adding new languages
- Performance and scale for large repositories

## Outputs
Generate these files in the output directory:
- selitys-overview.md
- selitys-architecture.md
- selitys-request-flow.md
- selitys-first-read.md
- selitys-config.md

Optional:
- selitys-analysis.json

All markdown outputs must be deterministic and stable.

## Evidence Model
Every derived fact includes:
- File path
- Line number range when available
- Evidence snippet or symbol name
- Confidence: high, medium, low

If evidence is missing, label the statement as uncertain.

## Analysis Pipeline
1. Scan repository
2. Parse and index files by language
3. Extract facts per language analyzer
4. Merge facts into a unified model
5. Generate markdown and JSON

## Language Support
v2 must support:
- Python: AST-based extraction
- JavaScript/TypeScript: parser-based extraction

Heuristic-only analysis is allowed for other languages, but must be marked low confidence.

## Facts to Extract
- Entry points
- Frameworks and libraries
- Routes and handlers
- Domain models and persistence
- Configuration files and environment variables
- Subsystems and likely dependency flow
- Risk areas and technical debt signals

## Output Schema
Each markdown file must include these sections.

selitys-overview.md
- System Purpose
- What This System Does
- Domain Entities
- API Surface
- Technology Stack
- Project Structure
- Entry Points
- Configuration
- Quick Stats

selitys-architecture.md
- Subsystems
- Patterns Detected
- Coupling and Dependencies
- Risk Areas

selitys-request-flow.md
- Overview
- Step-by-Step Flow
- Key Touchpoints

selitys-first-read.md
- Start Here
- Core Logic
- Can Skip Initially
- Reading Order Rationale

selitys-config.md
- Overview
- Configuration Files
- Environment Variables
- Local Setup
- Security Notes

## CLI
Required:
- selitys explain <repo> -o <output>

Optional:
- --json
- --include <glob>
- --exclude <glob>
- --max-file-size <bytes>
- --respect-gitignore

## Performance
- Skip binary and oversized files
- Respect .gitignore by default
- Cache parsed results by file hash
- Parallelize parsing where safe

## Versioning
- CLI version and JSON schema version must match

## Definition of Done for v2
- Python AST analyzer shipped
- JS/TS analyzer shipped
- Evidence present or uncertainty marked
- Five markdown outputs are stable
- JSON output matches the same facts
- Large repo scan completes in acceptable time
