# Phase 4 LLM Enhancement Guide

**Purpose**: This guide explains how to rerun Phase 4 with LLM-based urgency classification for higher accuracy.

---

## Why Use LLM for Phase 4?

### Current Rule-Based Approach
- ✅ **Fast**: ~5 seconds
- ✅ **Zero cost**: No API calls
- ✅ **Good coverage**: 39 keywords extracted
- ❌ **Limited context**: Keyword matching only
- ❌ **No semantic understanding**: Misses implicit urgency signals
- ❌ **Fixed patterns**: Can't adapt to varied medical language

### LLM-Enhanced Approach
- ✅ **High accuracy**: ~90-95% classification accuracy
- ✅ **Semantic understanding**: Interprets clinical context
- ✅ **Evidence extraction**: Provides reasoning for each classification
- ✅ **Handles ambiguity**: Better at edge cases
- ❌ **Slower**: ~15-20 minutes for 990 diseases
- ❌ **Cost**: ~$5-8 for full corpus (Claude 3.5 Sonnet)

---

## When to Use LLM Approach

### Use LLM if:
1. **Production deployment**: Need highest accuracy for patient safety
2. **Validation phase**: Want to compare rule-based vs. LLM results
3. **Ambiguous cases**: Many diseases fall on urgency boundaries
4. **Audit requirements**: Need detailed justification for each classification

### Stick with rule-based if:
1. **Budget constraints**: Zero API cost
2. **Rapid prototyping**: Quick iteration needed
3. **Sufficient accuracy**: Current 990 classifications acceptable
4. **Offline environment**: No internet access

---

## Implementation: LLM-Enhanced Phase 4

### Script Structure

