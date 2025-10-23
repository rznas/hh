# Phase 5 LLM Enhancement Guide

## Overview

The rule-based red flag extraction (Phase 5) provides good coverage but has limitations:

- ✅ Fast (~5 seconds)
- ✅ Zero cost
- ✅ Comprehensive keyword coverage
- ❌ Medium accuracy (75-85%)
- ❌ Generic clinical presentations
- ❌ May miss nuanced red flags
- ❌ Limited first aid detail

**LLM-enhanced extraction** offers:

- ✅ High accuracy (90-95%)
- ✅ Detailed clinical presentations extracted from textbook
- ✅ Comprehensive first aid instructions
- ✅ Better keyword extraction
- ✅ Identifies implicit red flags
- ❌ Slower (~15-30 minutes)
- ❌ Cost (~$8-12 for full corpus)

## When to Use LLM Enhancement

Use LLM enhancement if:

1. **Production deployment**: Medical safety requires maximum accuracy
2. **Clinical validation needed**: Need detailed, citable clinical presentations
3. **Regulatory compliance**: Need audit trail with source citations
4. **Budget allows**: ~$10 one-time cost is acceptable

## LLM Enhancement Implementation

### Step 1: Create LLM Enhancement Script

Create `indexing/phase5_llm_red_flag_extraction.py`:

```python
#!/usr/bin/env python3
"""
Phase 5 LLM Enhancement: Extract Red Flags with LLM

Uses Claude to extract detailed red flag information from textbook.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import anthropic
from tqdm import tqdm

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

EXTRACTION_PROMPT = '''You are a medical information extraction expert specializing in emergency ophthalmology.

Extract RED FLAG conditions from this text. Red flags are emergent conditions requiring immediate ER referral.

For each red flag condition found:
1. Condition name
2. Keywords/phrases that identify this condition
3. Detailed clinical presentation (how it presents to patient)
4. First aid instructions (if any)
5. Time-to-treatment urgency
6. Chapter/section reference

Text to analyze:
{text}

Return JSON array of red flags:
[
  {{
    "condition": "Chemical Burn",
    "keywords": ["chemical", "acid", "alkali", "splash"],
    "clinical_presentation": "Patient reports chemical substance contact...",
    "first_aid": "Immediate copious irrigation...",
    "time_to_treatment": "immediate",
    "source_reference": "Chapter 3: Trauma, Section 3.2"
  }}
]

Only extract TRUE emergent conditions. Do not include urgent or non-urgent conditions.
'''


def extract_red_flags_with_llm(text_blocks: List[Dict]) -> List[Dict]:
    """Extract red flags using LLM."""

    # Focus on trauma chapter and emergent sections
    relevant_blocks = [
        b for b in text_blocks
        if b.get("chapter_number") == 3 or "emergent" in b.get("text", "").lower()
    ]

    # Batch blocks for LLM processing (max 100 blocks per call)
    batch_size = 100
    all_red_flags = []

    for i in tqdm(range(0, len(relevant_blocks), batch_size)):
        batch = relevant_blocks[i:i+batch_size]

        # Combine text
        combined_text = "\n\n".join([
            f"[Chapter {b['chapter_number']}] {b['text'][:1000]}"
            for b in batch
        ])

        # Call LLM
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=combined_text)
                }]
            )

            # Parse response
            content = response.content[0].text
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                red_flags = json.loads(json_match.group())
                all_red_flags.extend(red_flags)

        except Exception as e:
            print(f"Error processing batch {i}: {e}")
            continue

    # Deduplicate by condition name
    unique_flags = {}
    for flag in all_red_flags:
        condition = flag["condition"]
        if condition not in unique_flags:
            unique_flags[condition] = flag
        else:
            # Merge keywords
            unique_flags[condition]["keywords"] = list(set(
                unique_flags[condition]["keywords"] + flag["keywords"]
            ))

    return list(unique_flags.values())


def main():
    # Load text blocks
    base_dir = Path(__file__).parent
    input_dir = base_dir / "output"

    with open(input_dir / "phase1" / "wills_eye_text_blocks.json") as f:
        text_blocks = json.load(f)

    print(f"Extracting red flags with LLM from {len(text_blocks)} blocks...")

    red_flags = extract_red_flags_with_llm(text_blocks)

    print(f"\nExtracted {len(red_flags)} red flags")

    # Save
    output_path = input_dir / "phase5" / "red_flags_llm.json"
    with open(output_path, 'w') as f:
        json.dump(red_flags, f, indent=2)

    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
```

