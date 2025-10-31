# LLM Error Handling & Manual Review Guide

## Overview

All LLM-based scripts (Phase 2 & Phase 3) now have comprehensive error handling and logging for manual review. Errors are categorized and recorded with full context for efficient troubleshooting.

## Error Categories

### 1. **Schema Validation Failures**
When the LLM response doesn't match the expected JSON schema.

**Recorded in:** `invalid_{entity_type}_TIMESTAMP.json`

**Contains:**
- Original text block (200 char preview)
- Exact prompt sent to LLM
- LLM's actual response
- Validation error details
- Expected JSON schema
- Chapter/section metadata
- Timestamp

**Example record:**
```json
{
  "timestamp": "2024-10-31T15:23:45.123456",
  "chapter": 3,
  "section": "Trauma",
  "text_block_id": "block_001",
  "text_preview": "Corneal abrasion presents with...",
  "prompt": "You are a medical knowledge graph expert...",
  "llm_response": "Invalid JSON or malformed response",
  "error": "Schema validation error: 'anatomical_entities' is required",
  "error_category": "schema_validation",
  "expected_schema": {...},
  "entity_type": "anatomy"
}
```

### 2. **Connection Errors**
API failures, timeouts, network issues, or any exceptions during processing.

**Recorded in:** `connection_errors_{entity_type}_TIMESTAMP.json`

**Contains:**
- Original text block (200 char preview)
- Prompt that was being sent
- Exception type (ConnectionError, Timeout, etc.)
- Error message and full stack trace
- Retry count (for future use)
- Suggested action: "Retry the extraction for this text block"

**Example record:**
```json
{
  "timestamp": "2024-10-31T15:25:12.987654",
  "chapter": 5,
  "section": "Anterior Segment",
  "text_block_id": "block_042",
  "text_preview": "Keratitis caused by bacteria...",
  "prompt": "You are a medical knowledge graph expert...",
  "error_type": "ConnectionError",
  "error_message": "Error extracting anatomy: ConnectionError",
  "full_error": "HTTPConnectionPool(host='api.example.com', port=443): Max retries exceeded",
  "error_category": "connection_error",
  "retry_count": 0,
  "entity_type": "anatomy",
  "action_needed": "Retry the extraction for this text block"
}
```

## Summary Report

Each run generates a summary report: `invalid_{entity_type}_summary.json`

**Contains:**
- Entity type being processed
- Timestamp of run
- Total errors found
- Breakdown by error type
  - Schema validation failures by type
  - Connection errors by type
- File paths to detailed error logs

**Example summary:**
```json
{
  "entity_type": "anatomy",
  "timestamp": "20241031_152310",
  "total_invalid": 5,
  "total_connection_errors": 2,
  "errors_by_type": {
    "Schema validation error": 3,
    "JSON parsing error": 2
  },
  "connection_errors_by_type": {
    "ConnectionError": 1,
    "TimeoutError": 1
  },
  "saved_files": [
    "/path/to/invalid_anatomy_20241031_152310.json",
    "/path/to/connection_errors_anatomy_20241031_152310.json"
  ],
  "total_errors": 7,
  "file_path": "/path/to/invalid_anatomy_summary.json",
  "connection_errors_file_path": "/path/to/connection_errors_anatomy_20241031_152310.json"
}
```

## File Structure

```
phase2/invalid_responses/
├── invalid_anatomy_20241031_152310.json          # Schema validation failures
├── connection_errors_anatomy_20241031_152310.json # Connection errors
├── invalid_anatomy_summary.json                   # Summary report
├── invalid_etiology_20241031_152315.json
├── connection_errors_etiology_20241031_152315.json
├── invalid_etiology_summary.json
└── ... (one set per entity type)

phase3/invalid_responses/
├── invalid_edges_20241031_152320.json
├── connection_errors_edges_20241031_152320.json
├── invalid_edges_summary.json
├── invalid_complications_20241031_152325.json
├── connection_errors_complications_20241031_152325.json
└── invalid_complications_summary.json
```

## Manual Review Process

### Step 1: Check Summary
Start with the summary file to understand error distribution:
```bash
cat invalid_anatomy_summary.json
```

