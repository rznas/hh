# Microsoft GraphRAG Architecture for Medical Triage

## Overview

This document describes the implementation of Microsoft GraphRAG approach for the medical triage knowledge graph, replacing the previous Zep Graphiti implementation.

## Architecture Components

### 1. Data Indexing Pipeline

```
Wills Eye Manual JSON
    ↓
Entity Extraction (LLM)
    ↓
Relationship Extraction (LLM)
    ↓
Community Detection (Leiden algorithm)
    ↓
Hierarchical Clustering
    ↓
Community Summarization (LLM)
    ↓
Neo4j Storage
```

### 2. Query Pipeline

#### Local Search (Entity-Based)
Used for specific medical queries about particular conditions, symptoms, or treatments.

```
User Query
    ↓
Query Embedding
    ↓
Entity Retrieval (semantic similarity)
    ↓
Expand to Neighbors (relationships)
    ↓
Context Assembly
    ↓
LLM Response Generation
```

#### Global Search (Community-Based)
Used for broad questions requiring understanding of multiple conditions or overarching themes.

```
User Query
    ↓
Community Summary Retrieval
    ↓
Hierarchical Context Assembly
    ↓
Map-Reduce LLM Summarization
    ↓
Final Response
```

## Key Differences from Zep Graphiti

| Aspect | Zep Graphiti | Microsoft GraphRAG |
|--------|--------------|-------------------|
| **Knowledge Addition** | Episode-based | Entity + Relationship extraction |
| **Graph Structure** | Dynamic episodes | Static entities with communities |
| **Retrieval** | Semantic search | Local (entity) + Global (community) |
| **Summarization** | None | Hierarchical community summaries |
| **Best For** | Temporal/narrative data | Structured knowledge domains |

## Implementation Phases

### Phase 1: Entity Extraction
- Extract medical entities (conditions, symptoms, signs, treatments)
- Use Claude/GPT-4 with medical prompts
- Store entities with embeddings in Neo4j

### Phase 2: Relationship Extraction
- Extract relationships between entities
- Classify relationships (presents_with, treated_with, etc.)
- Build knowledge graph structure

### Phase 3: Community Detection
- Use Leiden algorithm for community detection
- Create hierarchical levels (L0, L1, L2...)
- L0 = individual entities, higher levels = communities of communities

### Phase 4: Community Summarization
- LLM generates summaries for each community
- Summaries describe:
  - Common themes
  - Key entities
  - Medical relationships
  - Urgency patterns

### Phase 5: Query Interface
- Local search for specific entity queries
- Global search for broad questions
- Hybrid search combining both approaches

## Medical Domain Considerations

### Entity Types
- **DISEASE**: Ocular conditions (e.g., "Acute Angle-Closure Glaucoma")
- **SYMPTOM**: Patient-reported (e.g., "sudden vision loss")
- **SIGN**: Clinical findings (e.g., "corneal edema")
- **TREATMENT**: Interventions (e.g., "topical antibiotics")
- **ANATOMY**: Eye structures (e.g., "cornea", "retina")
- **URGENCY**: Classification (EMERGENT, URGENT, NON_URGENT)

### Relationship Types
- PRESENTS_WITH: Disease → Symptom
- SHOWS_SIGN: Disease → Sign
- TREATED_WITH: Disease → Treatment
- AFFECTS: Disease → Anatomy
- DIFFERENTIATES: Disease → Disease (differential diagnosis)
- HAS_URGENCY: Disease → Urgency Level

### Community Structure
Communities will naturally group:
- **Trauma conditions** (chemical burns, foreign bodies, etc.)
- **Infectious conditions** (conjunctivitis, keratitis, etc.)
- **Glaucoma-related conditions**
- **Retinal conditions**
- **Anterior segment vs posterior segment**

### Safety Considerations
- Red flags must be accessible via both local and global search
- Emergent conditions must be in high-visibility communities
- All medical recommendations must cite source (Wills Eye section)
- Maintain audit trail for medical decision points

