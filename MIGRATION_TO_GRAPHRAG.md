# Migration from Zep Graphiti to Microsoft GraphRAG

## Executive Summary

We are migrating from **Zep Graphiti** to **Microsoft GraphRAG** for our medical triage knowledge graph. This decision is based on better alignment with structured medical knowledge, hierarchical search capabilities, and improved domain optimization.

**Migration Status**: 🟡 In Progress (40% complete)

## Why Migrate?

### Limitations of Zep Graphiti
- **Episode-based model**: Designed for narrative/temporal data, not structured medical knowledge
- **Flat structure**: No hierarchical organization of medical conditions
- **Single search mode**: Only semantic search, no community-based queries
- **Limited explainability**: Difficult to trace reasoning through relationships

### Advantages of Microsoft GraphRAG
- ✅ **Hierarchical communities**: Natural grouping of related conditions (trauma, infections, glaucoma, etc.)
- ✅ **Dual search modes**: Local (entity-specific) + Global (broad thematic queries)
- ✅ **Better medical fit**: Entity-relationship model aligns with medical knowledge
- ✅ **Cost efficiency**: Pre-computed community summaries reduce LLM calls
- ✅ **Enhanced explainability**: Can trace reasoning through graph structure
- ✅ **Domain optimization**: Support for medical-specific embeddings (BioBERT)

## Architecture Comparison

### Zep Graphiti (Old)
```
User Query
    ↓
Episode-based semantic search
    ↓
LLM summarization
    ↓
Response
```

### Microsoft GraphRAG (New)
```
User Query
    ↓
Query Classification (Local vs Global)
    ↓
├─ Local Search (Entity-specific)
│  ├─ Vector similarity
│  ├─ Entity retrieval
│  ├─ Neighbor expansion
│  └─ Context assembly
│
└─ Global Search (Broad themes)
   ├─ Community retrieval
   ├─ Hierarchical summaries
   └─ Map-reduce aggregation
    ↓
LLM Response Generation
```

## Implementation Progress

### ✅ Completed (40%)
1. **Architecture Design** - Complete GraphRAG architecture document
2. **Configuration System** - Multi-provider LLM and embedding support
3. **Entity Extraction** - LLM-based medical entity extraction
4. **Relationship Extraction** - Medical relationship detection with weighting
5. **Documentation** - Comprehensive guides and implementation plans
6. **Dependencies Updated** - All required packages specified

### 🚧 In Progress (60% remaining)
1. **Embedding Service** - Text-to-vector conversion (OpenAI + BioBERT)
2. **Community Detection** - Leiden algorithm for hierarchical clustering
3. **Community Summarization** - LLM-generated summaries at multiple levels
4. **Neo4j Storage Layer** - Graph persistence with vector indexes
5. **Local Search** - Entity-based retrieval system
6. **Global Search** - Community-based retrieval system
7. **Main Indexing Pipeline** - Orchestration of full workflow
8. **GraphRAG Client** - Unified query interface (backward compatible)
9. **Testing Suite** - Comprehensive tests for all components
10. **Migration Script** - Safe migration from Graphiti data

## File Changes

### New Files Created
- `docs/GRAPHRAG_ARCHITECTURE.md` - Complete architecture design
- `GRAPHRAG_IMPLEMENTATION_STATUS.md` - Detailed progress tracker
- `indexing/QUICKSTART_GRAPHRAG.md` - Developer quick start guide
- `indexing/graphrag_config.py` - Configuration system
- `indexing/entity_extractor.py` - Entity extraction implementation
- `indexing/relationship_extractor.py` - Relationship extraction

### Files to Create (Implementation Guides Provided)
- `indexing/graphrag_embeddings.py` - Embedding service
- `indexing/community_detector.py` - Community detection
- `indexing/community_summarizer.py` - Community summaries
- `indexing/graphrag_storage.py` - Neo4j storage layer
- `indexing/local_search.py` - Local search implementation
- `indexing/global_search.py` - Global search implementation
- `indexing/graphrag_indexer.py` - Main pipeline orchestrator
- `indexing/graphrag_client.py` - Client interface

### Updated Files
- `CLAUDE.md` - Updated with GraphRAG references
- `INTEGRATION_COMPLETE.md` - Reflects migration status
- `indexing/requirements.txt` - New dependencies

### Deprecated Files (Keep for Reference)
- `indexing/graphiti_client.py` - Old Graphiti wrapper
- `indexing/graph_builder.py` - Old graph builder
- `indexing/index_knowledge_graph.py` - Old indexing script
- `indexing/embedding_service.py` - Old embedding service

## Key Differences

| Aspect | Zep Graphiti | Microsoft GraphRAG |
|--------|--------------|-------------------|
| **Data Model** | Episodes (narrative) | Entities + Relationships |
| **Knowledge Addition** | Episode-based | Entity extraction |
| **Graph Structure** | Flat, temporal | Hierarchical communities |
| **Search Modes** | Semantic only | Local + Global |
| **Summarization** | None | Multi-level community summaries |
| **Best For** | Narrative/temporal data | Structured knowledge domains |
| **Medical Fit** | Poor | Excellent |
| **Cost per Query** | Higher (more LLM calls) | Lower (cached summaries) |
| **Explainability** | Limited | High (graph traversal) |

