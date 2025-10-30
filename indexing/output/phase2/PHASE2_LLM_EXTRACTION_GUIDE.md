# Phase 2 LLM-Enhanced Entity Extraction Guide

## Overview

Phase 2 extracts medical entities from The Wills Eye Manual using LLM (Language Model) for high accuracy and completeness. This approach is superior to pattern-matching and handles medical terminology variations effectively.

**This is a replacement/enhancement of the existing Phase 2 rule-based extraction methods.**

## What Gets Extracted

Phase 2 extracts **5 types of medical entities**:

1. **DISEASE** - Ocular conditions/diseases
   - Examples: Keratitis, Glaucoma, Retinal Detachment, Corneal Ulcer
   - Output file: `diseases.json`

2. **SYMPTOM** - Patient-reported symptoms
   - Examples: Pain, vision loss, photophobia, blurred vision, floaters
   - Output file: `symptoms.json`

3. **SIGN** - Clinical examination findings
   - Examples: Corneal edema, exudate, infiltrate, anterior chamber reaction
   - Output file: `signs.json`

4. **TREATMENT** - Medications, procedures, interventions
   - Examples: Antibiotics, surgery, laser therapy, topical steroids
   - Output file: `treatments.json`

5. **DIAGNOSTIC_TEST** - Diagnostic tests and imaging modalities
   - Examples: OCT, fluorescein staining, tonometry, slit lamp examination
   - Output file: `diagnostic_tests.json`

## How It Works

### Processing Pipeline

```
Phase 1 Text Blocks
         ↓
    [LLM Extraction]
    (Parallel processing with 5 workers)
         ↓
   [Deduplication]
   (Keep highest confidence version)
         ↓
   [Entity ID Generation]
   (disease_001, symptom_001, etc.)
         ↓
   [Save by Type]
   (diseases.json, symptoms.json, etc.)
```

### Key Features

1. **Parallel Processing**: Uses ThreadPoolExecutor for concurrent API calls
   - Default: 5 workers
   - Configurable via `--num-workers` flag
   - Significantly speeds up processing (~1726 blocks in ~30 min with 5 workers)

2. **Checkpoint Support**: Saves progress every 10 blocks
   - Allows resuming from interruptions
   - Prevents re-processing blocks
   - Tracks cost, tokens, and stats

3. **Deduplication**: Removes duplicate entities
   - Keeps highest confidence version
   - Merges synonyms across mentions

4. **Confidence Scoring**: LLM assigns confidence to each entity
   - 1.0 = Explicit, clear entity in text
   - 0.7-0.9 = Contextual/implied entity
   - Can filter by confidence threshold if needed

## Running Phase 2 LLM Extraction

### Basic Usage

```bash
# Full extraction (will use checkpoints to resume if interrupted)
.venv/bin/python indexing/phase2_llm_entity_extraction.py

# Check what the prompt looks like (dry-run mode)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --dry-run

# Test with small sample (50 blocks)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --max-blocks 50

# Start fresh, ignore any checkpoint
.venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint

# Use more workers for faster processing
.venv/bin/python indexing/phase2_llm_entity_extraction.py --num-workers 10
```

### Command-line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--num-workers` | 5 | Number of parallel workers for API calls |
| `--max-blocks` | None | Process only N blocks (for testing) |
| `--dry-run` | False | Preview prompt without making API calls |
| `--no-checkpoint` | False | Ignore checkpoint and start fresh |

### Example Commands

```bash
# Full run with 5 workers (default)
.venv/bin/python indexing/phase2_llm_entity_extraction.py

# Full run with 10 workers (faster)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --num-workers 10

# Test extraction on 100 blocks with 2 workers
.venv/bin/python indexing/phase2_llm_entity_extraction.py --max-blocks 100 --num-workers 2

# Resume from checkpoint after interruption
.venv/bin/python indexing/phase2_llm_entity_extraction.py
```

## Output Files

