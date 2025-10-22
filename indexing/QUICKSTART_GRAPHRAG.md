# Microsoft GraphRAG Quick Start Guide

## Overview

This guide will help you get started with the Microsoft GraphRAG implementation for the medical triage knowledge graph.

## What is GraphRAG?

GraphRAG (Graph-based Retrieval Augmented Generation) combines:
1. **Entity extraction** - Extract medical entities from text
2. **Knowledge graph** - Build relationships between entities
3. **Community detection** - Find clusters of related entities
4. **Hierarchical summaries** - Generate summaries at multiple levels
5. **Smart search** - Local (specific) and global (broad) queries

## Why GraphRAG for Medical Triage?

- **Better organization**: Medical conditions naturally cluster (trauma, infections, glaucoma, etc.)
- **Dual search modes**: Specific entity queries AND broad thematic questions
- **Explainability**: Can trace reasoning through graph relationships
- **Safety**: Red flags accessible via multiple paths
- **Performance**: Pre-computed summaries reduce LLM calls

## Current Implementation Status

### ✅ Completed
- Architecture design
- Configuration system
- Entity extraction (LLM-based)
- Relationship extraction (LLM-based)
- Dependencies updated

### 🚧 In Progress
- Embedding service
- Neo4j storage layer
- Community detection
- Community summarization
- Search interfaces (local & global)
- Main indexing pipeline

## Installation

### Prerequisites
- Python 3.10+
- Neo4j 5.14+ running locally or hosted
- Anthropic API key (Claude) OR OpenAI API key

### Install Dependencies
```bash
cd indexing
pip install -r requirements.txt
```

### Configure Environment
Create `.env` file in project root:
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# LLM (choose one or both)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Optional: Configuration
LLM_PROVIDER=anthropic  # or openai
EMBEDDING_PROVIDER=openai  # or sentence_transformers
```

## Components Overview

### 1. Entity Extractor (`entity_extractor.py`)

Extracts medical entities from text:
- Diseases, symptoms, signs, treatments
- Anatomical structures, etiologies
- Procedures, lab tests, imaging

**Example**:
```python
from entity_extractor import EntityExtractor
from graphrag_config import load_config

config = load_config()
extractor = EntityExtractor(config)

text = "Acute angle-closure glaucoma presents with severe eye pain..."
entities = await extractor.extract_entities(text)
```

### 2. Relationship Extractor (`relationship_extractor.py`)

Extracts relationships between entities:
- PRESENTS_WITH: Disease → Symptom
- TREATED_WITH: Disease → Treatment
- AFFECTS: Disease → Anatomy
- And more...

**Example**:
```python
from relationship_extractor import RelationshipExtractor

extractor = RelationshipExtractor(config)
relationships = await extractor.extract_relationships(entities, text)
```

### 3. Configuration (`graphrag_config.py`)

Centralized configuration management:
```python
from graphrag_config import load_config, validate_config

config = load_config()
validate_config(config)

# Access settings
print(config.llm_provider)
print(config.embedding_model)
print(config.community_resolution)
```

## Next Steps for Developers

### To Complete the Implementation

1. **Embedding Service** (`graphrag_embeddings.py`)
   - Implement text-to-vector conversion
   - Support OpenAI and BioBERT models
   - Batch processing for efficiency

2. **Neo4j Storage** (`graphrag_storage.py`)
   - Store entities with embeddings
   - Store relationships
   - Create vector indexes for similarity search

3. **Community Detection** (`community_detector.py`)
   - Implement Leiden algorithm
   - Generate hierarchical community structure
   - Store communities in Neo4j

4. **Community Summarization** (`community_summarizer.py`)
   - Generate LLM summaries for each community
   - Multi-level summarization
   - Store summaries for fast retrieval

5. **Search Interfaces** (`local_search.py`, `global_search.py`)
   - Local: Entity-based specific queries
   - Global: Community-based broad queries
   - Hybrid: Combine both approaches

6. **Main Pipeline** (`graphrag_indexer.py`)
   - Orchestrate full indexing process
   - Process Wills Eye Manual JSON
   - Generate complete knowledge graph

### Testing Strategy

Test each component independently:
```bash
# Test entity extraction
python entity_extractor.py

# Test relationship extraction
python relationship_extractor.py

# Test full pipeline (once complete)
python graphrag_indexer.py --dry-run
```

### Integration with Triage System

The GraphRAG client will replace the existing Graphiti client:

**Before (Graphiti)**:
```python
from graphiti_client import GraphitiClient

