# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered medical triage system for ocular emergencies using The Wills Eye Manual (7th Edition) as the authoritative knowledge base. This is **medical software** where safety is paramount.

**Technology Stack:**
- Backend: Django 5.0 + Django REST Framework
- Frontend: Next.js 14 (App Router)
- LLM: Claude 3.5 Sonnet (primary) / GPT-4o (fallback)
- Knowledge Graph: Zep Graphiti
- Database: PostgreSQL 15+
- Monitoring: Langfuse
- Deployment: Docker + Kubernetes

## Critical Safety Requirements

**THESE ARE NON-NEGOTIABLE:**
1. NEVER bypass or weaken red flag detection logic
2. ALWAYS validate medical recommendations against Wills Eye Manual source
3. NEVER suggest specific medications without "consult doctor" disclaimer
4. ALL medical decision points must be logged for audit trail
5. 100% detection rate for emergent conditions (no false negatives on red flags)

## Development Commands

### Environment Setup
```bash
# Full setup
./scripts/setup_dev_environment.sh

# Backend only
cd backend && poetry install

# Frontend only
cd frontend && npm install
```

### Testing
```bash
# All tests
pytest

# Medical logic tests (REQUIRED for any triage changes)
pytest apps/triage/tests/test_triage_agent.py -v

# Red flag detection tests (CRITICAL - must pass)
pytest apps/triage/tests/test_red_flags.py -v

# With coverage (minimum 80% for medical code)
pytest --cov=apps --cov-report=html
```

### Running Locally
```bash
# All services
docker-compose up

# Backend only
python manage.py runserver

# Frontend only
cd frontend && npm run dev
```

### Data Pipeline
```bash
# Parse Wills Eye Manual EPUB to JSON (if needed)
python scripts/parse_wills_eye.py data/wills_eye_manual.epub

# Populate knowledge graph with medical data
# See indexing/QUICKSTART_INDEXING.md for full guide
python indexing/index_knowledge_graph.py --data data/wills_eye_structured.json --dry-run
python indexing/index_knowledge_graph.py --data data/wills_eye_structured.json
```

## Architecture Overview

### Triage Flow
```
Patient Input → Red Flag Check → Systematic Questions → Risk Stratification → Recommendation
```

**Phase 1: Red Flag Detection (0.2s threshold)**
- Immediate check for emergent conditions
- If detected: bypass all other logic, direct to ER
- Keywords + semantic analysis using LLM
- Located in: `backend/apps/triage/services/red_flag_detector.py`

**Phase 2: Systematic Interrogation**
- Query GraphRAG with standardized chief complaint
- Retrieve differential diagnoses (DDx) with urgency levels
- Use safety-first decision tree:
  1. Rule out Emergent (if likelihood >0.2, refer to ER)
  2. Rule out Urgent (if likelihood >0.2, refer within 24-48h)
  3. Identify Non-Urgent (schedule routine appointment)

**Phase 3: Virtual Exam & Recommendations**
- Guided self-tests (safe, non-invasive only)
- Educational component from Wills Eye Manual
- Home care advice (conservative, no specific drug recommendations)
- Appointment booking integration (Paziresh24, Nobat.ir)

### Key Components

**Triage Agent** (`backend/apps/triage/services/triage_agent.py`)
- Main orchestrator of triage flow
- Manages conversation state
- Calls red flag detector, knowledge graph, and LLM

**Red Flag Detector** (`backend/apps/triage/services/red_flag_detector.py`)
- Keyword matching + semantic analysis
- Must have zero false negatives
- See docs/medical/red-flags.md for complete list

**Knowledge Graph** (`backend/knowledge_graph/`)
- Zep Graphiti integration
- Structured Wills Eye Manual content
- Schema: Condition → Symptoms → Signs → DDx → Urgency Level

**LLM Prompts** (`backend/prompts/`)
- System prompts for each phase
- Few-shot examples for standardization
- All prompts must include safety disclaimers

## Medical Domain Rules

