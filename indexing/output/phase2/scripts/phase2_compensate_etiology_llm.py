#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract ETIOLOGY entities using LLM (Issue 1.3)

LLM-enhanced approach for extracting etiology (causative factors) from The Wills Eye Manual.

Input: Phase 1: wills_eye_text_blocks.json
Output: etiology_llm.json, phase2_etiology_llm_report.json, checkpoint

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology_llm.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology_llm.py --dry-run
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "etiology_llm.json"
REPORT_FILE = PHASE2_DIR / "phase2_etiology_llm_report.json"
CHECKPOINT_FILE = PHASE2_DIR / "phase2_etiology_llm_checkpoint.json"

# OpenAI setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTAyNTk3MWYwN2ViNTczMjgzZmIxMjkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxNzYxNjQ5fQ.Wllnd6Fn-fghYv1uk18ZoXNXHDRw30vDiEwNBQXUqR8")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/68721419652cec5504661aec/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")

for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)
stats_lock = threading.Lock()


@dataclass
class ExtractionStats:
    total_blocks: int = 0
    blocks_processed: int = 0
    entities_extracted: int = 0
    llm_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


ETIOLOGY_EXTRACTION_PROMPT = """You are a medical knowledge graph expert extracting etiology entities from The Wills Eye Manual.

**Your task:** Analyze the text and identify ALL etiological causes and causative factors.

**Entity Type to Extract:**
- **ETIOLOGY**: Causes and causative factors of diseases (e.g., "bacterial infection", "trauma", "autoimmune disorder", "aging", "genetic mutation", "viral infection", "chemical exposure")

**Categories to consider:**
- Infectious: bacteria, viruses, fungi, parasites
- Traumatic: injury, blunt trauma, penetrating trauma
- Autoimmune: immune-mediated conditions
- Degenerative: age-related, wear-and-tear
- Congenital: genetic, hereditary
- Iatrogenic: post-surgical, medication-induced
- Metabolic: diabetes, thyroid disorders
- Vascular: ischemia, hemorrhage
- Idiopathic: unknown cause

**Guidelines:**
- Extract ALL causative factors mentioned
- Include both specific causes (e.g., "Staphylococcus aureus") and general categories (e.g., "bacterial infection")
- Confidence: 1.0 for explicitly stated causes; 0.7-0.9 for implied causes
- Include the disease context if mentioned

**Text to analyze:**
{text}"""

ETIOLOGY_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "etiology_entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Etiology/cause name"},
                    "category": {
                        "type": "string",
                        "enum": ["infectious", "traumatic", "autoimmune", "degenerative", "congenital", "iatrogenic", "inflammatory", "neoplastic", "vascular", "metabolic", "toxic", "idiopathic", "unclassified"],
                        "description": "Etiology category"
                    },
                    "associated_disease": {"type": "string", "description": "Disease this etiology causes (if mentioned)"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["name", "category", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["etiology_entities"],
    "additionalProperties": False
}


def load_text_blocks() -> List[Dict]:
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def extract_etiology_with_llm(text_block: Dict, stats: ExtractionStats) -> List[Dict]:
    text = text_block.get("text", "")
    if not text or len(text.strip()) < 50:
        return []

    prompt = ETIOLOGY_EXTRACTION_PROMPT.format(text=text[:3000])

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=1500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "etiology_extraction",
                    "strict": True,
                    "schema": ETIOLOGY_EXTRACTION_SCHEMA
                }
            }
        )

        with stats_lock:
            stats.llm_calls += 1
            stats.total_tokens += response.usage.prompt_tokens + response.usage.completion_tokens
            stats.total_cost += (response.usage.prompt_tokens * 5 + response.usage.completion_tokens * 15) / 1000000

        result = json.loads(response.choices[0].message.content.strip())
        entities = result.get("etiology_entities", [])

        for entity in entities:
            entity["type"] = "etiology"
            entity["metadata"] = {
                "chapter": text_block.get("chapter_number"),
                "section": text_block.get("section_title", ""),
                "extraction_method": "llm",
                "model": OPENAI_MODEL_NAME
            }

        with stats_lock:
            stats.entities_extracted += len(entities)

        return entities

    except Exception as e:
        print(f"  ⚠ Error: {e}")
        return []


def normalize_name(name: str) -> str:
    return name.lower().strip()


def deduplicate_entities(all_entities: List[Dict]) -> Dict[str, Dict]:
    entity_map = {}
    for entity in all_entities:
        normalized = normalize_name(entity["name"])
        if normalized not in entity_map:
            entity_map[normalized] = entity
        else:
            if entity.get("confidence", 0.7) > entity_map[normalized].get("confidence", 0.7):
                entity_map[normalized] = entity
    return entity_map


def create_entity_id(index: int) -> str:
    return f"etiology_{index:03d}"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--max-blocks", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-checkpoint", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: ETIOLOGY Entity Extraction (LLM)")
    print("=" * 80)

    text_blocks = load_text_blocks()
    if args.max_blocks:
        text_blocks = text_blocks[:args.max_blocks]

    print(f"  ✓ Loaded {len(text_blocks)} text blocks")

    if args.dry_run:
        print("\n[DRY RUN] Sample prompt:")
        print(ETIOLOGY_EXTRACTION_PROMPT.format(text=text_blocks[0].get("text", "")[:3000]))
        return

    stats = ExtractionStats(total_blocks=len(text_blocks))
    all_entities = []

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {executor.submit(extract_etiology_with_llm, block, stats): block for block in text_blocks}

        for future in tqdm(as_completed(futures), total=len(futures), desc="  Processing"):
            try:
                entities = future.result()
                all_entities.extend(entities)
                with stats_lock:
                    stats.blocks_processed += 1
            except Exception as e:
                print(f"\n  ⚠ Error: {e}")

    unique_entities = deduplicate_entities(all_entities)
    print(f"  ✓ Final count: {len(unique_entities)} unique entities")

    entities_list = []
    for idx, (normalized, entity) in enumerate(sorted(unique_entities.items()), 1):
        entity["entity_id"] = create_entity_id(idx)
        entity["name_normalized"] = normalized
        entities_list.append(entity)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entities_list, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved to {OUTPUT_FILE}")

    report = {
        "extraction_method": "llm_enhanced",
        "model": OPENAI_MODEL_NAME,
        "total_entities": len(entities_list),
        "statistics": {
            "blocks_processed": stats.blocks_processed,
            "total_cost_usd": round(stats.total_cost, 2)
        }
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nTotal: {len(entities_list)} | Cost: ${stats.total_cost:.2f}")


if __name__ == "__main__":
    main()
