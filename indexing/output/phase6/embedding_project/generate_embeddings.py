"""
Embedding Generation for GraphRAG Knowledge Graph
=================================================

Generates vector embeddings for medical entities using PubMedBERT.
Can be run on a separate machine with GPU support.

Usage:
    python generate_embeddings.py [--batch-size 32] [--device cuda|cpu]

Author: GraphRAG Preparation Pipeline
Date: 2025-10-23
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm


class EmbeddingGenerator:
    """Generates embeddings for medical entities using PubMedBERT."""

    def __init__(
        self,
        model_name: str = "NeuML/pubmedbert-base-embeddings",
        device: str = "auto",
        batch_size: int = 32
    ):
        self.model_name = model_name
        self.batch_size = batch_size

        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device}")
        print(f"Loading model: {model_name}")

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir="./embedding_cache"
        )
        self.model = AutoModel.from_pretrained(
            model_name,
            cache_dir="./embedding_cache"
        ).to(self.device)

        self.model.eval()  # Set to evaluation mode

        self.stats = {
            "total_entities": 0,
            "embeddings_generated": 0,
            "failed": 0,
            "avg_text_length": 0
        }

    def create_entity_text(self, node: Dict) -> str:
        """Create text representation of entity for embedding."""
        parts = []

        # Main label
        if "label" in node:
            parts.append(node["label"])

        # Type
        if "type" in node:
            parts.append(f"Type: {node['type']}")

        # Description
        if "properties" in node and "description" in node["properties"]:
            parts.append(node["properties"]["description"])

        # Synonyms
        if "properties" in node and "synonyms" in node["properties"]:
            synonyms = node["properties"]["synonyms"]
            if synonyms:
                parts.append(f"Synonyms: {', '.join(synonyms[:5])}")  # Limit to 5

        # Medical codes (provides additional context)
        if "properties" in node:
            props = node["properties"]
            if "icd_10" in props and props["icd_10"]:
                parts.append(f"ICD-10: {props['icd_10']}")
            if "snomed_ct" in props and props["snomed_ct"]:
                parts.append(f"SNOMED: {props['snomed_ct']}")

        # Urgency (for diseases)
        if "properties" in node and "urgency_level" in node["properties"]:
            parts.append(f"Urgency: {node['properties']['urgency_level']}")

        return ". ".join(parts)

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        # Generate embedding
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Use [CLS] token embedding (first token)
        embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]

        return embedding

    def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts."""
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Use [CLS] token embeddings
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        return [emb for emb in embeddings]

    def process_nodes(self, nodes: List[Dict]) -> Dict[str, List[float]]:
        """Process all nodes and generate embeddings."""
        self.stats["total_entities"] = len(nodes)

        embeddings_map = {}
        texts = []
        node_ids = []

        print(f"\nProcessing {len(nodes)} entities...")

        # Prepare texts
        for node in tqdm(nodes, desc="Preparing texts"):
            text = self.create_entity_text(node)
            texts.append(text)
            node_ids.append(node["id"])
            self.stats["avg_text_length"] += len(text)

        self.stats["avg_text_length"] /= len(nodes)

        # Generate embeddings in batches
        print(f"\nGenerating embeddings (batch size: {self.batch_size})...")
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Generating embeddings"):
            batch_texts = texts[i:i+self.batch_size]
            batch_ids = node_ids[i:i+self.batch_size]

            try:
                batch_embeddings = self.generate_batch_embeddings(batch_texts)

                for node_id, embedding in zip(batch_ids, batch_embeddings):
                    embeddings_map[node_id] = embedding.tolist()
                    self.stats["embeddings_generated"] += 1

            except Exception as e:
                print(f"\nError processing batch {i}-{i+self.batch_size}: {e}")
                self.stats["failed"] += len(batch_texts)

        return embeddings_map

    def generate_report(self) -> Dict:
        """Generate embedding generation report."""
        return {
            "phase": "6.3",
            "title": "Embedding Generation",
            "model": self.model_name,
            "device": self.device,
            "generated_at": datetime.now().isoformat(),
            "statistics": self.stats,
            "validation": {
                "embeddings_generated": self.stats["embeddings_generated"] > 0,
                "success_rate": self.stats["embeddings_generated"] / self.stats["total_entities"]
                if self.stats["total_entities"] > 0 else 0
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for GraphRAG entities")
    parser.add_argument(
        "--input",
        type=str,
        default="graphrag_nodes.json",
        help="Input nodes file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="embeddings_output.json",
        help="Output embeddings file"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to use (auto, cuda, cpu)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="NeuML/pubmedbert-base-embeddings",
        help="Model name (default: NeuML/pubmedbert-base-embeddings)"
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        print("\nPlease copy graphrag_nodes.json from the main project to this directory.")
        return

    # Load nodes
    print(f"Loading nodes from {args.input}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        nodes = json.load(f)

    print(f"Loaded {len(nodes)} nodes")

    # Generate embeddings
    generator = EmbeddingGenerator(
        model_name=args.model,
        device=args.device,
        batch_size=args.batch_size
    )

    embeddings = generator.process_nodes(nodes)

    # Save embeddings
    output_path = Path(args.output)
    print(f"\nSaving embeddings to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, indent=2)

    # Generate and save report
    report = generator.generate_report()
    report_path = Path("embeddings_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("Embedding Generation Complete")
    print("=" * 80)
    print(f"Total entities: {generator.stats['total_entities']}")
    print(f"Embeddings generated: {generator.stats['embeddings_generated']}")
    print(f"Failed: {generator.stats['failed']}")
    print(f"Average text length: {generator.stats['avg_text_length']:.1f} chars")
    print(f"\nOutputs:")
    print(f"  - {output_path}")
    print(f"  - {report_path}")
    print("\nNext steps:")
    print("  1. Copy embeddings_output.json to indexing/output/phase6/entity_embeddings.json")
    print("  2. Copy embeddings_report.json to indexing/output/phase6/embeddings_report.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
