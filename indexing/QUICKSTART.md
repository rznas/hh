# Quick Start Guide - Knowledge Graph Indexing

## Prerequisites

1. **Neo4j Database**
   - Install Neo4j Desktop or use Neo4j AuraDB
   - Version 5.0+ recommended
   - Start the database and note connection details

2. **OpenAI API Key** (or compatible endpoint)
   - For Graphiti's LLM operations
   - Can use custom endpoints (Azure OpenAI, local LLM, etc.)

3. **Python 3.10+**

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd indexing

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# REQUIRED:
#   - NEO4J_PASSWORD
#   - CUSTOM_OPENAI_API_KEY
```

Example `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

CUSTOM_OPENAI_BASE_URL=https://api.openai.com/v1
CUSTOM_OPENAI_API_KEY=sk-...
CUSTOM_OPENAI_MODEL=gpt-4
```

### 3. Verify Setup

```bash
# Test configuration
python -c "from config import validate_config; validate_config(); print('✓ Config valid')"
```

## Usage Examples

### Dry Run (Preview)
```bash
# See what will be indexed without actually indexing
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --dry-run
```

Output:
```
======================================================================
  Wills Eye Manual - Knowledge Graph Indexing
======================================================================

----------------------------------------------------------------------
  DRY RUN - Preview Mode
----------------------------------------------------------------------

Chapter: Trauma
  ├─ Conditions: 23
  ├─ Sample: 3.1 Chemical Burn
  ├─ Urgency: EMERGENT
  ├─ Red Flags: 2
  ├─ Entities: 45
  └─ Relationships: 127

Total conditions to index: 23
Estimated episodes: 23
----------------------------------------------------------------------
```

### Index Single Chapter (Recommended First)
```bash
# Start with Trauma chapter (well-defined, critical)
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --chapter "Trauma"
```

### Index Multiple Chapters
```bash
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --chapter "Trauma" \
    --chapter "Cornea" \
    --chapter "Glaucoma"
```

### Index All Chapters
```bash
# Full indexing (10-15 minutes)
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json
```

### With Verbose Logging
```bash
python index_knowledge_graph.py \
    --data ../data/wills_eye_structured.json \
    --chapter "Trauma" \
    --verbose
```

## Testing the Graph

### Test Parser (Standalone)
```bash
cd parsers
python wills_eye_parser.py
```

### Test Graphiti Client
```bash
python -c "
import asyncio
from graphiti_client import GraphitiClient

async def test():
    client = GraphitiClient()
    print('✓ Graphiti client connected')
    client.close()

asyncio.run(test())
"
```

### Test Embeddings
```bash
python embedding_service.py
```

Expected output:
```
Embedding shape: (768,)
Embedding dimension: 768

User: 'I can't see out of my left eye'
Matches:
  - sudden vision loss: 0.892
  - blurry vision: 0.756
  - floaters: 0.634
```

## Querying the Graph

After indexing, you can query using Python:

```python
import asyncio
from graph_builder import GraphIndexer

async def query_example():
    indexer = GraphIndexer("../data/wills_eye_structured.json")

    # Search for conditions by symptom
    results = await indexer.builder.search_conditions_by_symptom(
        "eye pain",
        urgency_filter="EMERGENT"
    )

    print(f"Found {len(results)} emergent conditions with eye pain")

    # Check for red flags
    red_flags = await indexer.builder.check_for_red_flags(
        ["sudden vision loss", "severe pain"]
    )

    print(f"Red flag conditions: {red_flags}")

    indexer.close()

asyncio.run(query_example())
```

## Troubleshooting

### Issue: "NEO4J_PASSWORD is required"
**Solution:** Set environment variable in `.env` file

### Issue: "Cannot connect to Neo4j"
**Solution:**
1. Check Neo4j is running: `neo4j status`
2. Verify URI in `.env` matches Neo4j connection details
3. Test connection: `neo4j-admin database ping`

### Issue: "OpenAI API key invalid"
**Solution:**
1. Verify API key is correct in `.env`
2. Check API key has not expired
3. For custom endpoints, verify `CUSTOM_OPENAI_BASE_URL`

### Issue: "Out of memory during embedding"
**Solution:** Reduce batch size in `.env`:
```bash
EMBEDDING_BATCH_SIZE=16  # Default is 32
BATCH_SIZE=5             # Default is 10
```

### Issue: UnicodeDecodeError
**Solution:** Ensure JSON file is UTF-8 encoded

### Issue: "Model not found" (BioBERT)
**Solution:** First run will download model (~400MB). Ensure internet connection.

## Performance Optimization

### Use GPU for Embeddings
If you have NVIDIA GPU:
```bash
# Install CUDA-enabled PyTorch first
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

The embedding service will auto-detect and use GPU.

### Batch Size Tuning
- **CPU**: `BATCH_SIZE=5-10`
- **GPU**: `BATCH_SIZE=20-50`

### Parallel Processing
```bash
# Increase workers (requires more memory)
MAX_WORKERS=8  # Default is 4
```

## Output Files

After indexing:
- `knowledge_graph_indexing.log` - Detailed log
- `indexing_results_YYYYMMDD_HHMMSS.json` - Summary statistics
- `indexing_errors.json` - Failed entries (if any)

## Next Steps

1. **Validate Indexing:**
   ```bash
   python index_knowledge_graph.py \
       --data ../data/wills_eye_structured.json \
       --chapter "Trauma"

   # Check validation results in output
   ```

2. **Integrate with Triage Agent:**
   - Use `graph_builder.py` in `backend/apps/triage/services/`
   - Query graph for differential diagnosis
   - Check red flags during triage

3. **Monitor Performance:**
   - Check Neo4j query performance
   - Optimize indexes if needed
   - Add Langfuse monitoring for LLM calls

## Environment Variables Reference

### Required
| Variable | Description | Example |
|----------|-------------|---------|
| `NEO4J_PASSWORD` | Neo4j database password | `your_password` |
| `CUSTOM_OPENAI_API_KEY` | OpenAI API key | `sk-...` |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `CUSTOM_OPENAI_BASE_URL` | Custom OpenAI endpoint | `https://api.openai.com/v1` |
| `CUSTOM_OPENAI_MODEL` | LLM model name | `gpt-4` |
| `EMBEDDING_MODEL` | Sentence transformer model | `BioBERT-...` |
| `EMBEDDING_BATCH_SIZE` | Embedding batch size | `32` |
| `BATCH_SIZE` | Indexing batch size | `10` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Support

For issues:
1. Check logs in `knowledge_graph_indexing.log`
2. Review `indexing_errors.json` for failed entries
3. See main README.md for detailed troubleshooting
4. Consult `docs/technical/graphrag-strategy.md` for architecture details
