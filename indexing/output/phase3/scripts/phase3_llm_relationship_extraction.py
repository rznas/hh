"""
Phase 3 LLM-Enhanced: Extract relationships between medical entities using LLM.

This script improves upon the co-occurrence approach by using Claude to:
- Identify explicit relationships in medical text
- Extract relationship context and evidence
- Classify relationship types with higher accuracy
- Handle implicit relationships (e.g., contraindications)
- PARALLEL PROCESSING: Uses ThreadPoolExecutor for concurrent API calls (default: 5 workers)
- CHECKPOINT SUPPORT: Saves progress every 10 blocks and can resume from interruptions

Input:
- Phase 2 outputs: diseases.json, symptoms.json, signs.json, treatments.json, diagnostic_tests.json
- Phase 1 outputs: wills_eye_text_blocks.json

Output:
- graphrag_edges_llm.json (LLM-extracted relationships)
- phase3_llm_report.json (extraction statistics and costs)
- phase3_checkpoint.json (progress checkpoint for resuming)

Usage:
    # Full extraction with parallel processing (will resume from checkpoint if interrupted)
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py

    # With custom number of workers
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py --num-workers 10

    # Start fresh (ignore checkpoint)
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py --no-checkpoint

    # Test with limited blocks (useful for development)
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py --max-blocks 100 --num-workers 2

    # Dry run (preview prompt without API calls)
    .venv/Scripts/python indexing/phase3_llm_relationship_extraction.py --dry-run
"""

import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

# Paths
PHASE1_DIR = Path(__file__).parent / "output" / "phase1"
PHASE2_DIR = Path(__file__).parent / "output" / "phase2"
PHASE3_DIR = Path(__file__).parent / "output" / "phase3"
INVALID_RESPONSES_DIR = PHASE3_DIR / "invalid_responses"

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from llm_schema_utils import InvalidResponseHandler, SchemaValidator

# Create output directory
PHASE3_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI client with custom base URL
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTA0ZTRlNzZhMjI0NjZkMzJjZjRjZDIiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxOTI4NDIzfQ.OTuh9hdtjeF6Bi2xrqVnOlam_HGfKNniVyoUbjqfHbs")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/6904e4e0298745c23b64f56d/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct")

# Disable environment-based proxy settings to avoid SOCKS proxy issues
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("ALL_PROXY", None)
os.environ.pop("all_proxy", None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)

# Thread-safe lock for stats updates
stats_lock = threading.Lock()


