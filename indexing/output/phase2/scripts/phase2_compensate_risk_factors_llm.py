#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract RISK_FACTOR entities using LLM (Issue 1.4)

LLM-enhanced approach for extracting risk factors from The Wills Eye Manual.

Input: Phase 1: wills_eye_text_blocks.json
Output: risk_factors_llm.json, phase2_risk_factors_llm_report.json

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_risk_factors_llm.py
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

SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "risk_factors_llm.json"
REPORT_FILE = PHASE2_DIR / "phase2_risk_factors_llm_report.json"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTAyNTk3MWYwN2ViNTczMjgzZmIxMjkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxNzYxNjQ5fQ.Wllnd6Fn-fghYv1uk18ZoXNXHDRw30vDiEwNBQXUqR8")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/68721419652cec5504661aec/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")

for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)
stats_lock = threading.Lock()


@dataclass
class ExtractionStats:
    blocks_processed: int = 0
    entities_extracted: int = 0
    total_cost: float = 0.0


RISK_FACTOR_EXTRACTION_PROMPT = """You are a medical knowledge graph expert extracting risk factor entities from The Wills Eye Manual.

**Your task:** Identify ALL risk factors that increase the likelihood of developing ocular diseases.

**Entity Type to Extract:**
- **RISK_FACTOR**: Factors that increase disease risk (e.g., "advanced age", "diabetes mellitus", "contact lens wear", "smoking", "immunocompromised state", "family history", "trauma")

**Categories:**
- Demographic: age, gender, race
- Comorbidity: diabetes, hypertension, systemic diseases
- Behavioral: smoking, contact lens wear, poor hygiene
- Environmental: exposure, climate, occupational hazards
- Anatomical: structural abnormalities
- Iatrogenic: post-surgical, medication-induced
- Genetic: family history, hereditary conditions

**Guidelines:**
- Extract ALL risk factors mentioned
- Include both modifiable (smoking) and non-modifiable (age) risk factors
- Confidence: 1.0 for explicit risk factors; 0.7-0.9 for implied factors
- Include associated disease if mentioned

**Text to analyze:**
{text}"""

RISK_FACTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_factor_entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["demographic", "comorbidity", "behavioral", "environmental", "anatomical", "iatrogenic", "genetic", "infectious", "unclassified"]
                    },
                    "associated_disease": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["name", "category", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["risk_factor_entities"],
    "additionalProperties": False
}


def load_text_blocks() -> List[Dict]:
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def extract_risk_factors_with_llm(text_block: Dict, stats: ExtractionStats) -> List[Dict]:
    text = text_block.get("text", "")
    if not text or len(text.strip()) < 50:
        return []

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=1500,
            temperature=0.0,
            messages=[{"role": "user", "content": RISK_FACTOR_EXTRACTION_PROMPT.format(text=text[:3000])}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "risk_factor_extraction",
                    "strict": True,
                    "schema": RISK_FACTOR_SCHEMA
                }
            }
        )

        with stats_lock:
            stats.total_cost += (response.usage.prompt_tokens * 5 + response.usage.completion_tokens * 15) / 1000000

        result = json.loads(response.choices[0].message.content.strip())
        entities = result.get("risk_factor_entities", [])

        for entity in entities:
            entity["type"] = "risk_factor"
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
        return []


def deduplicate_entities(all_entities: List[Dict]) -> Dict[str, Dict]:
    entity_map = {}
    for entity in all_entities:
        normalized = entity["name"].lower().strip()
        if normalized not in entity_map or entity.get("confidence", 0) > entity_map[normalized].get("confidence", 0):
            entity_map[normalized] = entity
    return entity_map


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2: RISK_FACTOR Extraction (LLM)")
    print("=" * 80)

    text_blocks = load_text_blocks()
    print(f"  ✓ Loaded {len(text_blocks)} blocks")

    if args.dry_run:
        print("\n[DRY RUN] Sample:")
        print(RISK_FACTOR_EXTRACTION_PROMPT.format(text=text_blocks[0].get("text", "")[:500]))
        return

    stats = ExtractionStats()
    all_entities = []

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {executor.submit(extract_risk_factors_with_llm, block, stats): block for block in text_blocks}

        for future in tqdm(as_completed(futures), total=len(futures)):
            entities = future.result()
            all_entities.extend(entities)
            stats.blocks_processed += 1

    unique_entities = deduplicate_entities(all_entities)
    entities_list = [dict(entity, entity_id=f"risk_factor_{i:03d}", name_normalized=norm)
                     for i, (norm, entity) in enumerate(sorted(unique_entities.items()), 1)]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entities_list, f, indent=2, ensure_ascii=False)

    report = {"extraction_method": "llm", "total": len(entities_list), "cost_usd": round(stats.total_cost, 2)}
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ {len(entities_list)} entities | ${stats.total_cost:.2f}")


if __name__ == "__main__":
    main()
