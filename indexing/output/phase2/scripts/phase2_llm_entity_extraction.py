#!/usr/bin/env python3
"""
Phase 2 LLM-Enhanced: Extract medical entities using LLM.

This script extracts disease, symptom, sign, treatment, and diagnostic test entities
from The Wills Eye Manual using Claude/OpenAI LLM for high accuracy.

Features:
- PARALLEL PROCESSING: Uses ThreadPoolExecutor for concurrent API calls (default: 5 workers)
- CHECKPOINT SUPPORT: Saves progress every 10 blocks and can resume from interruptions
- ENTITY TYPES: Diseases, Symptoms, Signs, Treatments, Diagnostic Tests
- CONFIDENCE SCORING: LLM assigns confidence to each extracted entity
- BATCH DEDUPLICATION: Removes duplicates and keeps highest confidence versions

Input:
- Phase 1 outputs: wills_eye_text_blocks.json

Output:
- diseases.json (LLM-extracted disease entities)
- symptoms.json (LLM-extracted symptom entities)
- signs.json (LLM-extracted sign entities)
- treatments.json (LLM-extracted treatment entities)
- diagnostic_tests.json (LLM-extracted diagnostic test entities)
- phase2_llm_report.json (extraction statistics and costs)
- phase2_checkpoint.json (progress checkpoint for resuming)

Usage:
    # Full extraction with parallel processing (will resume from checkpoint if interrupted)
    .venv/bin/python indexing/phase2_llm_entity_extraction.py

    # With custom number of workers
    .venv/bin/python indexing/phase2_llm_entity_extraction.py --num-workers 10

    # Start fresh (ignore checkpoint)
    .venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint

    # Test with limited blocks (useful for development)
    .venv/bin/python indexing/phase2_llm_entity_extraction.py --max-blocks 50 --num-workers 2

    # Dry run (preview prompt without API calls)
    .venv/bin/python indexing/phase2_llm_entity_extraction.py --dry-run
"""

import json
import os
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict

# Paths
PHASE1_DIR = Path(__file__).parent / "output" / "phase1"
PHASE2_DIR = Path(__file__).parent / "output" / "phase2"

# Create output directory
PHASE2_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI client with custom base URL
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTAyNTk3MWYwN2ViNTczMjgzZmIxMjkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxNzYxNjQ5fQ.Wllnd6Fn-fghYv1uk18ZoXNXHDRw30vDiEwNBQXUqR8")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/68721419652cec5504661aec/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")

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
    entities_extracted: int = 0
    llm_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    by_type: Dict[str, int] = field(default_factory=lambda: {
        'disease': 0,
        'symptom': 0,
        'sign': 0,
        'treatment': 0,
        'diagnostic_test': 0
    })


ENTITY_EXTRACTION_PROMPT = """You are a medical knowledge graph expert extracting medical entities from The Wills Eye Manual.

**Your task:** Analyze the medical text and identify all medical entities.

**Entity Types to Extract:**
1. **DISEASE**: Ocular conditions/diseases (e.g., "Keratitis", "Glaucoma", "Retinal Detachment")
2. **SYMPTOM**: Patient-reported symptoms (e.g., "pain", "vision loss", "photophobia", "blurred vision")
3. **SIGN**: Clinical findings/examination signs (e.g., "corneal edema", "photophobia", "exudate", "infiltrate")
4. **TREATMENT**: Medications, procedures, interventions (e.g., "antibiotics", "surgery", "laser therapy", "topical steroids")
5. **DIAGNOSTIC_TEST**: Diagnostic tests and imaging (e.g., "OCT", "fluorescein staining", "tonometry", "slit lamp examination")

**Guidelines:**
- Extract ALL entities present in the text
- Use exact names from the text when possible
- Normalize names (e.g., "bacterial keratitis" → "Keratitis")
- Include variations and synonyms as separate entries
- Confidence: 1.0 for explicit, clear entities; 0.7-0.9 for contextual/implied entities
- Focus on medical accuracy and completeness

**Text to analyze:**
{text}"""

