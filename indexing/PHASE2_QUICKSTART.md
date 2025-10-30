# Phase 2 LLM Entity Extraction - Quick Start

## TL;DR

```bash
# Test extraction on 50 blocks (fast, ~5 minutes)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --max-blocks 50 --num-workers 3

# Full extraction on all blocks (~1726 blocks, ~30-60 minutes)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --num-workers 5

# Preview the prompt without making API calls
.venv/bin/python indexing/phase2_llm_entity_extraction.py --dry-run

# Resume from checkpoint if interrupted
.venv/bin/python indexing/phase2_llm_entity_extraction.py

# Start fresh (ignore checkpoint)
.venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint
```

## What It Does

Extracts **5 types of medical entities** from The Wills Eye Manual using LLM:

1. **Diseases** (e.g., Keratitis, Glaucoma)
2. **Symptoms** (e.g., pain, vision loss)
3. **Signs** (e.g., corneal edema, exudate)
4. **Treatments** (e.g., antibiotics, surgery)
5. **Diagnostic Tests** (e.g., OCT, tonometry)

## Output Files

```
indexing/output/phase2/
├── diseases.json           (disease entities)
├── symptoms.json           (symptom entities)
├── signs.json              (sign entities)
├── treatments.json         (treatment entities)
├── diagnostic_tests.json   (diagnostic test entities)
└── phase2_llm_report.json  (statistics)
```

## Features

✅ **Parallel Processing**: 5 workers by default, customizable
✅ **Checkpoint Support**: Resume from interruptions
✅ **Cost Tracking**: Shows API cost in real-time
✅ **Confidence Scoring**: Each entity gets confidence 0.0-1.0
✅ **Deduplication**: Removes duplicates, keeps best version

## Key Options

| Option | Example | Purpose |
|--------|---------|---------|
| `--num-workers` | `--num-workers 10` | Set number of parallel workers (faster = higher cost) |
| `--max-blocks` | `--max-blocks 100` | Test on N blocks instead of all 1726 |
| `--dry-run` | `--dry-run` | Preview prompt, don't make API calls |
| `--no-checkpoint` | `--no-checkpoint` | Ignore checkpoint, start fresh |

## Cost & Time

- **Cost**: ~$10-15 for full extraction (1726 blocks)
- **Time**: ~30-60 min with 5 workers, ~15-30 min with 10 workers
- **Per block**: ~$0.007, ~2 seconds

## Troubleshooting

**Interrupted? Just run again:**
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py
```
(It will automatically resume from the last checkpoint)

**Want to start over:**
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py --no-checkpoint
```

**Check progress:**
```bash
# Look at the progress bar - shows:
# - entities = total entities extracted so far
# - cost = total API cost so far
# - calls = number of API calls made
```

## Next Steps

1. Run Phase 2: `python phase2_llm_entity_extraction.py`
2. Review output files (diseases.json, symptoms.json, etc.)
3. Run Phase 3 to extract relationships: `python phase3_llm_relationship_extraction.py`

## Full Documentation

See `indexing/output/phase2/PHASE2_LLM_EXTRACTION_GUIDE.md` for detailed documentation.
