# GraphRAG Preparation - Quick Reference Guide

## TL;DR
The Wills Eye Manual EPUB has been analyzed and is ready for GraphRAG indexing preparation. It contains:
- **2,009 headings** across 14 chapters
- **1,086 lists** (differential diagnoses, symptoms, treatments)
- **21 tables** with diagnostic and classification info
- **522 images** (clinical photos, diagrams)

**Estimated effort:** 124-178 hours to prepare for GraphRAG indexing

---

## What Needs to Be Done?

### Phase 1: Extract Content (16-24 hours)
Extract structured data from EPUB into JSON:
- Chapter hierarchy and sections
- Table data (21 tables total)
- List items (1,086 lists)
- Image metadata (522 images)

### Phase 2: Extract Medical Entities (20-30 hours)
Identify and classify medical concepts:
- Diseases/conditions (expect 100+)
- Symptoms (expect 50+)
- Signs (expect 30+)
- Treatments/procedures
- Diagnostic tests

### Phase 3: Extract Relationships (24-36 hours)
Connect entities with medical relationships:
- Disease → Symptoms (presents_with)
- Disease → Signs (associated_with)
- Disease → Treatments (treated_with)
- Symptoms → Differential diagnoses (suggests)
- Treatment → Contraindications

### Phase 4: Standardize (16-24 hours)
Add medical codes and classifications:
- ICD-10 codes for diseases
- SNOMED CT codes for procedures
- Urgency levels (Emergent/Urgent/Non-urgent)
- Red flag identification

### Phase 5: Extract Red Flags (12-16 hours) 🚨 CRITICAL
Extract emergent conditions for triage:
- Must have 100% recall (no false negatives)
- Extract keywords and identifying features
- Examples: chemical burn, penetrating trauma, sudden vision loss

### Phase 6: Prepare for Neo4j (12-16 hours)
Convert to knowledge graph format:
- Node format for all entities
- Edge format for all relationships
- Cypher import scripts

### Phase 7: Validate (16-20 hours) 🔍 CRITICAL
Verify medical accuracy:
- Check all red flags are correct
- Verify urgency classifications
- Validate entity relationships
- Test triage recommendations

### Phase 8: Final Deliverables (8-12 hours)
Generate final outputs and documentation

---

## Files Already Generated

✅ **data/epub_structure_summary.json**
- Chapter statistics (headings, tables, lists, images)

✅ **data/epub_analysis.json**
- Detailed analysis with recommendations

✅ **data/GRAPHRAG_PREPARATION_TODO.md** ⭐
- Complete TODO list with 8 phases and 40+ tasks
- Dependency graph and implementation order
- Effort estimates

✅ **data/EPUB_ANALYSIS_SUMMARY.txt**
- Visual overview of content structure

---

## Implementation Roadmap

### Step 1: Start with Phase 1 (Content Extraction)
```
Create: scripts/extract_epub_content.py
- Parse all chapters
- Extract section hierarchy
- Extract tables
- Extract lists
Output: wills_eye_chapters_structured.json
```

### Step 2: Move to Phase 2 (Entity Extraction)
```
Use: indexing/entity_extractor.py (enhanced)
- Extract diseases from chapters
- Extract symptoms and signs
- Extract treatments
Output: diseases.json, symptoms.json, treatments.json
```

### Step 3: Phase 3 (Relationship Extraction)
```
Use: indexing/relationship_extractor.py (enhanced)
- Create disease-symptom relationships
- Create treatment relationships
- Create differential diagnosis mappings
Output: graphrag_edges.json
```

### Step 4: Phase 4 & 5 (Domain Standardization + Red Flags)
```
Create: scripts/medical_standardization.py
- Assign ICD-10/SNOMED codes
- Classify urgency levels
- Extract red flags
Output: entity_medical_codes.json, red_flags.json
```

### Step 5: Phase 6 (Graph Preparation)
```
Create: scripts/prepare_for_neo4j.py
- Convert to Neo4j node format
- Convert to Neo4j edge format
- Generate Cypher scripts
Output: graphrag_nodes.json, graphrag_edges.json, neo4j_import.cypher
```

### Step 6: Phase 7 (Validation)
```
Create: scripts/validate_graphrag_data.py
- Check entity completeness
- Validate relationships
- Verify medical accuracy
- Test red flag detection
Output: validation_reports/
```

### Step 7: Phase 8 (Import & Testing)
```
Run Neo4j import
Test GraphRAG queries
Document final schema
```

---

## Critical Chapters by Content Type

### Differential Diagnosis
- **Chapter 1**: Symptom-based DDx (11 lists)
- **Chapter 2**: Sign-based DDx (9 lists)
- **All chapters**: Condition-specific DDx (1,086 lists total)

