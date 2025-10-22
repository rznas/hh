# Phase 1 Output - Quick Reference

## What's in this folder?

This directory contains structured extracts from The Wills Eye Manual (Chapters 1-5) ready for GraphRAG processing.

## Files

### Primary Data Files (Use these for Phase 2)

1. **wills_eye_text_blocks.json** (472 KB)
   - 609 text blocks with hierarchical context
   - Ready for entity extraction
   - Fields: `block_id`, `chapter_number`, `chapter_title`, `section_path`, `heading_level`, `text`

2. **wills_eye_lists.json** (411 KB)
   - 313 classified medical lists
   - Types: differential_diagnosis, treatment, medication, procedure, symptoms_signs, examination, general
   - Fields: `list_id`, `chapter_number`, `section`, `list_type`, `items[]`

3. **wills_eye_tables.json** (26 KB)
   - 21 structured tables from 8 chapters
   - Fields: `table_id`, `chapter_number`, `section`, `headers[]`, `rows[][]`

4. **wills_eye_chapters_structured.json** (451 KB)
   - Full hierarchical chapter structure
   - Preserves section/subsection relationships
   - Use for understanding content organization

### Reports & Documentation

- **PHASE1_SUMMARY.md** - Comprehensive summary with statistics
- **phase1_1_report.json** - Chapter extraction report
- **phase1_2_report.json** - Table extraction report
- **phase1_3_report.json** - List extraction report

## Quick Stats

| Metric | Count |
|--------|-------|
| Chapters processed | 5 of 14 |
| Text blocks | 609 |
| Lists | 313 |
| Tables | 21 |
| Differential diagnoses | 48 lists |
| Treatment protocols | 143 lists |
| Medications | 56 lists |

## Usage Examples

### Loading text blocks for entity extraction
```python
import json

with open('wills_eye_text_blocks.json') as f:
    blocks = json.load(f)

# Process each block
for block in blocks:
    text = block['text']
    chapter = block['chapter_number']
    section = block['section_path']
    # Extract entities from text...
```

### Finding differential diagnosis lists
```python
import json

with open('wills_eye_lists.json') as f:
    lists = json.load(f)

ddx_lists = [
    lst for lst in lists
    if lst['list_type'] == 'differential_diagnosis'
]

print(f"Found {len(ddx_lists)} differential diagnosis lists")
# Output: Found 48 differential diagnosis lists
```

### Processing tables
```python
import json

with open('wills_eye_tables.json') as f:
    tables = json.load(f)

for table in tables:
    print(f"Chapter {table['chapter_number']}: {table['section']}")
    print(f"  {table['num_rows']} × {table['num_columns']}")
```

## Next Steps

See `PHASE1_SUMMARY.md` for detailed analysis and Phase 2 recommendations.

**Ready for:**
- ✅ Phase 2.1: Disease entity extraction
- ✅ Phase 2.2: Symptom/sign entity extraction
- ✅ Phase 3.1: Relationship extraction
- ✅ Phase 5.1: Red flag extraction (Chapter 3 Trauma)

## Scripts Used

Located in `/indexing/`:
- `phase1_extract_chapters_v2.py` - Chapter content extraction
- `phase1_extract_tables.py` - Table extraction
- `phase1_extract_lists.py` - List extraction and classification

---
**Generated**: October 22, 2025
**Total Size**: 1.4 MB
