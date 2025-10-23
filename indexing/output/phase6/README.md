# Phase 6 Output - Graph Preparation for Neo4j

✅ **Status**: Phase 6 Complete

## Overview

Converts extracted medical entities and relationships into Neo4j-compatible knowledge graph format.

## Files Generated

### Core Outputs

- **graphrag_nodes.json** - All entities in Neo4j node format (~5MB)
- **graphrag_edges.json** - All relationships in Neo4j edge format (~10MB)
- **neo4j_import.cypher** - Cypher script for Neo4j database import
- **nodes.csv** - CSV export of nodes for bulk import
- **relationships.csv** - CSV export of edges for bulk import
- **phase6_report.json** - Phase 6 statistics and validation

### Embedding Project (Run Separately)

- **embedding_project/** - Standalone Python project for generating embeddings
  - `generate_embeddings.py` - PubMedBERT embedding generation
  - `RERUN_WITH_LLM.md` - Alternative LLM API approach
  - `requirements.txt` - Dependencies
  - `README.md` - Full documentation

## Quick Start

### 1. Run Phase 6 Script

```bash
cd indexing
.venv/Scripts/python phase6_prepare_graph.py
```

This generates:
- Neo4j-compatible JSON files
- Cypher import script
- CSV exports

### 2. Generate Embeddings (Optional, Run on GPU Machine)

```bash
# Copy files to embedding project
cd output/phase6/embedding_project
cp ../graphrag_nodes.json .

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate embeddings (recommended: GPU machine)
python generate_embeddings.py --batch-size 32 --device cuda

# Copy outputs back
cp embeddings_output.json ../entity_embeddings.json
cp embeddings_report.json ../
```

### 3. Import to Neo4j

**Option A: Using Cypher Script**

```bash
# Connect to Neo4j
neo4j-shell -file neo4j_import.cypher
```

**Option B: Using CSV Bulk Import**

```bash
neo4j-admin import \
  --nodes=nodes.csv \
  --relationships=relationships.csv \
  --delimiter=","
```

## Schema

### Node Format

```json
{
  "id": "disease_001",
  "label": "Acute Angle-Closure Glaucoma",
  "type": "Disease",
  "properties": {
    "description": "...",
    "synonyms": ["acute glaucoma", "..."],
    "icd_10": "H40.2",
    "urgency_level": "emergent",
    "urgency_source": "Extracted from Wills Eye Manual...",
    "red_flag": true,
    "chapters": [9],
    "sections": ["Glaucoma"]
  }
}
```

### Edge Format

```json
{
  "source": "disease_001",
  "target": "symptom_042",
  "relationship_type": "presents_with",
  "properties": {
    "weight": 0.85,
    "description": "Acute Angle-Closure Glaucoma presents with Severe Eye Pain",
    "chapter": 9,
    "extraction_method": "co-occurrence"
  }
}
```

## Statistics (Example)

Based on Wills Eye Manual extraction:

```
Nodes: ~5,000
  - Diseases: ~400
  - Symptoms: ~150
  - Signs: ~120
  - Treatments: ~300
  - Diagnostic Tests: ~80

Edges: ~28,000
  - presents_with: ~12,000
  - treated_with: ~8,000
  - associated_with: ~5,000
  - other: ~3,000

Red Flags: ~10 emergent conditions
```

## Validation

The Phase 6 script validates:

✅ All nodes have unique IDs
✅ All edges reference existing nodes
✅ Red flag conditions are present
✅ Urgency levels are assigned
✅ Medical codes are preserved

## Next Steps

### Immediate (Phase 7)

1. **Validate knowledge graph**
   - Check entity completeness
   - Verify relationship accuracy
   - Test red flag detection

2. **Test Neo4j queries**
   - Search by symptoms
   - Search by diseases
   - Red flag lookup

### Future (Community Detection)

Once Phase 6 is complete and validated:

1. **Phase 6.5: Community Detection** (not yet implemented)
   - Run Leiden algorithm on graph
   - Create hierarchical communities
   - Generate community summaries with LLM

2. **Phase 7: Search Implementation**
   - Local search (entity-based)
   - Global search (community-based)
   - Hybrid search

## Embedding Details

### Why PubMedBERT?

Model: **NeuML/pubmedbert-base-embeddings**

- **Domain-specific**: Pre-trained on PubMed medical literature
- **Optimized for embeddings**: Fine-tuned for semantic similarity tasks
- **Better accuracy**: Understands medical terminology
- **768 dimensions**: Good balance of size/performance
- **Free**: No API costs

### Alternative: OpenAI Embeddings

If you cannot run PubMedBERT locally:

```bash
cd embedding_project
pip install openai
export OPENAI_API_KEY="your-key"
python generate_embeddings_openai.py
```

Cost: ~$0.10 for 5000 entities

See `embedding_project/RERUN_WITH_LLM.md` for details.

## Neo4j Import Examples

### Cypher Query Examples

```cypher
// Find all diseases with emergent urgency
MATCH (d:Entity {type: 'Disease'})
WHERE d.urgency_level = 'emergent'
RETURN d.label, d.description

// Find symptoms of a disease
MATCH (d:Entity {type: 'Disease', label: 'Acute Angle-Closure Glaucoma'})
      -[r:PRESENTS_WITH]->
      (s:Entity {type: 'Symptom'})
RETURN s.label, r.weight

// Find treatments for a disease
MATCH (d:Entity {label: 'Bacterial Keratitis'})
      -[r:TREATED_WITH]->
      (t:Entity {type: 'Treatment'})
RETURN t.label, r.description

// Red flag detection
MATCH (d:Entity {type: 'Disease'})
WHERE d.red_flag = true
RETURN d.label, d.urgency_level, d.clinical_presentation
```

## Troubleshooting

### "Node ID not found" error
- Ensure Phase 2 entities have been generated
- Check entity IDs are consistent across phases

### Cypher import fails
- Verify Neo4j version (4.4+ recommended)
- Check file paths are absolute
- Ensure database is empty before import

### Embedding generation out of memory
- Reduce batch size: `--batch-size 8`
- Use CPU instead: `--device cpu`
- Use OpenAI API instead (see RERUN_WITH_LLM.md)

## Performance Notes

**Graph preparation:** ~30 seconds for 5000 nodes + 28K edges

**Embedding generation:**
- GPU (T4): ~2 minutes
- GPU (A100): <1 minute
- CPU: ~1-2 hours
- OpenAI API: ~30 seconds ($0.10)

**Neo4j import:**
- Cypher script: ~2-5 minutes
- CSV bulk import: ~30 seconds

## Medical Safety Compliance

✅ All red flags preserved from Phase 5
✅ Urgency levels extracted from Wills Eye Manual (Phase 4)
✅ Source citations maintained for audit trail
✅ Medical codes (ICD-10, SNOMED) preserved

## Phase 6 Complete ✓

**Ready for:**
- Phase 7: Validation & Testing
- Neo4j database import
- GraphRAG search implementation

**Total preparation time:** ~5-10 minutes (graph prep) + embedding time (varies)

---

Generated: 2025-10-23
