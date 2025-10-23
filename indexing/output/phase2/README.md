# Phase 2 Output - Quick Reference

## Medical Entity Extraction Results (v2)

Extracted **2,002 medical entities** from The Wills Eye Manual (all 14 chapters).

## Files

### Entity Data Files

1. **diseases.json** (990 entities)
   - Clean disease names extracted from differential diagnoses
   - Severity: emergent/urgent/non-urgent/varies
   - Red flag identification: 103 emergent conditions

2. **symptoms.json** (38 entities)
   - Patient-reported symptoms from Chapter 1 and text analysis
   - Keywords: pain, vision loss, photophobia, floaters, etc.

3. **signs.json** (74 entities)
   - Clinician-observed signs from Chapter 2 and text analysis
   - Keywords: redness, swelling, opacity, hemorrhage, etc.

4. **treatments.json** (845 entities)
   - Medications: 602
   - Procedures: 243

5. **diagnostic_tests.json** (55 entities)
   - Imaging: 13
   - Laboratory: 7
   - Functional: 3
   - Examination: 32

### Reports

- **PHASE2_SUMMARY.md** - Comprehensive summary with statistics
- **phase2_1_report.json** - Disease extraction report
- **phase2_2_report.json** - Symptom/sign extraction report
- **phase2_3_report.json** - Treatment extraction report
- **phase2_4_report.json** - Diagnostic test extraction report

## Quick Stats

| Entity Type | Count |
|-------------|-------|
| Diseases | 990 |
| Symptoms | 38 |
| Signs | 74 |
| Treatments | 845 |
| Diagnostic Tests | 55 |
| **TOTAL** | **2,002** |

## Ready For

- ✅ Phase 3.1: Disease-Symptom relationships
- ✅ Phase 3.2: Disease-Treatment relationships
- ✅ Phase 3.3: Differential diagnosis relationships
- ✅ Phase 3.4: Disease-Test associations
- ✅ Phase 5.1: Red flag extraction (103 emergent diseases identified)

## Scripts Used

Located in `/indexing/`:
- `phase2_extract_diseases_v2.py`
- `phase2_extract_symptoms_signs_v2.py`
- `phase2_extract_treatments_v2.py`
- `phase2_extract_diagnostic_tests.py`

---
**Generated**: 2025-10-23
**Total Size**: ~2 MB
**Entities**: 2,002 medical entities ready for GraphRAG
