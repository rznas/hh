# Documentation Index

Start here for all project documentation.

## 🚀 Quick Start
1. Read [GRAPHRAG_ARCHITECTURE.md](./GRAPHRAG_ARCHITECTURE.md) for Microsoft GraphRAG implementation
2. Follow [../indexing/QUICKSTART_GRAPHRAG.md](../indexing/QUICKSTART_GRAPHRAG.md) for GraphRAG setup
3. Review [medical/framework.md](./medical/framework.md) for triage logic
4. Check [ARCHITECTURE.md](./ARCHITECTURE.md) for complete system overview
5. See [../GRAPHRAG_IMPLEMENTATION_STATUS.md](../GRAPHRAG_IMPLEMENTATION_STATUS.md) for current progress

## 📋 Documentation by Role

### For New Developers
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [SETUP.md](./SETUP.md) - Development setup
- [technical/api-specifications.md](./technical/api-specifications.md) - API contracts
- [../backend/README.md](../backend/README.md) - Backend structure
- [../frontend/README.md](../frontend/README.md) - Frontend structure

### For Medical Domain Experts
- [medical/framework.md](./medical/framework.md) - Triage framework
- [medical/urgency-levels.md](./medical/urgency-levels.md) - Classification system
- [medical/safety-protocols.md](./medical/safety-protocols.md) - Safety requirements
- **Red Flags**: Extracted from Wills Eye Manual via `indexing/output/phase5/red_flags.json` (see [GRAPHRAG_PREPARATION_TODO.md](./GRAPHRAG_PREPARATION_TODO.md) Phase 5.1)

### For AI/ML Engineers
- [GRAPHRAG_ARCHITECTURE.md](./GRAPHRAG_ARCHITECTURE.md) - Microsoft GraphRAG architecture
- [../indexing/QUICKSTART_GRAPHRAG.md](../indexing/QUICKSTART_GRAPHRAG.md) - GraphRAG implementation guide
- [../GRAPHRAG_IMPLEMENTATION_STATUS.md](../GRAPHRAG_IMPLEMENTATION_STATUS.md) - Current development status
- [technical/llm-integration.md](./technical/llm-integration.md) - LLM setup
- [technical/triage-algorithm.md](./technical/triage-algorithm.md) - Core algorithm
- [integrations/langfuse.md](./integrations/langfuse.md) - Monitoring

### For DevOps
- [deployment/docker-compose.md](./deployment/docker-compose.md) - Local setup
- [deployment/kubernetes.md](./deployment/kubernetes.md) - Production
- [deployment/monitoring.md](./deployment/monitoring.md) - Observability

## 📚 Core Documentation

### Medical Domain
- [framework.md](./medical/framework.md) - Complete triage framework
- [urgency-levels.md](./medical/urgency-levels.md) - Emergent/Urgent/Non-urgent
- [safety-protocols.md](./medical/safety-protocols.md) - Safety requirements
- **Red Flags**: Extracted via GraphRAG pipeline (see [GRAPHRAG_PREPARATION_TODO.md](./GRAPHRAG_PREPARATION_TODO.md) Phase 5.1)

### Technical Implementation
- [GRAPHRAG_ARCHITECTURE.md](./GRAPHRAG_ARCHITECTURE.md) - Microsoft GraphRAG architecture
- [data-pipeline.md](./technical/data-pipeline.md) - EPUB → JSON → GraphRAG
- [llm-integration.md](./technical/llm-integration.md) - LLM usage
- [knowledge-graph.md](./technical/knowledge-graph.md) - Graph schema (legacy)
- [triage-algorithm.md](./technical/triage-algorithm.md) - Core logic
- [api-specifications.md](./technical/api-specifications.md) - API docs

### Microsoft GraphRAG Implementation
- [../indexing/QUICKSTART_GRAPHRAG.md](../indexing/QUICKSTART_GRAPHRAG.md) - Step-by-step implementation guide
- [../GRAPHRAG_IMPLEMENTATION_STATUS.md](../GRAPHRAG_IMPLEMENTATION_STATUS.md) - Development progress tracker
- [../indexing/](../indexing/) - GraphRAG implementation code
  - Entity extraction: `entity_extractor.py`
  - Relationship extraction: `relationship_extractor.py`
  - Community detection: `community_detector.py`
  - Embedding service: `embedding_service.py`
  - Neo4j storage: `neo4j_storage.py`
  - Search interfaces: `local_search.py`, `global_search.py`