# JSON Schema for structured output
ENTITY_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Entity name as appears in text"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["DISEASE", "SYMPTOM", "SIGN", "TREATMENT", "DIAGNOSTIC_TEST"],
                        "description": "Type of medical entity"
                    },
                    "synonyms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Alternative names for this entity"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description from context"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score for this extraction"
                    }
                },
                "required": ["name", "type", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["entities"],
    "additionalProperties": False
}


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def extract_entities_with_llm(text_block: Dict, stats: ExtractionStats) -> List[Dict]:
    """Use LLM to extract entities from a text block."""

    text = text_block.get("text", "")
    if not text or len(text.strip()) < 50:  # Skip very short blocks
        return []

    # Prepare prompt
    prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:3000])  # Limit text length

    try:
        # Call OpenAI with structured output
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=2000,
            temperature=0.0,  # Deterministic for consistency
            messages=[{
                "role": "user",
                "content": prompt
            }],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "entity_extraction",
                    "strict": True,
                    "schema": ENTITY_EXTRACTION_SCHEMA
                }
            }
        )

        # Update stats
        with stats_lock:
            stats.llm_calls += 1
            stats.total_tokens += response.usage.prompt_tokens + response.usage.completion_tokens

            # Cost calculation (GPT-4o pricing: $5/1M input, $15/1M output)
            input_cost = response.usage.prompt_tokens * 5 / 1000000
            output_cost = response.usage.completion_tokens * 15 / 1000000
            stats.total_cost += input_cost + output_cost

        # Parse response (structured output returns valid JSON directly)
        response_text = response.choices[0].message.content.strip()
        result = json.loads(response_text)
        entities = result.get("entities", [])

        # Add metadata to each entity
        chapter = text_block.get("chapter_number")
        section = text_block.get("section_title", "")

        for entity in entities:
            entity["metadata"] = {
                "chapter": chapter,
                "section": section,
                "extraction_method": "llm",
                "model": OPENAI_MODEL_NAME
            }

            # Update stats by type
            entity_type = entity.get("type", "").lower()
            if entity_type in stats.by_type:
                with stats_lock:
                    stats.by_type[entity_type] += 1

        with stats_lock:
            stats.entities_extracted += len(entities)

        return entities

    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON decode error in block {text_block.get('chapter_number')}: {e}")
        return []

    except Exception as e:
        print(f"  ⚠ Error extracting entities: {e}")
        return []


