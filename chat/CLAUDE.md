# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered ocular triage chat interface using Chainlit and LangGraph. This is **medical software** where safety is paramount.

**Technology Stack:**
- **Chat Framework**: Chainlit 1.0+ (conversational AI interface)
- **Workflow Engine**: LangGraph (state machine for multi-phase triage)
- **LLM**: Claude 3.5 Sonnet (langchain-anthropic) / GPT-4o fallback (langchain-openai)
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Authentication**: Password-based (bcrypt hashing)
- **Migrations**: Alembic
- **Monitoring**: Langfuse (LLM observability)
- **Knowledge Graph**: Neo4j integration (planned)

## Critical Safety Requirements

**THESE ARE NON-NEGOTIABLE:**
1. NEVER bypass or weaken red flag detection in `src/agents/nodes.py:red_flag_check_node`
2. ALWAYS validate medical recommendations against Wills Eye Manual source
3. NEVER suggest specific medications without "consult doctor" disclaimer
4. ALL medical decision points must be logged for audit trail
5. 100% detection rate for emergent conditions (no false negatives on red flags)

## Development Commands

### Environment Setup
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# OR using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database URL

# Initialize database
alembic upgrade head

# Create admin user
python scripts/create_user.py
```

### Running the Application
```bash
# Run locally (default port 8000)
chainlit run src/app.py

# Run on custom port
chainlit run src/app.py --port 8080

# Run with hot reload
chainlit run src/app.py --watch

# Production mode
chainlit run src/app.py --host 0.0.0.0 --port 8000
```

### Testing
```bash
# All tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_triage_agent.py -v

# Red flag detection tests (CRITICAL - must pass)
pytest tests/test_red_flags.py -v

# Run tests in watch mode
pytest-watch
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (DESTRUCTIVE)
alembic downgrade base
alembic upgrade head
```

### Code Quality
```bash
# Format code
black src tests

# Check formatting without changes
black --check src tests

# Lint with ruff
ruff check src tests

# Auto-fix linting issues
ruff check --fix src tests

# Type checking
mypy src

# Run all quality checks
black src tests && ruff check src tests && mypy src
```

### Docker
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after code changes
docker-compose up -d --build

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## Architecture Overview

### Workflow Structure
```
Chainlit UI → LangGraph State Machine → LLM (Claude/GPT-4) → PostgreSQL
                      ↓
         [Consent → Red Flag Check → Chief Complaint →
          Systematic Questions → Risk Stratification →
          Recommendation → Appointment Booking → Completed]
```

### LangGraph State Machine
The triage workflow is implemented as a LangGraph `StateGraph` with 7 phases:

1. **Consent Phase** (`src/agents/nodes.py:consent_node`)
   - Displays medical disclaimer
   - Obtains user consent
   - HIPAA/GDPR compliance notice

2. **Red Flag Check** (`src/agents/nodes.py:red_flag_check_node`)
   - Immediate keyword-based detection of emergencies
   - **TODO**: Replace with LLM semantic analysis + GraphRAG
   - If detected: bypass all other phases, direct to ER

3. **Chief Complaint** (`src/agents/nodes.py:chief_complaint_node`)
   - Captures patient's description
   - **TODO**: Standardize with LLM + query GraphRAG for differential diagnoses

4. **Systematic Questions** (`src/agents/nodes.py:systematic_questions_node`)
   - Asks targeted questions based on symptoms
   - **TODO**: Dynamic questioning from GraphRAG DDx

5. **Risk Stratification** (`src/agents/nodes.py:risk_stratification_node`)
   - Determines urgency level (emergent/urgent/non-urgent)
   - **TODO**: Use GraphRAG + LLM for analysis

6. **Recommendation** (`src/agents/nodes.py:recommendation_node`)
   - Provides triage assessment
   - Educational content
   - Offers appointment booking

7. **Appointment Booking** (`src/agents/nodes.py:appointment_booking_node`)
   - **TODO**: Integrate with internal appointment system

### State Management
- State defined in `src/agents/state.py:TriageState`
- Extends LangGraph's `MessagesState` for message history
- Persisted using `MemorySaver` checkpointer (in-memory)
- **TODO**: Replace with PostgresCheckpointer for production persistence

### Key Files

**Application Entry Point:**
- `src/app.py` - Main Chainlit application with auth callback and message handlers

**LangGraph Workflow:**
- `src/agents/workflow.py` - StateGraph definition and compilation
- `src/agents/state.py` - TriageState TypedDict definition
- `src/agents/nodes.py` - All phase node implementations and routing logic

**Database Models:**
- `src/models/user.py` - User authentication (email, username, hashed password, role)
- `src/models/conversation.py` - Chat conversation persistence
- `src/models/appointment.py` - Internal appointment booking
- `src/models/base.py` - SQLAlchemy declarative base

**Services:**
- `src/services/auth.py` - User authentication and password verification
- `src/services/database.py` - Database connection and session management

**Configuration:**
- `src/config/settings.py` - Pydantic settings with environment variables
- `.env.example` - Template for environment variables
- `.chainlit/config.toml` - Chainlit UI configuration

**Database Migrations:**
- `alembic/` - Alembic migration scripts
- `alembic.ini` - Alembic configuration

## Medical Domain Rules

### Urgency Classification
**Currently using placeholder logic - MUST be replaced with GraphRAG-extracted urgency levels.**

- **Emergent**: ER immediately (e.g., sudden vision loss, chemical burn, penetrating trauma)
- **Urgent**: Doctor within 24-48 hours (e.g., keratitis, acute glaucoma, severe pain)
- **Non-Urgent**: Schedule appointment 1-2 weeks (e.g., mild allergic conjunctivitis)

**Source (when integrated)**: `../indexing/output/phase4/urgency_classification_criteria.json`

### Red Flags
**Currently using hardcoded keywords in `nodes.py` - MUST be replaced with GraphRAG-extracted red flags.**

Current keyword-based detection (TEMPORARY):
- Sudden vision loss: "sudden", "lost vision", "can't see", "went blind"
- Chemical burn: "chemical", "splash", "burned", "acid", "alkali"
- Penetrating trauma: "penetrat", "stab", "puncture", "sharp object"
- Severe pain with nausea: "severe pain", "nausea", "vomit"
- New floaters with flashes: "floater", "flashes", "flash", "curtain"

**Source (when integrated)**: `../indexing/output/phase5/red_flags.json`

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
async def consent_node(state: TriageState) -> dict[str, Any]:
    """Phase 1: Obtain user consent for triage.

    Args:
        state: Current workflow state

    Returns:
        Updated state dict
    """
```

