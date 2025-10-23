# Knowledge Graph Indexing

This module handles the extraction, transformation, and indexing of the Wills Eye Manual into a Microsoft GraphRAG knowledge graph for medical triage.

## Quick Start

```bash
# Install dependencies
cd indexing
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables (see .env.example)
export NEO4J_PASSWORD="your_neo4j_password"
export ANTHROPIC_API_KEY="your_anthropic_api_key"  # or OPENAI_API_KEY

# Dry run (preview what will be indexed)
python graphrag_indexer.py --data ../data/wills_eye_structured.json --dry-run

# Index a single chapter (recommended for testing)
python graphrag_indexer.py --data ../data/wills_eye_structured.json --chapter "Trauma"

# Full indexing (all chapters)
python graphrag_indexer.py --data ../data/wills_eye_structured.json

# With verbose logging
python graphrag_indexer.py --data ../data/wills_eye_structured.json --verbose
```

## Architecture

### Data Flow
```
wills_eye_structured.json
        ↓
    Entity Extraction (LLM-based)
        ↓
    Relationship Extraction (LLM-based)
        ↓
    Embedding Service (vector representations)
        ↓
    Community Detection (Leiden algorithm)
        ↓
    Neo4j Storage (Microsoft GraphRAG)
```

### Module Structure
```
indexing/
├── entity_extractor.py           # Extract medical entities (LLM-based)
├── relationship_extractor.py     # Extract relationships (LLM-based)
├── graphrag_embeddings.py        # Generate embeddings (OpenAI/BioBERT)
├── community_detector.py         # Community detection (Leiden algorithm)
├── community_summarizer.py       # Multi-level summarization
├── graphrag_storage.py           # Neo4j storage layer
├── local_search.py               # Entity-based specific queries
├── global_search.py              # Community-based broad queries
├── graphrag_indexer.py           # Main indexing pipeline
├── graphrag_config.py            # GraphRAG configuration
├── config.py                     # Legacy configuration
├── requirements.txt              # Python dependencies
└── tests/
    └── test_*.py                 # Unit tests
```

## Key Features

### 1. Hierarchical Entity Extraction
- **Chapters** → **Sections** → **Conditions** → **Symptoms/Signs/Treatments**
- Preserves medical knowledge structure
- Maintains source attribution (Wills Eye Manual section numbers)

### 2. Multi-Relationship Modeling
- Symptom → Disease associations with confidence scores
- Treatment protocols with contraindications
- Differential diagnoses with distinguishing features
- Risk factors and complications

### 3. Urgency Metadata
Every disease node includes:
- `urgency_level`: EMERGENT | URGENT | NON_URGENT
- `red_flag_keywords`: List of emergency indicators
- `triage_threshold`: Likelihood threshold for referral (default: 0.2)

### 4. Semantic Embeddings
- Medical BERT embeddings for all symptoms/conditions
- Enables semantic matching: "I can't see" → "vision loss"
- Cached embeddings for query performance

## Configuration

### Environment Variables
```bash
# Required
NEO4J_URI=bolt://localhost:7687        # Neo4j connection URI
NEO4J_USER=neo4j                       # Neo4j username
NEO4J_PASSWORD=your_password           # Neo4j password
ANTHROPIC_API_KEY=sk-ant-xxx           # Anthropic API key (for Claude)
# OR
OPENAI_API_KEY=sk-xxx                  # OpenAI API key (alternative)

# Optional
LLM_PROVIDER=anthropic                 # anthropic or openai
EMBEDDING_PROVIDER=openai              # openai or sentence_transformers
EMBEDDING_MODEL=text-embedding-3-small # OpenAI embedding model
BATCH_SIZE=10                          # Conditions per batch
LOG_LEVEL=INFO                         # DEBUG | INFO | WARNING | ERROR
```

### Customization
Edit `config.py` to adjust:
- Node/edge types
- Urgency classification rules
- Red flag keyword lists
- Embedding model selection

## Usage Examples

### Index Specific Chapters
```bash
# Only index trauma and cornea chapters
python graphrag_indexer.py \
    --data ../data/wills_eye_structured.json \
    --chapter "Trauma" --chapter "Cornea"
```

### Test Individual Components
```bash
# Test entity extraction
python entity_extractor.py

# Test relationship extraction
python relationship_extractor.py

# Test embedding service
python graphrag_embeddings.py
```

### Validate Existing Graph
```bash
# Check graph integrity and medical accuracy
python graphrag_indexer.py --validate
```

## Output & Logging

