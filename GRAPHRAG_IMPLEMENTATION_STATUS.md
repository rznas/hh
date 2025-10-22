# Microsoft GraphRAG Implementation Status

## Overview

This document tracks the implementation of Microsoft GraphRAG approach for the medical triage knowledge graph.

**Status**: 🟡 In Progress (Core components implemented, remaining components outlined)

**Last Updated**: 2025-10-14

## Completed Components

### ✅ 1. Architecture Design
**File**: `docs/GRAPHRAG_ARCHITECTURE.md`

Complete architectural design document including:
- Data indexing pipeline (entity extraction → community detection → summarization)
- Query pipeline (local search and global search)
- Medical domain considerations
- Storage schema
- Performance targets
- Migration strategy

### ✅ 2. Configuration System
**File**: `indexing/graphrag_config.py`

GraphRAG configuration management with:
- Pydantic-based configuration model
- Support for multiple LLM providers (OpenAI, Anthropic)
- Support for multiple embedding providers
- Community detection parameters
- Search configuration
- Environment variable loading
- Configuration validation

### ✅ 3. Entity Extraction
**File**: `indexing/entity_extractor.py`

LLM-based entity extraction with:
- Support for Anthropic Claude and OpenAI GPT models
- Medical entity types (DISEASE, SYMPTOM, SIGN, TREATMENT, etc.)
- Structured JSON output parsing
- Batch processing with concurrency control
- Retry logic with exponential backoff
- Context preservation (chapter, section references)
- Example usage and testing code

### ✅ 4. Relationship Extraction
**File**: `indexing/relationship_extractor.py`

LLM-based relationship extraction with:
- Medical relationship types (PRESENTS_WITH, TREATED_WITH, etc.)
- Relationship weights/strengths
- Support for multiple LLM providers
- Batch processing
- Context-aware extraction
- Retry logic

### ✅ 5. Dependencies Updated
**File**: `indexing/requirements.txt`

Updated dependencies including:
- Microsoft GraphRAG package
- Community detection libraries (leidenalg, igraph)
- Graph analysis tools (networkx, graspologic)
- Sentence transformers for BioBERT embeddings
- Additional utilities (tenacity, tiktoken)

### ✅ 6. Documentation
**File**: `.gitignore` (created)

Added comprehensive gitignore for Python, Django, Node.js, and sensitive medical data.

## Remaining Components

### 🔲 7. Embedding Service
**File to create**: `indexing/graphrag_embeddings.py`

Required features:
- OpenAI text-embedding-3-large integration
- BioBERT embedding support for medical domain
- Batch embedding generation
- Caching for performance
- Vector similarity search utilities

**Implementation Guide**:
```python
class EmbeddingService:
    """Generate and manage embeddings for entities and text."""
    - async def embed_text(text: str) -> List[float]
    - async def embed_batch(texts: List[str]) -> List[List[float]]
    - async def similarity(emb1, emb2) -> float
    - Support both OpenAI and sentence-transformers
```

### 🔲 8. Community Detection
**File to create**: `indexing/community_detector.py`

Required features:
- Leiden algorithm implementation using igraph + leidenalg
- Hierarchical clustering (multiple levels)
- NetworkX integration for graph building
- Community quality metrics
- Visualization utilities (optional)

**Implementation Guide**:
```python
class CommunityDetector:
    """Detect communities in entity graph."""
    - def build_graph(entities, relationships) -> Graph
    - def detect_communities(graph, resolution=1.0) -> Dict
    - def hierarchical_clustering(graph, levels=3) -> Dict
    - def get_community_stats(communities) -> Dict
```

### 🔲 9. Community Summarization
**File to create**: `indexing/community_summarizer.py`

Required features:
- LLM-based community summary generation
- Multi-level summarization (L0, L1, L2...)
- Medical context preservation
- Summary caching
- Batch processing

**Implementation Guide**:
```python
class CommunitySummarizer:
    """Generate summaries for communities."""
    - async def summarize_community(entities, relationships) -> str
    - async def hierarchical_summarize(communities) -> Dict
    - Focus on: common themes, key entities, urgency patterns
```

### 🔲 10. Neo4j Storage Layer
**File to create**: `indexing/graphrag_storage.py`

Required features:
- Neo4j connection management
- Entity node creation with embeddings
- Relationship edge creation
- Community node creation
- Hierarchical community structure
- Vector index creation for similarity search
- Cypher query builders

**Implementation Guide**:
```python
class GraphRAGStorage:
    """Neo4j storage for GraphRAG."""
    - async def store_entity(entity: MedicalEntity, embedding: List[float])
    - async def store_relationship(relationship: MedicalRelationship)
    - async def store_community(community_id, entities, summary, level)
    - async def create_vector_index(index_name: str)
    - async def similarity_search(embedding, top_k) -> List[Entity]
```

### 🔲 11. Local Search
**File to create**: `indexing/local_search.py`

Required features:
- Entity-based retrieval using vector similarity
- Neighbor expansion (1-hop, 2-hop)
- Context assembly for LLM
- Relevance scoring
- Result ranking

**Implementation Guide**:
```python
class LocalSearch:
    """Local search for entity-specific queries."""
    - async def search(query: str, top_k=10) -> SearchResult
    - async def expand_neighbors(entity_ids, hops=1) -> Graph
    - async def assemble_context(entities, relationships) -> str
    - async def generate_response(query, context) -> str
```

### 🔲 12. Global Search
**File to create**: `indexing/global_search.py`

Required features:
- Community-based retrieval
- Hierarchical context assembly
- Map-reduce summarization
- Multi-level search (start at high level, drill down)