### Integrations
- [paziresh24.md](./integrations/paziresh24.md) - Appointment booking (Iran)
- [nobat.md](./integrations/nobat.md) - Alternative booking
- [langfuse.md](./integrations/langfuse.md) - LLM monitoring

## 🔍 Quick Reference

### Triage Flow
```
Patient Input → Red Flag Check → Systematic Questions → Risk Stratification → Recommendation
```

### Urgency Levels
- **Emergent**: ER immediately (e.g., sudden vision loss)
- **Urgent**: Doctor within 24-48 hours (e.g., keratitis)
- **Non-Urgent**: Schedule appointment (e.g., mild allergic conjunctivitis)

### Key Files in Codebase
- Triage Agent: `backend/apps/triage/services/triage_agent.py`
- Red Flag Detector: `backend/apps/triage/services/red_flag_detector.py`
- Microsoft GraphRAG Implementation: `indexing/`
  - Main indexer: `indexing/graphrag_indexer.py`
  - Entity extraction: `indexing/entity_extractor.py`
  - Relationship extraction: `indexing/relationship_extractor.py`
  - Community detection: `indexing/community_detector.py`
  - Embedding service: `indexing/embedding_service.py`
  - Neo4j storage: `indexing/neo4j_storage.py`
  - Search interfaces: `indexing/local_search.py`, `indexing/global_search.py`
- LLM Prompts: `backend/prompts/`
- Wills Eye Data: `data/wills_eye_structured.json`

### Environment Variables
See `.env.example` in project root.

## 🧪 Testing Documentation
- Unit Testing: [../tests/README.md](../tests/README.md)
- Integration Testing: [../tests/integration/README.md](../tests/integration/README.md)
- Medical Validation: [medical/testing-protocol.md](./medical/testing-protocol.md)

## 📊 Data Documentation
- Wills Eye Manual: `data/wills_eye_structured.json` (parsed from EPUB)
- EPUB Parser: `scripts/parse_wills_eye.py`
- GraphRAG Indexing Pipeline: [../indexing/QUICKSTART_GRAPHRAG.md](../indexing/QUICKSTART_GRAPHRAG.md)
- Data Pipeline Overview: [technical/data-pipeline.md](./technical/data-pipeline.md)

## 🔄 Current Development Status

**MVP Development Phase** - Focus Areas:
- ✅ Entity extraction implementation
- ✅ Relationship extraction implementation
- 🚧 Embedding service
- 🚧 Community detection (hierarchical clustering)
- 🚧 Neo4j storage layer
- 🚧 Local search (entity-specific queries)
- 🚧 Global search (community-based reasoning)
- 🚧 Main indexing pipeline integration

See [../GRAPHRAG_IMPLEMENTATION_STATUS.md](../GRAPHRAG_IMPLEMENTATION_STATUS.md) for detailed progress.

## 🛠️ Development Commands

### GraphRAG Indexing
```bash
# Parse Wills Eye Manual EPUB to JSON (if needed)
python scripts/parse_wills_eye.py data/wills_eye_manual.epub

# Populate knowledge graph (Microsoft GraphRAG)
python indexing/graphrag_indexer.py --data data/wills_eye_structured.json --dry-run
python indexing/graphrag_indexer.py --data data/wills_eye_structured.json

# Index specific chapter
python indexing/graphrag_indexer.py --data data/wills_eye_structured.json --chapter "Cornea and External Disease"
```

### Testing
```bash
# All tests
pytest

# Medical logic tests (REQUIRED for any triage changes)
pytest backend/apps/triage/tests/test_triage_agent.py -v

# Red flag detection tests (CRITICAL - must pass)
pytest backend/apps/triage/tests/test_red_flags.py -v

# GraphRAG tests
pytest indexing/tests/ -v

# With coverage (minimum 80% for medical code)
pytest --cov=apps --cov-report=html
```