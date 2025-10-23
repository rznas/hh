# Phase 6: Graph Preparation - Summary Report

**Status:** ✅ Complete
**Generated:** 2025-10-23
**Total Time:** ~5 minutes

---

## Overview

Phase 6 converts extracted medical entities and relationships from previous phases into Neo4j-compatible knowledge graph format. This phase is the bridge between data extraction and the final knowledge graph database.

## What Was Generated

### Core Outputs

1. **graphrag_nodes.json** (1.1 MB)
   - 2,002 medical entities in Neo4j node format
   - Includes diseases, symptoms, signs, treatments, and diagnostic tests

2. **graphrag_edges.json** (9.2 MB)
   - 28,941 relationships between entities
   - 5 relationship types (presents_with, treated_with, associated_with, etc.)

3. **neo4j_import.cypher** (7.2 MB)
   - Ready-to-run Cypher script for Neo4j import
   - Creates indexes and constraints
   - Batched for efficiency

4. **nodes.csv + relationships.csv** (481 KB + 2.8 MB)
   - CSV exports for bulk Neo4j import
   - Alternative to Cypher script

5. **embedding_project/** (Standalone Python project)
   - PubMedBERT embedding generation script
   - Documentation for running on GPU machine
   - Alternative LLM API approach (OpenAI, Cohere)

---

## Statistics

### Nodes by Type

| Type | Count | Description |
|------|-------|-------------|
| Disease | 990 | Medical conditions from Wills Eye Manual |
| Treatment | 845 | Medications, procedures, interventions |
| Sign | 74 | Clinical examination findings |
| DiagnosticTest | 55 | Tests and imaging modalities |
| Symptom | 38 | Patient-reported symptoms |
| **Total** | **2,002** | |

### Edges by Type

| Relationship | Count | Description |
|--------------|-------|-------------|
| treated_with | 14,738 | Disease → Treatment |
| associated_with | 8,367 | Disease → Sign |
| presents_with | 3,213 | Disease → Symptom |
| diagnosed_with | 2,518 | Disease → DiagnosticTest |
| differential_diagnosis | 105 | Disease → Disease |
| **Total** | **28,941** | |

### Medical Safety

- **Red Flags:** 103 emergent conditions marked
- **Urgency Levels:** All diseases classified (emergent/urgent/non-urgent)
- **Source Citations:** Maintained for audit trail

---

## How to Use

### 1. Import to Neo4j (Choose One Method)

**Option A: Cypher Script (Recommended)**
```bash
# Connect to Neo4j and run script
neo4j-shell -file indexing/output/phase6/neo4j_import.cypher
```

**Option B: CSV Bulk Import (Faster for Large Datasets)**
```bash
neo4j-admin import \
  --nodes=indexing/output/phase6/nodes.csv \
  --relationships=indexing/output/phase6/relationships.csv
```

### 2. Generate Embeddings (Optional)

**For semantic search, generate entity embeddings:**

```bash
# On a machine with GPU
cd indexing/output/phase6/embedding_project

# Copy input file
cp ../graphrag_nodes.json .

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate embeddings
python generate_embeddings.py --device cuda --batch-size 32

# Copy results back
cp embeddings_output.json ../entity_embeddings.json
```

**Estimated time:**
- GPU (T4): ~2 minutes
- CPU: ~1-2 hours
- OpenAI API: ~30 seconds (costs ~$0.10)

---

## Node Schema

Each node follows this structure:

```json
{
  "id": "disease_001",
  "label": "Acute Angle-Closure Glaucoma",
  "type": "Disease",
  "properties": {
    "description": "...",
    "synonyms": ["acute glaucoma"],
    "icd_10": "H40.2",
    "urgency_level": "emergent",
    "urgency_source": "Extracted from Wills Eye Manual...",
    "red_flag": true,
    "chapters": [9],
    "sections": ["Glaucoma"]
  }
}
```

## Edge Schema

Each edge follows this structure:

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

---

## Example Queries

Once imported to Neo4j, you can run queries like:

```cypher
// Find all emergent conditions
MATCH (d:Entity {type: 'Disease'})
WHERE d.urgency_level = 'emergent'
RETURN d.label, d.description
LIMIT 10;

// Find symptoms of a specific disease
MATCH (d:Entity {label: 'Acute Angle-Closure Glaucoma'})
      -[r:PRESENTS_WITH]->
      (s:Entity {type: 'Symptom'})
RETURN s.label, r.weight;

// Find treatments for keratitis
MATCH (d:Entity {type: 'Disease'})
WHERE d.label CONTAINS 'Keratitis'
MATCH (d)-[r:TREATED_WITH]->(t:Entity {type: 'Treatment'})
RETURN d.label, t.label, r.description;

// Red flag detection
MATCH (d:Entity {type: 'Disease'})
WHERE d.red_flag = true
RETURN d.label, d.urgency_level
ORDER BY d.mention_count DESC;
```

---

## Validation Results

✅ **All validations passed:**

- Nodes created: 2,002 ✓
- Edges created: 28,941 ✓
- Red flags present: 103 ✓
- All edges reference existing nodes ✓
- Medical codes preserved ✓
- Source citations maintained ✓

---

## Next Steps

### Immediate (Required for MVP)

1. **Import to Neo4j**
   - Set up Neo4j database (4.4+ recommended)
   - Run import script (2-5 minutes)
   - Verify node/edge counts

2. **Generate Embeddings** (if doing semantic search)
   - Run embedding_project on GPU machine
   - Use PubMedBERT for medical domain accuracy
   - Alternative: OpenAI API for faster setup

3. **Phase 7: Validation & Testing**
   - Test red flag detection queries
   - Validate urgency classifications
   - Check entity completeness

### Future Enhancements

1. **Community Detection** (Phase 6.5)
   - Run Leiden algorithm on graph
   - Create hierarchical clusters
   - Generate community summaries with LLM

2. **Search Implementation**
   - Local search (entity-based)
   - Global search (community-based)
   - Hybrid search combining both

3. **Integration**
   - Connect to triage agent
   - Implement GraphRAG queries
   - Add Langfuse monitoring

---

## Files Generated

```
indexing/output/phase6/
├── graphrag_nodes.json          # 2,002 nodes (1.1 MB)
├── graphrag_edges.json          # 28,941 edges (9.2 MB)
├── neo4j_import.cypher          # Import script (7.2 MB)
├── nodes.csv                    # CSV export (481 KB)
├── relationships.csv            # CSV export (2.8 MB)
├── phase6_report.json           # Statistics
├── README.md                    # Full documentation
└── embedding_project/           # Standalone project
    ├── generate_embeddings.py   # PubMedBERT script
    ├── RERUN_WITH_LLM.md        # Alternative approach
    ├── requirements.txt         # Dependencies
    └── README.md                # Full guide
```

---

## Performance Metrics

- **Graph Preparation:** ~30 seconds
- **Cypher Script Generation:** ~10 seconds
- **CSV Export:** ~5 seconds
- **Total Phase 6 Runtime:** ~5 minutes

**Neo4j Import Estimates:**
- Cypher script: ~2-5 minutes
- CSV bulk import: ~30 seconds

**Embedding Generation Estimates:**
- GPU (T4): ~2 minutes
- GPU (A100): <1 minute
- CPU: ~1-2 hours
- OpenAI API: ~30 seconds (~$0.10 cost)

---

## Medical Safety Compliance

✅ **Phase 6 maintains all medical safety requirements:**

- Red flags from Phase 5 preserved (103 conditions)
- Urgency levels from Phase 4 maintained (emergent/urgent/non-urgent)
- Source citations from Wills Eye Manual included
- ICD-10/SNOMED codes preserved where available
- Audit trail maintained for all medical decisions

---

## Troubleshooting

**Q: Neo4j import fails with "constraint violation"**
A: Drop existing database first: `DROP DATABASE neo4j` then re-run import

**Q: Embedding generation runs out of memory**
A: Reduce batch size: `--batch-size 8` or use CPU: `--device cpu`

**Q: Want faster embedding generation without GPU**
A: Use OpenAI API (see embedding_project/RERUN_WITH_LLM.md)

**Q: Some edges reference non-existent nodes**
A: This should not happen - Phase 6 validates all edges. Report if found.

---

## Phase 6 Complete ✓

**Ready for:**
- ✅ Neo4j database import
- ✅ Embedding generation (optional)
- ✅ Phase 7: Validation & Testing
- ✅ GraphRAG search implementation

**Total GraphRAG Preparation Progress:**
- Phase 1: Content Extraction ✓
- Phase 2: Entity Extraction ✓
- Phase 3: Relationship Extraction ✓
- Phase 4: Domain Standardization ✓
- Phase 5: Red Flag Extraction ✓
- **Phase 6: Graph Preparation ✓** ← YOU ARE HERE
- Phase 7: Validation (next)
- Phase 8: Final Deliverables (pending)

---

**Generated:** 2025-10-23
**Source:** Wills Eye Manual (7th Edition)
**Author:** GraphRAG Preparation Pipeline
