# Complete Schema Analysis: Node & Edge Type Implementation Status

**Date**: 2025-10-30
**Analysis Type**: Comprehensive audit of all schema types vs actual implementation
**Data Source**: Phase 6 graph preparation output (2,002 nodes, 28,941 edges)

---

## Executive Summary

**Critical Findings**:
- **5 of 15 node types** are actually implemented (33% coverage)
- **5 of 15 edge types** are actually implemented (33% coverage)
- **10 node types** defined but NEVER extracted
- **10 edge types** defined but NEVER created
- **2 undefined types** are being used (`DiagnosticTest`, `diagnosed_with`)

**Impact**: The knowledge graph is missing critical structural relationships and entity types that would enable advanced GraphRAG queries.

---

## Part 1: NODE TYPE ANALYSIS

### Schema Definition (15 types)
From `backend/schema/knowladge_base.py`:

```python
class NodeType(str, Enum):
    DISEASE = "disease"              # Line 6
    SYMPTOM = "symptom"              # Line 7
    SIGN = "sign"                    # Line 8
    TREATMENT = "treatment"          # Line 9
    MEDICATION = "medication"        # Line 10
    PROCEDURE = "procedure"          # Line 11
    ANATOMY = "anatomy"              # Line 12
    ETIOLOGY = "etiology"            # Line 13
    RISK_FACTOR = "risk_factor"      # Line 14
    DIFFERENTIAL = "differential"    # Line 15
    COMPLICATION = "complication"    # Line 16
    LAB_TEST = "lab_test"            # Line 17
    IMAGING = "imaging"              # Line 18
    CHAPTER = "chapter"              # Line 19
    SECTION = "section"              # Line 20
```

### Actual Implementation Status

| Node Type | Schema | Extracted | Count | Files | Status |
|-----------|--------|-----------|-------|-------|--------|
| **DISEASE** | ✅ Yes | ✅ Yes | **990** | diseases.json | ✅ **IMPLEMENTED** |
| **SYMPTOM** | ✅ Yes | ✅ Yes | **38** | symptoms.json | ✅ **IMPLEMENTED** |
| **SIGN** | ✅ Yes | ✅ Yes | **74** | signs.json | ✅ **IMPLEMENTED** |
| **TREATMENT** | ✅ Yes | ✅ Yes | **845** | treatments.json | ✅ **IMPLEMENTED** |
| **MEDICATION** | ✅ Yes | ⚠️ Partial | *Merged* | treatments.json | ⚠️ **MERGED INTO TREATMENT** |
| **PROCEDURE** | ✅ Yes | ⚠️ Partial | *Merged* | treatments.json | ⚠️ **MERGED INTO TREATMENT** |
| **ANATOMY** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **ETIOLOGY** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **RISK_FACTOR** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **DIFFERENTIAL** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **COMPLICATION** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **LAB_TEST** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **IMAGING** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **CHAPTER** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **SECTION** | ✅ Yes | ❌ No | **0** | None | ❌ **NOT EXTRACTED** |
| **DiagnosticTest** | ❌ **NOT IN SCHEMA** | ✅ Yes | **55** | diagnostic_tests.json | ⚠️ **UNDEFINED TYPE USED** |

### Node Type Issues

#### Issue 1.1: MEDICATION and PROCEDURE merged into TREATMENT ⚠️

**Problem**: Phase 2 extraction scripts merge medications and procedures into single "treatment" entity type.

**Evidence**:
- `treatments.json` contains 845 entities
- No separate `medications.json` or `procedures.json` files
- LLM prompt in `phase2_llm_entity_extraction.py` (line 108) lists both as extraction targets but outputs combine them

**Impact**:
- Cannot query specifically for medications vs procedures
- Cannot build medication-specific relationships (e.g., contraindications)
- GraphRAG community detection cannot cluster by intervention type

**Fix Required**: Split extraction logic to create separate files

---

