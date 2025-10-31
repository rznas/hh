# Extraction Configuration System

This system allows easy switching between baseline (pattern-matching) and LLM extraction outputs for downstream phases.

## Quick Start

### View Current Configuration
```bash
python indexing/output/configure_extraction.py --show
```

### Switch All to LLM Mode
```bash
python indexing/output/configure_extraction.py --set-mode llm
```

### Switch Specific Entity to LLM
```bash
python indexing/output/configure_extraction.py --set anatomy=llm etiology=llm
```

### Switch All Edges to LLM
```bash
python indexing/output/configure_extraction.py --set-edges llm
```

### Validate Configuration
Check that all configured files exist:
```bash
python indexing/output/configure_extraction.py --validate
```

### Resolve File Paths
Generate resolved paths for downstream phases:
```bash
python indexing/output/configure_extraction.py --resolve
```

## Configuration Modes

### Baseline Mode (Default)
- **Method**: Pattern matching + keyword extraction
- **Cost**: Free (no API calls)
- **Speed**: Fast
- **Quality**: Good for structured data
- **Output files**: `anatomy.json`, `etiology.json`, etc.

### LLM Mode
- **Method**: Claude/GPT-4 enhanced extraction
- **Cost**: Paid (API usage)
- **Speed**: Slower (parallel processing helps)
- **Quality**: Higher accuracy, better context understanding
- **Output files**: `anatomy_llm.json`, `etiology_llm.json`, etc.

## Using in Downstream Phases

### Python API

```python
from indexing.output.load_configured_data import ConfiguredDataLoader

# Initialize loader
loader = ConfiguredDataLoader()

# Load entities
diseases = loader.load_entities("diseases")
anatomy = loader.load_entities("anatomy")
etiology = loader.load_entities("etiology")

# Load all entities
all_entities = loader.load_all_entities()

# Load edges
caused_by_edges = loader.load_edges("caused_by")
affects_edges = loader.load_edges("affects")

# Load all edges
all_edges = loader.load_all_edges()

# Get statistics
stats = loader.get_stats()
print(f"Total entities: {stats['total_entities']}")
print(f"Total edges: {stats['total_edges']}")

# Print formatted stats
loader.print_stats()
```

### Example: Phase 6 Integration

```python
# In your phase 6 script
from indexing.output.load_configured_data import ConfiguredDataLoader

loader = ConfiguredDataLoader()

# Load all entities for graph preparation
all_entities = loader.load_all_entities()

# Each entity has metadata indicating source
for entity in all_entities["anatomy"]:
    method = entity["metadata"]["extraction_method"]  # "llm" or "pattern_matching"
    model = entity["metadata"].get("model", "N/A")    # Model name if LLM

    print(f"Entity: {entity['name']} (extracted via {method})")
```

## Configuration File Structure

`extraction_config.json` contains:

```json
{
  "default_mode": "baseline",
  "entity_sources": {
    "anatomy": {
      "baseline": "phase2/anatomy.json",
      "llm": "phase2/anatomy_llm.json",
      "active_mode": "baseline"
    },
    ...
  },
  "edge_sources": {
    "caused_by": {
      "baseline": "phase3/caused_by_edges.json",
      "llm": "phase3/caused_by_edges_llm.json",
      "active_mode": "baseline"
    },
    ...
  }
}
```

## Entity & Edge Types

### Entities (Phase 2)
- ✅ `anatomy` - Anatomical structures (cornea, retina, etc.)
- ✅ `etiology` - Causative factors (bacteria, trauma, etc.)
- ✅ `risk_factors` - Risk factors (age, diabetes, etc.)
- ✅ `medications` - Medication treatments
- ✅ `procedures` - Procedural treatments
- ✅ `chapters` - Book chapter structure (baseline only)
- ✅ `sections` - Book section structure (baseline only)
- ✅ `diseases` - Diseases (existing, no compensation)
- ✅ `symptoms` - Symptoms (existing, no compensation)
- ✅ `signs` - Clinical signs (existing, no compensation)
- ✅ `diagnostic_tests` - Diagnostic tests (existing, no compensation)

### Edges (Phase 3)
- ✅ `caused_by` - Disease → Etiology
- ✅ `affects` - Disease → Anatomy
- ✅ `increases_risk` - Risk Factor → Disease
- ✅ `contraindicates` - Condition → Treatment (CRITICAL for safety)
- ✅ `complicates` - Complication → Disease
- ✅ `temporal_follows` - Disease progression
- ✅ `presents_with` - Disease → Symptom (existing)
- ✅ `treated_with` - Disease → Treatment (existing)
- ✅ `associated_with` - Disease → Sign (existing, should be `shows_sign`)

## Workflow Example

### 1. Run Baseline Extraction (Fast, Free)
```bash
# Run all baseline scripts
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy.py
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology.py
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_risk_factors.py
.venv/bin/python indexing/output/phase2/scripts/phase2_split_treatments.py
.venv/bin/python indexing/output/phase2/scripts/phase2_extract_structure.py
.venv/bin/python indexing/output/phase3/scripts/phase3_compensate_edges.py
.venv/bin/python indexing/output/phase3/scripts/phase3_compensate_complications.py

# Validate
python indexing/output/configure_extraction.py --validate
```

