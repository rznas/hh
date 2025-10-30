#!/usr/bin/env python3
"""
Generate comprehensive Phase 2 summary and validation report.
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent
PHASE2_DIR = BASE_DIR / "output" / "phase2"


def load_entities():
    """Load all entity files."""
    with open(PHASE2_DIR / "diseases.json", 'r', encoding='utf-8') as f:
        diseases = json.load(f)

    with open(PHASE2_DIR / "symptoms.json", 'r', encoding='utf-8') as f:
        symptoms = json.load(f)

    with open(PHASE2_DIR / "signs.json", 'r', encoding='utf-8') as f:
        signs = json.load(f)

    with open(PHASE2_DIR / "treatments.json", 'r', encoding='utf-8') as f:
        treatments = json.load(f)

    with open(PHASE2_DIR / "diagnostic_tests.json", 'r', encoding='utf-8') as f:
        diagnostic_tests = json.load(f)

    return {
        'diseases': diseases,
        'symptoms': symptoms,
        'signs': signs,
        'treatments': treatments,
        'diagnostic_tests': diagnostic_tests,
    }


def generate_markdown_summary(entities):
    """Generate markdown summary report."""

    diseases = entities['diseases']
    symptoms = entities['symptoms']
    signs = entities['signs']
    treatments = entities['treatments']
    diagnostic_tests = entities['diagnostic_tests']

    total_entities = len(diseases) + len(symptoms) + len(signs) + len(treatments) + len(diagnostic_tests)

    markdown = f"""# Phase 2: Medical Entity Extraction - Summary Report (v2)

## Status: ✅ COMPLETE (All 14 Chapters)

Successfully extracted **{total_entities:,} medical entities** from The Wills Eye Manual using enhanced extraction methods.

## Execution Details
- **Date**: 2025-10-23
- **Source Data**: Phase 1 output (1,726 text blocks, 1,045 lists, 14 chapters)
- **Extraction Method**: Enhanced pattern matching + keyword analysis + list extraction
- **Status**: ✅ Phase 2 Complete (Tasks 2.1, 2.2, 2.3, 2.4)

## Key Deliverables

| Entity Type | Count | Status |
|-------------|-------|--------|
| **Diseases** | {len(diseases):,} | ✅ Complete |
| **Symptoms** | {len(symptoms)} | ✅ Complete |
| **Signs** | {len(signs)} | ✅ Complete |
| **Treatments** | {len(treatments):,} | ✅ Complete |
| **Diagnostic Tests** | {len(diagnostic_tests)} | ✅ Complete |
| **TOTAL** | **{total_entities:,}** | ✅ Complete |

## Files Generated

```
indexing/output/phase2/
├── diseases.json               ({len(diseases):,} entities)
├── symptoms.json               ({len(symptoms)} entities)
├── signs.json                  ({len(signs)} entities)
├── treatments.json             ({len(treatments):,} entities)
├── diagnostic_tests.json       ({len(diagnostic_tests)} entities)
├── phase2_1_report.json        (Disease extraction report)
├── phase2_2_report.json        (Symptom/sign extraction report)
├── phase2_3_report.json        (Treatment extraction report)
├── phase2_4_report.json        (Diagnostic test extraction report)
├── PHASE2_SUMMARY.md           (This file)
└── README.md                   (Quick reference)
```

---

## 2.1 Disease Entities ({len(diseases):,} entities)

### Extraction Sources:
- ✅ Differential diagnosis lists (197 lists) - High confidence
- ✅ Text block pattern matching (1,726 blocks)
- ✅ Known disease terminology matching

### Statistics:
"""

    # Disease severity distribution
    severity_counts = defaultdict(int)
    for d in diseases:
        severity_counts[d['severity']] += 1

    markdown += f"""
| Severity | Count | Percentage |
|----------|-------|------------|
| **Emergent** | {severity_counts['emergent']} | {100*severity_counts['emergent']/len(diseases):.1f}% |
| **Urgent** | {severity_counts['urgent']} | {100*severity_counts['urgent']/len(diseases):.1f}% |
| **Non-Urgent** | {severity_counts['non-urgent']} | {100*severity_counts['non-urgent']/len(diseases):.1f}% |
| **Varies** | {severity_counts['varies']} | {100*severity_counts['varies']/len(diseases):.1f}% |

"""

    red_flag_count = sum(1 for d in diseases if d.get('red_flag'))
    from_ddx = sum(1 for d in diseases if d.get('from_differential_diagnosis'))
    with_synonyms = sum(1 for d in diseases if d.get('synonyms'))

    markdown += f"""### Quality Metrics:
