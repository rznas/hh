# Phase 2 Output - Quick Reference

## Medical Entity Extraction Results

Extracted 475 medical entities from The Wills Eye Manual (Chapters 1-5).

## Files

### Entity Data Files

1. **diseases.json** (180 KB, 395 entities)
   - Disease/condition entities
   - Fields: `entity_id`, `name`, `severity`, `red_flag`, `chapters`, `mention_count`
   - Severity: emergent (109), urgent (286)
   - 91.6% from differential diagnosis lists

2. **symptoms.json** (2 KB, 5 entities)
   - Patient-reported symptoms from Chapter 1
   - Fields: `entity_id`, `name`, `type`, `category`, `associated_conditions`
   - Examples: Pain, Double Vision, Photophobia, Spots/Floaters

3. **signs.json** (4 KB, 9 entities)
   - Clinician-observed signs from Chapter 2
   - Fields: `entity_id`, `name`, `type`, `category`, `associated_conditions`
   - Examples: Corneal Opacity, Proptosis, Injection/Redness

4. **treatments.json** (15 KB, 66 entities)
   - Medications (48) and procedures (18)
   - Fields: `entity_id`, `name`, `type`, `category`, `chapters`, `mention_count`
   - Types: medication, procedure

### Reports

- **PHASE2_SUMMARY.md** - Comprehensive summary with statistics
- **phase2_1_report.json** - Disease extraction report
- **phase2_2_report.json** - Symptom/sign extraction report
- **phase2_3_report.json** - Treatment extraction report

## Quick Stats

| Entity Type | Count |
|-------------|-------|
| Diseases | 395 |
| Symptoms | 5 |
| Signs | 9 |
| Treatments | 66 |
| **TOTAL** | **475** |

### Disease Breakdown
- Emergent (Red Flag): 109
- Urgent: 286
- From DDx Lists: 362 (91.6%)

### Treatment Breakdown
- Medications: 48
- Procedures: 18

## Usage Examples

### Find red flag diseases
```python
import json

with open('diseases.json') as f:
    diseases = json.load(f)

red_flags = [d for d in diseases if d['red_flag']]
print(f"Red flag conditions: {len(red_flags)}")

for disease in red_flags[:5]:
    print(f"- {disease['name']} (Chapter {disease['chapters'][0]})")
```

### List all medications
```python
import json

with open('treatments.json') as f:
    treatments = json.load(f)

medications = [t for t in treatments if t['type'] == 'medication']
print(f"Total medications: {len(medications)}")

for med in medications[:10]:
    print(f"- {med['name']} (mentioned {med['mention_count']}x)")
```

### Find symptoms and their associated conditions
```python
import json

with open('symptoms.json') as f:
    symptoms = json.load(f)

for symptom in symptoms:
    print(f"\n{symptom['name']}:")
    print(f"  Associated: {symptom['associated_conditions'][:3]}")
```

## Entity Schema

### Disease Entity
```json
{
  "entity_id": "disease_001",
  "name": "Keratitis",
  "name_normalized": "keratitis",
  "synonyms": [],
  "icd_10": null,
  "snomed_ct": null,
  "description": "...",
  "chapters": [4],
  "sections": ["Bacterial Keratitis"],
  "severity": "urgent",
  "red_flag": true,
  "from_differential_diagnosis": true,
  "mention_count": 15
}
```

### Symptom/Sign Entity
```json
{
  "entity_id": "symptom_001",
  "name": "Pain",
  "name_normalized": "pain",
  "type": "symptom",
  "category": "ocular",
  "red_flag": false,
  "chapter": 1,
  "section": "Pain",
  "associated_conditions": ["Dry eye", "Keratitis"],
  "variations": []
}
```

### Treatment Entity
```json
{
  "entity_id": "treatment_001",
  "name": "Prednisolone",
  "name_normalized": "prednisolone",
  "type": "medication",
  "category": "pharmacological",
  "chapters": [3, 4, 5],
  "sections": ["Chemical Burn", "Keratitis"],
  "description": "...",
  "mention_count": 12
}
```

## Ready For

- ✅ Phase 3.1: Disease-Symptom relationships
- ✅ Phase 3.2: Disease-Treatment relationships
- ✅ Phase 3.3: Differential diagnosis relationships
- ✅ Phase 5.1: Red flag extraction (109 emergent diseases identified)

## Scripts Used

Located in `/indexing/`:
- `phase2_extract_diseases.py` - Disease entity extraction
- `phase2_extract_symptoms_signs.py` - Symptom/sign extraction
- `phase2_extract_treatments.py` - Treatment/procedure extraction

---
**Generated**: October 22, 2025
**Total Size**: ~200 KB
**Entities**: 475 medical entities ready for GraphRAG
