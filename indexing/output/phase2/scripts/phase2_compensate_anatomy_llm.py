#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract ANATOMY entities using LLM (Issue 1.2)

This script implements the LLM-enhanced approach for extracting anatomical entities
from The Wills Eye Manual text blocks using Claude/OpenAI.

Approach:
- LLM-based entity extraction with structured output
- Confidence scoring
- Parallel processing for performance
- Checkpoint support for resumability

Input:
- Phase 1: wills_eye_text_blocks.json

Output:
- anatomy_llm.json (anatomical entities with metadata)
- phase2_anatomy_llm_report.json (extraction statistics and costs)
- phase2_anatomy_llm_checkpoint.json (progress checkpoint)

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy_llm.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy_llm.py --dry-run
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy_llm.py --num-workers 10
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "anatomy_llm.json"
REPORT_FILE = PHASE2_DIR / "phase2_anatomy_llm_report.json"
CHECKPOINT_FILE = PHASE2_DIR / "phase2_anatomy_llm_checkpoint.json"

# OpenAI client setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTAyNTk3MWYwN2ViNTczMjgzZmIxMjkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxNzYxNjQ5fQ.Wllnd6Fn-fghYv1uk18ZoXNXHDRw30vDiEwNBQXUqR8")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/68721419652cec5504661aec/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")

# Disable proxy
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)
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


ANATOMY_EXTRACTION_PROMPT = """You are a medical knowledge graph expert extracting anatomical entities from The Wills Eye Manual.

**Your task:** Analyze the medical text and identify ALL anatomical structures mentioned.

**Entity Type to Extract:**
- **ANATOMY**: Eye structures and anatomical locations (e.g., "cornea", "retina", "optic nerve", "iris", "lens", "macula", "vitreous", "conjunctiva", "sclera", "anterior chamber", "eyelid", "orbit")

**Guidelines:**
- Extract ALL anatomical structures present in the text
- Use exact anatomical names from the text
- Normalize names to standard anatomical terminology
- Include variations (e.g., "cornea" and "corneal epithelium" are different)
- Confidence: 1.0 for explicit anatomical terms; 0.7-0.9 for contextual/implied structures
- Focus on ocular anatomy specifically

**Text to analyze:**
{text}"""

# JSON Schema for structured output
ANATOMY_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "anatomical_entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Anatomical structure name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description from context"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Confidence score"
                    }
                },
                "required": ["name", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["anatomical_entities"],
    "additionalProperties": False
}


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def extract_anatomy_with_llm(text_block: Dict, stats: ExtractionStats) -> List[Dict]:
    """Use LLM to extract anatomy entities from a text block."""
    text = text_block.get("text", "")
    if not text or len(text.strip()) < 50:
        return []

    prompt = ANATOMY_EXTRACTION_PROMPT.format(text=text[:3000])

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=1500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "anatomy_extraction",
                    "strict": True,
                    "schema": ANATOMY_EXTRACTION_SCHEMA
                }
            }
        )

        # Update stats
        with stats_lock:
            stats.llm_calls += 1
            stats.total_tokens += response.usage.prompt_tokens + response.usage.completion_tokens
            input_cost = response.usage.prompt_tokens * 5 / 1000000
            output_cost = response.usage.completion_tokens * 15 / 1000000
            stats.total_cost += input_cost + output_cost

        # Parse response
        response_text = response.choices[0].message.content.strip()
        result = json.loads(response_text)
        entities = result.get("anatomical_entities", [])

        # Add metadata
        chapter = text_block.get("chapter_number")
        section = text_block.get("section_title", "")

        for entity in entities:
            entity["type"] = "anatomy"
            entity["metadata"] = {
                "chapter": chapter,
                "section": section,
                "extraction_method": "llm",
                "model": OPENAI_MODEL_NAME
            }

        with stats_lock:
            stats.entities_extracted += len(entities)

        return entities

    except Exception as e:
        print(f"  ⚠ Error extracting anatomy: {e}")
        return []


def process_block(block: Dict, stats: ExtractionStats) -> List[Dict]:
    """Process a single block."""
    return extract_anatomy_with_llm(block, stats)


def normalize_name(name: str) -> str:
    """Normalize entity name."""
    return name.lower().strip()


def deduplicate_entities(all_entities: List[Dict]) -> Dict[str, Dict]:
    """Deduplicate entities, keeping highest confidence."""
    entity_map = {}

    for entity in all_entities:
        normalized = normalize_name(entity["name"])

        if normalized not in entity_map:
            entity_map[normalized] = entity
        else:
            existing = entity_map[normalized]
            if entity.get("confidence", 0.7) > existing.get("confidence", 0.7):
                entity_map[normalized] = entity

    return entity_map


def create_entity_id(index: int) -> str:
    """Generate anatomy entity ID."""
    return f"anatomy_{index:03d}"