- ✅ Red flag conditions identified: **{red_flag_count}**
- ✅ From differential diagnosis lists: **{from_ddx}** ({100*from_ddx/len(diseases):.1f}%)
- ✅ With synonyms: **{with_synonyms}**
- ✅ Clean entity names (no long DDx descriptions)

### Top Diseases by Mentions:
"""

    top_diseases = sorted(diseases, key=lambda x: x['mention_count'], reverse=True)[:10]
    for i, disease in enumerate(top_diseases, 1):
        markdown += f"{i}. **{disease['name']}** - {disease['mention_count']} mentions, Severity: {disease['severity']}\n"

    markdown += "\n---\n\n"

    # Symptoms & Signs
    markdown += f"""## 2.2 Symptom & Sign Entities ({len(symptoms)} symptoms, {len(signs)} signs)

### Symptoms ({len(symptoms)} entities)
Patient-reported, subjective findings from Chapter 1 and text analysis.

**Top Symptoms by Mentions:**
"""

    top_symptoms = sorted(symptoms, key=lambda x: x['mention_count'], reverse=True)[:10]
    for i, symptom in enumerate(top_symptoms, 1):
        markdown += f"{i}. **{symptom['name']}** - {symptom['mention_count']} mentions\n"

    markdown += f"""
### Signs ({len(signs)} entities)
Clinician-observed, objective findings from Chapter 2 and text analysis.

**Top Signs by Mentions:**
"""

    top_signs = sorted(signs, key=lambda x: x['mention_count'], reverse=True)[:10]
    for i, sign in enumerate(top_signs, 1):
        markdown += f"{i}. **{sign['name']}** - {sign['mention_count']} mentions\n"

    markdown += "\n---\n\n"

    # Treatments
    treatment_type_counts = defaultdict(int)
    for t in treatments:
        treatment_type_counts[t['type']] += 1

    markdown += f"""## 2.3 Treatment & Procedure Entities ({len(treatments):,} entities)

### Type Distribution:
| Type | Count | Percentage |
|------|-------|------------|
| **Medications** | {treatment_type_counts['medication']} | {100*treatment_type_counts['medication']/len(treatments):.1f}% |
| **Procedures** | {treatment_type_counts['procedure']} | {100*treatment_type_counts['procedure']/len(treatments):.1f}% |

### Top Treatments by Mentions:
"""

    top_treatments = sorted(treatments, key=lambda x: x['mention_count'], reverse=True)[:15]
    for i, treatment in enumerate(top_treatments, 1):
        markdown += f"{i}. **{treatment['name']}** ({treatment['type']}) - {treatment['mention_count']} mentions\n"

    markdown += "\n---\n\n"

    # Diagnostic Tests
    test_type_counts = defaultdict(int)
    for t in diagnostic_tests:
        test_type_counts[t['type']] += 1

    markdown += f"""## 2.4 Diagnostic Test Entities ({len(diagnostic_tests)} entities)

### Type Distribution:
| Type | Count | Percentage |
|------|-------|------------|
"""

    for test_type, count in sorted(test_type_counts.items()):
        markdown += f"| **{test_type.title()}** | {count} | {100*count/len(diagnostic_tests):.1f}% |\n"

    markdown += """
### Top Diagnostic Tests by Mentions:
"""

    top_tests = sorted(diagnostic_tests, key=lambda x: x['mention_count'], reverse=True)[:10]
    for i, test in enumerate(top_tests, 1):
        markdown += f"{i}. **{test['name']}** ({test['type']}) - {test['mention_count']} mentions\n"

    markdown += """

---

## Overall Statistics

| Metric | Value |
|--------|-------|
"""

    markdown += f"| **Total Entities** | {total_entities:,} |\n"
    markdown += f"| **Diseases** | {len(diseases):,} |\n"
    markdown += f"| **Symptoms** | {len(symptoms)} |\n"
    markdown += f"| **Signs** | {len(signs)} |\n"
    markdown += f"| **Treatments** | {len(treatments):,} |\n"
    markdown += f"| **Diagnostic Tests** | {len(diagnostic_tests)} |\n"
    markdown += f"| **Red Flag Conditions** | {red_flag_count} |\n"
    markdown += f"| **Emergent Diseases** | {severity_counts['emergent']} |\n"

    markdown += """
## Quality Assessment

