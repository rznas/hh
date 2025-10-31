# Phase 7 Output - Knowledge Graph Validation & Testing

✅ **Status**: Phase 7 Complete

## Overview

Validates the quality and medical accuracy of the knowledge graph created in Phase 6. Ensures data integrity, medical consistency, and readiness for Neo4j deployment.

## Files Generated

### Validation Reports

- **entity_validation_report.json** - Entity data quality validation
- **relationship_validation_report.json** - Relationship data quality validation
- **red_flag_validation_report.json** - Red flag condition validation
- **urgency_validation_report.json** - Urgency classification validation
- **medical_consistency_report.json** - Medical consistency checks
- **phase7_summary_report.json** - Combined summary of all validations

### Scripts

All scripts located in `scripts/` directory:
- **phase7_validate_data_quality.py** - Data quality validation
- **phase7_validate_medical_accuracy.py** - Medical accuracy validation
- **phase7_generate_summary.py** - Summary report generation

## Quick Start

### Run All Validations

```bash
cd indexing

# 1. Data quality validation
.venv/bin/python output/phase7/scripts/phase7_validate_data_quality.py

# 2. Medical accuracy validation
.venv/bin/python output/phase7/scripts/phase7_validate_medical_accuracy.py

# 3. Generate summary
.venv/bin/python output/phase7/scripts/phase7_generate_summary.py
```

## Validation Results Summary

### Overall Status: FAIL (with warnings)

While the knowledge graph is structurally sound, there are areas requiring attention before production deployment.

### Data Quality (Phase 7.1)

**Entity Validation:**
- ✅ 2,002 total entities
- ✅ All entity IDs are unique (no duplicates)
- ✅ 1,889 entities validated successfully (94.4%)
- ⚠ 113 entities with incomplete properties (5.6%)
  - Missing descriptions (primarily symptoms and signs)

**Relationship Validation:**
- ✅ 28,941 total relationships
- ✅ 28,836 relationships validated successfully (99.6%)
- ⚠ 105 relationships with issues (0.4%)
  - 10 orphaned edges (missing source or target nodes)
  - Valid directionality for all checked relationships
  - No circular relationships found

### Medical Accuracy (Phase 7.2)

**Red Flag Validation:**
- ⚠ 50.0% coverage of source red flags
- ⚠ 103 red flags in graph vs 10 in source
- ⚠ 5 missing from graph: "sudden vision loss", "temporal arteritis", "severe trauma", "acute angle closure glaucoma", "endophthalmitis"
- ⚠ 20 critical issues (red flags not marked as emergent)

**Urgency Classification:**
- ✅ All 990 diseases have urgency levels
- Distribution:
  - Emergent: 380 (38.4%)
  - Urgent: 147 (14.8%)
  - Non-urgent: 463 (46.8%)
- ⚠ 20 critical issues (urgency inconsistencies)

**Medical Consistency:**
- ✅ 624 diseases have symptoms (63.0%)
- ✅ 567 diseases have treatments (57.3%)
- ⚠ 366 diseases without symptoms (37.0%)
- ⚠ 423 diseases without treatments (42.7%)

## Key Findings

### Strengths

1. **Excellent structural integrity**: No duplicate IDs, valid relationships
2. **Comprehensive urgency coverage**: All diseases classified
3. **High validation rate**: >94% entities and >99% relationships validated
4. **Good medical coverage**: Most diseases have symptoms and treatments

### Issues Requiring Attention

1. **Incomplete entity properties** (113 entities)
   - Symptoms and signs missing descriptions
   - Quick fix: Add descriptions from source text

2. **Orphaned relationships** (10 edges)
   - Edges referencing non-existent nodes
   - Needs investigation: data extraction bug?

3. **Red flag coverage gaps** (50%)
   - Only 5 of 10 source red flags captured
   - Critical for patient safety
   - Action: Re-run Phase 5 with improved extraction

4. **Urgency inconsistencies** (20 critical)
   - Some red flags not marked as "emergent"
   - Action: Cross-reference Phase 4 and Phase 5 outputs

## Detailed Validation Checks

### Phase 7.1: Data Quality

**Entity Checks:**
- ✓ Duplicate ID detection
- ✓ Required fields validation (id, label, type, properties)
- ✓ Property completeness (description, chapters)
- ✓ Description quality (length > 10 characters)
- ✓ Chapter references (non-empty)

**Relationship Checks:**
- ✓ Orphaned edge detection (missing source/target)
- ✓ Relationship directionality validation
- ✓ Circular relationship detection
- ✓ Node type compatibility

### Phase 7.2: Medical Accuracy

**Red Flag Checks:**
- ✓ Coverage vs source (Phase 5 red_flags.json)
- ✓ Red flag urgency consistency (should be emergent)
- ✓ Source citation presence
- ✓ False positive/negative analysis

**Urgency Checks:**
- ✓ Valid urgency levels (emergent, urgent, non-urgent)
- ✓ Source citation presence
- ✓ Red flag consistency (red flags must be emergent)
- ✓ Distribution analysis

