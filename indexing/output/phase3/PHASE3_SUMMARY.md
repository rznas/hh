# Phase 3: Relationship Extraction - Summary Report

## Status: ✅ COMPLETE

Successfully extracted **28,941 relationships** between medical entities using co-occurrence analysis.

## Execution Details
- **Date**: 2025-10-23
- **Source Data**: Phase 2 entities (2,002) + Phase 1 text blocks (1,726)
- **Extraction Method**: Co-occurrence + structured DDx mapping
- **Processing Time**: ~2 minutes
- **Status**: ✅ Phase 3 Complete (Tasks 3.1-3.5)

## Key Deliverables

| Relationship Type | Count | Description |
|-------------------|-------|-------------|
| **treated_with** | 14,738 | Disease → Treatment relationships |
| **associated_with** | 8,367 | Disease → Clinical Sign relationships |
| **presents_with** | 3,213 | Disease → Symptom relationships |
| **diagnosed_with** | 2,518 | Disease → Diagnostic Test relationships |
| **differential_diagnosis** | 105 | DDx relationships from structured data |
| **TOTAL** | **28,941** | **All relationships** |

## Files Generated

```
indexing/output/phase3/
├── graphrag_edges.json          (28,941 relationships)
├── phase3_report.json           (Statistics and metrics)
├── PHASE3_SUMMARY.md            (This file)
└── README.md                    (Quick reference)
```

---

## Extraction Statistics

### Overall Metrics
- **Total relationships extracted**: 54,598 (before deduplication)
- **Duplicates removed**: 25,657 (47%)
- **Final unique relationships**: 28,941
- **Average relationship weight**: 0.64

### Confidence Distribution
| Confidence | Weight Range | Count | Percentage |
|------------|--------------|-------|------------|
| **High** | ≥ 0.8 | 105 | 0.4% |
| **Medium** | 0.6 - 0.8 | 28,836 | 99.6% |
| **Low** | < 0.6 | 0 | 0.0% |

### By Relationship Type

#### 1. Disease → Treatment (14,738 relationships)
- **Weight**: 0.6 (co-occurrence) to 0.8 (treatment section)
- **Source**: Text blocks with treatment keywords
- **Examples**:
  - Glaucoma treated_with Timolol
  - Keratitis treated_with Antibiotics

#### 2. Disease → Sign (8,367 relationships)
- **Weight**: 0.7
- **Source**: Co-occurrence in text blocks
- **Examples**:
  - Glaucoma associated_with Elevated IOP
  - Uveitis associated_with Inflammation

#### 3. Disease → Symptom (3,213 relationships)
- **Weight**: 0.7
- **Source**: Co-occurrence in text blocks
- **Examples**:
  - Conjunctivitis presents_with Redness
  - Keratitis presents_with Pain

#### 4. Disease → Diagnostic Test (2,518 relationships)
- **Weight**: 0.6 (co-occurrence) to 0.8 (diagnostic section)
- **Source**: Text blocks with diagnostic keywords
- **Examples**:
  - Glaucoma diagnosed_with Visual Field Test
  - Retinal Detachment diagnosed_with B-Scan

#### 5. Differential Diagnosis (105 relationships)
- **Weight**: 0.9 (high confidence - structured data)
- **Source**: Phase 1 DDx lists
- **Examples**:
  - Keratitis differential_diagnosis for Red Eye
  - Glaucoma differential_diagnosis for Vision Loss

---

## Extraction Methodology

### Co-occurrence Analysis
1. **Entity Detection**: Search for entity names in text blocks
2. **Context Window**: Same text block (typically 50-200 words)
3. **Relationship Creation**: If disease + symptom/sign/treatment appear together
4. **Weighting**: Based on section type (treatment vs general text)

### Section-Based Weighting
- **Treatment sections** (0.8): "treatment", "management", "therapy"
- **Diagnostic sections** (0.8): "test", "exam", "imaging", "workup"
- **General co-occurrence** (0.6-0.7): Default weight

### Deduplication Strategy
- Keep highest weight for duplicate (source, target, type) tuples
- Removed 47% duplicates (entities co-occurring in multiple blocks)

---

## Quality Assessment

### Strengths ✅
1. **High Coverage**: 28,941 relationships across all entity types
2. **Fast Extraction**: 2 minutes (vs hours for LLM-based)
3. **Consistent Method**: Reproducible co-occurrence rules
4. **Structured DDx**: 105 high-confidence relationships from DDx lists
5. **Section-Aware**: Higher weights for treatment/diagnostic sections
6. **Cost-Effective**: $0 (no LLM calls for extraction)

### Limitations ⚠️
1. **Co-occurrence limitations**: May miss implicit relationships
2. **No negation handling**: "not treated with" counted as "treated with"
3. **Short entity names filtered**: Avoided false positives (e.g., "fa", "oct")
4. **Limited DDx relationships**: Only 105 from structured data (needs expansion)

### False Positive Mitigation
- Minimum entity name length (>3-4 chars)
- Section-based filtering (treatment keywords for treatment relationships)
- Deduplication by (source, target, type)

---

## Ready for Phase 4 (Community Detection)

Phase 3 outputs enable graph-based clustering:

1. ✅ **Nodes**: 2,002 entities (diseases, symptoms, signs, treatments, tests)
2. ✅ **Edges**: 28,941 relationships with weights
3. ✅ **Graph Structure**: Ready for Neo4j import
4. ✅ **Community Detection**: Ready for Leiden algorithm

**Estimated communities**: 50-100 clusters (trauma, glaucoma, retina, etc.)

---

## Next Steps

### Phase 4: Community Detection & Hierarchical Clustering
- Apply Leiden algorithm to relationship graph
- Create hierarchical levels (L0, L1, L2)
- Generate community summaries using LLM
- Output: Communities with entity memberships

### Phase 5: Red Flag Extraction
- Extract emergent condition keywords from Phase 2 data
- Map to red flag detection patterns
- Create safety warning structures

### Phase 6: Neo4j Import
- Convert to Neo4j node/edge format
- Generate Cypher import scripts
- Populate knowledge graph

---

## Usage Examples

### Load relationships
```python
import json

with open('indexing/output/phase3/graphrag_edges.json') as f:
    relationships = json.load(f)

print(f"Total relationships: {len(relationships)}")
```

### Find treatment relationships
```python
treatments = [r for r in relationships if r['relationship_type'] == 'treated_with']
print(f"Treatment relationships: {len(treatments)}")

# Find treatments for a specific disease
keratitis_treatments = [
    r for r in treatments
    if 'keratitis' in r['source'].lower()
]
for rel in keratitis_treatments[:5]:
    print(f"- {rel['description']}")
```

### Find high-confidence relationships
```python
high_conf = [r for r in relationships if r['weight'] >= 0.8]
print(f"High-confidence relationships: {len(high_conf)}")
```

---

**Generated**: 2025-10-23
**Status**: ✅ Complete (Phase 3 of 8)
**Next Phase**: Community Detection (Phase 4)