## Migration Steps

### Phase 1: Foundation (Complete) ✅
- [x] Architecture design
- [x] Configuration system
- [x] Entity extraction
- [x] Relationship extraction
- [x] Documentation

### Phase 2: Core Components (In Progress) 🚧
- [ ] Embedding service
- [ ] Community detection
- [ ] Neo4j storage
- [ ] Community summarization

### Phase 3: Search Interfaces (Pending)
- [ ] Local search
- [ ] Global search
- [ ] Client interface

### Phase 4: Integration (Pending)
- [ ] Main indexing pipeline
- [ ] Integrate with triage agent
- [ ] Testing suite

### Phase 5: Deployment (Pending)
- [ ] Migration script
- [ ] A/B testing
- [ ] Performance monitoring
- [ ] Production rollout

## Timeline

- **Week 1-2**: Complete core components (embedding, communities, storage)
- **Week 3-4**: Implement search interfaces and pipeline
- **Week 5-6**: Testing and integration with triage system
- **Week 7-8**: Migration and A/B testing
- **Week 9-10**: Production deployment

## Backward Compatibility

### API Compatibility
The new `GraphRAGClient` will maintain the same interface as `GraphitiClient`:
```python
# Old (Graphiti)
from graphiti_client import GraphitiClient
client = GraphitiClient()
results = await client.search("sudden vision loss")

# New (GraphRAG) - Same interface!
from graphrag_client import GraphRAGClient
client = GraphRAGClient()
results = await client.search("sudden vision loss")
```

### Data Migration
- Existing Graphiti data can be exported
- New GraphRAG indexing will process Wills Eye Manual from source
- No data loss - both systems can coexist during transition

## Testing Strategy

### Component Testing
- Unit tests for each new component
- Integration tests for full pipeline
- Performance benchmarks

### Medical Validation
- Red flag detection (100% accuracy required)
- Urgency classification accuracy
- Differential diagnosis quality
- Source attribution correctness

### A/B Testing
- Run both systems in parallel
- Compare query results
- Measure performance and cost
- Gradual rollout based on metrics

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Implementation delays | Medium | Detailed implementation guides provided |
| Integration issues | Medium | Maintain backward-compatible API |
| Data quality | High | Comprehensive validation suite |
| Performance degradation | Medium | Benchmark against old system |
| Cost overruns | Low | Pre-computed summaries reduce LLM calls |

## Documentation

### For Developers
- **Architecture**: `docs/GRAPHRAG_ARCHITECTURE.md`
- **Implementation Status**: `GRAPHRAG_IMPLEMENTATION_STATUS.md`
- **Quick Start**: `indexing/QUICKSTART_GRAPHRAG.md`
- **Project Instructions**: `CLAUDE.md`

### For Stakeholders
- **This Document**: Migration overview and status
- **Architecture**: High-level design decisions
- **Timeline**: Expected completion dates

## Success Criteria

### Technical
- [ ] All components implemented and tested
- [ ] 100% red flag detection accuracy
- [ ] <2s local search latency
- [ ] <5s global search latency
- [ ] <$0.05 per triage session cost

### Medical
- [ ] Urgency classification >90% accuracy
- [ ] Source attribution for all recommendations
- [ ] Zero false negatives on emergent conditions
- [ ] Explainable reasoning paths

### Operational
- [ ] Backward-compatible API
- [ ] Smooth migration process
- [ ] Performance meets or exceeds old system
- [ ] Cost reduction vs Graphiti

## Next Actions

### Immediate (This Week)
1. Implement embedding service (`indexing/graphrag_embeddings.py`)
2. Implement Neo4j storage layer (`indexing/graphrag_storage.py`)
3. Implement community detection (`indexing/community_detector.py`)

### Short-term (Next 2 Weeks)
4. Implement community summarization
5. Implement local and global search
6. Complete main indexing pipeline
7. Test with Trauma chapter

### Medium-term (Next Month)
8. Complete testing suite
9. Integrate with triage agent
10. Migration script and A/B testing
11. Production deployment

## Support

For implementation assistance:
- Review `GRAPHRAG_IMPLEMENTATION_STATUS.md` for detailed component guides
- Check `indexing/QUICKSTART_GRAPHRAG.md` for developer instructions
- Consult `docs/GRAPHRAG_ARCHITECTURE.md` for design decisions

## Conclusion

The migration to Microsoft GraphRAG represents a significant architectural improvement for our medical triage system. The entity-relationship model with hierarchical communities is a better fit for structured medical knowledge than Graphiti's episode-based approach.

**Key Benefits:**
- Better medical knowledge organization
- Dual search modes (local + global)
- Cost efficiency through pre-computed summaries
- Enhanced explainability
- Domain-specific optimization potential

**Status:** Core foundation complete (40%), remaining components have detailed implementation guides.

**Timeline:** 8-10 weeks to full production deployment.

---

**Last Updated**: 2025-10-15
**Status**: 🟡 In Progress
**Contact**: See implementation status document for component details