### 2. (Optional) Run LLM Extraction (Higher Quality)
```bash
# Run LLM scripts for entities
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy_llm.py
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology_llm.py
.venv/bin/python indexing/output/phase2/scripts/phase2_compensate_risk_factors_llm.py
.venv/bin/python indexing/output/phase2/scripts/phase2_split_treatments_llm.py

# Run LLM scripts for edges
.venv/bin/python indexing/output/phase3/scripts/phase3_compensate_edges_llm.py
.venv/bin/python indexing/output/phase3/scripts/phase3_compensate_complications_llm.py

# Switch to LLM mode
python indexing/output/configure_extraction.py --set-mode llm

# Validate
python indexing/output/configure_extraction.py --validate
```

### 3. Use in Downstream Phases
```python
# Your phase 6+ scripts automatically use configured sources
from indexing.output.load_configured_data import ConfiguredDataLoader

loader = ConfiguredDataLoader()
all_entities = loader.load_all_entities()
all_edges = loader.load_all_edges()
```

## Comparison & Quality Control

### Compare Baseline vs LLM
```bash
# Set to baseline
python indexing/output/configure_extraction.py --set-mode baseline
python indexing/output/load_configured_data.py  # View stats

# Set to LLM
python indexing/output/configure_extraction.py --set-mode llm
python indexing/output/load_configured_data.py  # View stats
```

### Mix and Match
Use LLM for critical data, baseline for less critical:
```bash
# Critical entities use LLM
python indexing/output/configure_extraction.py --set \
    anatomy=llm \
    etiology=llm \
    risk_factors=llm

# Edges use LLM (especially contraindicates - medical safety!)
python indexing/output/configure_extraction.py --set-edges llm

# View result
python indexing/output/configure_extraction.py --show
```

## Metadata Tracking

Every loaded entity/edge includes metadata:

```json
{
  "entity_id": "anatomy_001",
  "name": "Cornea",
  "type": "anatomy",
  "metadata": {
    "extraction_method": "llm",
    "model": "openai/gpt-4o-mini",
    "loaded_from": "/path/to/anatomy_llm.json",
    "config_mode": "llm",
    "chapter": 4,
    "section": "Corneal Anatomy"
  }
}
```

This allows:
- Quality analysis by extraction method
- A/B testing baseline vs LLM
- Preferring LLM results in merge scenarios
- Debugging data provenance

## Files

### Configuration
- `extraction_config.json` - Main configuration file
- `resolved_paths.json` - Generated by `--resolve`, contains absolute paths

### Scripts
- `configure_extraction.py` - Configuration management CLI
- `load_configured_data.py` - Python API for loading data

### Compensation Scripts
See `indexing/output/phase2/scripts/` and `indexing/output/phase3/scripts/`

## Troubleshooting

### "File not found" errors
Run validation to see which files are missing:
```bash
python indexing/output/configure_extraction.py --validate
```

Then run the appropriate compensation scripts.

### Can't load entities in downstream phase
Make sure you're using the loader:
```python
from indexing.output.load_configured_data import ConfiguredDataLoader
loader = ConfiguredDataLoader()
```

### Want to use both baseline and LLM
Load both manually and merge:
```python
loader = ConfiguredDataLoader()

# Load baseline
loader.config["entity_sources"]["anatomy"]["active_mode"] = "baseline"
anatomy_baseline = loader.load_entities("anatomy")

# Load LLM
loader.config["entity_sources"]["anatomy"]["active_mode"] = "llm"
anatomy_llm = loader.load_entities("anatomy")

# Merge with your custom logic
merged = merge_entities(anatomy_baseline, anatomy_llm)
```

## Cost Estimation

### LLM Extraction Costs (Approximate)
Based on Claude Sonnet 4.5 pricing ($5/1M input, $15/1M output):

- **Anatomy**: ~$2-5 (500 text blocks)
- **Etiology**: ~$3-6 (500 text blocks)
- **Risk Factors**: ~$3-6 (500 text blocks)
- **Treatment Split**: ~$0.50 (845 treatments, simple classification)
- **Edge Extraction**: ~$5-10 (500 text blocks, more complex)
- **Complications**: ~$4-8 (500 text blocks)

**Total estimated cost**: ~$20-40 for full LLM pipeline

### Baseline Extraction Costs
- **All scripts**: $0 (no API calls)

## Best Practices

1. **Start with baseline** - Run free extraction first to validate pipeline
2. **Validate early** - Use `--validate` to catch missing files
3. **Selective LLM use** - Use LLM only for entities/edges where quality matters most
4. **Track metadata** - Always check `extraction_method` in loaded data
5. **Version control config** - Commit `extraction_config.json` to track which sources are active
6. **Document decisions** - Add notes to config about why certain modes are chosen

## Next Steps

After running compensation scripts and configuring sources:

1. ✅ Validate configuration
2. ✅ Update Phase 6 to use `ConfiguredDataLoader`
3. ✅ Run Phase 6 graph preparation
4. ✅ Analyze results and compare baseline vs LLM quality
5. ✅ Adjust configuration based on quality/cost tradeoffs
6. ✅ Proceed with Phase 7 validation
