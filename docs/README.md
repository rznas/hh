# Documentation Index

Start here for all project documentation.

## 🚀 Quick Start
1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
2. Follow [SETUP.md](./SETUP.md) to set up development environment
3. Review [medical/framework.md](./medical/framework.md) for triage logic
4. Check [technical/data-pipeline.md](./technical/data-pipeline.md) for data flow

## 📋 Documentation by Role

### For New Developers
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [SETUP.md](./SETUP.md) - Development setup
- [technical/api-specifications.md](./technical/api-specifications.md) - API contracts
- [../backend/README.md](../backend/README.md) - Backend structure
- [../frontend/README.md](../frontend/README.md) - Frontend structure

### For Medical Domain Experts
- [medical/framework.md](./medical/framework.md) - Triage framework
- [medical/red-flags.md](./medical/red-flags.md) - Emergency conditions
- [medical/urgency-levels.md](./medical/urgency-levels.md) - Classification system
- [medical/safety-protocols.md](./medical/safety-protocols.md) - Safety requirements

### For AI/ML Engineers
- [technical/llm-integration.md](./technical/llm-integration.md) - LLM setup
- [technical/knowledge-graph.md](./technical/knowledge-graph.md) - Zep Graphiti
- [technical/triage-algorithm.md](./technical/triage-algorithm.md) - Core algorithm
- [integrations/langfuse.md](./integrations/langfuse.md) - Monitoring

### For DevOps
- [deployment/docker-compose.md](./deployment/docker-compose.md) - Local setup
- [deployment/kubernetes.md](./deployment/kubernetes.md) - Production
- [deployment/monitoring.md](./deployment/monitoring.md) - Observability

## 📚 Core Documentation

### Medical Domain
- [framework.md](./medical/framework.md) - Complete triage framework
- [red-flags.md](./medical/red-flags.md) - Emergency red flags
- [urgency-levels.md](./medical/urgency-levels.md) - Emergent/Urgent/Non-urgent
- [safety-protocols.md](./medical/safety-protocols.md) - Safety requirements

### Technical Implementation
- [data-pipeline.md](./technical/data-pipeline.md) - EPUB → JSON → Zep
- [llm-integration.md](./technical/llm-integration.md) - LLM usage
- [knowledge-graph.md](./technical/knowledge-graph.md) - Graph schema
- [triage-algorithm.md](./technical/triage-algorithm.md) - Core logic
- [api-specifications.md](./technical/api-specifications.md) - API docs

### Integrations
- [paziresh24.md](./integrations/paziresh24.md) - Appointment booking (Iran)
- [nobat.md](./integrations/nobat.md) - Alternative booking
- [langfuse.md](./integrations/langfuse.md) - LLM monitoring
- [zep-graphiti.md](./integrations/zep-graphiti.md) - Knowledge graph

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
- Knowledge Graph: `backend/knowledge_graph/`
- LLM Prompts: `backend/prompts/`

### Environment Variables
See `.env.example` in project root.

## 🧪 Testing Documentation
- Unit Testing: [../tests/README.md](../tests/README.md)
- Integration Testing: [../tests/integration/README.md](../tests/integration/README.md)
- Medical Validation: [medical/testing-protocol.md](./medical/testing-protocol.md)

## 📊 Data Documentation
- Wills Eye JSON Schema: [../data/schemas/wills_eye_schema.json](../data/schemas/wills_eye_schema.json)
- Sample Data: [../data/sample/](../data/sample/)
- Data Pipeline: [technical/data-pipeline.md](./technical/data-pipeline.md)