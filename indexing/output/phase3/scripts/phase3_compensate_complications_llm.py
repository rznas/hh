#!/usr/bin/env python3
"""
Phase 3 Compensation: Extract complication relationships using LLM (Issue 2.9)

LLM-enhanced extraction of complicates and temporal_follows relationships.

Input: Phase 1 text blocks + Phase 2 diseases
Output: complicates_edges_llm.json, temporal_follows_edges_llm.json

Usage:
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_complications_llm.py
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
PHASE2_DIR = SCRIPT_DIR.parent.parent / "phase2"
PHASE3_DIR = SCRIPT_DIR.parent

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
    relationships_extracted: int = 0
    total_cost: float = 0.0


COMPLICATION_EXTRACTION_PROMPT = """You are extracting complication and progression relationships from medical text.

**Your task:** Identify disease complications and progression patterns.

**Relationship Types to Extract:**

1. **complicates**: One disease is a complication of another
   Example: "Corneal perforation is a complication of untreated keratitis"
   → (Corneal perforation, complicates, Keratitis)

2. **temporal_follows**: One disease progresses/evolves into another
   Example: "Conjunctivitis may progress to keratitis"
   → (Keratitis, temporal_follows, Conjunctivitis)

**Guidelines:**
- Extract ALL complication and progression relationships
- Source is the complication/later disease, target is the primary/earlier disease
- Confidence: 1.0 for explicit statements, 0.7-0.9 for implied
- Include context

**Text to analyze:**
{text}"""

COMPLICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_disease": {"type": "string", "description": "Complication/later disease"},
                    "target_disease": {"type": "string", "description": "Primary/earlier disease"},
                    "relationship_type": {
                        "type": "string",
                        "enum": ["complicates", "temporal_follows"]
                    },
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "context": {"type": "string"}
                },
                "required": ["source_disease", "target_disease", "relationship_type", "confidence"],
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


def load_diseases() -> Dict[str, str]:
    """Load diseases and create name->id map."""
    file_path = PHASE2_DIR / "diseases.json"
    if not file_path.exists():
        return {}

    with open(file_path, encoding="utf-8") as f:
        entities = json.load(f)

    return {e.get("name", "").lower(): e.get("entity_id", "") for e in entities}


def extract_complications_with_llm(text_block: Dict, stats: ExtractionStats, diseases: Dict[str, str]) -> List[Dict]:
    text = text_block.get("text", "")
    if not text or len(text.strip()) < 100:
        return []

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=1500,
            temperature=0.0,
            messages=[{"role": "user", "content": COMPLICATION_EXTRACTION_PROMPT.format(text=text[:3500])}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "complication_extraction",
                    "strict": True,
                    "schema": COMPLICATION_SCHEMA
                }
            }
        )

        with stats_lock:
            stats.total_cost += (response.usage.prompt_tokens * 5 + response.usage.completion_tokens * 15) / 1000000

        result = json.loads(response.choices[0].message.content.strip())
        relationships = result.get("relationships", [])

        # Resolve entity IDs
        resolved_edges = []
        for rel in relationships:
            source_name = rel.get("source_disease", "").lower().strip()
            target_name = rel.get("target_disease", "").lower().strip()

            source_id = diseases.get(source_name, "")
            target_id = diseases.get(target_name, "")

            if source_id and target_id and source_id != target_id:
                resolved_edges.append({
                    "source": source_id,
                    "target": target_id,
                    "relationship_type": rel.get("relationship_type", "complicates"),
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
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3: Complication Relationships (LLM)")
    print("=" * 80)

    diseases = load_diseases()
    text_blocks = load_text_blocks()
    print(f"  ✓ {len(diseases)} diseases")
    print(f"  ✓ {len(text_blocks)} blocks")

    if args.dry_run:
        print("\n[DRY RUN]")
        print(COMPLICATION_EXTRACTION_PROMPT.format(text=text_blocks[0].get("text", "")[:500]))
        return

    stats = ExtractionStats()
    all_edges = []

    with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        futures = {executor.submit(extract_complications_with_llm, block, stats, diseases): block for block in text_blocks}

        for future in tqdm(as_completed(futures), total=len(futures)):
            edges = future.result()
            all_edges.extend(edges)
            stats.blocks_processed += 1

    # Separate by type
    complicates_edges = [e for e in all_edges if e["relationship_type"] == "complicates"]
    temporal_edges = [e for e in all_edges if e["relationship_type"] == "temporal_follows"]

    print("\nSaving edges...")
    with open(PHASE3_DIR / "complicates_edges_llm.json", "w", encoding="utf-8") as f:
        json.dump(complicates_edges, f, indent=2, ensure_ascii=False)
    print(f"  ✓ complicates: {len(complicates_edges)}")

    with open(PHASE3_DIR / "temporal_follows_edges_llm.json", "w", encoding="utf-8") as f:
        json.dump(temporal_edges, f, indent=2, ensure_ascii=False)
    print(f"  ✓ temporal_follows: {len(temporal_edges)}")

    report = {
        "method": "llm",
        "total": len(all_edges),
        "cost_usd": round(stats.total_cost, 2),
        "by_type": {
            "complicates": len(complicates_edges),
            "temporal_follows": len(temporal_edges)
        }
    }
    with open(PHASE3_DIR / "phase3_complications_llm_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Total: {len(all_edges)} | Cost: ${stats.total_cost:.2f}")


if __name__ == "__main__":
    main()