**Async/Await:**
- All LangGraph nodes must be async functions
- Use `await` for LLM calls and database operations
- Chainlit handlers are async by default

**Imports:**
- Use absolute imports: `from agents.state import TriageState`
- Group imports: stdlib → third-party → local
- Use ruff to auto-organize imports

**Commits:**
- Conventional Commits format
- Examples:
  - `feat(triage): add LLM-based red flag detection`
  - `fix(auth): handle account lockout correctly`
  - `docs(readme): update setup instructions`

## Testing Requirements

**For Medical Logic Changes:**
1. Unit tests with 80%+ coverage
2. Integration tests for complete triage flow
3. Mock LLM calls to avoid API costs during testing
4. Test all edge cases in `tests/test_triage_agent.py`

**Red Flag Tests:**
- Must test all red flag keywords
- Must test edge cases (e.g., "sudden" vs "suddenly", "lost vision" vs "blurry vision")
- Must validate no false negatives (100% detection for emergencies)
- Located in `tests/test_red_flags.py`

**Database Tests:**
- Test all CRUD operations for User, Conversation, Appointment models
- Test authentication flow (login, failed attempts, account lockout)
- Use pytest fixtures for database setup/teardown

## Authentication & User Management

### Creating Users
```bash
# Interactive script
python scripts/create_user.py

# Follow prompts for:
# - Email address
# - Username
# - Password (hashed with bcrypt)
# - Full name (optional)
# - Role (admin, doctor, nurse, patient, guest)
# - Preferred language (en, fa)
```

### User Roles
- **admin**: Full system access, can view all sessions
- **doctor**: Can view all triage sessions and appointments
- **nurse**: Can assist with triage
- **patient**: Standard user, can only view own sessions
- **guest**: Limited access (read-only)

### Security Features
- Passwords hashed with bcrypt (12 rounds)
- Account lockout after 5 failed login attempts (30 min timeout)
- Session timeout after 30 minutes of inactivity
- All timestamps are timezone-aware (UTC)

## Internationalization (i18n)

### Supported Languages
- 🇺🇸 **English** (`en-US`) - Default
- 🇮🇷 **فارسی / Persian** (`fa-IR`) - Full RTL support

### Translation Files
- UI translations: `.chainlit/translations/en-US.json`, `.chainlit/translations/fa-IR.json`
- Markdown content: `chainlit.md` (English), `chainlit_fa-IR.md` (Persian)

### How Language Detection Works
1. Checks user profile's `preferred_language` field
2. Falls back to browser `Accept-Language` header
3. Defaults to English if no match found

### Adding New Languages
1. Copy `.chainlit/translations/en-US.json` to `.chainlit/translations/{lang}.json`
2. Translate all values
3. Create `chainlit_{lang}.md` with translated disclaimer
4. Update User model to include new language in preferred_language field
5. Run `chainlit lint-translations` to validate

## Key Documentation