### Disease Information
- **Chapter 3**: Trauma (16+ conditions, 72 images)
- **Chapter 4**: Cornea (30+ conditions, 84 images, LARGEST)
- **Chapter 9**: Glaucoma (10+ types, classification tables)
- **Chapter 10**: Neuro-ophthalmology (MOST COMPLEX, 266 headings)
- **Chapter 11**: Retina (25+ conditions)
- **Chapter 12**: Uveitis (20+ entities, 6 tables)

### Diagnostic Content
- **Chapter 14**: Imaging Modalities (diagnostic tests)

---

## Expected Entities & Relationships

### Entities to Extract
- **Diseases**: ~100+ ocular/systemic diseases
- **Symptoms**: ~50+ patient-reported symptoms (pain, vision changes, etc.)
- **Signs**: ~30+ clinical examination findings (redness, swelling, etc.)
- **Treatments**: ~100+ treatments (medications, procedures, surgeries)
- **Procedures**: ~50+ diagnostic and surgical procedures
- **Tests**: ~30+ diagnostic tests and imaging modalities

### Relationships to Create
- **Disease → Symptoms** (presents_with): Each disease mapped to its symptoms
- **Disease → Signs** (associated_with): Clinical findings for each disease
- **Disease → Treatments** (treated_with): Management options
- **Symptom/Sign → Diseases** (suggests): Differential diagnosis
- **Treatment → Contraindications** (contraindicated_with): Safety
- **Disease → Complications** (can_cause): Potential complications
- **Disease → Risk Factors** (has_risk_factor): Predisposing factors
- **Disease → Related Diseases** (see_also): Cross-references

---

## Success Criteria

✅ **Phase 1**: All chapters parsed into structured JSON
✅ **Phase 2**: 100+ diseases, 50+ symptoms, 30+ signs extracted
✅ **Phase 3**: All relationships created with proper types
✅ **Phase 4**: All entities have ICD-10/SNOMED codes and urgency levels
✅ **Phase 5**: All red flags identified (100% recall requirement)
✅ **Phase 6**: Nodes and edges in Neo4j compatible format
✅ **Phase 7**: All validation tests pass
✅ **Phase 8**: Neo4j populated and queryable

---

## Key Files to Review

1. **GRAPHRAG_PREPARATION_TODO.md** ⭐
   - Comprehensive task list
   - All phases and dependencies
   - Detailed descriptions

2. **EPUB_ANALYSIS_SUMMARY.txt**
   - Visual overview of content
   - Chapter breakdown
   - Insights and recommendations

3. **docs/GRAPHRAG_ARCHITECTURE.md**
   - GraphRAG design for this project
   - Entity types and relationships
   - Search strategies

4. **docs/medical/red-flags.md**
   - Complete list of red flag conditions
   - Keywords and identifying features
   - Triage recommendations

5. **docs/medical/framework.md**
   - Medical triage framework
   - Urgency classification rules
   - Safety protocols

---

## Important Notes

⚠️ **Medical Safety Critical**
- Red flag detection must have 100% recall (no false negatives)
- Urgency classifications must match medical standards
- Every extracted entity should be validated

🔧 **Technical Requirements**
- BeautifulSoup4 for HTML/XHTML parsing ✓
- Python for scripting (entity extraction, graph generation)
- Neo4j for knowledge graph storage
- GraphRAG for entity extraction enhancement

📚 **Data Quality**
- Handle synonym normalization (e.g., keratitis vs. corneal inflammation)
- Standardize medical terminology
- Verify cross-references between chapters
- Validate extraction against source material

---

## Next Steps

1. **Read** `data/GRAPHRAG_PREPARATION_TODO.md` for detailed task list
2. **Assess** current entity extraction capabilities in `indexing/`
3. **Plan** which phases to tackle first (recommend Phase 1 → 2 → 5.1 → 4.2)
4. **Implement** content extraction scripts
5. **Validate** outputs against CLAUDE.md medical safety requirements
6. **Populate** Neo4j with prepared data

---

## Resources

- **EPUB Analysis**: `data/epub_analysis.json`, `data/epub_structure_summary.json`
- **EPUB File**: `data/The Wills Eye Manual - Kalla Gervasio.epub` (326 files)
- **Entity Extractor**: `indexing/entity_extractor.py`
- **Relationship Extractor**: `indexing/relationship_extractor.py`
- **Medical Docs**: `docs/medical/`, `docs/technical/`
- **Project Config**: `CLAUDE.md`

---

## Questions?

Refer to:
- `GRAPHRAG_PREPARATION_TODO.md` - For detailed task descriptions
- `docs/GRAPHRAG_ARCHITECTURE.md` - For GraphRAG design
- `CLAUDE.md` - For medical safety requirements
- `docs/medical/framework.md` - For triage/urgency rules