**Consistency Checks:**
- ✓ Diseases have symptoms
- ✓ Diseases have treatments
- ✓ Medical relationship coherence

## Recommendations

### Priority 1: Critical (Patient Safety)

1. **Improve red flag coverage to 100%**
   - Re-run Phase 5.1 with improved LLM prompts
   - Manually validate against Wills Eye Manual Chapter 3
   - Target: 10/10 red flags captured with 0 false negatives

2. **Fix urgency inconsistencies**
   - All red flags must be "emergent"
   - Cross-reference Phase 4 and Phase 5 data
   - Validate against medical framework (docs/medical/framework.md)

### Priority 2: High (Data Quality)

3. **Add descriptions for symptoms and signs**
   - Extract from Phase 1 structured text
   - Use LLM to generate concise descriptions
   - Improves semantic search quality

4. **Fix orphaned relationships**
   - Investigate data extraction pipeline
   - Re-run Phase 3 if necessary
   - Validate entity IDs match between phases

### Priority 3: Medium (Completeness)

5. **Expand disease coverage**
   - 366 diseases without symptoms
   - 423 diseases without treatments
   - May be incomplete entities or extraction gaps

6. **Validate medical codes**
   - Check ICD-10 and SNOMED CT codes
   - Ensure standardization compliance

## Usage Examples

### Check Specific Entity

```bash
# Find entity with ID
jq '.[] | select(.id == "disease_001")' output/phase6/graphrag_nodes.json

# Check entity validation
jq '.validation.statistics.incomplete_properties[] | select(.id == "symptom_001")' \
   output/phase7/entity_validation_report.json
```

### Check Relationship Issues

```bash
# Find orphaned edges
jq '.validation.statistics.orphaned_edges' \
   output/phase7/relationship_validation_report.json

# Check invalid directionality
jq '.validation.statistics.invalid_directionality' \
   output/phase7/relationship_validation_report.json
```

### Check Red Flags

```bash
# List missing red flags
jq '.validation.statistics.missing_red_flags' \
   output/phase7/red_flag_validation_report.json

# List red flag issues
jq '.validation.issues[] | select(.type == "red_flag_urgency_mismatch")' \
   output/phase7/red_flag_validation_report.json
```

## Next Steps

### Immediate Actions

1. **Fix critical issues**
   - Address red flag coverage gaps
   - Fix urgency inconsistencies
   - Resolve orphaned relationships

2. **Re-run validation**
   - After fixes, re-run all validation scripts
   - Target: All validations PASS

### Phase 8: Final Deliverables

Once validation passes:

1. **Create test scenarios** (Phase 7.3)
   - Symptom → disease queries
   - Treatment → disease queries
   - Red flag detection test cases

2. **Test Neo4j import** (Phase 8.1)
   - Import nodes and relationships
   - Create indexes
   - Benchmark query performance

3. **Generate final deliverables** (Phase 8.2)
   - Complete dataset export
   - Documentation
   - Query pattern examples

## Troubleshooting

### "Validation FAIL" status

**Normal for first run.** Knowledge graphs require iterative refinement:
1. Review specific issues in detailed reports
2. Fix issues in source data or extraction scripts
3. Re-run affected phases
4. Re-run validation

### High number of incomplete properties

Check Phase 2 entity extraction:
```bash
# Check symptom entities
jq '.[] | select(.id | startswith("symptom_"))' output/phase2/symptoms.json | head
```

If descriptions missing in Phase 2, re-run entity extraction.

### Orphaned relationships

Check Phase 3 relationship extraction:
```bash
# Find orphaned edge
jq '.validation.statistics.orphaned_edges[0]' \
   output/phase7/relationship_validation_report.json

# Check if node exists
jq --arg id "disease_123" '.[] | select(.id == $id)' \
   output/phase6/graphrag_nodes.json
```

If node missing, check Phase 2 entity extraction.

### Red flag coverage low

Re-run Phase 5.1 with improved extraction:
```bash
cd indexing
.venv/bin/python output/phase5/scripts/phase5_extract_red_flags.py
```

## Performance

**Validation time:** ~5-10 seconds for 2K nodes + 29K edges

**Memory usage:** ~200 MB (loads full graph into memory)

**Disk usage:** ~100 KB (all reports combined)

## Medical Safety Compliance

### Validation Coverage

✅ All red flag conditions checked against source
✅ All urgency classifications validated
✅ Medical consistency verified
✅ Source citations tracked

### Patient Safety Priorities

🔴 **CRITICAL**: Red flag coverage must reach 100% before production
🟡 **HIGH**: Urgency inconsistencies must be resolved
🟢 **MEDIUM**: Entity completeness desirable but not blocking

## Phase 7 Complete ✓

**Validation Status:** FAIL (requires fixes before Phase 8)

**Ready for:**
- Issue resolution
- Data refinement
- Re-validation

**Next Phase:**
- Phase 7 fixes (iterative)
- Phase 8: Final deliverables (after validation passes)

---

Generated: 2025-10-30
Validated: 2,002 nodes, 28,941 edges
