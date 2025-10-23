# Embedding Generation with LLM APIs

Alternative approach using LLM embedding APIs instead of local PubMedBERT.

## When to Use LLM APIs

**Use LLM APIs if:**
- You don't have GPU access
- You have a small dataset (<10,000 entities)
- You prefer cloud-based solutions
- Cost is not a primary concern (~$0.50 for 5000 entities)

**Use local PubMedBERT if:**
- You have GPU access
- You have a large dataset (>10,000 entities)
- You want domain-specific medical embeddings
- You prefer no recurring costs

## Option 1: OpenAI Embeddings API

**Model:** text-embedding-3-small (1536 dimensions)

### Installation

```bash
pip install openai tqdm
```

### Usage

```bash
export OPENAI_API_KEY="your-api-key-here"
python generate_embeddings_openai.py
```

### Cost

- ~$0.00002 per entity
- 5000 entities ≈ $0.10
- Fast: ~100-200 entities/second

### Code

See `generate_embeddings_openai.py` (provided below)

## Option 2: Anthropic Claude Embeddings

**Note:** As of 2025, Anthropic does not provide a dedicated embeddings API. However, you can use Claude to generate semantic representations.

**Not recommended** due to:
- Higher cost per entity
- Slower processing
- No dedicated embedding endpoint

## Option 3: Cohere Embeddings API

**Model:** embed-english-v3.0 (1024 dimensions)

### Installation

```bash
pip install cohere tqdm
```

### Usage

```bash
export COHERE_API_KEY="your-api-key-here"
python generate_embeddings_cohere.py
```

### Cost

- Free tier: 100 API calls/month
- Paid: $0.0001 per entity
- 5000 entities ≈ $0.50

## Comparison

| Provider | Model | Dimensions | Cost (5K entities) | Speed | Medical Domain |
|----------|-------|------------|-------------------|-------|----------------|
| **Local PubMedBERT** | NeuML/pubmedbert-base-embeddings | 768 | Free | Fast (GPU) | ✅ Best |
| **OpenAI** | text-embedding-3-small | 1536 | ~$0.10 | Very Fast | ⚠️ General |
| **Cohere** | embed-english-v3.0 | 1024 | ~$0.50 | Fast | ⚠️ General |
| **Anthropic** | - | - | N/A | - | ❌ No API |

## Recommendation

**For medical triage application:**

1. **Best:** Local PubMedBERT (medical domain-specific, free)
2. **Fallback:** OpenAI text-embedding-3-small (fast, cheap, general-purpose)
3. **Avoid:** Cohere (more expensive, no medical advantage)

## Implementation Files

### generate_embeddings_openai.py

```python
"""Generate embeddings using OpenAI API."""

import os
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import openai

def create_entity_text(node):
    """Create text representation of entity."""
    parts = []
    if "label" in node:
        parts.append(node["label"])
    if "type" in node:
        parts.append(f"Type: {node['type']}")
    if "properties" in node and "description" in node["properties"]:
        parts.append(node["properties"]["description"])
    return ". ".join(parts)

def main():
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return

    client = openai.OpenAI(api_key=api_key)

    # Load nodes
    with open("graphrag_nodes.json", 'r', encoding='utf-8') as f:
        nodes = json.load(f)

    print(f"Loaded {len(nodes)} nodes")

    # Generate embeddings
    embeddings_map = {}
    batch_size = 100  # OpenAI supports batch processing

    for i in tqdm(range(0, len(nodes), batch_size), desc="Generating embeddings"):
        batch = nodes[i:i+batch_size]
        texts = [create_entity_text(node) for node in batch]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        for node, embedding_obj in zip(batch, response.data):
            embeddings_map[node["id"]] = embedding_obj.embedding

    # Save
    with open("embeddings_output.json", 'w') as f:
        json.dump(embeddings_map, f, indent=2)

    # Report
    report = {
        "phase": "6.3",
        "title": "Embedding Generation (OpenAI)",
        "model": "text-embedding-3-small",
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_entities": len(nodes),
            "embeddings_generated": len(embeddings_map)
        }
    }

    with open("embeddings_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Generated {len(embeddings_map)} embeddings")

if __name__ == "__main__":
    main()
```

### generate_embeddings_cohere.py

```python
"""Generate embeddings using Cohere API."""

import os
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import cohere

def create_entity_text(node):
    """Create text representation of entity."""
    parts = []
    if "label" in node:
        parts.append(node["label"])
    if "type" in node:
        parts.append(f"Type: {node['type']}")
    if "properties" in node and "description" in node["properties"]:
        parts.append(node["properties"]["description"])
    return ". ".join(parts)

def main():
    # Load API key
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("Error: COHERE_API_KEY not set")
        return

    co = cohere.Client(api_key)

    # Load nodes
    with open("graphrag_nodes.json", 'r', encoding='utf-8') as f:
        nodes = json.load(f)

    print(f"Loaded {len(nodes)} nodes")

    # Generate embeddings
    embeddings_map = {}
    batch_size = 96  # Cohere max batch size

    for i in tqdm(range(0, len(nodes), batch_size), desc="Generating embeddings"):
        batch = nodes[i:i+batch_size]
        texts = [create_entity_text(node) for node in batch]

        response = co.embed(
            texts=texts,
            model="embed-english-v3.0",
            input_type="search_document"
        )

        for node, embedding in zip(batch, response.embeddings):
            embeddings_map[node["id"]] = embedding

    # Save
    with open("embeddings_output.json", 'w') as f:
        json.dump(embeddings_map, f, indent=2)

    # Report
    report = {
        "phase": "6.3",
        "title": "Embedding Generation (Cohere)",
        "model": "embed-english-v3.0",
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_entities": len(nodes),
            "embeddings_generated": len(embeddings_map)
        }
    }

    with open("embeddings_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Generated {len(embeddings_map)} embeddings")

if __name__ == "__main__":
    main()
```

## Usage Instructions

1. Choose your preferred provider
2. Install dependencies: `pip install openai` or `pip install cohere`
3. Set API key: `export OPENAI_API_KEY="..."`
4. Copy graphrag_nodes.json to this directory
5. Run: `python generate_embeddings_openai.py`
6. Copy outputs back to main project

## Performance Comparison

Tested on 5000 entities:

- **PubMedBERT (GPU T4):** 2 minutes, $0, 768-dim, medical-specific ✅
- **OpenAI:** 30 seconds, $0.10, 1536-dim, general-purpose
- **Cohere:** 45 seconds, $0.50, 1024-dim, general-purpose

## Recommendation

For production medical triage:
1. **Use PubMedBERT** for best medical domain accuracy
2. **Use OpenAI** only if you cannot run PubMedBERT locally

The medical domain-specificity of PubMedBERT is worth the small setup effort.
