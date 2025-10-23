# Phase 4 Extraction Method Flags

**Date**: 2025-10-23
**Purpose**: Document all flags indicating rule-based extraction method

---

## Overview

All Phase 4 outputs now include flags indicating that the urgency classification was performed using a **rule-based (keyword matching)** approach rather than LLM-based semantic analysis.

---

## Flags Added

### 1. Urgency Classification Criteria (`urgency_classification_criteria.json`)

**Location**: Root level `_metadata` object

```json
{
  "_metadata": {
    "extraction_method": "rule_based",
    "extraction_approach": "keyword_matching",
    "note": "For production use, consider LLM-based extraction for higher accuracy (90-95% vs 75-85%)",
    "llm_guide": "See PHASE4_LLM_ENHANCEMENT_GUIDE.md for LLM-based rerun instructions"
  },
  "emergent": { ... },
  "urgent": { ... },
  "non_urgent": { ... }
}
```

### 2. Disease Entities (`diseases_with_urgency.json`)

**Location**: Each disease object

```json
{
  "entity_id": "disease_001",
  "name": "Nongranulomatous Anterior Uveitis",
  "urgency_level": "urgent",
  "urgency_source": "Extracted from Wills Eye Manual based on urgent criteria",
  "urgency_extraction_method": "rule_based",
  "urgency_confidence": "medium",
  ...
}
```

**New fields**:
- `urgency_extraction_method`: "rule_based"
- `urgency_confidence`: "medium" (vs "high" for LLM)

### 3. Phase 4 Report (`phase4_report.json`)

**Location**: Root level

```json
{
  "phase": "4: Medical Domain Standardization (Urgency Classification)",
  "extraction_method": "rule_based",
  "extraction_approach": "keyword_matching",
  "confidence_level": "medium",
  "note": "For production use, consider LLM-based extraction for higher accuracy (90-95% vs 75-85%)",
  "llm_enhancement_guide": "See PHASE4_LLM_ENHANCEMENT_GUIDE.md",
  ...
}
```

### 4. README.md

**Location**: Top of file

```markdown
# Phase 4 Output - Urgency Classification

⚠️ **Extraction Method**: Rule-Based (Keyword Matching)
📊 **Confidence Level**: Medium (75-85% accuracy)
💡 **For Production**: Consider LLM-based extraction (90-95% accuracy) - See PHASE4_LLM_ENHANCEMENT_GUIDE.md
```

---

## Flag Meanings

### `extraction_method: "rule_based"`
- Indicates classification was performed using pattern matching
- No LLM/AI was used in the extraction
- Deterministic approach based on keyword lists

### `extraction_approach: "keyword_matching"`
- Specific technique: regex pattern matching against predefined keyword lists
- Co-occurrence analysis between diseases and urgency keywords
- Section-aware weighting

### `confidence_level: "medium"`
- Estimated accuracy: 75-85%
- Appropriate for prototyping and initial development
- For production, consider LLM enhancement (90-95% accuracy)

---

## Comparison: Rule-Based vs LLM

| Aspect | Rule-Based (Current) | LLM-Based (Optional) |
|--------|---------------------|----------------------|
| **Method Flag** | `rule_based` | `llm_enhanced` |
| **Confidence** | `medium` | `high` |
| **Accuracy** | 75-85% | 90-95% |
| **Speed** | Fast (~5 seconds) | Slower (~15-20 min) |
| **Cost** | $0 | ~$3-5 |
| **Evidence** | Keyword matches | Direct textbook quotes |
| **Reasoning** | Pattern-based | Semantic understanding |

---

## Usage in Code

### Check Extraction Method

```python
import json

# Load criteria
criteria = json.load(open('urgency_classification_criteria.json'))

# Check method
if criteria['_metadata']['extraction_method'] == 'rule_based':
    print("⚠️  Using rule-based classifications")
    print(f"   Confidence: {criteria['_metadata']['extraction_approach']}")
```

### Filter Diseases by Confidence

```python
# Load diseases
diseases = json.load(open('diseases_with_urgency.json', encoding='utf-8'))

# Get high-confidence classifications (none in rule-based)
rule_based = [d for d in diseases if d.get('urgency_extraction_method') == 'rule_based']
print(f"Rule-based classifications: {len(rule_based)} ({len(rule_based)/len(diseases)*100:.1f}%)")

# For production, you might want to flag these for review
medium_confidence = [d for d in diseases if d.get('urgency_confidence') == 'medium']
print(f"Medium confidence (review recommended): {len(medium_confidence)}")
```

### Display Warning in UI

```python
def get_urgency_warning(disease):
    if disease.get('urgency_extraction_method') == 'rule_based':
        return {
            "level": "info",
            "message": "Urgency classification based on keyword matching. For critical decisions, consult a medical professional."
        }
    elif disease.get('urgency_confidence') == 'medium':
        return {
            "level": "warning",
            "message": "Medium confidence classification. Clinical judgment recommended."
        }
    return None
```

---

## When to Rerun with LLM

### Indicators for LLM Enhancement

✅ **Rerun with LLM if**:
1. Deploying to production
2. Medical accuracy is critical (patient safety)
3. Need detailed evidence/reasoning for each classification
4. Regulatory audit trail required
5. Budget allows (~$3-5 one-time cost)

❌ **Stick with rule-based if**:
1. Prototyping or MVP development
2. Budget constraints (zero cost)
3. Offline/air-gapped environment
4. Current accuracy acceptable for use case
5. Rapid iteration needed (5 seconds vs 20 minutes)

---

## Upgrading to LLM

### Step 1: Set API Key
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Step 2: Install Dependencies
```bash
cd indexing
.venv/Scripts/pip install anthropic tqdm
```

### Step 3: Run LLM Enhancement
```bash
# Create LLM version (saved separately)
.venv/Scripts/python phase4_llm_urgency_extraction.py

# Output: phase4_llm/diseases_with_urgency_llm.json
```

### Step 4: Compare Results
```bash
# Compare rule-based vs LLM
.venv/Scripts/python scripts/compare_phase4_methods.py

# Shows disagreements and confidence levels
```

### Step 5: Choose Version
- Keep rule-based for development: `phase4/diseases_with_urgency.json`
- Use LLM for production: `phase4_llm/diseases_with_urgency_llm.json`

---

## Validation Checklist

When using rule-based classifications:

- [ ] Users are informed of extraction method (show flags)
- [ ] Medium confidence is acknowledged in UI/docs
- [ ] Critical decisions verified by medical professional
- [ ] Emergent conditions manually reviewed (red flags)
- [ ] Audit trail includes extraction method
- [ ] Consider LLM upgrade for production deployment

---

## References

- **LLM Enhancement Guide**: `PHASE4_LLM_ENHANCEMENT_GUIDE.md`
- **Phase 4 Summary**: `PHASE4_SUMMARY.md`
- **Quick Start**: `QUICK_START.md`
- **Medical Framework**: `../../docs/medical/framework.md`

---

## Summary

All Phase 4 outputs now clearly indicate:
- ✅ Extraction method: **Rule-based**
- ✅ Confidence level: **Medium (75-85%)**
- ✅ Alternative: **LLM-based available** (90-95% accuracy)
- ✅ Upgrade path: **See PHASE4_LLM_ENHANCEMENT_GUIDE.md**

This transparency ensures users and developers understand the limitations and can make informed decisions about production deployment.

---

**Generated**: 2025-10-23
**Version**: 1.0
**Status**: All flags in place ✅