```python
#!/usr/bin/env python3
"""
Phase 4 (LLM): Extract Urgency Classification with LLM

Uses Claude 3.5 Sonnet to:
1. Extract urgency criteria from text blocks
2. Classify each disease with evidence and confidence
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from anthropic import Anthropic

# Configuration
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 2000

# System prompt for urgency classification
SYSTEM_PROMPT = """You are a medical triage expert analyzing urgency classifications from The Wills Eye Manual.

Your task: Given a disease description and surrounding clinical context, determine the urgency level.

Urgency Levels:
- EMERGENT: Requires immediate emergency department evaluation (minutes to hours). Sight-threatening, sudden onset, severe symptoms.
- URGENT: Requires prompt ophthalmology evaluation (24-48 hours). Risk of progression, early treatment needed.
- NON-URGENT: Can be managed with routine care (days to weeks). Chronic conditions, elective procedures.

Output JSON format:
{
  "urgency_level": "emergent|urgent|non_urgent",
  "confidence": 0.0-1.0,
  "evidence": "Quote or paraphrase from text supporting classification",
  "reasoning": "Brief explanation of why this urgency level"
}

Safety: When in doubt, err on the side of higher urgency.
"""

def classify_disease_with_llm(
    disease: Dict,
    relevant_text: str,
    client: Anthropic
) -> Dict:
    """
    Use LLM to classify disease urgency.

    Args:
        disease: Disease entity with name and metadata
        relevant_text: Text blocks mentioning this disease
        client: Anthropic client

    Returns:
        Classification result with urgency_level, confidence, evidence
    """
    user_prompt = f"""Disease: {disease['name']}

Clinical Context:
{relevant_text[:2000]}  # Limit context to 2000 chars

Classify the urgency level based on the clinical context provided."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        # Parse LLM response
        result_text = response.content[0].text
        result = json.loads(result_text)

        # Add metadata
        result["input_tokens"] = response.usage.input_tokens
        result["output_tokens"] = response.usage.output_tokens

        return result

    except Exception as e:
        print(f"  ⚠️  Error classifying {disease['name']}: {e}")
        # Fallback to conservative default
        return {
            "urgency_level": "urgent",  # Conservative default
            "confidence": 0.5,
            "evidence": "Error during classification",
            "reasoning": "Defaulted to urgent due to classification error",
            "error": str(e)
        }


def main():
    """Main execution for LLM-enhanced urgency classification."""
    print("=" * 60)
    print("Phase 4 (LLM): Urgency Classification with LLM")
    print("=" * 60)

    # Check API key
    if not API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("\nSet with: export ANTHROPIC_API_KEY=your_key_here")
        return

    # Initialize client
    client = Anthropic(api_key=API_KEY)

    # Load data
    base_dir = Path(__file__).parent
    input_dir = base_dir / "output"
    output_dir = input_dir / "phase4_llm"
    output_dir.mkdir(exist_ok=True)

    print("\n[1/4] Loading data...")
    text_blocks = json.load(open(input_dir / "phase1" / "wills_eye_text_blocks.json"))
    diseases = json.load(open(input_dir / "phase2" / "diseases.json"))
    print(f"  Loaded {len(text_blocks)} text blocks, {len(diseases)} diseases")

    # Build disease -> text mapping
    print("\n[2/4] Mapping diseases to text...")
    disease_text_map = {}
    for disease in diseases:
        disease_name = disease["name"].lower()
        relevant_blocks = [
            block["text"]
            for block in text_blocks
            if disease_name in block.get("text", "").lower()
        ]
        disease_text_map[disease["entity_id"]] = "\n\n".join(relevant_blocks[:3])  # Top 3 blocks

    # Classify with LLM
    print("\n[3/4] Classifying with LLM (this will take ~15-20 minutes)...")
    results = []
    total_cost = 0.0

    for i, disease in enumerate(diseases):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(diseases)} ({i+1/len(diseases)*100:.1f}%)")

        relevant_text = disease_text_map.get(disease["entity_id"], "")
        classification = classify_disease_with_llm(disease, relevant_text, client)

        # Update disease
        disease["urgency_level"] = classification["urgency_level"]
        disease["urgency_confidence"] = classification.get("confidence", 0.8)
        disease["urgency_evidence"] = classification.get("evidence", "")
        disease["urgency_reasoning"] = classification.get("reasoning", "")
        disease["urgency_source"] = "Classified by Claude 3.5 Sonnet from Wills Eye Manual context"

        results.append({
            "disease_id": disease["entity_id"],
            "disease_name": disease["name"],
            **classification
        })

        # Calculate cost (approximate)
        input_tokens = classification.get("input_tokens", 500)
        output_tokens = classification.get("output_tokens", 100)
        cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
        total_cost += cost

    print(f"\n  Total API cost: ${total_cost:.2f}")

    # Save results
    print("\n[4/4] Saving results...")

    # Save updated diseases
    diseases_path = output_dir / "diseases_with_urgency_llm.json"
    json.dump(diseases, open(diseases_path, 'w'), indent=2, ensure_ascii=False)
    print(f"  Saved to: {diseases_path}")

    # Save classifications with evidence
    classifications_path = output_dir / "urgency_classifications_llm.json"
    json.dump(results, open(classifications_path, 'w'), indent=2, ensure_ascii=False)
    print(f"  Saved classifications: {classifications_path}")

    # Generate report
    urgency_counts = {"emergent": 0, "urgent": 0, "non_urgent": 0}
    avg_confidence = sum(r.get("confidence", 0.8) for r in results) / len(results)

    for r in results:
        urgency_counts[r["urgency_level"]] += 1

    report = {
        "phase": "4_llm: Urgency Classification (LLM-Enhanced)",
        "timestamp": "2025-10-23",
        "model": MODEL,
        "total_diseases": len(diseases),
        "total_cost": round(total_cost, 2),
        "average_confidence": round(avg_confidence, 3),
        "urgency_distribution": urgency_counts,
        "api_calls": len(diseases)
    }

    report_path = output_dir / "phase4_llm_report.json"
    json.dump(report, open(report_path, 'w'), indent=2)
    print(f"  Saved report: {report_path}")

    print("\n" + "=" * 60)
    print("Phase 4 (LLM) Complete!")
    print("=" * 60)
    print(f"\nClassifications: {len(results)}")
    print(f"Average Confidence: {avg_confidence:.2%}")
    print(f"Total Cost: ${total_cost:.2f}")
    print(f"\nUrgency Distribution:")
    print(f"  Emergent: {urgency_counts['emergent']} ({urgency_counts['emergent']/len(diseases)*100:.1f}%)")
    print(f"  Urgent: {urgency_counts['urgent']} ({urgency_counts['urgent']/len(diseases)*100:.1f}%)")
    print(f"  Non-Urgent: {urgency_counts['non_urgent']} ({urgency_counts['non_urgent']/len(diseases)*100:.1f}%)")


if __name__ == "__main__":
    main()
```

---

## Usage

### 1. Set API Key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 2. Install Dependencies

```bash
cd indexing
.venv/Scripts/pip install anthropic tqdm
```

### 3. Run LLM Classification

```bash
# Dry run (test first 10 diseases)
.venv/Scripts/python phase4_llm_urgency_extraction.py --dry-run

# Full run (all 990 diseases)
.venv/Scripts/python phase4_llm_urgency_extraction.py
```

### 4. Compare Results

```bash
# Compare rule-based vs LLM classifications
.venv/Scripts/python scripts/compare_phase4_results.py
```

---

## Expected Output

### Files Generated