## Performance Targets

- **Indexing**: Process full Wills Eye Manual in <30 minutes
- **Local Search**: <2 seconds per query
- **Global Search**: <5 seconds per query
- **Cost**: <$0.05 per triage session (LLM calls)
- **Accuracy**: 100% red flag detection, >90% correct urgency classification

## Storage Schema

### Neo4j Node Labels
- Entity (with type property)
- Community (with level property)
- Document (source reference)

### Neo4j Relationships
- HAS_RELATIONSHIP (between entities)
- BELONGS_TO_COMMUNITY (entity → community)
- PART_OF (community → parent community)
- SOURCED_FROM (entity → document)

### Node Properties
- `id`: Unique identifier
- `name`: Entity/community name
- `type`: Entity type or community level
- `embedding`: Vector embedding (for search)
- `summary`: Community summary (for communities)
- `urgency_level`: For disease entities
- `red_flag_keywords`: For emergent conditions
- `source_section`: Wills Eye Manual reference

## Configuration

### LLM Settings
- **Entity Extraction**: Claude 3.5 Sonnet (best for medical text)
- **Relationship Extraction**: Claude 3.5 Sonnet
- **Community Summarization**: Claude 3.5 Sonnet
- **Query Processing**: Claude 3.5 Sonnet (primary), GPT-4o (fallback)

### Embedding Settings
- **Model**: text-embedding-3-large (OpenAI)
- **Dimensions**: 1536
- **Alternative**: BioBERT for domain-specific embeddings

### Community Detection
- **Algorithm**: Leiden (better than Louvain for hierarchical)
- **Resolution**: 1.0 (default)
- **Levels**: 3-4 levels of hierarchy

## Migration from Zep Graphiti

### Backward Compatibility
- Keep existing triage API interface unchanged
- Replace GraphitiClient with GraphRAGClient internally
- Maintain same query methods (search_conditions_by_symptom, etc.)

### Migration Steps
1. Export existing Graphiti data (if any)
2. Install Microsoft GraphRAG package
3. Run new indexing pipeline on Wills Eye JSON
4. Update client code to use GraphRAG API
5. Test against validation scenarios
6. Deploy new version

### Rollback Plan
- Keep Graphiti code in separate branch
- Feature flag to switch between implementations
- Maintain same Neo4j instance (different node labels)

## Testing Strategy

### Unit Tests
- Entity extraction accuracy
- Relationship classification
- Community detection correctness
- Search relevance scoring

### Integration Tests
- Full indexing pipeline
- Local search accuracy
- Global search accuracy
- Red flag detection (100% required)

### Validation Scenarios
Test against known medical cases:
- Emergent: Chemical burn, sudden vision loss, penetrating trauma
- Urgent: Keratitis, acute glaucoma, corneal ulcer
- Non-Urgent: Mild conjunctivitis, chalazion

### Performance Tests
- Indexing throughput
- Query latency
- Concurrent query handling
- Memory usage during indexing

## Monitoring and Observability

### Metrics
- Entity extraction success rate
- Community count per level
- Search query latency (p50, p95, p99)
- LLM token usage per query
- Red flag detection rate

### Logging
- All entity extractions (for audit)
- All medical queries (HIPAA-compliant)
- All red flag detections
- LLM API errors and retries

### Langfuse Integration
- Trace entity extraction prompts
- Trace community summarization
- Trace search queries
- Track token usage and costs

## Future Enhancements

### Short Term (MVP)
- Basic local and global search
- Red flag detection via both methods
- Simple community structure (2-3 levels)

### Medium Term
- Hybrid search (combine local + global)
- Query classification (route to local vs global)
- Custom community algorithms for medical domain
- Multi-lingual support (Farsi for Iran market)

### Long Term
- Real-time knowledge graph updates
- Federated learning across hospitals
- Integration with EHR systems
- Clinical trial matching
