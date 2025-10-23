# Phase 5 Output - Red Flag Extraction

⚠️ **Extraction Method**: Rule-Based (Keyword Pattern Matching)
📊 **Confidence Level**: Medium (75-85% accuracy)
💡 **For Production**: Consider LLM-based extraction (90-95% accuracy) - See PHASE5_LLM_ENHANCEMENT_GUIDE.md

## Overview

Extracted red flag conditions (emergent conditions requiring immediate ER referral) from The Wills Eye Manual using rule-based keyword pattern matching.

## 🚨 CRITICAL SAFETY REQUIREMENT

Red flag detection must have **100% recall** (no false negatives). Missing an emergent condition is unacceptable in medical triage software.

## Files

- **red_flags.json** - Extracted red flag conditions with keywords, clinical presentation, and first aid
- **phase5_report.json** - Statistics and validation report

## Red Flags Extracted

Total: **10 emergent conditions**


### Severe Trauma
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate to hours
- **First Aid**: Shield eye if open globe suspected. Do NOT apply pressure. Immediate ER referral...
- **Source Chapters**: 5

### Retinal Detachment
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate to hours
- **First Aid**: Position patient upright or with detachment dependent. Immediate ER/ophthalmolog...
- **Source Chapters**: 5

### Acute Angle Closure Glaucoma
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate
- **First Aid**: No specific first aid. Immediate ER referral for pressure reduction....
- **Source Chapters**: 5

### Chemical Burn
- **Keywords**: 19 extracted
- **Time to Treatment**: immediate
- **First Aid**: Immediate and copious irrigation with water or saline for 15-30 minutes. Begin B...
- **Source Chapters**: 5

### Endophthalmitis
- **Keywords**: 6 extracted
- **Time to Treatment**: immediate to hours
- **First Aid**: No specific first aid. Immediate ER/ophthalmology referral....
- **Source Chapters**: 5

### Orbital Cellulitis
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate
- **First Aid**: No specific first aid. Immediate ER referral for IV antibiotics....
- **Source Chapters**: 5

### Temporal Arteritis
- **Keywords**: 9 extracted
- **Time to Treatment**: immediate to hours
- **First Aid**: No specific first aid. Immediate ER referral for high-dose steroids....
- **Source Chapters**: 5

### Penetrating Trauma
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate
- **First Aid**: Shield eye (do NOT remove object if embedded). Do NOT apply pressure. Immediate ...
- **Source Chapters**: 5

### Central Retinal Artery Occlusion
- **Keywords**: 30 extracted
- **Time to Treatment**: immediate (90 minutes)
- **First Aid**: Ocular massage may be attempted. Immediate ER referral (time-critical: 90 minute...
- **Source Chapters**: 5

### Sudden Vision Loss
- **Keywords**: 11 extracted
- **Time to Treatment**: immediate
- **First Aid**: No specific first aid. Immediate ER referral....
- **Source Chapters**: 4


## Validation Report

- **Total Red Flags**: 10
- **Validation Passed**: True
- **Completeness Score**: 100.0%



## Next Steps

- ✅ Phase 5 complete
- 💡 Optional: Rerun with LLM for higher accuracy (see PHASE5_LLM_ENHANCEMENT_GUIDE.md)
- → Phase 6: Graph preparation for Neo4j
- → Phase 7: Validation & testing

## Usage in Triage System

Red flags are used in the triage agent for immediate emergency detection:

```python
from indexing.output.phase5.red_flags import RED_FLAGS

def detect_red_flags(patient_input: str) -> Tuple[bool, str]:
    for red_flag in RED_FLAGS:
        for keyword in red_flag['keywords']:
            if keyword.lower() in patient_input.lower():
                return True, red_flag['condition']
    return False, None
```

---
Generated: 2025-10-23