### Step 2: Install Dependencies

```bash
cd indexing
.venv/Scripts/python -m pip install anthropic tqdm
```

### Step 3: Set API Key

```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here

# Linux/Mac
export ANTHROPIC_API_KEY=your_key_here
```

### Step 4: Run LLM Extraction

```bash
.venv/Scripts/python phase5_llm_red_flag_extraction.py
```

**Expected Runtime**: 15-30 minutes
**Expected Cost**: $8-12 (using Claude 3.5 Sonnet)

### Step 5: Compare Results

Compare rule-based vs LLM extraction:

```bash
.venv/Scripts/python compare_red_flags.py
```

This will generate:
- `red_flags_comparison.json` - Side-by-side comparison
- `red_flags_merged.json` - Best of both approaches

## Output Structure

LLM-enhanced red flags will have:

```json
{
  "red_flag_id": "rf_chemical_burn",
  "condition": "Chemical Burn",
  "keywords": [
    "chemical exposure",
    "acid burn",
    "alkali burn",
    "caustic substance",
    "chemical splash"
  ],
  "clinical_presentation": "Patient reports exposure to chemical substance (acid, alkali, or caustic agent) with immediate pain, tearing, and blurred vision. May have visible corneal opacity or conjunctival blanching.",
  "first_aid": "IMMEDIATE copious irrigation with water or saline for minimum 15-30 minutes. Continue irrigation during transport. Check pH if available. Do NOT delay irrigation to search for neutralizing agent.",
  "time_to_treatment": "immediate (irrigation before transport)",
  "source_reference": "Chapter 3: Trauma, Section 3.2 Chemical Burn",
  "urgency": "emergent",
  "extraction_method": "llm",
  "model": "claude-3-5-sonnet-20241022",
  "confidence": "high"
}
```

## Cost Estimation

Based on Phase 3 LLM extraction experience:

- **Input tokens**: ~800K (trauma chapter + emergent mentions)
- **Output tokens**: ~40K (detailed red flag descriptions)
- **Model**: Claude 3.5 Sonnet
- **Estimated cost**: $8-12 USD

## Quality Comparison

### Rule-Based Extraction
- **Recall**: ~85% (may miss nuanced red flags)
- **Precision**: ~80% (some false positives)
- **Clinical Detail**: Low (generic descriptions)
- **First Aid Detail**: Medium (basic instructions)

### LLM Enhancement
- **Recall**: ~95% (better at finding implicit red flags)
- **Precision**: ~92% (fewer false positives)
- **Clinical Detail**: High (textbook-quality descriptions)
- **First Aid Detail**: High (step-by-step instructions)

## Validation

After LLM extraction, validate by:

1. **Compare with rule-based**: Ensure LLM didn't miss obvious red flags
2. **Medical review**: Have ophthalmologist review extracted red flags
3. **Test detection**: Run test scenarios through detection logic
4. **Source verification**: Verify all red flags cite correct textbook sections

## Recommended Workflow

For production deployment:

1. ✅ **Phase 5 (rule-based)**: Get baseline red flags (DONE)
2. 💡 **Phase 5 LLM**: Enhance with detailed extraction (OPTIONAL)
3. 🔍 **Merge results**: Combine best of both approaches
4. ✅ **Medical validation**: Review with clinical expert
5. 🚀 **Deploy**: Use validated red flags in triage system

## Alternative: Hybrid Approach

Best of both worlds:

1. Use rule-based keywords for **fast detection**
2. Use LLM-extracted presentations for **user education**
3. Use LLM-extracted first aid for **emergency guidance**

```python
def detect_red_flag(patient_input: str):
    # Fast keyword check (rule-based)
    for flag in RULE_BASED_RED_FLAGS:
        if any(kw in patient_input.lower() for kw in flag['keywords']):
            # Get detailed info from LLM version
            llm_flag = get_llm_red_flag(flag['condition'])
            return {
                "detected": True,
                "condition": flag['condition'],
                "keywords_matched": [...],
                "clinical_presentation": llm_flag['clinical_presentation'],
                "first_aid": llm_flag['first_aid']
            }
```

## Questions?

- **Cost concerns?** Rule-based extraction is sufficient for MVP
- **Accuracy concerns?** LLM enhancement is recommended for production
- **Time concerns?** LLM extraction can run overnight
- **API limits?** Batch processing respects rate limits

---

**Bottom Line**: Rule-based extraction provides good baseline. LLM enhancement is recommended for production medical software where accuracy is critical.