### Main Entity Files

```
indexing/output/phase2/
├── diseases.json              # Disease entities
├── symptoms.json              # Symptom entities
├── signs.json                 # Sign entities
├── treatments.json            # Treatment entities
├── diagnostic_tests.json      # Diagnostic test entities
├── phase2_llm_report.json     # Extraction statistics
└── phase2_checkpoint.json     # Progress checkpoint (hidden during normal run)
```

### Entity Schema

Each entity file contains an array of entity objects with this structure:

```json
[
  {
    "entity_id": "disease_001",
    "name": "Keratitis",
    "name_normalized": "keratitis",
    "synonyms": ["corneal inflammation"],
    "description": "Brief description from extracted context",
    "confidence": 0.95,
    "metadata": {
      "chapter": 4,
      "section": "Bacterial Keratitis",
      "extraction_method": "llm",
      "model": "openai/gpt-4o-mini"
    }
  }
]
```

### Report Structure

The `phase2_llm_report.json` contains:

```json
{
  "extraction_method": "llm_enhanced",
  "model": "openai/gpt-4o-mini",
  "total_unique_entities": 1234,
  "by_type": {
    "disease": 450,
    "symptom": 300,
    "sign": 250,
    "treatment": 150,
    "diagnostic_test": 44
  },
  "statistics": {
    "blocks_processed": 1726,
    "total_blocks": 1726,
    "llm_calls": 1726,
    "total_tokens": 250000,
    "total_cost_usd": 12.50,
    "avg_cost_per_block": 0.0072,
    "avg_entities_per_block": 0.71
  }
}
```

## Cost & Performance

### Estimated Costs

Using OpenAI GPT-4o-mini pricing:
- **Input**: $5 per 1M tokens
- **Output**: $15 per 1M tokens
- **Estimated total**: ~$10-15 for full corpus (1726 blocks)

### Processing Time

With 5 parallel workers on OpenAI:
- **Per block**: ~1-2 seconds
- **Full extraction**: ~30-60 minutes
- With 10 workers: ~15-30 minutes

### Token Usage

- **Average per block**: ~150 tokens (input + output)
- **Total for corpus**: ~250,000 tokens
- **Cost per block**: ~$0.007

## Checkpointing & Resume

### How Checkpointing Works

1. **Initial Run**: Starts from block 0
2. **Every 10 blocks**: Saves checkpoint with:
   - All entities extracted so far
   - Current statistics (cost, tokens, LLM calls)
   - Current position (start_index)
3. **Interruption/Crash**: Can resume from last checkpoint
4. **Completion**: Final checkpoint marks completion

### Resuming After Interruption

If the script is interrupted (Ctrl+C, crash, etc.):

```bash
# Simply run again - it will auto-resume from checkpoint
.venv/bin/python indexing/phase2_llm_entity_extraction.py
```

To start fresh instead:

```bash
# Ignore checkpoint and start from beginning
.venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint
```

### Checkpoint File Location

`indexing/output/phase2/phase2_checkpoint.json`

Contains:
- `entities`: All entities extracted so far
- `stats`: Statistics and cost tracking
- `start_index`: Which block to resume from next

## API Configuration

### Environment Variables

The script uses OpenAI-compatible API. Configure via environment variables:

```bash
# Custom API key
export OPENAI_API_KEY="your-key-here"

# Custom API base URL (for local API or proxies)
export OPENAI_BASE_URL="https://api.openai.com/v1"

# Custom model name
export OPENAI_MODEL_NAME="gpt-4o-mini"
```

### Default Configuration

If not set, uses:
- **API Key**: Embedded (Liara AI proxy)
- **Base URL**: `https://ai.liara.ir/api/68721419652cec5504661aec/v1`
- **Model**: `openai/gpt-4o-mini`

### Proxy Handling

The script automatically clears HTTP proxy settings to avoid SOCKS proxy conflicts:

```python
# Auto-disabled in script
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
```