def load_checkpoint():
    """Load checkpoint if exists."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        print(f"  ✓ Loaded checkpoint from previous run")
        print(f"    • Blocks processed: {checkpoint['stats']['blocks_processed']}")
        print(f"    • Entities extracted: {checkpoint['stats']['entities_extracted']}")
        return checkpoint['entities'], checkpoint['stats'], checkpoint['start_index']
    return [], {}, 0


def save_checkpoint(entities: List[Dict], stats: dict, start_index: int):
    """Save checkpoint."""
    checkpoint = {
        "entities": entities,
        "stats": stats,
        "start_index": start_index
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract ANATOMY entities using LLM")
    parser.add_argument("--num-workers", type=int, default=5, help="Number of parallel workers")
    parser.add_argument("--max-blocks", type=int, default=None, help="Maximum blocks to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    parser.add_argument("--no-checkpoint", action="store_true", help="Ignore checkpoint")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: ANATOMY Entity Extraction (LLM)")
    print("=" * 80)
    print(f"Model: {OPENAI_MODEL_NAME}")
    print("=" * 80)

    # Load text blocks
    print("\n[1/4] Loading text blocks...")
    text_blocks = load_text_blocks()

    if args.max_blocks:
        text_blocks = text_blocks[:args.max_blocks]

    print(f"  ✓ Loaded {len(text_blocks)} text blocks")

    if args.dry_run:
        print("\n[DRY RUN] Sample prompt:")
        print("=" * 80)
        if text_blocks:
            sample_prompt = ANATOMY_EXTRACTION_PROMPT.format(text=text_blocks[0].get("text", "")[:3000])
            print(sample_prompt)
        print("=" * 80)
        return

    # Extract entities
    print("\n[2/4] Extracting anatomy entities with LLM...")

    # Load checkpoint
    if args.no_checkpoint:
        all_entities, stats_dict, start_index = [], {}, 0
        stats = ExtractionStats(total_blocks=len(text_blocks))
    else:
        all_entities, stats_dict, start_index = load_checkpoint()
        stats = ExtractionStats(
            total_blocks=stats_dict.get('total_blocks', len(text_blocks)),
            blocks_processed=stats_dict.get('blocks_processed', 0),
            entities_extracted=stats_dict.get('entities_extracted', 0),
            llm_calls=stats_dict.get('llm_calls', 0),
            total_tokens=stats_dict.get('total_tokens', 0),
            total_cost=stats_dict.get('total_cost', 0.0)
        )

    print(f"  Using {args.num_workers} parallel workers")

    # Process blocks
    remaining_blocks = text_blocks[start_index:]
    pbar = tqdm(total=len(remaining_blocks), desc="  Processing", unit="block")

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {
            executor.submit(process_block, block, stats): idx
            for idx, block in enumerate(remaining_blocks, start=start_index)
        }

        processed_count = 0
        for future in as_completed(futures):
            try:
                entities = future.result()
                all_entities.extend(entities)

                with stats_lock:
                    stats.blocks_processed += 1

                processed_count += 1
                pbar.update(1)
                pbar.set_postfix({"entities": len(all_entities), "cost": f"${stats.total_cost:.2f}"})

                # Checkpoint every 10 blocks
                if processed_count % 10 == 0:
                    save_checkpoint(all_entities, vars(stats), start_index + processed_count)

            except Exception as e:
                print(f"\n  ⚠ Error: {e}")
                pbar.update(1)

    pbar.close()
    print(f"  ✓ Total entities extracted: {len(all_entities)}")

    # Deduplicate
    print("\n[3/4] Deduplicating entities...")
    unique_entities = deduplicate_entities(all_entities)
    print(f"  ✓ Removed {len(all_entities) - len(unique_entities)} duplicates")
    print(f"  ✓ Final count: {len(unique_entities)} unique entities")

    # Save entities
    print("\n[4/4] Saving entities...")
    entities_list = []
    for idx, (normalized, entity) in enumerate(sorted(unique_entities.items()), 1):
        entity["entity_id"] = create_entity_id(idx)
        entity["name_normalized"] = normalized
        entities_list.append(entity)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entities_list, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(entities_list)} entities to {OUTPUT_FILE}")

    # Generate report
    report = {
        "extraction_method": "llm_enhanced",
        "model": OPENAI_MODEL_NAME,
        "total_entities": len(entities_list),
        "statistics": {
            "blocks_processed": stats.blocks_processed,
            "llm_calls": stats.llm_calls,
            "total_tokens": stats.total_tokens,
            "total_cost_usd": round(stats.total_cost, 2)
        }
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved report to {REPORT_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Entities: {len(entities_list)}")
    print(f"Cost: ${stats.total_cost:.2f}")
    print(f"Tokens: {stats.total_tokens:,}")
    print("=" * 80)


if __name__ == "__main__":
    main()