#### Issue 1.2: ANATOMY entities not extracted ❌

**Problem**: No anatomical entities extracted despite being critical for medical knowledge graph.

**Evidence**:
- No `anatomy.json` file exists
- Zero ANATOMY nodes in phase 6 output
- config.py defines 16 anatomical terms (line 166-172) but they're not used in extraction

**Impact**:
- Cannot answer queries like "What diseases affect the cornea?"
- Missing AFFECTS relationships (Disease → Anatomy)
- Cannot build anatomical hierarchy for search

**Data Available**: Wills Eye Manual has extensive anatomical references in every chapter

**Fix Required**:
1. Add ANATOMY to phase 2 LLM extraction prompt
2. Use predefined anatomical terms from config.py as seed list
3. Extract anatomical mentions from all chapters

---

#### Issue 1.3: ETIOLOGY entities not extracted ❌

**Problem**: No causative factors extracted.

**Evidence**:
- No `etiology.json` file
- Zero ETIOLOGY nodes
- Phase 2 LLM prompt mentions "ETIOLOGY: Causes and risk factors" but doesn't extract separately

**Impact**:
- Cannot answer "What causes X disease?"
- Missing CAUSED_BY relationships
- Reduced medical understanding in graph

**Data Available**: Most disease sections in Wills Eye Manual include "Etiology" subsections

**Fix Required**: Add ETIOLOGY as separate extraction target in phase 2

---

#### Issue 1.4: RISK_FACTOR entities not extracted ❌

**Problem**: No risk factors extracted.

**Evidence**:
- No `risk_factors.json` file
- Zero RISK_FACTOR nodes
- Often merged with etiology or ignored

**Impact**:
- Cannot answer "What increases risk for X disease?"
- Missing INCREASES_RISK relationships
- Cannot stratify patient risk in triage

**Fix Required**: Extract risk factors separately from etiology

---

#### Issue 1.5: DIFFERENTIAL entities not extracted ❌

**Problem**: Differential diagnoses are NOT entities, they're relationships.

**Evidence**:
- No `differential.json` file
- Zero DIFFERENTIAL nodes
- Phase 1 has `differential_diagnoses.json` but these are relationships, not entities

**Analysis**: This is likely a **schema design error**. Differential diagnoses are relationships between diseases, not separate entities.