### Urgency Classification
- **Emergent**: ER immediately (e.g., sudden vision loss, chemical burn, penetrating trauma)
- **Urgent**: Doctor within 24-48 hours (e.g., keratitis, acute glaucoma)
- **Non-Urgent**: Schedule appointment 1-2 weeks (e.g., mild allergic conjunctivitis)

### Red Flags (See docs/medical/red-flags.md)
Examples include:
- Sudden vision loss (painless or painful)
- Chemical exposure to eye
- Penetrating trauma
- New floaters with flashes
- Severe eye pain with nausea/vomiting

**Testing Red Flag Detection:**
Every red flag must have:
1. Keyword list
2. Test cases in `apps/triage/tests/test_red_flags.py`
3. False positive/negative analysis

### Safety Protocols
1. Never provide diagnosis (only triage)
2. All responses include disclaimer
3. Consent required before any questions
4. HIPAA/GDPR compliant data handling
5. Explainable recommendations (cite Wills Eye Manual sections)

## Code Style & Standards

**Python:**
- Black formatter (line length 88)
- Type hints required for all functions
- Docstrings for all public methods (Google style)
- Example:
```python
def detect_red_flags(text: str) -> tuple[bool, str | None]:
    """Check patient input for emergent conditions.

    Args:
        text: Patient's description of symptoms

    Returns:
        Tuple of (is_red_flag, flag_type)
    """
```

**JavaScript/TypeScript:**
- Prettier + ESLint strict mode
- Functional components with TypeScript
- No `any` types

**Commits:**
- Conventional Commits format
- Examples: `feat(triage): add corneal ulcer detection`, `fix(red-flags): improve chemical burn keywords`

**Branches:**
- `feature/` for new features
- `bugfix/` for bug fixes
- `hotfix/` for production emergencies

## Testing Requirements

**For Medical Logic Changes:**
1. Unit tests with 80%+ coverage
2. Integration tests for triage flow
3. Mock external APIs (Zep, Claude, Paziresh24)
4. Test against validation scenarios in `test_scenarios/`

**Red Flag Tests:**
- Must test all red flag keywords
- Must test edge cases (e.g., "sudden" vs "suddenly", "lost vision" vs "blurry vision")
- Must validate no false negatives

## Key Documentation

Always check these before making changes:
- **Medical Framework**: docs/medical/framework.md (authoritative triage logic)
- **Red Flags**: docs/medical/red-flags.md (complete emergent conditions list)
- **Urgency Levels**: docs/medical/urgency-levels.md
- **Triage Algorithm**: docs/technical/triage-algorithm.md
- **API Specs**: docs/technical/api-specifications.md

## File Locations

- **LLM Prompts**: `backend/prompts/`
- **Medical Logic**: `backend/apps/triage/services/`
- **Knowledge Graph**: `backend/knowledge_graph/`
- **Knowledge Graph Indexing**: `indexing/` (scripts to populate Zep Graphiti)
- **Tests**: `backend/apps/triage/tests/`
- **Wills Eye Data**: `data/wills_eye_structured.json`
- **Test Scenarios**: `test_scenarios/`

## When Making Changes

1. **Check docs first**: Read relevant docs/medical/ and docs/technical/ files
2. **Update tests**: Medical logic changes require test updates
3. **Run medical tests**: `pytest apps/triage/tests/ -v` must pass
4. **Add Langfuse traces**: New LLM calls need monitoring
5. **Update documentation**: Architecture changes require doc updates
6. **Validate against Wills Eye**: Medical content must match source

## External Dependencies

- **Wills Eye Manual JSON**: Primary medical knowledge source
- **Zep API**: Knowledge graph requires API key
- **Paziresh24 API**: Iran appointment booking
- **Langfuse**: LLM call monitoring and token tracking
- **Claude API**: Primary LLM (Anthropic key required)

## Development Priorities

1. **Medical safety and accuracy** (highest priority - never compromise)
2. **HIPAA/GDPR compliance** (legal requirement)
3. **Performance and cost optimization** (<$0.10 per session target)
4. **User experience** (<5 minutes per triage)

## Current Development Phase

MVP Development - Focus on:
- Core triage flow with red flag detection
- Wills Eye Manual knowledge graph population
- Basic appointment booking integration
- Comprehensive testing of medical logic
