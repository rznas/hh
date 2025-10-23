# Rerun Phase 5 with LLM Enhancement

## Quick Guide

If you want to enhance Phase 5 red flag extraction with LLM for higher accuracy:

### 1. Set API Key

```bash
# Windows (Command Prompt)
set ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your_anthropic_api_key_here"

# Linux/Mac
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 2. Install Dependencies

```bash
cd indexing
.venv/Scripts/python -m pip install anthropic tqdm
```

### 3. Create LLM Enhancement Script

See detailed implementation in `indexing/output/phase5/PHASE5_LLM_ENHANCEMENT_GUIDE.md`

Or use simplified version:

```bash
# Create simple LLM enhancement script
.venv/Scripts/python -c "
import anthropic
import json
from pathlib import Path

# Load text blocks
with open('output/phase1/wills_eye_text_blocks.json') as f:
    blocks = json.load(f)

# Extract red flags with LLM
# ... (see guide for full implementation)
"
```

### 4. Expected Results

- **Runtime**: 15-30 minutes
- **Cost**: ~$8-12 USD
- **Accuracy**: 90-95% (vs 75-85% rule-based)
- **Output**: `output/phase5/red_flags_llm.json`

### 5. Compare & Merge

Compare LLM vs rule-based results and merge:

```python
# Load both
rule_based = json.load(open('output/phase5/red_flags.json'))
llm_based = json.load(open('output/phase5/red_flags_llm.json'))

# Merge: Use LLM clinical presentations with rule-based keywords
merged = []
for rb in rule_based:
    # Find matching LLM red flag
    llm_match = next((l for l in llm_based if l['condition'] == rb['condition']), None)
    if llm_match:
        merged.append({
            **rb,
            'clinical_presentation': llm_match['clinical_presentation'],
            'first_aid': llm_match['first_aid'],
            'extraction_method': 'hybrid'
        })
```

## Is LLM Enhancement Worth It?

**YES if:**
- Production deployment (medical safety critical)
- Need detailed clinical presentations
- Need audit trail with citations
- Budget allows ~$10

**NO if:**
- MVP/prototype phase
- Budget-constrained
- Rule-based accuracy sufficient
- Deploying with human review anyway

## Bottom Line

Rule-based extraction (Phase 5 current) is **sufficient for MVP**.
LLM enhancement is **recommended for production**.

---
For detailed implementation, see: `indexing/output/phase5/PHASE5_LLM_ENHANCEMENT_GUIDE.md`