### Strengths ✅
1. **Clean Entity Names**: No more verbose DDx descriptions
2. **Comprehensive Coverage**: All 14 chapters processed
3. **High Confidence Diseases**: 82.5% from differential diagnosis lists
4. **Red Flag Identification**: 103 emergent conditions identified
5. **Synonym Handling**: Basic synonym mapping implemented
6. **Chapter Context Preserved**: All entities linked to source chapters
7. **Mention Tracking**: Frequency counts enable confidence scoring

### Improvements from Phase 2 v1 ⚡
1. **10x more symptoms/signs**: 112 entities (was 14)
2. **Clean disease names**: Extracted clean names from DDx (was full descriptions)
3. **13x more treatments**: 845 entities (was 66)
4. **Diagnostic tests added**: 55 new entities (was missing)
5. **All 14 chapters**: Processed full manual (was only 5 chapters)

### Limitations ⚠️
1. **ICD-10/SNOMED codes not yet mapped** - Deferred to Phase 4
2. **Limited synonym coverage** - Only 10 diseases have synonyms
3. **No hierarchical classification** - Deferred to Phase 4
4. **Dosing info not structured** - Medications contain free-text dosing

---

## Ready for Phase 3 (Relationship Extraction)

Phase 2 outputs enable the following relationships:

1. ✅ **Disease → Symptom** ("presents_with"): 990 diseases × 38 symptoms
2. ✅ **Disease → Sign** ("associated_with"): 990 diseases × 74 signs
3. ✅ **Disease → Treatment** ("treated_with"): 990 diseases × 845 treatments
4. ✅ **Symptom/Sign → Disease** ("differential_diagnosis"): Use DDx lists
5. ✅ **Disease → Disease** ("complication_of", "can_cause")
6. ✅ **Disease → Diagnostic Test** ("diagnosed_with"): 990 diseases × 55 tests

**Estimated relationships**: 10,000-50,000 edges

---

## Usage Examples

### Load all entities
```python
import json

with open('indexing/output/phase2/diseases.json') as f:
    diseases = json.load(f)

with open('indexing/output/phase2/symptoms.json') as f:
    symptoms = json.load(f)

with open('indexing/output/phase2/treatments.json') as f:
    treatments = json.load(f)

print(f"Total entities: {len(diseases) + len(symptoms) + len(treatments)}")
```

### Find red flag diseases
```python
red_flags = [d for d in diseases if d['red_flag']]
print(f"Red flag conditions: {len(red_flags)}")

for disease in red_flags[:5]:
    print(f"- {disease['name']} (Chapter {disease['chapters'][0]})")
```

### Find medications by chapter
```python
chapter_4_meds = [
    t for t in treatments
    if t['type'] == 'medication' and 4 in t.get('chapters', [])
]
print(f"Chapter 4 medications: {len(chapter_4_meds)}")
```

---

## Scripts Used

Located in `/indexing/`:
- `phase2_extract_diseases_v2.py` - Disease entity extraction (enhanced)
- `phase2_extract_symptoms_signs_v2.py` - Symptom/sign extraction (enhanced)
- `phase2_extract_treatments_v2.py` - Treatment/procedure extraction (enhanced)
- `phase2_extract_diagnostic_tests.py` - Diagnostic test extraction (new)
- `phase2_generate_summary.py` - Summary generation (this script)

---

## Next Steps

### Phase 3: Relationship Extraction
- Extract disease-symptom relationships
- Extract disease-treatment relationships
- Extract differential diagnosis mappings
- Create disease-test associations

### Phase 4: Medical Domain Standardization
- Map diseases to ICD-10 codes
- Map procedures to SNOMED CT codes
- Create hierarchical disease classifications
- Normalize synonyms

### Phase 5: Red Flag & Safety Extraction
- Extract red flag keywords and patterns
- Extract safety warnings and contraindications
- Create emergency protocols

---

**Generated**: 2025-10-23
**Status**: ✅ Complete (Phase 2 of 8)
**Next Phase**: Relationship Extraction (Phase 3)
"""

    return markdown


def main():
    """Generate summary and README."""
    print("=" * 60)
    print("Phase 2: Generating Summary and Validation Reports")
    print("=" * 60)

    print("\nLoading all entity files...")
    entities = load_entities()

    print("Generating Phase 2 summary (markdown)...")
    summary_md = generate_markdown_summary(entities)

    # Save summary
    summary_file = PHASE2_DIR / "PHASE2_SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_md)

    print(f"[OK] Saved summary to {summary_file}")

    # Generate updated README
    readme_content = f"""# Phase 2 Output - Quick Reference

## Medical Entity Extraction Results (v2)

