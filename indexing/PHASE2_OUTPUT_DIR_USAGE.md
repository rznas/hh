# Phase 2 LLM Entity Extraction - Custom Output Directory Usage

## Overview

The Phase 2 LLM extraction script now supports saving output to a custom directory using the `--output-dir` flag. This allows you to:

- Save results to different locations for different models
- Keep multiple extraction runs separate
- Organize results by experiment or version
- Use Claude instead of GPT-4o-mini (or vice versa)

## Quick Usage

### Default Output (Phase 2 standard location)
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py
# Output: indexing/output/phase2/
```

### Custom Output Directory
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py --output-dir /path/to/output
```

## Usage Examples

### Example 1: Save to Claude Results Directory
```bash
mkdir -p indexing/output/phase2_claude
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_claude \
  --max-blocks 50
```

Output files:
- `indexing/output/phase2_claude/diseases.json`
- `indexing/output/phase2_claude/symptoms.json`
- `indexing/output/phase2_claude/signs.json`
- `indexing/output/phase2_claude/treatments.json`
- `indexing/output/phase2_claude/diagnostic_tests.json`
- `indexing/output/phase2_claude/phase2_llm_report.json`

### Example 2: Absolute Path
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir /home/reza/projects/hh/results/phase2_v1
```

### Example 3: Full Extraction with Custom Output
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_anthropic \
  --num-workers 10 \
  --no-checkpoint
```

### Example 4: Compare Multiple Models
```bash
# Extract with GPT-4o-mini (default)
export OPENAI_MODEL_NAME="openai/gpt-4o-mini"
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_gpt4o_mini \
  --max-blocks 100

# Extract with Claude (after changing model in code)
export OPENAI_MODEL_NAME="anthropic/claude-sonnet-4.5"
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_claude \
  --max-blocks 100
```

## Model Configuration

The script uses OpenAI-compatible API. You can change the model in the script:

### Current Default
```python
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "openai/gpt-4o-mini")
```

### Change to Claude
Edit line 66 in `phase2_llm_entity_extraction.py`:
```python
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")
```

Or set via environment variable:
```bash
export OPENAI_MODEL_NAME="anthropic/claude-sonnet-4.5"
.venv/bin/python indexing/phase2_llm_entity_extraction.py --output-dir indexing/output/phase2_claude
```

## Command Line Options

```
usage: phase2_llm_entity_extraction.py [-h] [--num-workers NUM_WORKERS]
                                       [--max-blocks MAX_BLOCKS] [--dry-run]
                                       [--no-checkpoint]
                                       [--output-dir OUTPUT_DIR]

options:
  --output-dir OUTPUT_DIR
                        Custom output directory (default: indexing/output/phase2)
  --num-workers NUM_WORKERS
                        Number of parallel workers (default: 5)
  --max-blocks MAX_BLOCKS
                        Maximum text blocks to process (for testing)
  --dry-run             Preview prompt without API calls
  --no-checkpoint       Ignore checkpoint, start fresh
```

## Output Files

Regardless of output directory, the script generates these files:

```
<output-dir>/
├── diseases.json              # Disease entities
├── symptoms.json              # Symptom entities
├── signs.json                 # Sign entities
├── treatments.json            # Treatment entities
├── diagnostic_tests.json      # Diagnostic test entities
└── phase2_llm_report.json     # Statistics and costs
```

## Checkpointing with Custom Output

**Important:** Checkpoints are saved in the SAME directory as output:

```
<output-dir>/
├── phase2_checkpoint.json     # Checkpoint (auto-created)
├── diseases.json
├── symptoms.json
└── ...
```

When you re-run with the same `--output-dir`, it will resume from the checkpoint.

### Start Fresh (Ignore Checkpoint)
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_v2 \
  --no-checkpoint
```

## Practical Workflow

### Scenario 1: Test with Different Models

```bash
# Create separate directories for each model
mkdir -p indexing/output/phase2_models/{gpt4o_mini,claude}

# Test GPT-4o-mini with 50 blocks
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_models/gpt4o_mini \
  --max-blocks 50 \
  --num-workers 2

