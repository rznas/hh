# Embedding Generation Project

This is a standalone Python project for generating embeddings for the GraphRAG knowledge graph. It can be run on a separate machine with GPU support for faster embedding generation.

## Overview

Generates vector embeddings for all medical entities using **PubMedBERT**, a biomedical domain-specific model. These embeddings enable semantic search in the Neo4j knowledge graph.

## Requirements

- Python 3.9+
- GPU recommended (CUDA) for faster processing
- ~4GB disk space for model + embeddings
- ~8GB RAM minimum

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Step 1: Copy Input Files

Copy the following files from the main project to this directory:

```
graphrag_nodes.json  (from indexing/output/phase6/)
```

### Step 2: Generate Embeddings

```bash
# Run embedding generation
python generate_embeddings.py

# Options:
python generate_embeddings.py --batch-size 32  # Adjust batch size based on GPU memory
python generate_embeddings.py --model pubmedbert  # Default
python generate_embeddings.py --device cuda  # Use GPU (default if available)
python generate_embeddings.py --device cpu  # Force CPU
```

### Step 3: Copy Output Back

Copy the generated files back to the main project:

```
embeddings_output.json → indexing/output/phase6/entity_embeddings.json
embeddings_report.json → indexing/output/phase6/embeddings_report.json
```

## Output Files

- **embeddings_output.json**: Entity IDs mapped to embeddings (768-dimensional vectors)
- **embeddings_report.json**: Statistics and validation report
- **embedding_cache/**: Cached model files (can be deleted after completion)

## Model Information

**PubMedBERT Embeddings** (NeuML/pubmedbert-base-embeddings)
- Domain: Biomedical text (optimized for embeddings)
- Embedding dimension: 768
- Pre-trained on: PubMed abstracts and full-text articles
- Better for medical entities than general-purpose models
- Optimized for semantic similarity and search tasks

## Performance

Approximate processing times:
- CPU: ~1-2 entities/second (~1-2 hours for 5000 entities)
- GPU (T4): ~50-100 entities/second (~1-5 minutes for 5000 entities)
- GPU (A100): ~200+ entities/second (<1 minute for 5000 entities)

## Troubleshooting

### Out of Memory Error
Reduce batch size: `python generate_embeddings.py --batch-size 8`

### CUDA Not Available
Install PyTorch with CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Slow on CPU
Consider using cloud GPU (Google Colab, AWS, etc.) or reduce dataset size for testing

## Alternative: Using LLM for Rerun

If you want to use an LLM API (Claude/GPT) instead of local embeddings:

See: `RERUN_WITH_LLM.md` for instructions on using OpenAI embeddings API or Anthropic Claude embeddings.

This approach:
- ✅ No local compute required
- ✅ Faster for small datasets
- ❌ Cost: ~$0.0001 per entity (~$0.50 for 5000 entities)
- ❌ Requires API key and internet connection

## License

This project uses PubMedBERT which is licensed under Apache 2.0.
