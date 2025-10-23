"""
Phase 3 LLM-Enhanced: Extract relationships between medical entities using LLM.

This script improves upon the co-occurrence approach by using Claude to:
- Identify explicit relationships in medical text
- Extract relationship context and evidence
- Classify relationship types with higher accuracy
- Handle implicit relationships (e.g., contraindications)

Input:
- Phase 2 outputs: diseases.json, symptoms.json, signs.json, treatments.json, diagnostic_tests.json
- Phase 1 outputs: wills_eye_text_blocks.json

Output:
- graphrag_edges_llm.json (LLM-extracted relationships)
- phase3_llm_report.json (extraction statistics and costs)

Usage:
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py --batch-size 10 --max-blocks 100
"""

import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import anthropic
from tqdm import tqdm

# Paths
PHASE1_DIR = Path(__file__).parent / "output" / "phase1"
PHASE2_DIR = Path(__file__).parent / "output" / "phase2"
PHASE3_DIR = Path(__file__).parent / "output" / "phase3"

# Create output directory
PHASE3_DIR.mkdir(parents=True, exist_ok=True)

# Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


@dataclass
class ExtractionStats:
    """Track extraction statistics."""
    total_blocks: int = 0
    blocks_processed: int = 0
    relationships_extracted: int = 0
    llm_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


RELATIONSHIP_EXTRACTION_PROMPT = """You are a medical knowledge graph expert extracting relationships between medical entities from The Wills Eye Manual.

**Your task:** Analyze the medical text and identify explicit relationships between entities.

**Entity Types:**
- DISEASE: Ocular conditions (e.g., "Keratitis", "Glaucoma")
- SYMPTOM: Patient-reported (e.g., "pain", "vision loss")
- SIGN: Clinical findings (e.g., "corneal edema", "photophobia")
- TREATMENT: Medications/procedures (e.g., "antibiotics", "surgery")
- DIAGNOSTIC_TEST: Tests/imaging (e.g., "OCT", "fluorescein staining")

**Relationship Types to Extract:**
1. **presents_with**: Disease → Symptom (e.g., "Keratitis presents with pain")
2. **associated_with**: Disease → Sign (e.g., "Keratitis shows corneal infiltrate")
3. **treated_with**: Disease → Treatment (e.g., "Bacterial keratitis treated with antibiotics")
4. **diagnosed_with**: Disease → Diagnostic Test (e.g., "Glaucoma diagnosed with tonometry")
5. **contraindicated_with**: Treatment → Disease/Condition (safety)
6. **can_cause**: Disease → Complication (e.g., "Untreated glaucoma can cause vision loss")

**Output Format (JSON):**
Return a JSON array of relationships. Each relationship must have:
```json
[
  {
    "source_entity": "entity name",
    "source_type": "DISEASE|SYMPTOM|SIGN|TREATMENT|DIAGNOSTIC_TEST",
    "target_entity": "entity name",
    "target_type": "DISEASE|SYMPTOM|SIGN|TREATMENT|DIAGNOSTIC_TEST",
    "relationship_type": "presents_with|associated_with|treated_with|diagnosed_with|contraindicated_with|can_cause",
    "evidence": "exact quote from text supporting this relationship",
    "confidence": 0.0-1.0
  }
]
```

**Guidelines:**
- Only extract relationships explicitly stated in the text
- Provide exact text evidence for each relationship
- Confidence: 1.0 for explicit statements, 0.7-0.9 for implied relationships
- Extract ALL relationships, but prioritize high-confidence ones
- Normalize entity names (e.g., "bacterial keratitis" → "Keratitis")
- Focus on medical accuracy

**Text to analyze:**
{text}

**Known entities in this text:**
Diseases: {diseases}
Symptoms: {symptoms}
Signs: {signs}
Treatments: {treatments}
Diagnostic Tests: {tests}

Return ONLY the JSON array, no additional text."""


def load_entities() -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
    """Load all Phase 2 entities."""
    with open(PHASE2_DIR / "diseases.json", encoding="utf-8") as f:
        diseases = json.load(f)
    with open(PHASE2_DIR / "symptoms.json", encoding="utf-8") as f:
        symptoms = json.load(f)
    with open(PHASE2_DIR / "signs.json", encoding="utf-8") as f:
        signs = json.load(f)
    with open(PHASE2_DIR / "treatments.json", encoding="utf-8") as f:
        treatments = json.load(f)
    with open(PHASE2_DIR / "diagnostic_tests.json", encoding="utf-8") as f:
        tests = json.load(f)

    return diseases, symptoms, signs, treatments, tests


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def find_entities_in_text(
    text: str,
    diseases: List[Dict],
    symptoms: List[Dict],
    signs: List[Dict],
    treatments: List[Dict],
    tests: List[Dict]
) -> Dict[str, List[str]]:
    """Find which entities appear in the given text."""
    text_lower = text.lower()

    found = {
        "diseases": [],
        "symptoms": [],
        "signs": [],
        "treatments": [],
        "tests": []
    }

    # Search for diseases
    for disease in diseases:
        if disease["name"].lower() in text_lower and len(disease["name"]) > 4:
            found["diseases"].append(disease["name"])

    # Search for symptoms
    for symptom in symptoms:
        if symptom["name"].lower() in text_lower and len(symptom["name"]) > 3:
            found["symptoms"].append(symptom["name"])

    # Search for signs
    for sign in signs:
        if sign["name"].lower() in text_lower and len(sign["name"]) > 3:
            found["signs"].append(sign["name"])

    # Search for treatments
    for treatment in treatments:
        if treatment["name"].lower() in text_lower and len(treatment["name"]) > 3:
            found["treatments"].append(treatment["name"])

    # Search for tests
    for test in tests:
        if test["name"].lower() in text_lower and len(test["name"]) > 3:
            found["tests"].append(test["name"])

    return found