# Test Claude with 50 blocks (after changing model)
export OPENAI_MODEL_NAME="anthropic/claude-sonnet-4.5"
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_models/claude \
  --max-blocks 50 \
  --num-workers 2
```

Then compare results:
```bash
diff <(jq '.by_type' indexing/output/phase2_models/gpt4o_mini/phase2_llm_report.json) \
     <(jq '.by_type' indexing/output/phase2_models/claude/phase2_llm_report.json)
```

### Scenario 2: Version Control

```bash
# Version 1 - Initial extraction
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_v1.0

# Version 2 - Improved prompt
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_v1.1

# Compare extraction quality
ls -lh indexing/output/phase2_v*/diseases.json
wc -l indexing/output/phase2_v*/diseases.json
```

### Scenario 3: Incremental Extraction

```bash
# Extract first batch
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_final \
  --max-blocks 500

# Resume (auto-resumes from checkpoint)
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_final

# Check final results
cat indexing/output/phase2_final/phase2_llm_report.json | jq '.statistics'
```

## Integration with Phase 3

Phase 3 expects entity files in a specific location. After running with custom `--output-dir`:

1. Copy results to phase2 standard location:
```bash
cp indexing/output/phase2_claude/* indexing/output/phase2/
```

Or:

2. Update Phase 3 to read from custom location (if implementing that feature)

## File Structure Examples

### Default Setup
```
indexing/
├── phase2_llm_entity_extraction.py
├── phase3_llm_relationship_extraction.py
└── output/
    └── phase2/                    ← Default output
        ├── diseases.json
        ├── symptoms.json
        ├── signs.json
        ├── treatments.json
        ├── diagnostic_tests.json
        ├── phase2_llm_report.json
        └── phase2_checkpoint.json
```

### With Multiple Models
```
indexing/
├── phase2_llm_entity_extraction.py
└── output/
    ├── phase2/                    ← GPT-4o-mini (default)
    ├── phase2_claude/             ← Claude results
    ├── phase2_v1.0/               ← Version 1.0
    ├── phase2_v1.1/               ← Version 1.1
    └── phase2_models/
        ├── gpt4o_mini/
        └── claude/
```

## Tips & Tricks

### Monitor Multiple Runs Simultaneously
```bash
# Terminal 1: Run with GPT-4o-mini
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_gpt &

# Terminal 2: Run with Claude
export OPENAI_MODEL_NAME="anthropic/claude-sonnet-4.5"
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_claude &

# Monitor progress
watch -n 5 'cat indexing/output/phase2_*/phase2_llm_report.json | jq ".statistics"'
```

### Compare Entity Counts Across Runs
```bash
for dir in indexing/output/phase2_*/; do
  count=$(jq '.total_unique_entities' "$dir/phase2_llm_report.json")
  echo "$(basename $dir): $count entities"
done
```

### Validate Output Files
```bash
# Check all output files exist
for dir in indexing/output/phase2_*/; do
  echo "Checking $dir..."
  ls -1 "$dir"/*.json | wc -l
done
```

## Troubleshooting

### Directory Doesn't Exist
**Q**: Error: "No such file or directory"
**A**: The script auto-creates the directory, but parent dirs must exist:
```bash
# This works (creates phase2_v2)
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_v2

# This fails (indexing/output2 doesn't exist)
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output2/phase2
```

### Permission Denied
**Q**: Error: "Permission denied"
**A**: Check directory permissions:
```bash
chmod 755 indexing/output/
```

### Mixing Checkpoints
**Q**: Running with same `--output-dir` continues from checkpoint, but I want fresh start
**A**: Use `--no-checkpoint` flag:
```bash
.venv/bin/python indexing/phase2_llm_entity_extraction.py \
  --output-dir indexing/output/phase2_v2 \
  --no-checkpoint
```

## Next Steps

1. **Run with custom output**: `python phase2_llm_entity_extraction.py --output-dir <path>`
2. **Compare results**: Use different models or versions
3. **Use results**: Copy to phase2 standard location or update Phase 3

## References

- **Main Script**: `indexing/phase2_llm_entity_extraction.py`
- **Full Guide**: `indexing/output/phase2/PHASE2_LLM_EXTRACTION_GUIDE.md`
- **Quick Start**: `indexing/PHASE2_QUICKSTART.md`