@dataclass
class ExtractionStats:
    """Track extraction statistics."""
    total_blocks: int = 0
    blocks_processed: int = 0
    relationships_extracted: int = 0
    llm_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    schema_validation_failures: int = 0


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
  {{
    "source_entity": "entity name",
    "source_type": "DISEASE|SYMPTOM|SIGN|TREATMENT|DIAGNOSTIC_TEST",
    "target_entity": "entity name",
    "target_type": "DISEASE|SYMPTOM|SIGN|TREATMENT|DIAGNOSTIC_TEST",
    "relationship_type": "presents_with|associated_with|treated_with|diagnosed_with|contraindicated_with|can_cause",
    "evidence": "exact quote from text supporting this relationship",
    "confidence": 0.0-1.0
  }}
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
    stats: ExtractionStats,
    invalid_handler: InvalidResponseHandler
) -> List[Dict]:
    """Use LLM to extract relationships from a text block."""

    # Skip if too few entities
    total_entities = sum(len(v) for v in entities_found.values())
    if total_entities < 2:
        return []

    # Prepare prompt
    prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
        text=text_block.get("text", ""),
        diseases=", ".join(entities_found["diseases"][:10]),
        symptoms=", ".join(entities_found["symptoms"][:10]),
        signs=", ".join(entities_found["signs"][:10]),
        treatments=", ".join(entities_found["treatments"][:10]),
        tests=", ".join(entities_found["tests"][:10])
    )

    try:
        # Call OpenAI
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=2000,
            temperature=0.0,  # Deterministic for consistency
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Update stats
        with stats_lock:
            stats.llm_calls += 1
            stats.total_tokens += response.usage.prompt_tokens + response.usage.completion_tokens

            # Cost calculation (GPT-4o pricing: $5/1M input, $15/1M output)
            input_cost = response.usage.prompt_tokens * 5 / 1000000
            output_cost = response.usage.completion_tokens * 15 / 1000000
            stats.total_cost += input_cost + output_cost

        # Parse response
        response_text = response.choices[0].message.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Validate JSON structure (expect array of relationship objects)
        try:
            relationships = json.loads(response_text)

            # Validate it's a list
            if not isinstance(relationships, list):
                error_msg = f"Expected array but got {type(relationships).__name__}"
                with stats_lock:
                    stats.schema_validation_failures += 1
                invalid_handler.record_invalid_response(
                    text_block=text_block,
                    prompt=prompt,
                    llm_response=response_text,
                    error=error_msg,
                    schema={"type": "array"}
                )
                return []

            # Validate each relationship has required fields
            valid_relationships = []
            for rel in relationships:
                if isinstance(rel, dict) and all(k in rel for k in ["source_entity", "target_entity", "relationship_type"]):
                    valid_relationships.append(rel)
                else:
                    # Skip invalid items but don't fail the whole batch
                    continue

            relationships = valid_relationships

        except json.JSONDecodeError as e:
            with stats_lock:
                stats.schema_validation_failures += 1
            invalid_handler.record_invalid_response(
                text_block=text_block,
                prompt=prompt,
                llm_response=response_text,
                error=f"JSON parsing error: {str(e)}",
                schema={"type": "array"}
            )
            return []

        # Add metadata to each relationship
        chapter = text_block.get("chapter_number")
        section = text_block.get("section_title", "")

        for rel in relationships:
            rel["metadata"] = {
                "chapter": chapter,
                "section": section,
                "extraction_method": "llm",
                "model": OPENAI_MODEL_NAME
            }

        with stats_lock:
            stats.relationships_extracted += len(relationships)

        return relationships

    except Exception as e:
        error_type = type(e).__name__
        print(f"  ⚠ Error extracting relationships ({error_type}): {e}")
        invalid_handler.record_connection_error(
            text_block=text_block,
            prompt=prompt,
            error=e,
            error_message=f"Error extracting relationships: {error_type}",
            retry_count=0
        )
        return []


def process_block_parallel(
    block: Dict,
    entities_found: Dict[str, List[str]],
    stats: ExtractionStats,
    diseases: List[Dict],
    symptoms: List[Dict],
    signs: List[Dict],
    treatments: List[Dict],
    tests: List[Dict],
    invalid_handler: InvalidResponseHandler
) -> Tuple[List[Dict], int]:
    """Process a single block and return mapped relationships with block index."""
    relationships = extract_relationships_with_llm(block, entities_found, stats, invalid_handler)

    # Map to entity IDs
    mapped = map_to_entity_ids(relationships, diseases, symptoms, signs, treatments, tests)

    return mapped, len(mapped)


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


def load_checkpoint() -> Tuple[List[Dict], ExtractionStats, int]:
    """Load checkpoint if it exists, returns (relationships, stats, start_index)."""
    checkpoint_file = PHASE3_DIR / "phase3_checkpoint.json"

    if checkpoint_file.exists():
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)

        print(f"  ✓ Loaded checkpoint from previous run")
        print(f"    • Blocks processed: {checkpoint['stats']['blocks_processed']}")
        print(f"    • Relationships extracted: {checkpoint['stats']['relationships_extracted']}")
        print(f"    • Total cost so far: ${checkpoint['stats']['total_cost']:.2f}")
        print(f"    • Resuming from block {checkpoint['start_index']}")

        stats = ExtractionStats(
            total_blocks=checkpoint['stats']['total_blocks'],
            blocks_processed=checkpoint['stats']['blocks_processed'],
            relationships_extracted=checkpoint['stats']['relationships_extracted'],
            llm_calls=checkpoint['stats']['llm_calls'],
            total_tokens=checkpoint['stats']['total_tokens'],
            total_cost=checkpoint['stats']['total_cost']
        )

        return checkpoint['relationships'], stats, checkpoint['start_index']

    return [], ExtractionStats(), 0