Always check these before making changes:
- **GraphRAG Architecture**: `../docs/GRAPHRAG_ARCHITECTURE.md` (knowledge graph design)
- **GraphRAG Quick Start**: `../indexing/QUICKSTART_GRAPHRAG.md` (implementation guide)
- **Medical Framework**: `../docs/medical/framework.md` (authoritative triage logic)
- **Red Flags**: `../indexing/output/phase5/red_flags.json` (when ready)
- **Urgency Levels**: `../indexing/output/phase4/urgency_classification_criteria.json` (when ready)

## When Making Changes

1. **Check docs first**: Read relevant `../docs/medical/` and `../docs/technical/` files
2. **Update tests**: Medical logic changes require test updates
3. **Run tests**: `pytest -v` must pass before committing
4. **Add type hints**: All new functions need proper typing
5. **Format code**: Run `black src tests` before committing
6. **Update migrations**: Database model changes need Alembic migrations
7. **Validate against Wills Eye**: Medical content must match source (when GraphRAG integrated)

## Environment Variables

Key variables in `.env` (see `.env.example` for full list):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ocular_triage

# LLM APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # Optional fallback

# Neo4j (when integrated)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Langfuse (optional monitoring)
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Chainlit
CHAINLIT_AUTH_SECRET=your-secret-key-here
```

## Current Development Status

**Implemented:**
- ✅ Chainlit chat interface with authentication
- ✅ LangGraph state machine (7 phases)
- ✅ Basic keyword-based red flag detection
- ✅ PostgreSQL database with SQLAlchemy
- ✅ User authentication with bcrypt
- ✅ Multi-language support (English, Persian)
- ✅ Docker deployment configuration
- ✅ Database migrations with Alembic

**In Progress / TODO:**
- 🚧 LLM-based semantic red flag detection
- 🚧 GraphRAG integration for differential diagnoses
- 🚧 Dynamic questioning based on DDx from knowledge graph
- 🚧 LLM-powered risk stratification
- 🚧 Internal appointment booking system
- 🚧 PostgresCheckpointer for conversation persistence
- 🚧 Langfuse tracing integration
- 🚧 Neo4j knowledge graph queries
- 🚧 Educational content from Wills Eye Manual

## Common Development Tasks

### Adding a New Phase to Workflow
1. Define phase in `src/agents/state.py:TriageState` Literal type
2. Create node function in `src/agents/nodes.py`
3. Add node to workflow in `src/agents/workflow.py:create_triage_workflow`
4. Add conditional edges for routing
5. Update `should_continue` function
6. Write tests in `tests/`

### Adding a New Database Model
1. Create model in `src/models/your_model.py`
2. Import in `src/models/__init__.py`
3. Generate migration: `alembic revision --autogenerate -m "add your_model"`
4. Review generated migration in `alembic/versions/`
5. Apply migration: `alembic upgrade head`
6. Write tests for model CRUD operations

### Integrating an LLM Call
1. Import from langchain: `from langchain_anthropic import ChatAnthropic`
2. Initialize model: `model = ChatAnthropic(model="claude-3-5-sonnet-20241022")`
3. Use in node function: `response = await model.ainvoke(messages)`
4. Add Langfuse tracing (when integrated)
5. Track token usage in state: `state["total_tokens"] += response.usage_metadata.total_tokens`
6. Mock in tests to avoid API costs

### Modifying Red Flag Detection
1. Update keywords/logic in `src/agents/nodes.py:red_flag_check_node`
2. Add test cases in `tests/test_red_flags.py`
3. Ensure 100% detection rate (no false negatives)
4. Test edge cases and variations
5. Document changes in commit message with medical justification

## Debugging Tips

### Chainlit Debugging
- Use `print()` statements (appears in terminal)
- Check Chainlit logs in `.chainlit/` directory
- Use `cl.Message(..., author="System").send()` for debug messages visible to user

### LangGraph Debugging
- Print state between nodes: `print(f"Current state: {state}")`
- Use LangGraph's built-in debugging: `workflow.get_graph().print_ascii()`
- Check state transitions with: `print(f"Phase: {state['phase']}")`

### Database Debugging
- Enable SQLAlchemy echo: `engine = create_engine(..., echo=True)`
- Check current migration: `alembic current`
- View raw SQL: Use PostgreSQL logs or pgAdmin

### Docker Debugging
- View container logs: `docker-compose logs -f app`
- Access container shell: `docker-compose exec app bash`
- Check database connection: `docker-compose exec db psql -U postgres`

## Performance Considerations

- Each triage session target: <$0.10 in LLM costs
- Session duration target: <5 minutes
- Red flag detection latency: <0.5 seconds
- Use Claude Haiku for non-critical classification tasks
- Use Claude Sonnet for medical reasoning and risk stratification
- Cache GraphRAG results when possible

## License

Proprietary - All Rights Reserved