### Step 2: Review Error Types
- **Schema Validation Failures**: Check if LLM needs better prompting
- **Connection Errors**: Check network/API status, retry with exponential backoff

### Step 3: For Schema Failures
1. Open `invalid_anatomy_TIMESTAMP.json`
2. Review a few records:
   - Compare `llm_response` with `expected_schema`
   - Check if prompt is clear enough
   - Identify patterns in failures
3. Options:
   - Improve the prompt in the script
   - Re-run extraction
   - Manually fix responses if count is small

### Step 4: For Connection Errors
1. Open `connection_errors_anatomy_TIMESTAMP.json`
2. Check error types:
   - `ConnectionError`: Network/API issue
   - `TimeoutError`: LLM response too slow
   - `RateLimitError`: Too many API calls
3. Options:
   - Retry with exponential backoff
   - Check API status
   - Reduce parallel workers if rate-limited
   - Increase timeout if timeouts are frequent

## Scripts Using This System

### Phase 2 Scripts
✅ `phase2_compensate_anatomy_llm.py`
✅ `phase2_compensate_etiology_llm.py`
✅ `phase2_compensate_risk_factors_llm.py`
✅ `phase2_split_treatments_llm.py`

### Phase 3 Scripts
✅ `phase3_compensate_edges_llm.py`
✅ `phase3_compensate_complications_llm.py`
✅ `phase3_llm_relationship_extraction.py`

## Statistics in Report Files

Each script generates a report with validation statistics:

```json
{
  "extraction_method": "llm_enhanced",
  "model": "openai/gpt-4o-mini",
  "total_entities": 245,
  "statistics": {
    "blocks_processed": 100,
    "llm_calls": 98,
    "total_tokens": 45000,
    "total_cost_usd": 0.52,
    "schema_validation_failures": 2
  }
}
```

Key metrics:
- `schema_validation_failures`: Count of invalid schema responses
- `total_cost_usd`: Cost of successful API calls
- `blocks_processed`: Total blocks attempted

## Utilities Module

**Location:** `indexing/output/llm_schema_utils.py`

### Classes Available

#### `InvalidResponseHandler`
```python
# Initialize
handler = InvalidResponseHandler(output_dir=Path("invalid_responses"), entity_type="anatomy")

# Record schema validation failure
handler.record_invalid_response(
    text_block={...},
    prompt="...",
    llm_response="...",
    error="Schema validation error: ...",
    schema={...}
)

# Record connection error
handler.record_connection_error(
    text_block={...},
    prompt="...",
    error=Exception(),
    error_message="...",
    retry_count=0
)

# Save all errors
total_count, summary_path = handler.save_invalid_responses()
```

#### `SchemaValidator`
```python
# Validate JSON response
is_valid, parsed_json, error_msg = SchemaValidator.validate(
    response_text="json string",
    schema={...},
    strict=True
)
```

## Troubleshooting Guide

### High Schema Validation Failure Rate
**Problem:** Many responses don't match schema
- Check if prompt is clear
- Verify expected schema is reasonable
- Consider if LLM model needs change
- Review specific failures for patterns

**Solution:**
1. Review 5-10 sample failures
2. Identify common issues
3. Update prompt or schema
4. Re-run extraction

### Frequent Connection Errors
**Problem:** Many API failures
- Check internet/VPN connection
- Check API status page
- Check API quota/rate limits
- Check if timeout is too short

**Solution:**
1. Run with `--num-workers 1` to avoid rate limiting
2. Increase timeout if timeouts are frequent
3. Check API provider dashboard
4. Retry with exponential backoff delay

### Mixed Errors
**Problem:** Both schema and connection errors
- Process connection errors first (retry)
- Then fix schema validation issues
- Re-run extraction for both

## Best Practices

1. **Monitor Progress**: Check summary reports regularly
2. **Fix Early**: Address schema issues while extraction is running
3. **Batch Retries**: Use summary to identify blocks needing retry
4. **Document Issues**: Note patterns in error logs for future improvements
5. **Version Control**: Keep error logs for audit trail

## Future Enhancements

- Automatic retry logic with exponential backoff
- Web dashboard for error visualization
- Batch retry script using error logs
- ML model for error prediction/prevention