def save_checkpoint(relationships: List[Dict], stats: ExtractionStats, start_index: int):
    """Save checkpoint to disk for resuming."""
    checkpoint_file = PHASE3_DIR / "phase3_checkpoint.json"

    checkpoint = {
        "relationships": relationships,
        "stats": {
            "total_blocks": stats.total_blocks,
            "blocks_processed": stats.blocks_processed,
            "relationships_extracted": stats.relationships_extracted,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost": stats.total_cost
        },
        "start_index": start_index
    }

    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Extract relationships using LLM")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of text blocks to process in parallel (DEPRECATED - use --num-workers)")
    parser.add_argument("--num-workers", type=int, default=5, help="Number of parallel workers for processing (default: 5)")
    parser.add_argument("--max-blocks", type=int, default=None, help="Maximum number of text blocks to process (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Print first prompt without executing")
    parser.add_argument("--no-checkpoint", action="store_true", help="Ignore checkpoint and start fresh")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3 LLM-Enhanced: Relationship Extraction with OpenAI")
    print("=" * 80)
    print(f"Model: {OPENAI_MODEL_NAME}")
    print(f"Base URL: {OPENAI_BASE_URL}")
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

    # Extract relationships with checkpoint support
    print("\n[4/5] Extracting relationships with LLM...")

    # Initialize invalid response handler
    invalid_handler = InvalidResponseHandler(INVALID_RESPONSES_DIR, "relationships")

    # Load checkpoint if it exists (unless --no-checkpoint flag)
    if args.no_checkpoint:
        print("  ⚠ Checkpoint ignored (--no-checkpoint flag)")
        all_relationships, stats, start_index = [], ExtractionStats(), 0
    else:
        all_relationships, stats, start_index = load_checkpoint()

    if start_index == 0:
        stats.total_blocks = len(blocks_with_entities)
        print(f"  Starting fresh extraction")
    else:
        print(f"  Resuming from checkpoint")

    print(f"  Total blocks to process: {stats.total_blocks}")
    print(f"  Using parallel processing with {args.num_workers} workers")

    # Process remaining blocks in parallel with progress bar
    remaining_blocks = blocks_with_entities[start_index:]
    pbar = tqdm(total=len(remaining_blocks), initial=0, desc="  Processing", unit="block")

    # Collect results from parallel processing
    all_relationships = all_relationships or []
    processed_count = 0
    checkpoint_batch = []

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(
                process_block_parallel,
                block,
                entities_found,
                stats,
                diseases,
                symptoms,
                signs,
                treatments,
                tests,
                invalid_handler
            ): idx
            for idx, (block, entities_found) in enumerate(remaining_blocks, start=start_index)
        }

        # Process completed futures as they finish
        for future in as_completed(futures):
            try:
                mapped_rels, _ = future.result()
                all_relationships.extend(mapped_rels)
                checkpoint_batch.extend(mapped_rels)

                with stats_lock:
                    stats.blocks_processed += 1

                processed_count += 1
                pbar.update(1)

                # Update progress bar with stats
                pbar.set_postfix({
                    "rels": len(all_relationships),
                    "cost": f"${stats.total_cost:.2f}",
                    "calls": stats.llm_calls
                })

                # Save checkpoint every 10 blocks
                if processed_count % 10 == 0:
                    save_checkpoint(all_relationships, stats, start_index + processed_count)

            except Exception as e:
                print(f"\n  ⚠ Error processing block: {e}")
                pbar.update(1)

    pbar.close()

    # Save final checkpoint after completion
    save_checkpoint(all_relationships, stats, len(blocks_with_entities))
    print(f"  ✓ Checkpoint saved (completion)")
    print(f"  💾 Total relationships extracted: {len(all_relationships)}")

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

    # Save invalid responses for manual review
    invalid_count, invalid_file = invalid_handler.save_invalid_responses()
    if invalid_count > 0:
        print(f"  ⚠ {invalid_count} invalid responses saved to {invalid_file}")

    # Generate report
    report = {
        "extraction_method": "llm_enhanced",
        "model": OPENAI_MODEL_NAME,
        "total_relationships": len(unique_relationships),
        "by_type": {},
        "statistics": {
            "blocks_processed": stats.blocks_processed,
            "total_blocks": stats.total_blocks,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost_usd": round(stats.total_cost, 2),
            "avg_cost_per_block": round(stats.total_cost / stats.blocks_processed, 4) if stats.blocks_processed > 0 else 0,
            "avg_relationships_per_block": round(len(unique_relationships) / stats.blocks_processed, 2) if stats.blocks_processed > 0 else 0,
            "schema_validation_failures": stats.schema_validation_failures
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
    print(f"\nSchema Validation Failures: {stats.schema_validation_failures}")
    print("=" * 80)


if __name__ == "__main__":
    main()
