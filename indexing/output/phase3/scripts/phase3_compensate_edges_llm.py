#!/usr/bin/env python3
"""
Phase 3 Compensation: Extract missing edge types using LLM

LLM-enhanced extraction of: caused_by, affects, increases_risk, contraindicates

Input: Phase 1 text blocks + Phase 2 entities
Output: caused_by_edges_llm.json, affects_edges_llm.json, increases_risk_edges_llm.json, contraindicates_edges_llm.json

Usage:
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_edges_llm.py
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
import sys

SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent.parent / "phase2"
PHASE3_DIR = SCRIPT_DIR.parent
INVALID_RESPONSES_DIR = PHASE3_DIR / "invalid_responses"

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from llm_schema_utils import InvalidResponseHandler, SchemaValidator

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTA0ZTRlNzZhMjI0NjZkMzJjZjRjZDIiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxOTI4NDIzfQ.OTuh9hdtjeF6Bi2xrqVnOlam_HGfKNniVyoUbjqfHbs")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/6904e4e0298745c23b64f56d/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct")

for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)
stats_lock = threading.Lock()


@dataclass
class ExtractionStats:
    blocks_processed: int = 0
    relationships_extracted: int = 0
    total_cost: float = 0.0
    schema_validation_failures: int = 0


RELATIONSHIP_EXTRACTION_PROMPT = """You are extracting medical relationships from The Wills Eye Manual text.

**Your task:** Identify relationships between medical entities in the text.

**Relationship Types to Extract:**

1. **caused_by**: Disease → Etiology (cause)
   Example: "Keratitis caused by bacteria" → (Keratitis, caused_by, bacteria)

2. **affects**: Disease → Anatomy (affected structure)
   Example: "Glaucoma affects the optic nerve" → (Glaucoma, affects, optic nerve)

3. **increases_risk**: Risk Factor → Disease
   Example: "Diabetes increases risk for retinopathy" → (Diabetes, increases_risk, retinopathy)

4. **contraindicates**: Condition → Treatment (CRITICAL for safety)
   Example: "Steroids contraindicated in viral keratitis" → (viral keratitis, contraindicates, steroids)

**Guidelines:**
- Extract ALL relationships present in the text
- Use entity names exactly as they appear
- Confidence: 1.0 for explicit, 0.7-0.9 for implied
- Include context snippet