def process_block_parallel(
    block: Dict,
    stats: ExtractionStats
) -> List[Dict]:
    """Process a single block and return extracted entities."""
    entities = extract_entities_with_llm(block, stats)
    return entities


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for deduplication."""
    return name.lower().strip()


def deduplicate_entities(all_entities: List[Dict]) -> Dict[str, Dict]:
    """
    Deduplicate entities, keeping highest confidence version.
    Returns dict with normalized name as key.
    """
    entity_map = {}

    for entity in all_entities:
        # Normalize name for comparison
        normalized = normalize_entity_name(entity["name"])

        if normalized not in entity_map:
            entity_map[normalized] = entity
        else:
            # Keep if higher confidence
            existing = entity_map[normalized]
            if entity.get("confidence", 0.7) > existing.get("confidence", 0.7):
                entity_map[normalized] = entity
            else:
                # Merge synonyms
                existing_synonyms = set(existing.get("synonyms", []))
                new_synonyms = set(entity.get("synonyms", []))
                existing["synonyms"] = sorted(list(existing_synonyms | new_synonyms))

    return entity_map


def create_entity_id(entity_type: str, index: int) -> str:
    """Generate entity ID based on type."""
    type_map = {
        'disease': 'disease',
        'symptom': 'symptom',
        'sign': 'sign',
        'treatment': 'treatment',
        'diagnostic_test': 'test'
    }
    prefix = type_map.get(entity_type.lower(), 'entity')
    return f"{prefix}_{index:03d}"


def save_entities_by_type(all_entities_dict: Dict[str, Dict], output_dir: Path) -> Dict[str, List[Dict]]:
    """
    Organize entities by type and save to separate files.
    Returns dict with count of entities saved by type.
    """
    entities_by_type = defaultdict(list)

    # Organize by type
    for normalized_name, entity in all_entities_dict.items():
        entity_type = entity.get("type", "").lower()
        entities_by_type[entity_type].append(entity)

    # Save each type with entity IDs
    saved_counts = {}
    for entity_type, entities in entities_by_type.items():
        # Add entity_id to each entity
        for idx, entity in enumerate(entities, 1):
            entity["entity_id"] = create_entity_id(entity_type, idx)
            # Ensure name is title case for display
            if "name" in entity:
                entity["name_normalized"] = normalize_entity_name(entity["name"])

        # Sort by name
        entities_sorted = sorted(entities, key=lambda e: e.get("name", "").lower())

        # Determine output filename
        if entity_type == 'diagnostic_test':
            filename = output_dir / "diagnostic_tests.json"
        else:
            filename = output_dir / f"{entity_type}s.json"

        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entities_sorted, f, indent=2, ensure_ascii=False)

        saved_counts[entity_type] = len(entities_sorted)
        print(f"  ✓ Saved {len(entities_sorted)} {entity_type} entities to {filename.name}")

    return saved_counts


def load_checkpoint() -> Tuple[List[Dict], ExtractionStats, int]:
    """Load checkpoint if it exists, returns (entities, stats, start_index)."""
    checkpoint_file = PHASE2_DIR / "phase2_checkpoint.json"

    if checkpoint_file.exists():
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)

        print(f"  ✓ Loaded checkpoint from previous run")
        print(f"    • Blocks processed: {checkpoint['stats']['blocks_processed']}")
        print(f"    • Entities extracted: {checkpoint['stats']['entities_extracted']}")
        print(f"    • Total cost so far: ${checkpoint['stats']['total_cost']:.2f}")
        print(f"    • Resuming from block {checkpoint['start_index']}")

        stats = ExtractionStats(
            total_blocks=checkpoint['stats']['total_blocks'],
            blocks_processed=checkpoint['stats']['blocks_processed'],
            entities_extracted=checkpoint['stats']['entities_extracted'],
            llm_calls=checkpoint['stats']['llm_calls'],
            total_tokens=checkpoint['stats']['total_tokens'],
            total_cost=checkpoint['stats']['total_cost'],
            by_type=checkpoint['stats'].get('by_type', {})
        )

        return checkpoint['entities'], stats, checkpoint['start_index']

    return [], ExtractionStats(), 0


def save_checkpoint(entities: List[Dict], stats: ExtractionStats, start_index: int):
    """Save checkpoint to disk for resuming."""
    checkpoint_file = PHASE2_DIR / "phase2_checkpoint.json"

    checkpoint = {
        "entities": entities,
        "stats": {
            "total_blocks": stats.total_blocks,
            "blocks_processed": stats.blocks_processed,
            "entities_extracted": stats.entities_extracted,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost": stats.total_cost,
            "by_type": stats.by_type
        },
        "start_index": start_index
    }

    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Extract medical entities using LLM")
    parser.add_argument("--num-workers", type=int, default=5, help="Number of parallel workers for processing (default: 5)")
    parser.add_argument("--max-blocks", type=int, default=None, help="Maximum number of text blocks to process (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Print first prompt without executing")
    parser.add_argument("--no-checkpoint", action="store_true", help="Ignore checkpoint and start fresh")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory (default: indexing/output/phase2)")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 LLM-Enhanced: Medical Entity Extraction")
    print("=" * 80)
    print(f"Model: {OPENAI_MODEL_NAME}")
    print(f"Base URL: {OPENAI_BASE_URL}")
    print("=" * 80)

    # Set output directory
    output_dir = Path(args.output_dir) if args.output_dir else PHASE2_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    # Load text blocks
    print("\n[1/4] Loading Phase 1 text blocks...")
    text_blocks = load_text_blocks()

    if args.max_blocks:
        text_blocks = text_blocks[:args.max_blocks]
        print(f"  ℹ Limited to {args.max_blocks} blocks for testing")

    print(f"  ✓ Loaded {len(text_blocks)} text blocks")

    # Dry run mode
    if args.dry_run:
        print("\n[DRY RUN] Sample prompt:")
        print("=" * 80)
        if text_blocks:
            sample_block = text_blocks[0]
            sample_prompt = ENTITY_EXTRACTION_PROMPT.format(text=sample_block.get("text", "")[:3000])
            print(sample_prompt)
        print("=" * 80)
        print("\n✓ Dry run complete. Use without --dry-run to execute.")
        return

    # Extract entities with checkpoint support
    print("\n[2/4] Extracting entities with LLM...")

    # Load checkpoint if it exists (unless --no-checkpoint flag)
    if args.no_checkpoint:
        print("  ⚠ Checkpoint ignored (--no-checkpoint flag)")
        all_entities, stats, start_index = [], ExtractionStats(), 0
    else:
        all_entities, stats, start_index = load_checkpoint()

    if start_index == 0:
        stats.total_blocks = len(text_blocks)
        print(f"  Starting fresh extraction")
    else:
        print(f"  Resuming from checkpoint")

    print(f"  Total blocks to process: {stats.total_blocks}")
    print(f"  Using parallel processing with {args.num_workers} workers")

    # Process remaining blocks in parallel with progress bar
    remaining_blocks = text_blocks[start_index:]
    pbar = tqdm(total=len(remaining_blocks), initial=0, desc="  Processing", unit="block")

    # Collect results from parallel processing
    all_entities = all_entities or []
    processed_count = 0

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_block_parallel, block, stats): idx
            for idx, block in enumerate(remaining_blocks, start=start_index)
        }

        # Process completed futures as they finish
        for future in as_completed(futures):
            try:
                entities = future.result()
                all_entities.extend(entities)

                with stats_lock:
                    stats.blocks_processed += 1

                processed_count += 1
                pbar.update(1)

                # Update progress bar with stats
                pbar.set_postfix({
                    "entities": len(all_entities),
                    "cost": f"${stats.total_cost:.2f}",
                    "calls": stats.llm_calls
                })

                # Save checkpoint every 10 blocks
                if processed_count % 10 == 0:
                    save_checkpoint(all_entities, stats, start_index + processed_count)

            except Exception as e:
                print(f"\n  ⚠ Error processing block: {e}")
                pbar.update(1)

    pbar.close()

    # Save final checkpoint after completion
    save_checkpoint(all_entities, stats, len(text_blocks))
    print(f"  ✓ Checkpoint saved (completion)")
    print(f"  💾 Total entities extracted: {len(all_entities)}")

    # Deduplicate entities
    print("\n[3/4] Deduplicating entities...")
    unique_entities_dict = deduplicate_entities(all_entities)
    print(f"  ✓ Removed {len(all_entities) - len(unique_entities_dict)} duplicates")
    print(f"  ✓ Final count: {len(unique_entities_dict)} unique entities")

    # Save entities by type
    print("\n[4/4] Saving entities by type...")
    saved_counts = save_entities_by_type(unique_entities_dict, output_dir)

    # Generate report
    report = {
        "extraction_method": "llm_enhanced",
        "model": OPENAI_MODEL_NAME,
        "total_unique_entities": len(unique_entities_dict),
        "by_type": saved_counts,
        "statistics": {
            "blocks_processed": stats.blocks_processed,
            "total_blocks": stats.total_blocks,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost_usd": round(stats.total_cost, 2),
            "avg_cost_per_block": round(stats.total_cost / stats.blocks_processed, 4) if stats.blocks_processed > 0 else 0,
            "avg_entities_per_block": round(len(unique_entities_dict) / stats.blocks_processed, 2) if stats.blocks_processed > 0 else 0
        }
    }

    report_file = output_dir / "phase2_llm_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n✓ Report saved to: {report_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Unique Entities: {len(unique_entities_dict)}")
    print(f"\nBy Type:")
    for entity_type, count in sorted(saved_counts.items()):
        print(f"  • {entity_type}: {count}")
    print(f"\nCost:")
    print(f"  • Total: ${stats.total_cost:.2f}")
    print(f"  • Per block: ${stats.total_cost / stats.blocks_processed:.4f}")
    print(f"  • Total tokens: {stats.total_tokens:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