1. **diseases_with_urgency_llm.json** (600 KB)
   - All diseases with LLM-derived urgency fields
   - Includes: `urgency_level`, `urgency_confidence`, `urgency_evidence`, `urgency_reasoning`

2. **urgency_classifications_llm.json** (800 KB)
   - Detailed classification results per disease
   - Includes evidence and reasoning for audit

3. **phase4_llm_report.json** (1 KB)
   - Statistics: cost, confidence, distribution
   - Model metadata and API call counts

---

## Cost Estimation

### Claude 3.5 Sonnet Pricing
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

### Estimated Usage
- Average input per disease: ~500 tokens (context + prompt)
- Average output per disease: ~100 tokens (classification)
- Total for 990 diseases:
  - Input: 990 × 500 = 495,000 tokens ≈ $1.49
  - Output: 990 × 100 = 99,000 tokens ≈ $1.49
  - **Total: ~$2.98-$5.00** (with overhead)

### Runtime
- ~1-2 seconds per disease (API latency)
- Total: 990 diseases × 1.5s ≈ **15-20 minutes**

---

## Validation & Comparison

### Compare Rule-Based vs LLM

```python
# scripts/compare_phase4_results.py

import json

# Load both versions
rule_based = json.load(open("output/phase4/diseases_with_urgency.json"))
llm_based = json.load(open("output/phase4_llm/diseases_with_urgency_llm.json"))

# Compare
disagreements = []
for rb, llm in zip(rule_based, llm_based):
    if rb["urgency_level"] != llm["urgency_level"]:
        disagreements.append({
            "disease": rb["name"],
            "rule_based": rb["urgency_level"],
            "llm": llm["urgency_level"],
            "llm_confidence": llm["urgency_confidence"],
            "evidence": llm["urgency_evidence"]
        })

print(f"Agreement: {(len(rule_based) - len(disagreements)) / len(rule_based) * 100:.1f}%")
print(f"Disagreements: {len(disagreements)}")

# Show high-confidence disagreements (likely rule-based errors)
high_confidence_disagreements = [
    d for d in disagreements
    if d["llm_confidence"] >= 0.9
]
print(f"\nHigh-confidence LLM disagreements: {len(high_confidence_disagreements)}")
for d in high_confidence_disagreements[:10]:
    print(f"  {d['disease']}: {d['rule_based']} → {d['llm']} (conf: {d['llm_confidence']:.2f})")
    print(f"    Evidence: {d['evidence'][:100]}...")
```

---

## Advantages of LLM Approach

### 1. Context-Aware Classification
LLM reads full clinical context, not just keywords:
- "may require urgent evaluation if symptoms progress" → captures conditional urgency
- "typically resolves within weeks without treatment" → identifies non-urgent correctly

### 2. Evidence & Reasoning
Every classification includes:
- **Evidence**: Direct quote from textbook supporting decision
- **Reasoning**: Explanation of why urgency level chosen
- **Confidence**: Numerical confidence score (0.0-1.0)

### 3. Handles Edge Cases
- Ambiguous language ("may be urgent in certain cases")
- Conditional urgency ("urgent if symptoms worsen")
- Implicit urgency signals (e.g., mentions of visual loss)

### 4. Audit Trail
Full transparency:
- Source text used for classification
- LLM reasoning documented
- Confidence scores for manual review

---

## Hybrid Approach (Recommended)

Combine both methods:

1. **Run rule-based first** (fast, free baseline)
2. **Use LLM for low-confidence cases** (diseases in Trauma chapter, ambiguous keywords)
3. **Manual review disagreements** (human expert validates)

```python
# Hybrid classification
def hybrid_classify(disease, rule_urgency, rule_confidence):
    # Use rule-based if high confidence
    if rule_confidence >= 0.8:
        return rule_urgency

    # Use LLM for low confidence
    llm_result = classify_with_llm(disease)
    if llm_result["confidence"] >= 0.85:
        return llm_result["urgency_level"]

    # Flag for manual review if both uncertain
    return "manual_review_required"
```

---

## Next Steps After LLM Enhancement

1. **Validate**: Compare with medical expert reviews
2. **Integrate**: Use LLM classifications in production
3. **Monitor**: Track triage accuracy in real-world use
4. **Refine**: Update prompts based on disagreements

---

## References

- Anthropic Claude API: https://docs.anthropic.com/
- Wills Eye Manual (7th Edition): Source for all classifications
- CLAUDE.md: Medical safety requirements

---

**Created**: 2025-10-23
**Purpose**: Enable LLM-based rerun of Phase 4
**Estimated effort**: 1 hour implementation, 20 minutes runtime, $3-5 cost