**Fix Required**:
- **Option A**: Remove DIFFERENTIAL from NodeType schema (it's not an entity)
- **Option B**: Create DIFFERENTIAL_DIAGNOSIS_LIST entities (groups of differentials)

**Recommendation**: Option A - Remove from schema, use DIFFERENTIATES edge instead

---

#### Issue 1.6: COMPLICATION entities not extracted ❌

**Problem**: Complications are not extracted as separate entities.

**Evidence**:
- No `complications.json` file
- Zero COMPLICATION nodes
- Complications are often diseases themselves (e.g., "Corneal perforation is a complication of untreated keratitis")

**Analysis**: Complications are usually diseases with COMPLICATES relationships, not separate entity types.

**Fix Required**:
- **Option A**: Remove COMPLICATION from NodeType schema (they're diseases)
- **Option B**: Extract complications and tag with `is_complication=true` property

**Recommendation**: Option A - Remove from schema, use COMPLICATES edge instead

---

#### Issue 1.7: LAB_TEST and IMAGING not extracted (replaced by DiagnosticTest) ⚠️

**Problem**: Schema defines LAB_TEST + IMAGING separately, but extraction uses "DiagnosticTest" (not in schema).

**Evidence**:
- `diagnostic_tests.json` exists with 55 entities
- Phase 6 creates 55 "DiagnosticTest" nodes (not in schema)
- No `lab_tests.json` or `imaging.json` files

**Impact**:
- Schema violation
- Cannot distinguish between lab tests and imaging studies
- Validation failures in phase 7

**Fix Required**: Split `diagnostic_tests.json` into `lab_tests.json` + `imaging.json`

**Implementation**: See SCHEMA_ALIGNMENT_PLAN.md Section 3

---

#### Issue 1.8: CHAPTER and SECTION entities not created ❌

**Problem**: Chapter and section structure is not converted to graph entities.

**Evidence**:
- No `chapters.json` or `sections.json` files
- Zero CHAPTER or SECTION nodes in graph
- Entity properties include `"chapters": [3]` and `"sections": ["Differential Diagnosis"]` but these are NOT converted to nodes with BELONGS_TO edges

**Impact**:
- Cannot query "Show me all diseases in Chapter 3 (Trauma)"
- Cannot build hierarchical knowledge graph
- Cannot use chapter-based community detection
- BELONGS_TO relationships cannot be created

**Data Available**:
- Phase 1 has complete chapter structure in `wills_eye_chapters_structured.json`
- 14 chapters, ~1,086 sections

**Fix Required**:
1. Create phase 2 script to extract CHAPTER and SECTION entities
2. Assign entity IDs (chapter_01, section_3.2.1, etc.)
3. Create BELONGS_TO edges in phase 3 from entity properties
4. Update phase 6 to include these structural nodes

---

## Part 2: EDGE TYPE ANALYSIS

### Schema Definition (15 types)
From `backend/schema/knowladge_base.py`:

```python
class EdgeType(str, Enum):
    PRESENTS_WITH = "presents_with"          # Line 24 - Disease → Symptom
    SHOWS_SIGN = "shows_sign"                # Line 25 - Disease → Sign
    CAUSED_BY = "caused_by"                  # Line 26 - Disease → Etiology
    TREATED_WITH = "treated_with"            # Line 27 - Disease → Treatment
    REQUIRES = "requires"                    # Line 28 - Disease → Procedure/Test
    AFFECTS = "affects"                      # Line 29 - Disease → Anatomy
    INDICATES = "indicates"                  # Line 30 - Symptom → Disease
    DIFFERENTIATES = "differentiates"        # Line 31 - Disease → Differential
    INCREASES_RISK = "increases_risk"        # Line 32 - Risk Factor → Disease
    CONTRAINDICATES = "contraindicates"      # Line 33 - Condition → Treatment
    COMPLICATES = "complicates"              # Line 34 - Disease → Complication
    BELONGS_TO = "belongs_to"                # Line 35 - Disease → Chapter/Section
    SIMILAR_TO = "similar_to"                # Line 36 - Disease → Disease
    ASSOCIATED_WITH = "associated_with"      # Line 37 - Generic association
    TEMPORAL_FOLLOWS = "temporal_follows"    # Line 38 - For progression
```

### Actual Implementation Status

**Phase 6 Graph Statistics**: 28,941 edges across 5 relationship types

| Edge Type | Schema | Extracted | Count | Percentage | Status |
|-----------|--------|-----------|-------|------------|--------|
| **treated_with** | ✅ Yes | ✅ Yes | **14,738** | 50.9% | ✅ **IMPLEMENTED** |
| **associated_with** | ✅ Yes | ✅ Yes (WRONG) | **8,367** | 28.9% | ⚠️ **MISUSED (should be shows_sign)** |
| **presents_with** | ✅ Yes | ✅ Yes | **3,213** | 11.1% | ✅ **IMPLEMENTED** |
| **diagnosed_with** | ❌ **NOT IN SCHEMA** | ✅ Yes | **2,518** | 8.7% | ⚠️ **UNDEFINED TYPE USED** |
| **differential_diagnosis** | ❌ **NOT IN SCHEMA** | ✅ Yes | **105** | 0.4% | ⚠️ **UNDEFINED TYPE USED** |
| **shows_sign** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **caused_by** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **requires** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **affects** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **indicates** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **differentiates** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **increases_risk** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **contraindicates** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **complicates** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **belongs_to** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **similar_to** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |
| **temporal_follows** | ✅ Yes | ❌ No | **0** | 0% | ❌ **NOT EXTRACTED** |

### Edge Type Issues

#### Issue 2.1: shows_sign NOT EXTRACTED (replaced by associated_with) ⚠️

**Problem**: All Disease→Sign relationships incorrectly use `associated_with` instead of `shows_sign`.

**Evidence**:
- 8,367 `associated_with` edges (28.9% of all edges)
- 0 `shows_sign` edges
- Phase 3 scripts (line 100, 157) use `associated_with` for Disease-Sign relationships

**Impact**:
- Medical inaccuracy: "associated_with" is generic, not specific to clinical signs
- Cannot query specifically for clinical signs vs other associations
- GraphRAG cannot differentiate sign-based queries

**Example Wrong Relationship**:
```json
{
  "source": "Keratitis",
  "target": "corneal infiltrate",
  "relationship_type": "associated_with"  // WRONG - should be "shows_sign"
}
```

**Fix Required**: See SCHEMA_ALIGNMENT_PLAN.md Issue 3

---

#### Issue 2.2: caused_by NOT EXTRACTED ❌

**Problem**: No etiology relationships extracted.

**Evidence**:
- 0 `caused_by` edges
- No ETIOLOGY entities (Issue 1.3)

**Impact**:
- Cannot answer "What causes X?"
- Missing causal reasoning in knowledge graph

**Fix Required**:
1. Extract ETIOLOGY entities (Issue 1.3)
2. Add `caused_by` relationship extraction in phase 3
3. LLM prompt: "X is caused by Y" → creates CAUSED_BY edge

---

#### Issue 2.3: requires NOT EXTRACTED (replaced by diagnosed_with) ⚠️

**Problem**: Schema defines `requires` but scripts use `diagnosed_with` (not in schema).

**Evidence**:
- 2,518 `diagnosed_with` edges (8.7% of all edges)
- 0 `requires` edges
- `diagnosed_with` is semantically similar to `requires` but not defined in schema

**Analysis**: `diagnosed_with` is more medically intuitive than generic `requires`.

**Fix Options**:
- **Option A**: Add `DIAGNOSED_WITH` to schema (recommended)
- **Option B**: Map `diagnosed_with` → `REQUIRES` in all scripts

**Recommendation**: Option A - Add to schema (see SCHEMA_ALIGNMENT_PLAN.md Issue 2.1)

---

#### Issue 2.4: affects NOT EXTRACTED ❌

**Problem**: No anatomical relationships extracted.

**Evidence**:
- 0 `affects` edges
- No ANATOMY entities (Issue 1.2)

**Impact**:
- Cannot answer "What diseases affect the cornea?"
- Cannot build anatomical disease maps

**Fix Required**:
1. Extract ANATOMY entities (Issue 1.2)
2. Add `affects` relationship extraction
3. LLM prompt: "X affects Y anatomical structure"

---

#### Issue 2.5: indicates NOT EXTRACTED ❌

**Problem**: No reverse symptom→disease relationships.

**Evidence**:
- 0 `indicates` edges
- Only `presents_with` (Disease→Symptom) exists, not reverse

**Impact**:
- Cannot query "What diseases does this symptom indicate?"
- Graph traversal requires reverse edge computation
- Inefficient for symptom-based triage queries

**Fix Required**:
1. Add phase 3 script to create reverse edges
2. For each `presents_with` edge, create corresponding `indicates` edge
3. Add confidence/probability weights

---

#### Issue 2.6: differentiates NOT EXTRACTED (replaced by differential_diagnosis) ⚠️

**Problem**: Schema defines `differentiates` but scripts use `differential_diagnosis`.

**Evidence**:
- 105 `differential_diagnosis` edges
- 0 `differentiates` edges

**Impact**:
- Schema violation
- Inconsistent naming

**Fix Required**: Rename `differential_diagnosis` → `differentiates` in all scripts

---

#### Issue 2.7: increases_risk NOT EXTRACTED ❌

**Problem**: No risk factor relationships.

**Evidence**:
- 0 `increases_risk` edges
- No RISK_FACTOR entities (Issue 1.4)

**Impact**:
- Cannot answer "What increases risk for X?"
- Missing risk stratification in triage

**Fix Required**:
1. Extract RISK_FACTOR entities (Issue 1.4)
2. Add `increases_risk` extraction

---

#### Issue 2.8: contraindicates NOT EXTRACTED ❌

**Problem**: No contraindication relationships (critical for medical safety).

**Evidence**:
- 0 `contraindicates` edges
- LLM prompt mentions it (line 103) but not extracted

**Impact**:
- **MEDICAL SAFETY RISK**: Cannot warn about contraindicated treatments
- Missing critical clinical decision support

**Fix Required**:
1. Add `contraindicates` extraction in phase 3
2. Add to phase 7 validation (high priority)

---

#### Issue 2.9: complicates NOT EXTRACTED ❌

**Problem**: No complication relationships.

**Evidence**:
- 0 `complicates` edges
- No COMPLICATION entities (Issue 1.6)

**Impact**:
- Cannot answer "What are complications of X?"
- Missing progression/outcome tracking

**Fix Required**:
1. Determine if COMPLICATION nodes needed (see Issue 1.6)
2. Add `complicates` extraction (Disease→Disease)

---

#### Issue 2.10: belongs_to NOT EXTRACTED ❌

**Problem**: No chapter/section structural relationships.

**Evidence**:
- 0 `belongs_to` edges
- No CHAPTER/SECTION entities (Issue 1.8)
- Entity properties store `chapters` and `sections` but not converted to edges

**Impact**:
- Cannot query by chapter/section
- Missing hierarchical structure
- Cannot use book organization for search

**Example Missing Relationship**:
```json
// Current: Property on disease entity
{
  "entity_id": "disease_001",
  "name": "Keratitis",
  "chapters": [4],        // Property, not relationship
  "sections": ["Cornea"]  // Property, not relationship
}

// Should be: Separate edges
{
  "source": "disease_001",
  "target": "chapter_04",
  "relationship_type": "belongs_to"
}
```

**Fix Required**: See Issue 1.8 fix + create edges from properties

---

#### Issue 2.11: similar_to NOT EXTRACTED ❌

**Problem**: No disease similarity relationships.

**Evidence**:
- 0 `similar_to` edges
- Useful for differential diagnosis

**Impact**:
- Cannot find similar diseases
- Reduced differential diagnosis quality

**Fix Required**:
1. Use embedding similarity to create `similar_to` edges
2. Threshold: cosine similarity > 0.85
3. Add in post-processing after phase 6 embeddings

---

#### Issue 2.12: temporal_follows NOT EXTRACTED ❌

**Problem**: No disease progression relationships.

**Evidence**:
- 0 `temporal_follows` edges
- Useful for tracking disease progression

**Impact**:
- Cannot model disease progression
- Missing temporal reasoning

**Example**: "Untreated conjunctivitis → Keratitis → Corneal ulcer"

**Fix Required**:
1. Extract progression statements from text
2. LLM prompt: "X can progress to Y"

---

## Part 3: IMPLEMENTATION COVERAGE SUMMARY

### Node Types: 5/15 Implemented (33% coverage)

**Implemented (5)**:
1. ✅ DISEASE (990 nodes)
2. ✅ SYMPTOM (38 nodes)
3. ✅ SIGN (74 nodes)
4. ✅ TREATMENT (845 nodes) - includes medication + procedure
5. ⚠️ DiagnosticTest (55 nodes) - NOT IN SCHEMA

**Not Implemented (10)**:
1. ❌ MEDICATION (merged into TREATMENT)
2. ❌ PROCEDURE (merged into TREATMENT)
3. ❌ ANATOMY
4. ❌ ETIOLOGY
5. ❌ RISK_FACTOR
6. ❌ DIFFERENTIAL (schema design issue)
7. ❌ COMPLICATION (schema design issue)
8. ❌ LAB_TEST (replaced by DiagnosticTest)
9. ❌ IMAGING (replaced by DiagnosticTest)
10. ❌ CHAPTER
11. ❌ SECTION

### Edge Types: 5/15 Implemented (33% coverage)

**Implemented (5)**:
1. ✅ presents_with (3,213 edges) - Disease → Symptom
2. ⚠️ associated_with (8,367 edges) - MISUSED for Disease → Sign (should be shows_sign)
3. ✅ treated_with (14,738 edges) - Disease → Treatment
4. ⚠️ diagnosed_with (2,518 edges) - NOT IN SCHEMA (should be requires or added to schema)
5. ⚠️ differential_diagnosis (105 edges) - NOT IN SCHEMA (should be differentiates)

**Not Implemented (10)**:
1. ❌ shows_sign (replaced by associated_with)
2. ❌ caused_by
3. ❌ requires (replaced by diagnosed_with)
4. ❌ affects
5. ❌ indicates
6. ❌ differentiates (replaced by differential_diagnosis)
7. ❌ increases_risk
8. ❌ contraindicates ⚠️ **MEDICAL SAFETY RISK**
9. ❌ complicates
10. ❌ belongs_to
11. ❌ similar_to
12. ❌ temporal_follows

---

## Part 4: PRIORITIZED FIX PLAN

### Priority 1: CRITICAL (Medical Safety & Data Integrity)

1. **Fix associated_with → shows_sign** (Issue 2.1)
   - Effort: 2 hours
   - Impact: 8,367 edges (28.9% of graph)
   - Affects: Medical accuracy

2. **Add contraindicates extraction** (Issue 2.8)
   - Effort: 4 hours
   - Impact: Medical safety
   - Affects: Clinical decision support

3. **Split DiagnosticTest → LAB_TEST + IMAGING** (Issue 1.7)
   - Effort: 3 hours
   - Impact: 55 nodes
   - Affects: Schema compliance

4. **Add diagnosed_with to schema OR map to requires** (Issue 2.3)
   - Effort: 1 hour
   - Impact: 2,518 edges (8.7% of graph)
   - Affects: Schema compliance

### Priority 2: HIGH (Enhanced Medical Knowledge)

5. **Extract ANATOMY entities + affects relationships** (Issues 1.2, 2.4)
   - Effort: 6 hours
   - Impact: ~50 anatomy nodes, ~500 affects edges
   - Affects: Anatomical queries

6. **Extract ETIOLOGY entities + caused_by relationships** (Issues 1.3, 2.2)
   - Effort: 5 hours
   - Impact: ~200 etiology nodes, ~400 caused_by edges
   - Affects: Causal reasoning

7. **Create CHAPTER/SECTION entities + belongs_to relationships** (Issues 1.8, 2.10)
   - Effort: 4 hours
   - Impact: 14 chapters + 1,086 sections = 1,100 nodes, ~2,000 belongs_to edges
   - Affects: Hierarchical structure, book organization queries

8. **Rename differential_diagnosis → differentiates** (Issue 2.6)
   - Effort: 1 hour
   - Impact: 105 edges
   - Affects: Naming consistency

### Priority 3: MEDIUM (Enhanced Functionality)

9. **Split TREATMENT → MEDICATION + PROCEDURE** (Issue 1.1)
   - Effort: 5 hours
   - Impact: 845 nodes split into ~400 medications + ~445 procedures
   - Affects: Granular treatment queries

10. **Extract RISK_FACTOR entities + increases_risk relationships** (Issues 1.4, 2.7)
    - Effort: 5 hours
    - Impact: ~150 risk factor nodes, ~300 increases_risk edges
    - Affects: Risk stratification

11. **Create indicates reverse edges** (Issue 2.5)
    - Effort: 2 hours
    - Impact: 3,213 new edges (reverse of presents_with)
    - Affects: Symptom-based queries

12. **Extract complicates relationships** (Issue 2.9)
    - Effort: 4 hours
    - Impact: ~200 complicates edges
    - Affects: Progression tracking

### Priority 4: LOW (Advanced Features)

13. **Create similar_to relationships via embeddings** (Issue 2.11)
    - Effort: 3 hours
    - Impact: ~500 similarity edges
    - Affects: Differential diagnosis suggestions

14. **Extract temporal_follows relationships** (Issue 2.12)
    - Effort: 6 hours
    - Impact: ~100 progression edges
    - Affects: Temporal reasoning

15. **Remove DIFFERENTIAL and COMPLICATION from NodeType schema** (Issues 1.5, 1.6)
    - Effort: 1 hour
    - Impact: Schema cleanup
    - Affects: Design clarity

---

## Part 5: ESTIMATED TOTAL EFFORT

| Priority | Tasks | Effort | New Nodes | New Edges |
|----------|-------|--------|-----------|-----------|
| P1 (Critical) | 4 | ~10 hours | 0 | +2,518 corrected |
| P2 (High) | 4 | ~16 hours | +1,364 | +2,905 |
| P3 (Medium) | 4 | ~16 hours | +995 | +3,713 |
| P4 (Low) | 3 | ~10 hours | 0 | +600 |
| **TOTAL** | **15** | **~52 hours** | **+2,359** | **+9,736** |

**Final Graph Size** (projected):
- Nodes: 2,002 → 4,361 (+118% growth)
- Edges: 28,941 → 38,677 (+34% growth)
- Schema coverage: 33% → 93% (+180% improvement)

---

## Part 6: QUESTIONS FOR STAKEHOLDERS

### Medical Domain Experts
1. Should DIFFERENTIAL and COMPLICATION be entities or just relationship types?
2. Is `diagnosed_with` more intuitive than `requires` for medical users?
3. What anatomical structures are most important for triage?
4. Are contraindications critical enough for Priority 1?

### Engineering Team
1. Should we re-run full extraction pipeline or patch existing data?
2. What's the budget for LLM calls to extract missing entities?
3. Should case normalization happen at extraction or import time?
4. Do we need backward compatibility with existing graph data?

### Product Team
1. Which query types are most important for MVP triage?
2. Is hierarchical chapter/section navigation a requirement?
3. Do we need similarity-based differential diagnosis?
4. What's the timeline tolerance for these fixes?

---

## Part 7: NEXT STEPS

1. ✅ **Review this analysis** with stakeholders
2. ⏸️ **Approve prioritization** and scope
3. ⏸️ **Begin Priority 1 fixes** (critical issues)
4. ⏸️ **Update SCHEMA_ALIGNMENT_PLAN.md** with node type issues
5. ⏸️ **Create migration plan** for existing graph data
6. ⏸️ **Update phase scripts** systematically
7. ⏸️ **Re-run extraction pipeline** with fixes
8. ⏸️ **Validate with phase 7** tests
9. ⏸️ **Deploy to Neo4j** with corrected schema

---

## Appendix A: File References

**Schema**: `backend/schema/knowladge_base.py`
**Entity Data**: `indexing/output/phase2/*.json`
**Relationship Data**: `indexing/output/phase3/graphrag_edges.json`
**Graph Data**: `indexing/output/phase6/graphrag_*.json`
**Reports**: `indexing/output/phase6/phase6_report.json`

**Extraction Scripts**:
- Phase 2: `indexing/output/phase2/scripts/phase2_llm_entity_extraction.py`
- Phase 3: `indexing/output/phase3/scripts/phase3_llm_relationship_extraction.py`
- Phase 6: `indexing/output/phase6/scripts/phase6_prepare_graph.py`

---

**Report Generated**: 2025-10-30
**Analysis Author**: Claude Code
**Review Status**: Pending stakeholder review