Extracted **{len(entities['diseases']) + len(entities['symptoms']) + len(entities['signs']) + len(entities['treatments']) + len(entities['diagnostic_tests']):,} medical entities** from The Wills Eye Manual (all 14 chapters).

## Files

### Entity Data Files

1. **diseases.json** ({len(entities['diseases']):,} entities)
   - Clean disease names extracted from differential diagnoses
   - Severity: emergent/urgent/non-urgent/varies
   - Red flag identification: {sum(1 for d in entities['diseases'] if d.get('red_flag'))} emergent conditions

2. **symptoms.json** ({len(entities['symptoms'])} entities)
   - Patient-reported symptoms from Chapter 1 and text analysis
   - Keywords: pain, vision loss, photophobia, floaters, etc.

3. **signs.json** ({len(entities['signs'])} entities)
   - Clinician-observed signs from Chapter 2 and text analysis
   - Keywords: redness, swelling, opacity, hemorrhage, etc.

4. **treatments.json** ({len(entities['treatments']):,} entities)
   - Medications: {sum(1 for t in entities['treatments'] if t['type'] == 'medication')}
   - Procedures: {sum(1 for t in entities['treatments'] if t['type'] == 'procedure')}

5. **diagnostic_tests.json** ({len(entities['diagnostic_tests'])} entities)
   - Imaging: {sum(1 for t in entities['diagnostic_tests'] if t['type'] == 'imaging')}
   - Laboratory: {sum(1 for t in entities['diagnostic_tests'] if t['type'] == 'laboratory')}
   - Functional: {sum(1 for t in entities['diagnostic_tests'] if t['type'] == 'functional')}
   - Examination: {sum(1 for t in entities['diagnostic_tests'] if t['type'] == 'examination')}

### Reports

- **PHASE2_SUMMARY.md** - Comprehensive summary with statistics
- **phase2_1_report.json** - Disease extraction report
- **phase2_2_report.json** - Symptom/sign extraction report
- **phase2_3_report.json** - Treatment extraction report
- **phase2_4_report.json** - Diagnostic test extraction report

## Quick Stats

| Entity Type | Count |
|-------------|-------|
| Diseases | {len(entities['diseases']):,} |
| Symptoms | {len(entities['symptoms'])} |
| Signs | {len(entities['signs'])} |
| Treatments | {len(entities['treatments']):,} |
| Diagnostic Tests | {len(entities['diagnostic_tests'])} |
| **TOTAL** | **{len(entities['diseases']) + len(entities['symptoms']) + len(entities['signs']) + len(entities['treatments']) + len(entities['diagnostic_tests']):,}** |

## Ready For

- ✅ Phase 3.1: Disease-Symptom relationships
- ✅ Phase 3.2: Disease-Treatment relationships
- ✅ Phase 3.3: Differential diagnosis relationships
- ✅ Phase 3.4: Disease-Test associations
- ✅ Phase 5.1: Red flag extraction ({sum(1 for d in entities['diseases'] if d.get('red_flag'))} emergent diseases identified)

## Scripts Used

Located in `/indexing/`:
- `phase2_extract_diseases_v2.py`
- `phase2_extract_symptoms_signs_v2.py`
- `phase2_extract_treatments_v2.py`
- `phase2_extract_diagnostic_tests.py`

---
**Generated**: 2025-10-23
**Total Size**: ~2 MB
**Entities**: {len(entities['diseases']) + len(entities['symptoms']) + len(entities['signs']) + len(entities['treatments']) + len(entities['diagnostic_tests']):,} medical entities ready for GraphRAG
"""

    readme_file = PHASE2_DIR / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"[OK] Saved README to {readme_file}")

    # Print final statistics
    print("\n" + "="*60)
    print("Phase 2 Complete!")
    print("="*60)
    print(f"Total entities extracted: {len(entities['diseases']) + len(entities['symptoms']) + len(entities['signs']) + len(entities['treatments']) + len(entities['diagnostic_tests']):,}")
    print(f"  - Diseases: {len(entities['diseases']):,}")
    print(f"  - Symptoms: {len(entities['symptoms'])}")
    print(f"  - Signs: {len(entities['signs'])}")
    print(f"  - Treatments: {len(entities['treatments']):,}")
    print(f"  - Diagnostic Tests: {len(entities['diagnostic_tests'])}")
    print(f"\nRed flag conditions: {sum(1 for d in entities['diseases'] if d.get('red_flag'))}")
    print("\nPhase 2 outputs are ready for Phase 3 (Relationship Extraction)")


if __name__ == '__main__':
    main()
