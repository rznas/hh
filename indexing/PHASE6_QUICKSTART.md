# Phase 6: Quick Start Guide

**TL;DR:** Phase 6 converts medical entities → Neo4j knowledge graph format. Ready to import!

---

## What Happened

✅ **2,002 nodes** created (diseases, symptoms, signs, treatments, tests)
✅ **28,941 edges** created (presents_with, treated_with, etc.)
✅ **Neo4j import scripts** generated (Cypher + CSV)
✅ **Embedding project** created (PubMedBERT, runs on separate machine)

---

## Quick Import to Neo4j

```bash
# Option 1: Cypher script (recommended)
neo4j-shell -file indexing/output/phase6/neo4j_import.cypher

# Option 2: CSV bulk import (faster)
neo4j-admin import \
  --nodes=indexing/output/phase6/nodes.csv \
  --relationships=indexing/output/phase6/relationships.csv
```

**Time:** 2-5 minutes

---

## Generate Embeddings (Optional, for Semantic Search)

**On a GPU machine:**

```bash
cd indexing/output/phase6/embedding_project

# Copy input
cp ../graphrag_nodes.json .

# Set up
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate (uses NeuML/pubmedbert-base-embeddings)
python generate_embeddings.py --device cuda --batch-size 32

# Copy back
cp embeddings_output.json ../entity_embeddings.json
```

**Time:** GPU ~2 min, CPU ~1-2 hours

**Alternative:** Use OpenAI API (~$0.10, 30 seconds) - see `embedding_project/RERUN_WITH_LLM.md`

---

## File Locations

```
indexing/output/phase6/
├── graphrag_nodes.json       # 2,002 entities (ready for Neo4j)
├── graphrag_edges.json       # 28,941 relationships
├── neo4j_import.cypher       # Import script
├── nodes.csv                 # CSV export
├── relationships.csv         # CSV export
├── phase6_report.json        # Statistics
├── PHASE6_SUMMARY.md         # Full report
├── README.md                 # Documentation
└── embedding_project/        # Standalone Python project
    ├── generate_embeddings.py
    ├── requirements.txt
    ├── README.md
    └── RERUN_WITH_LLM.md
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Nodes | 2,002 |
| Total Edges | 28,941 |
| Red Flags | 103 |
| Diseases | 990 |
| Treatments | 845 |
| Signs | 74 |
| Diagnostic Tests | 55 |
| Symptoms | 38 |

**Top Relationship Types:**
- treated_with: 14,738
- associated_with: 8,367
- presents_with: 3,213
- diagnosed_with: 2,518

---

## Next Steps

1. ✅ Import to Neo4j (required)
2. ⚠️ Generate embeddings (optional, for semantic search)
3. → Phase 7: Validation & Testing
4. → Implement GraphRAG search (local + global)

---

## Full Documentation

- **Quick Summary:** `indexing/output/phase6/PHASE6_SUMMARY.md`
- **Full Guide:** `indexing/output/phase6/README.md`
- **Embedding Guide:** `indexing/output/phase6/embedding_project/README.md`
- **LLM Alternative:** `indexing/output/phase6/embedding_project/RERUN_WITH_LLM.md`

---

**Phase 6 Complete! 🎉**

Generated: 2025-10-23
