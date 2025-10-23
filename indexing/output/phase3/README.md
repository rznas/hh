# Phase 3 Output - Quick Reference

## Relationship Extraction Results

Extracted **28,941 relationships** between medical entities from The Wills Eye Manual.

## Files

### Relationship Data Files

1. **graphrag_edges.json** (28,941 relationships)
   - Disease → Treatment: 14,738
   - Disease → Sign: 8,367
   - Disease → Symptom: 3,213
   - Disease → Diagnostic Test: 2,518
   - Differential Diagnosis: 105

### Reports

- **PHASE3_SUMMARY.md** - Comprehensive summary with methodology
- **phase3_report.json** - Statistics and confidence metrics

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Relationships | 28,941 |
| Disease → Treatment | 14,738 |
| Disease → Sign | 8,367 |
| Disease → Symptom | 3,213 |
| Disease → Test | 2,518 |
| Differential DDx | 105 |

## Extraction Method

- **Co-occurrence analysis**: Entities appearing in same text block
- **Section-aware weighting**: Higher weights for treatment/diagnostic sections
- **Deduplication**: Removed 25,657 duplicates (47%)
- **Processing time**: ~2 minutes
- **Cost**: $0 (rule-based, no LLM calls)

## Confidence Levels

- **High (≥0.8)**: 105 relationships (DDx lists + treatment sections)
- **Medium (0.6-0.8)**: 28,836 relationships (co-occurrence)
- **Average weight**: 0.64

## Ready For

- ✅ Phase 4: Community Detection (Leiden algorithm)
- ✅ Phase 5: Red Flag Extraction
- ✅ Phase 6: Neo4j Import (nodes + edges ready)
- ✅ GraphRAG Local Search (entity-based queries)
- ✅ GraphRAG Global Search (community-based queries)

## Graph Structure

```
Nodes: 2,002 entities
  ├── 990 diseases
  ├── 845 treatments
  ├── 74 signs
  ├── 55 diagnostic tests
  └── 38 symptoms

Edges: 28,941 relationships
  ├── treated_with: 14,738
  ├── associated_with: 8,367
  ├── presents_with: 3,213
  ├── diagnosed_with: 2,518
  └── differential_diagnosis: 105
```

## Scripts Used

Located in `/indexing/`:
- `phase3_extract_relationships.py` - Main extraction script

---
**Generated**: 2025-10-23
**Total Size**: ~5 MB
**Relationships**: 28,941 edges ready for GraphRAG