def extract_relationships_with_llm(
    text_block: Dict,
    entities_found: Dict[str, List[str]],
    stats: ExtractionStats
) -> List[Dict]:
    """Use LLM to extract relationships from a text block."""

    # Skip if too few entities
    total_entities = sum(len(v) for v in entities_found.values())
    if total_entities < 2:
        return []

    # Prepare prompt
    prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
        text=text_block.get("text", "")[:2000],  # Limit text length
        diseases=", ".join(entities_found["diseases"][:10]),
        symptoms=", ".join(entities_found["symptoms"][:10]),
        signs=", ".join(entities_found["signs"][:10]),
        treatments=", ".join(entities_found["treatments"][:10]),
        tests=", ".join(entities_found["tests"][:10])
    )

    try:
        # Call Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.0,  # Deterministic for consistency
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Update stats
        stats.llm_calls += 1
        stats.total_tokens += response.usage.input_tokens + response.usage.output_tokens

        # Cost calculation (Claude 3.5 Sonnet pricing)
        input_cost = response.usage.input_tokens * 0.003 / 1000
        output_cost = response.usage.output_tokens * 0.015 / 1000
        stats.total_cost += input_cost + output_cost

        # Parse response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        relationships = json.loads(response_text)

        # Add metadata to each relationship
        chapter = text_block.get("chapter_number")
        section = text_block.get("section_title", "")

        for rel in relationships:
            rel["metadata"] = {
                "chapter": chapter,
                "section": section,
                "extraction_method": "llm",
                "model": "claude-3-5-sonnet"
            }

        stats.relationships_extracted += len(relationships)

        return relationships

    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON decode error: {e}")
        print(f"  Response: {response_text[:200]}")
        return []

    except Exception as e:
        print(f"  ⚠ Error extracting relationships: {e}")
        return []


def map_to_entity_ids(
    relationships: List[Dict],
    diseases: List[Dict],
    symptoms: List[Dict],
    signs: List[Dict],
    treatments: List[Dict],
    tests: List[Dict]
) -> List[Dict]:
    """Map entity names to entity IDs."""

    # Create lookup dictionaries
    entity_map = {}

    for disease in diseases:
        entity_map[disease["name"].lower()] = disease["entity_id"]
    for symptom in symptoms:
        entity_map[symptom["name"].lower()] = symptom["entity_id"]
    for sign in signs:
        entity_map[sign["name"].lower()] = sign["entity_id"]
    for treatment in treatments:
        entity_map[treatment["name"].lower()] = treatment["entity_id"]
    for test in tests:
        entity_map[test["name"].lower()] = test["entity_id"]

    # Map relationships
    mapped_relationships = []

    for rel in relationships:
        source_name = rel.get("source_entity", "").lower()
        target_name = rel.get("target_entity", "").lower()

        source_id = entity_map.get(source_name)
        target_id = entity_map.get(target_name)

        # Only keep if both entities found
        if source_id and target_id:
            mapped_rel = {
                "source": source_id,
                "target": target_id,
                "relationship_type": rel.get("relationship_type"),
                "description": f"{rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')}",
                "weight": rel.get("confidence", 0.8),
                "evidence": rel.get("evidence", ""),
                "metadata": rel.get("metadata", {})
            }
            mapped_relationships.append(mapped_rel)

    return mapped_relationships