client = GraphitiClient()
results = await client.search("sudden vision loss")
```

**After (GraphRAG)**:
```python
from graphrag_client import GraphRAGClient  # Once implemented

client = GraphRAGClient()
results = await client.search("sudden vision loss")
# Same interface, better results!
```

## Key Differences from Zep Graphiti

| Aspect | Zep Graphiti | Microsoft GraphRAG |
|--------|--------------|-------------------|
| **Data Model** | Episodes (narrative) | Entities + Relationships |
| **Structure** | Flat temporal | Hierarchical communities |
| **Search** | Semantic only | Local + Global |
| **Summarization** | None | Multi-level |
| **Best For** | Narrative data | Structured knowledge |

## Medical Domain Specifics

### Entity Types for Ophthalmology
```python
from config import NodeType

# Primary types
NodeType.DISEASE      # e.g., "acute angle-closure glaucoma"
NodeType.SYMPTOM      # e.g., "eye pain", "blurred vision"
NodeType.SIGN         # e.g., "corneal edema", "fixed pupil"
NodeType.TREATMENT    # e.g., "topical beta-blocker"
NodeType.ANATOMY      # e.g., "cornea", "retina", "optic nerve"
```

### Relationship Types
```python
from config import EdgeType

# Common relationships
EdgeType.PRESENTS_WITH    # Glaucoma PRESENTS_WITH eye pain
EdgeType.SHOWS_SIGN       # Glaucoma SHOWS_SIGN corneal edema
EdgeType.TREATED_WITH     # Glaucoma TREATED_WITH beta-blocker
EdgeType.AFFECTS          # Glaucoma AFFECTS anterior chamber
```

### Red Flag Detection

Red flags must be detectable via multiple paths:
1. **Direct entity match**: "sudden vision loss" entity
2. **Relationship traversal**: Symptoms → Emergent diseases
3. **Community membership**: "Ocular emergencies" community

## Performance Considerations

### Indexing
- **Batch size**: Process 5-10 conditions at a time
- **Concurrency**: Limit to 5 concurrent LLM calls
- **Caching**: Cache embeddings to avoid recomputation
- **Retries**: Exponential backoff for API failures

### Search
- **Local search**: <2 seconds (vector similarity is fast)
- **Global search**: <5 seconds (pre-computed summaries help)
- **Context limits**: Max 8K tokens for LLM context

### Cost Optimization
- **Entity extraction**: ~$0.01 per condition
- **Relationship extraction**: ~$0.005 per condition
- **Community summarization**: ~$0.02 per community
- **Query processing**: ~$0.001-0.01 per query

**Target**: <$0.05 per triage session

## Troubleshooting

### "Entity extraction returning empty results"
- Check LLM API key is valid
- Verify text has medical content
- Check temperature setting (should be low, 0.1-0.3)

### "Relationship extraction taking too long"
- Reduce number of entities per batch
- Check API rate limits
- Use retry logic with backoff

### "Neo4j connection failed"
- Verify Neo4j is running: `docker ps | grep neo4j`
- Check URI format: `bolt://localhost:7687`
- Verify credentials in .env

### "Out of memory during indexing"
- Reduce batch size
- Process one chapter at a time
- Clear Neo4j database between runs

## Resources

### Documentation
- Architecture: `docs/GRAPHRAG_ARCHITECTURE.md`
- Implementation status: `GRAPHRAG_IMPLEMENTATION_STATUS.md`
- Original project docs: `CLAUDE.md`

### External Links
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Leiden Algorithm](https://www.nature.com/articles/s41598-019-41695-z)
- [BioBERT Paper](https://arxiv.org/abs/1901.08746)

### Getting Help
- Check logs: `tail -f graphrag_indexing.log`
- Review tests: `pytest indexing/tests/`
- Consult architecture doc for design decisions

## Next Steps

1. **Review** the architecture document
2. **Complete** remaining components (see implementation status)
3. **Test** each component independently
4. **Integrate** with existing triage system
5. **Validate** against medical test cases
6. **Deploy** with feature flag for gradual rollout

## Contributing

When implementing new components:
1. Follow existing code structure and style
2. Add comprehensive docstrings (Google style)
3. Include example usage in `if __name__ == "__main__"`
4. Add unit tests
5. Update this guide and status document
6. Log all operations for debugging

## Safety Reminders

- **Red flags**: Test extensively, 100% detection required
- **Source attribution**: Always cite Wills Eye Manual section
- **Audit trail**: Log all medical decisions
- **Conservative urgency**: When uncertain, escalate
- **No PHI**: Never log patient identifiable information