**Text to analyze:**
{text}"""

RELATIONSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_entity": {"type": "string"},
                    "target_entity": {"type": "string"},
                    "relationship_type": {
                        "type": "string",
                        "enum": ["caused_by", "affects", "increases_risk", "contraindicates"]
                    },
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "context": {"type": "string"}
                },
                "required": ["source_entity", "target_entity", "relationship_type", "confidence"],
                "additionalProperties": False
            }
        }
    },
    "required": ["relationships"],
    "additionalProperties": False
}


def load_text_blocks() -> List[Dict]:
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def load_entities(entity_type: str) -> Dict[str, str]:
    """Load entities and create name->id map."""
    file_path = PHASE2_DIR / f"{entity_type}.json"
    if not file_path.exists():
        return {}

    with open(file_path, encoding="utf-8") as f:
        entities = json.load(f)

    return {e.get("name", "").lower(): e.get("entity_id", "") for e in entities}


def find_entity_id(entity_name: str, entity_maps: List[Dict[str, str]]) -> str:
    """Find entity ID across multiple entity types."""
    name_lower = entity_name.lower().strip()
    for entity_map in entity_maps:
        if name_lower in entity_map:
            return entity_map[name_lower]
    return ""


def extract_relationships_with_llm(text_block: Dict, stats: ExtractionStats, entity_maps: Dict, invalid_handler: InvalidResponseHandler) -> List[Dict]:
    text = text_block.get("text", "")
    if not text or len(text.strip()) < 100:
        return []

    prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(text=text)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=2000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "relationship_extraction",
                    "strict": True,
                    "schema": RELATIONSHIP_SCHEMA
                }
            }
        )

        with stats_lock:
            stats.total_cost += (response.usage.prompt_tokens * 5 + response.usage.completion_tokens * 15) / 1000000

        # Parse and validate response
        response_text = response.choices[0].message.content.strip()
        is_valid, parsed_json, error_msg = SchemaValidator.validate(
            response_text,
            RELATIONSHIP_SCHEMA,
            strict=True
        )

        if not is_valid:
            with stats_lock:
                stats.schema_validation_failures += 1
            invalid_handler.record_invalid_response(
                text_block=text_block,
                prompt=prompt,
                llm_response=response_text,
                error=error_msg,
                schema=RELATIONSHIP_SCHEMA
            )
            return []

        result = parsed_json
        relationships = result.get("relationships", [])

        # Resolve entity IDs
        resolved_edges = []
        for rel in relationships:
            source_name = rel.get("source_entity", "")
            target_name = rel.get("target_entity", "")
            rel_type = rel.get("relationship_type", "")

            # Find entity IDs
            if rel_type == "caused_by":
                source_id = find_entity_id(source_name, [entity_maps["diseases"]])
                target_id = find_entity_id(target_name, [entity_maps["etiologies"]])
            elif rel_type == "affects":
                source_id = find_entity_id(source_name, [entity_maps["diseases"]])
                target_id = find_entity_id(target_name, [entity_maps["anatomy"]])
            elif rel_type == "increases_risk":
                source_id = find_entity_id(source_name, [entity_maps["risk_factors"]])
                target_id = find_entity_id(target_name, [entity_maps["diseases"]])
            elif rel_type == "contraindicates":
                source_id = find_entity_id(source_name, [entity_maps["diseases"]])
                target_id = find_entity_id(target_name, [entity_maps["treatments"], entity_maps["medications"], entity_maps["procedures"]])
            else:
                continue

            if source_id and target_id:
                resolved_edges.append({
                    "source": source_id,
                    "target": target_id,
                    "relationship_type": rel_type,
                    "confidence": rel.get("confidence", 0.8),
                    "context": rel.get("context", "")[:200],
                    "metadata": {
                        "chapter": text_block.get("chapter_number"),
                        "extraction_method": "llm",
                        "model": OPENAI_MODEL_NAME
                    }
                })

        with stats_lock:
            stats.relationships_extracted += len(resolved_edges)

        return resolved_edges

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


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3: Missing Edge Types Extraction (LLM)")
    print("=" * 80)

    # Load entities
    print("Loading entities...")
    entity_maps = {
        "diseases": load_entities("diseases"),
        "etiologies": load_entities("etiology"),
        "anatomy": load_entities("anatomy"),
        "risk_factors": load_entities("risk_factors"),
        "treatments": load_entities("treatments"),
        "medications": load_entities("medications"),
        "procedures": load_entities("procedures")
    }

    text_blocks = load_text_blocks()
    print(f"  ✓ {len(text_blocks)} blocks")

    if args.dry_run:
        print("\n[DRY RUN]")
        print(RELATIONSHIP_EXTRACTION_PROMPT.format(text=text_blocks[0].get("text", "")[:500]))
        return

    # Initialize invalid response handler
    invalid_handler = InvalidResponseHandler(INVALID_RESPONSES_DIR, "edges")

    stats = ExtractionStats()
    all_edges = []

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {executor.submit(extract_relationships_with_llm, block, stats, entity_maps, invalid_handler): block for block in text_blocks}

        for future in tqdm(as_completed(futures), total=len(futures)):
            edges = future.result()
            all_edges.extend(edges)
            stats.blocks_processed += 1

    # Separate by type
    edges_by_type = {"caused_by": [], "affects": [], "increases_risk": [], "contraindicates": []}
    for edge in all_edges:
        rel_type = edge["relationship_type"]
        if rel_type in edges_by_type:
            edges_by_type[rel_type].append(edge)

    # Save
    print("\nSaving edges...")
    for rel_type, edges in edges_by_type.items():
        output_file = PHASE3_DIR / f"{rel_type}_edges_llm.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(edges, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {rel_type}: {len(edges)}")

    # Save invalid responses for manual review
    invalid_count, invalid_file = invalid_handler.save_invalid_responses()
    if invalid_count > 0:
        print(f"  ⚠ {invalid_count} invalid responses saved to {invalid_file}")

    report = {
        "method": "llm",
        "total": len(all_edges),
        "cost_usd": round(stats.total_cost, 2),
        "by_type": {k: len(v) for k, v in edges_by_type.items()},
        "schema_validation_failures": stats.schema_validation_failures
    }
    with open(PHASE3_DIR / "phase3_compensation_llm_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Total: {len(all_edges)} | Cost: ${stats.total_cost:.2f}")
    print(f"Schema Validation Failures: {stats.schema_validation_failures}")


if __name__ == "__main__":
    main()
