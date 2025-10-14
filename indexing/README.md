# Knowledge Graph Indexing

This module handles the extraction, transformation, and indexing of the Wills Eye Manual into a Zep Graphiti knowledge graph for medical triage.

## Quick Start

```bash
# Install dependencies
cd indexing
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export ZEP_API_KEY="your_zep_api_key"
export ZEP_GRAPH_NAME="wills_eye_medical_kg"

# Dry run (preview what will be indexed)
python index_knowledge_graph.py --data ../data/wills_eye_structured.json --dry-run

# Index a single chapter (recommended for testing)
python index_knowledge_graph.py --data ../data/wills_eye_structured.json --chapter "Trauma"

# Full indexing (all chapters)
python index_knowledge_graph.py --data ../data/wills_eye_structured.json

# With verbose logging
python index_knowledge_graph.py --data ../data/wills_eye_structured.json --verbose
```

## Architecture

### Data Flow
```
wills_eye_structured.json
        ↓
    Parser (entity extraction)
        ↓
    Schema Mapper (nodes + edges)
        ↓
    Embedding Service (vector representations)
        ↓
    Zep Graphiti (knowledge graph storage)
```

### Module Structure
```
indexing/
├── parsers/
│   ├── wills_eye_parser.py      # Main JSON parser
│   ├── entity_extractor.py      # Extract medical entities
│   ├── urgency_classifier.py    # Classify urgency levels
│   └── reference_resolver.py    # Handle cross-references
│
├── graph_builder.py              # Build Zep Graphiti nodes/edges
├── embedding_service.py          # Generate embeddings (BioBERT)
├── index_knowledge_graph.py      # Main indexing script
├── config.py                     # Configuration & constants
├── requirements.txt              # Python dependencies
└── tests/
    └── test_indexing.py          # Unit tests
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
ZEP_API_KEY=sk-xxx                    # Zep Graphiti API key
ZEP_GRAPH_NAME=wills_eye_medical_kg   # Graph database name

# Optional
EMBEDDING_MODEL=pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb
BATCH_SIZE=100                         # Nodes per batch
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
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --chapter "Trauma" --chapter "Cornea"
```

### Resume Interrupted Indexing
```bash
# Continues from last successful batch
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --resume
```

### Validate Existing Graph
```bash
# Check graph integrity and medical accuracy
python index_knowledge_graph.py --validate
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
from indexing.graph_builder import GraphClient

client = GraphClient()

# Check a specific condition
condition = client.get_node(type="DISEASE", name="3.1 Chemical Burn")
print(f"Urgency: {condition.urgency_level}")
print(f"Red Flags: {condition.red_flags}")

# Query differential diagnosis
ddx = client.query("""
    MATCH (s:SYMPTOM {name: "eye pain"})<-[:PRESENTS_WITH]-(d:DISEASE)
    RETURN d.name, d.urgency_level
    ORDER BY d.urgency_level DESC
    LIMIT 5
""")
print(ddx)
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

**Issue:** `ZepAPIError: Authentication failed`
- **Solution:** Check `ZEP_API_KEY` environment variable

**Issue:** `JSONDecodeError: Extra data`
- **Solution:** Verify JSON file encoding (use UTF-8)

**Issue:** `MemoryError during embedding generation`
- **Solution:** Reduce `BATCH_SIZE` or use GPU acceleration

**Issue:** Duplicate nodes created
- **Solution:** Run `python index_knowledge_graph.py --clean` to reset graph

### Debug Mode
```bash
# Enable verbose logging
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --verbose \
    --log-level DEBUG
```

## Medical Safety Notes

⚠️ **CRITICAL SAFETY REQUIREMENTS:**
1. All EMERGENT conditions must be tagged with `red_flag_keywords`
2. Urgency levels must match Wills Eye Manual source
3. No false negatives allowed for emergent conditions
4. All treatment recommendations must include "consult doctor" context

### Validation Checklist
Before deploying to production:
- [ ] All red flags from `docs/medical/red-flags.md` are indexed
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

- [GraphRAG Strategy](../docs/technical/graphrag-strategy.md)
- [Medical Framework](../docs/medical/framework.md)
- [Zep Graphiti Docs](https://docs.getzep.com/graphiti/)
- [Wills Eye Manual](../data/wills_eye_structured.json)