### Log Files
- `knowledge_graph_indexing.log` - Detailed indexing progress
- `indexing_errors.json` - Failed entries for manual review

### Console Output
```
[INFO] Starting indexing: Wills Eye Manual
[INFO] Total chapters to process: 14
[INFO] Processing chapter: Trauma (1/14)
[INFO]   ├─ Sections found: 23
[INFO]   ├─ Nodes created: 145
[INFO]   ├─ Edges created: 487
[INFO]   └─ Duration: 12.3s
[INFO] Processing chapter: Cornea (2/14)
...
[SUCCESS] Indexing complete!
[SUMMARY] Total nodes: 8,234 | Total edges: 52,891 | Duration: 8m 42s
```

## Validation & Testing

### Medical Accuracy Tests
```bash
# Run validation suite
pytest tests/test_indexing.py -v

# Specific test categories
pytest tests/test_indexing.py::test_red_flag_detection -v
pytest tests/test_indexing.py::test_urgency_classification -v
```

### Manual Verification
```python
from graphrag_client import GraphRAGClient

client = GraphRAGClient()

# Search for specific entities
results = await client.local_search("chemical burn")
print(f"Found {len(results)} related entities")

# Broad thematic search
results = await client.global_search("What are the emergent eye conditions?")
print(results)

# Direct Neo4j queries
from graphrag_storage import Neo4jStorage
storage = Neo4jStorage()
conditions = storage.query_cypher("""
    MATCH (e:Entity {type: 'DISEASE'})-[:PRESENTS_WITH]->(s:Entity {type: 'SYMPTOM'})
    WHERE s.name CONTAINS 'vision loss'
    RETURN e.name, e.urgency_level
    ORDER BY e.urgency_level DESC
    LIMIT 5
""")
print(conditions)
```

## Performance

### Expected Metrics
- **Indexing Speed:** ~500 nodes/minute
- **Full Indexing Time:** 10-15 minutes (all 14 chapters)
- **Graph Size:** ~8,000 nodes, ~50,000 edges
- **Embedding Storage:** ~30 MB

### Optimization Tips
1. Use batch processing (adjust `BATCH_SIZE` in config)
2. Cache embeddings to avoid recomputation
3. Run indexing during off-peak hours
4. Use `--chapter` flag for incremental updates

## Troubleshooting

### Common Issues

**Issue:** `Neo4jError: Connection refused`
- **Solution:** Ensure Neo4j is running and accessible at `NEO4J_URI`

**Issue:** `JSONDecodeError: Extra data`
- **Solution:** Verify JSON file encoding (use UTF-8)

**Issue:** `MemoryError during embedding generation`
- **Solution:** Reduce `BATCH_SIZE` or use GPU acceleration

**Issue:** Missing API key errors
- **Solution:** Check environment variables are set: `NEO4J_PASSWORD`, `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

### Debug Mode
```bash
# Enable verbose logging
python graphrag_indexer.py \
    --data ../data/wills_eye_structured.json \
    --verbose
```

## Medical Safety Notes

⚠️ **CRITICAL SAFETY REQUIREMENTS:**
1. All EMERGENT conditions must be tagged with `red_flag_keywords`
2. Urgency levels must match Wills Eye Manual source
3. No false negatives allowed for emergent conditions
4. All treatment recommendations must include "consult doctor" context

### Validation Checklist
Before deploying to production:
- [ ] All red flags extracted from Wills Eye Manual (Phase 5.1) are indexed in Neo4j
- [ ] Red flags output file (`indexing/output/phase5/red_flags.json`) is complete
- [ ] Urgency levels validated against `docs/medical/urgency-levels.md`
- [ ] 100% of emergent conditions correctly classified
- [ ] Cross-references properly resolved
- [ ] Treatment contraindications captured

## Contributing

### Adding New Parsers
1. Create parser in `parsers/`
2. Implement `BaseParser` interface
3. Add unit tests in `tests/`
4. Update `config.py` with new entity types

### Updating Schema
1. Modify `backend/schema/knowladge_base.py`
2. Update `graph_builder.py` mapping logic
3. Run migration script (if graph already exists)
4. Re-index affected chapters

## References

- [GraphRAG Architecture](../docs/GRAPHRAG_ARCHITECTURE.md)
- [GraphRAG Strategy](../docs/technical/graphrag-strategy.md)
- [GraphRAG Quick Start](QUICKSTART_GRAPHRAG.md)
- [Medical Framework](../docs/medical/framework.md)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Wills Eye Manual](../data/wills_eye_structured.json)