def deduplicate_relationships(relationships: List[Dict]) -> List[Dict]:
    """Remove duplicate relationships, keeping highest weight."""
    seen = {}

    for rel in relationships:
        key = (rel["source"], rel["target"], rel["relationship_type"])

        if key not in seen or rel["weight"] > seen[key]["weight"]:
            seen[key] = rel

    return list(seen.values())


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Extract relationships using LLM")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of text blocks to process in parallel")
    parser.add_argument("--max-blocks", type=int, default=None, help="Maximum number of text blocks to process (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Print first prompt without executing")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3 LLM-Enhanced: Relationship Extraction with Claude")
    print("=" * 80)

    # Load entities
    print("\n[1/5] Loading Phase 2 entities...")
    diseases, symptoms, signs, treatments, tests = load_entities()
    print(f"  ✓ Loaded {len(diseases)} diseases")
    print(f"  ✓ Loaded {len(symptoms)} symptoms")
    print(f"  ✓ Loaded {len(signs)} signs")
    print(f"  ✓ Loaded {len(treatments)} treatments")
    print(f"  ✓ Loaded {len(tests)} diagnostic tests")

    # Load text blocks
    print("\n[2/5] Loading Phase 1 text blocks...")
    text_blocks = load_text_blocks()

    if args.max_blocks:
        text_blocks = text_blocks[:args.max_blocks]
        print(f"  ℹ Limited to {args.max_blocks} blocks for testing")

    print(f"  ✓ Loaded {len(text_blocks)} text blocks")

    # Filter blocks with entities
    print("\n[3/5] Finding text blocks with multiple entities...")
    blocks_with_entities = []

    for block in tqdm(text_blocks, desc="  Scanning"):
        entities_found = find_entities_in_text(
            block.get("text", ""),
            diseases, symptoms, signs, treatments, tests
        )
        total_entities = sum(len(v) for v in entities_found.values())

        if total_entities >= 2:
            blocks_with_entities.append((block, entities_found))

    print(f"  ✓ Found {len(blocks_with_entities)} blocks with 2+ entities")

    # Dry run mode
    if args.dry_run:
        print("\n[DRY RUN] Sample prompt:")
        print("=" * 80)
        if blocks_with_entities:
            sample_block, sample_entities = blocks_with_entities[0]
            sample_prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
                text=sample_block.get("text", "")[:2000],
                diseases=", ".join(sample_entities["diseases"][:10]),
                symptoms=", ".join(sample_entities["symptoms"][:10]),
                signs=", ".join(sample_entities["signs"][:10]),
                treatments=", ".join(sample_entities["treatments"][:10]),
                tests=", ".join(sample_entities["tests"][:10])
            )
            print(sample_prompt)
        print("=" * 80)
        print("\n✓ Dry run complete. Use without --dry-run to execute.")
        return

    # Extract relationships
    print("\n[4/5] Extracting relationships with LLM...")
    stats = ExtractionStats(total_blocks=len(blocks_with_entities))
    all_relationships = []

    for block, entities_found in tqdm(blocks_with_entities, desc="  Processing"):
        relationships = extract_relationships_with_llm(block, entities_found, stats)

        # Map to entity IDs
        mapped = map_to_entity_ids(relationships, diseases, symptoms, signs, treatments, tests)
        all_relationships.extend(mapped)

        stats.blocks_processed += 1

    # Deduplicate
    print("\n[5/5] Deduplicating relationships...")
    unique_relationships = deduplicate_relationships(all_relationships)
    print(f"  ✓ Removed {len(all_relationships) - len(unique_relationships)} duplicates")
    print(f"  ✓ Final count: {len(unique_relationships)} unique relationships")

    # Save output
    output_file = PHASE3_DIR / "graphrag_edges_llm.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_relationships, f, indent=2)
    print(f"\n✓ Saved to: {output_file}")

    # Generate report
    report = {
        "extraction_method": "llm_enhanced",
        "model": "claude-3-5-sonnet-20241022",
        "total_relationships": len(unique_relationships),
        "by_type": {},
        "statistics": {
            "blocks_processed": stats.blocks_processed,
            "total_blocks": stats.total_blocks,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost_usd": round(stats.total_cost, 2),
            "avg_cost_per_block": round(stats.total_cost / stats.blocks_processed, 4) if stats.blocks_processed > 0 else 0,
            "avg_relationships_per_block": round(len(unique_relationships) / stats.blocks_processed, 2) if stats.blocks_processed > 0 else 0
        }
    }

    # Count by type
    for rel in unique_relationships:
        rel_type = rel["relationship_type"]
        report["by_type"][rel_type] = report["by_type"].get(rel_type, 0) + 1

    # Confidence breakdown
    high_conf = len([r for r in unique_relationships if r["weight"] >= 0.9])
    med_conf = len([r for r in unique_relationships if 0.7 <= r["weight"] < 0.9])
    low_conf = len([r for r in unique_relationships if r["weight"] < 0.7])

    report["confidence_breakdown"] = {
        "high_confidence_0.9+": high_conf,
        "medium_confidence_0.7-0.9": med_conf,
        "low_confidence_<0.7": low_conf
    }

    report_file = PHASE3_DIR / "phase3_llm_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Report saved to: {report_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Relationships: {len(unique_relationships)}")
    print(f"\nBy Type:")
    for rel_type, count in sorted(report["by_type"].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {rel_type}: {count}")
    print(f"\nConfidence:")
    print(f"  • High (≥0.9): {high_conf}")
    print(f"  • Medium (0.7-0.9): {med_conf}")
    print(f"  • Low (<0.7): {low_conf}")
    print(f"\nCost:")
    print(f"  • Total: ${stats.total_cost:.2f}")
    print(f"  • Per block: ${stats.total_cost / stats.blocks_processed:.4f}")
    print(f"  • Total tokens: {stats.total_tokens:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
