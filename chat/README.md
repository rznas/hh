# Ocular Triage Chat System

AI-powered medical triage chat interface for ocular emergencies using Chainlit and LangGraph.

## Features

- 🔐 **Authentication**: Secure password-based authentication with SQLAlchemy
- 🌍 **Internationalization**: Multi-language support (English, فارسی/Persian)
- 🤖 **Multi-phase triage workflow** with LangGraph state machine
- 💬 **Real-time chat interface** powered by Chainlit
- 🗄️ **PostgreSQL persistence** for conversations, appointments, and users
- 📅 **Internal appointment booking system**
- 🚨 **Red flag detection** for emergent conditions
- 🧠 **Neo4j knowledge graph** integration
- 📊 **LLM observability** with Langfuse

## Architecture

```
Chainlit UI → LangGraph State Machine → GraphRAG (Neo4j) → LLM (Claude/GPT-4)
                     ↓
              PostgreSQL (Conversations, Appointments, Triage Sessions)
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Neo4j (optional, for knowledge graph)
- uv (Python package manager)

### Installation

```bash
# Create virtual environment
uv venv

# Install dependencies
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Create an admin user
python scripts/create_user.py

# Run the application
chainlit run src/app.py
```

The application will be available at `http://localhost:8000`. You'll need to log in with the credentials you created.

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Project Structure

```
chat/
├── src/
│   ├── agents/           # LangGraph agents and nodes
│   ├── models/           # SQLAlchemy database models
│   ├── services/         # Business logic services
│   ├── utils/            # Utility functions
│   ├── config/           # Configuration and settings
│   └── app.py            # Main Chainlit application
├── tests/                # Test suite
├── alembic/              # Database migrations
├── docker/               # Docker configuration
├── .chainlit/            # Chainlit configuration
├── pyproject.toml        # Python dependencies
└── docker-compose.yml    # Docker Compose configuration
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_triage_agent.py -v
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: OpenAI API key (fallback)
- `NEO4J_URI`: Neo4j connection URI
- `LANGFUSE_PUBLIC_KEY`: Langfuse observability key

## Authentication

The system uses password-based authentication following Chainlit's authentication pattern:

### Creating Users

Use the provided script to create users:

```bash
python scripts/create_user.py
```

This will prompt you for:
- Email address
- Username
- Password (will be hashed with bcrypt)
- Full name (optional)
- Role (admin, doctor, nurse, patient, guest)
- Preferred language (en, fa)

### User Roles

- **Admin**: Full system access
- **Doctor**: Can view all triage sessions and appointments
- **Nurse**: Can assist with triage
- **Patient**: Standard user with access to their own sessions
- **Guest**: Limited access

### Security Features

- Passwords are hashed using bcrypt
- Account lockout after 5 failed login attempts (30 minutes)
- Session timeout after 30 minutes of inactivity
- Timezone-aware timestamps
- HIPAA/GDPR compliant data handling

## Internationalization (i18n)

The application supports multiple languages through Chainlit's translation system:

### Supported Languages

- 🇺🇸 **English** (`en-US`)
- 🇮🇷 **فارسی / Persian** (`fa-IR`)

### How It Works

- Language is automatically detected from the user's browser settings
- Falls back to English if the detected language is not supported
- Users can set their preferred language in their profile

### Translation Files

- UI translations: `.chainlit/translations/{lang}.json`
- Markdown content: `chainlit_{lang}.md`

### Adding New Languages

1. Copy `.chainlit/translations/en-US.json` to `.chainlit/translations/{lang}.json`
2. Translate all values in the JSON file
3. Create `chainlit_{lang}.md` with translated disclaimer content
4. Run `chainlit lint-translations` to validate

## Safety & Compliance

This is medical software where safety is paramount:

- Red flag detection for emergent conditions
- Audit trail for all medical decisions
- HIPAA/GDPR compliant data handling
- 100% detection rate for emergent conditions
- All recommendations include medical disclaimers

## License

Proprietary - All Rights Reserved