**Implementation Guide**:
```python
class GlobalSearch:
    """Global search for broad queries."""
    - async def search(query: str, top_k=5) -> SearchResult
    - async def retrieve_communities(query, level) -> List[Community]
    - async def map_reduce_summarize(communities, query) -> str
    - async def hierarchical_search(query, max_levels=3) -> str
```

### 🔲 13. Main Indexing Pipeline
**File to create**: `indexing/graphrag_indexer.py`

Required features:
- Orchestrate full indexing pipeline
- Read Wills Eye Manual JSON
- Extract entities from all conditions
- Extract relationships
- Build graph and detect communities
- Generate community summaries
- Store everything in Neo4j
- Progress tracking and logging

**Implementation Guide**:
```python
class GraphRAGIndexer:
    """Main indexing pipeline orchestrator."""
    - async def index_chapter(chapter_name: str)
    - async def index_all_chapters()
    - Pipeline: Parse → Extract Entities → Extract Relationships →
                Build Graph → Detect Communities → Summarize → Store
    - Progress bar with tqdm
    - Detailed logging
    - Error handling and retries
```

### 🔲 14. Query Interface
**File to create**: `indexing/graphrag_client.py`

Required features:
- Unified query interface for medical triage
- Automatic query classification (local vs global)
- Hybrid search option
- Medical domain query builders
- Red flag detection via graph search

**Implementation Guide**:
```python
class GraphRAGClient:
    """Main client interface for GraphRAG queries."""
    - async def search(query: str, method="auto") -> SearchResult
    - async def classify_query(query: str) -> str  # "local" or "global"
    - async def search_conditions_by_symptom(symptom: str)
    - async def check_red_flags(symptoms: List[str])
    - async def get_differential_diagnosis(symptoms: List[str])
```

### 🔲 15. Testing Suite
**File to create**: `indexing/tests/test_graphrag.py`

Required tests:
- Entity extraction accuracy
- Relationship extraction accuracy
- Community detection correctness
- Search relevance
- Red flag detection (100% accuracy required)
- Integration tests for full pipeline
- Performance benchmarks

### 🔲 16. Validation and Deployment
**File to update**: `scripts/deploy_graphrag.py`

Required features:
- Run new indexing pipeline
- Validate results against test scenarios
- Performance benchmarking
- Deployment verification

## Next Steps (Priority Order)

### Immediate (Required for MVP)

1. **Implement Embedding Service** - Required for all search functionality
   - Start with OpenAI embeddings (simpler)
   - Add BioBERT later for domain-specific improvements

2. **Implement Neo4j Storage Layer** - Required to persist data
   - Entity and relationship storage
   - Vector index creation
   - Basic query methods

3. **Implement Community Detection** - Core GraphRAG feature
   - Use Leiden algorithm
   - Start with 2-3 hierarchy levels
   - Store community structure in Neo4j

4. **Implement Community Summarization** - Required for global search
   - Use Claude/GPT to generate summaries
   - Store summaries with communities

5. **Implement Local Search** - Required for specific queries
   - Entity retrieval via embeddings
   - Neighbor expansion
   - LLM response generation

6. **Implement Main Indexing Pipeline** - Orchestrate everything
   - Process Wills Eye Manual
   - Run full pipeline
   - Generate knowledge graph

### Secondary (Enhanced Functionality)

7. **Implement Global Search** - For broad questions
   - Community-based retrieval
   - Map-reduce summarization

8. **Implement GraphRAG Client** - Unified interface
   - Query classification
   - Backward compatibility
   - Medical query builders

9. **Testing Suite** - Ensure quality
   - Unit tests
   - Integration tests
   - Validation scenarios

10. **Migration Script** - Production deployment
    - Safe migration path
    - Validation
    - Rollback capability

## Usage Instructions (Once Complete)

### Installation
```bash
cd indexing
pip install -r requirements.txt
```

### Configuration
```bash
# Set environment variables in .env file
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```

### Indexing
```bash
# Index all chapters
python graphrag_indexer.py --data ../data/wills_eye_structured.json

# Index specific chapter
python graphrag_indexer.py --data ../data/wills_eye_structured.json --chapter "Trauma"
```

### Querying
```python
from graphrag_client import GraphRAGClient

client = GraphRAGClient()

# Local search (specific entity)
result = await client.search("What causes sudden vision loss?")

# Global search (broad question)
result = await client.search("What are the most common eye emergencies?")

# Red flag check
is_emergency = await client.check_red_flags(["sudden vision loss", "eye pain"])
```

## Performance Targets

- **Indexing**: Process full Wills Eye Manual in <30 minutes
- **Local Search**: <2 seconds per query
- **Global Search**: <5 seconds per query
- **Cost**: <$0.05 per triage session
- **Accuracy**: 100% red flag detection, >90% urgency classification

## Critical Safety Notes

1. **Red flags MUST be tested extensively** - 100% detection rate required
2. **All medical decisions logged** - Audit trail for liability protection
3. **Source attribution** - Every recommendation must cite Wills Eye Manual section
4. **Conservative urgency** - When uncertain, escalate urgency level
5. **HIPAA compliance** - No patient data in logs, all PHI encrypted

## Questions / Decisions Needed

- [ ] Which embedding model? (OpenAI vs BioBERT vs both)
- [ ] How many community levels? (Recommend 3)
- [ ] Neo4j hosted or self-hosted?
- [ ] Feature flag for gradual rollout?

## Resources

- **Microsoft GraphRAG**: https://github.com/microsoft/graphrag
- **Leiden Algorithm**: https://leidenalg.readthedocs.io
- **Neo4j Vector Search**: https://neo4j.com/docs/vector-search
- **BioBERT**: https://huggingface.co/dmis-lab/biobert-v1.1