## Integration with GraphRAG Pipeline

### Phase 2 → Phase 3

Phase 2 outputs are used as input for Phase 3 (Relationship Extraction):

```
Phase 2 Outputs (Entity Files)
├── diseases.json
├── symptoms.json
├── signs.json
├── treatments.json
└── diagnostic_tests.json
         ↓
    Phase 1 Text Blocks
         ↓
   [Phase 3 LLM Extraction]
   Extract Relationships:
   - presents_with (Disease → Symptom)
   - associated_with (Disease → Sign)
   - treated_with (Disease → Treatment)
   - diagnosed_with (Disease → Test)
   - can_cause (Disease → Complication)
   - contraindicated_with (Treatment → Condition)
         ↓
   graphrag_edges_llm.json
```

See `PHASE3_LLM_EXTRACTION_GUIDE.md` for Phase 3 details.

## Performance Optimization Tips

1. **Increase Workers for Speed**
   ```bash
   .venv/bin/python indexing/phase2_llm_entity_extraction.py --num-workers 10
   ```
   - More workers = faster but higher concurrent API load
   - Recommended: 5-10 for most APIs

2. **Monitor Progress**
   - Progress bar shows: entities extracted, cost, API calls
   - Check `phase2_checkpoint.json` for current stats

3. **Cost Control**
   - With 5 workers and proper batching: ~$10-15 total
   - Monitor `total_cost_usd` in progress bar

4. **Handle Timeouts**
   - If API timeouts occur, just re-run (will resume from checkpoint)
   - Thread pool automatically retries failed tasks

## Troubleshooting

### Common Issues

**"JSON decode error"**
- LLM returned invalid JSON
- Script will log the error and skip that block
- Automatic retry on next run due to checkpoint resume

**"SOCKS proxy error"**
- Script auto-clears proxy settings
- If persists, clear manually: `unset HTTP_PROXY HTTPS_PROXY`

**"API rate limits"**
- Reduce `--num-workers` to slow down requests
- Add delay between requests (can modify script)

**"Out of memory"**
- Reduce `--num-workers` or `--max-blocks`
- Process in smaller batches

### Debug Mode

To see detailed progress:

```bash
# See checkpoint loading
.venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint

# See sample prompt
.venv/bin/python indexing/phase2_llm_entity_extraction.py --dry-run
```

## Validation & Quality Assurance

### Expected Results

For ~1726 text blocks:
- **Total entities**: ~1000-1500 unique entities
- **Confidence distribution**:
  - High (≥0.9): ~70%
  - Medium (0.7-0.9): ~25%
  - Low (<0.7): ~5%

### Manual Validation

Recommended to sample-check entities:

```python
import json

# Check high-confidence diseases
with open("indexing/output/phase2/diseases.json") as f:
    diseases = json.load(f)

high_conf = [d for d in diseases if d["confidence"] >= 0.9]
print(f"High confidence diseases: {len(high_conf)}")
print(diseases[:5])  # Sample first 5
```

### Filtering by Confidence

To use only high-confidence entities downstream:

```python
# Filter by confidence threshold
entities = [e for e in all_entities if e["confidence"] >= 0.85]
```

## Next Steps

1. **Run Phase 2**: `python phase2_llm_entity_extraction.py`
2. **Review outputs**: Check `diseases.json`, `symptoms.json`, etc.
3. **Run Phase 3**: `python phase3_llm_relationship_extraction.py`
4. **Validate relationships**: Sample-check relationship accuracy
5. **Proceed to Phase 4**: Domain standardization and urgency classification

## References

- **GRAPHRAG_PREPARATION_TODO.md**: Full preparation pipeline
- **PHASE3_LLM_EXTRACTION_GUIDE.md**: Relationship extraction guide
- **phase3_llm_relationship_extraction.py**: Example of parallel LLM processing
- **docs/GRAPHRAG_ARCHITECTURE.md**: Knowledge graph design
