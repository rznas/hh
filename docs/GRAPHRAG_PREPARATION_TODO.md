# GraphRAG Preparation TODO List for Wills Eye Manual

## Overview
The Wills Eye Manual (7th Edition) EPUB has been analyzed and contains substantial medical content that needs to be prepared for GraphRAG indexing. This document outlines the complete TODO list for making the book ready for GraphRAG knowledge graph construction.

## Content Statistics

| Metric | Count |
|--------|-------|
| **Total Chapters** | 14 |
| **Total Headings** | 2,009 |
| **Total Sections** | 1,086 (lists) |
| **Total Tables** | 21 |
| **Total Images** | 522 |
| **Front Matter Pages** | 10 |
| **Appendices** | 3 |

## Chapter Breakdown

| Chapter | Title | Headings | Tables | Lists | Images |
|---------|-------|----------|--------|-------|--------|
| 1 | Differential Diagnosis of Ocular Symptoms | 30 | 0 | 11 | 2 |
| 2 | Differential Diagnosis of Ocular Signs | 84 | 0 | 9 | 1 |
| 3 | Trauma | 182 | 2 | 81 | 72 |
| 4 | Cornea | 299 | 2 | 172 | 84 |
| 5 | Conjunctiva/Sclera/Iris/External Disease | 160 | 0 | 56 | 48 |
| 6 | Eyelid | 86 | 0 | 51 | 19 |
| 7 | Orbit | 80 | 5 | 50 | 28 |
| 8 | Pediatrics | 110 | 0 | 99 | 34 |
| 9 | Glaucoma | 179 | 1 | 91 | 39 |
| 10 | Neuro-ophthalmology | 266 | 0 | 152 | 65 |
| 11 | Retina | 155 | 1 | 79 | 48 |
| 12 | Uveitis | 154 | 6 | 126 | 40 |
| 13 | General Ophthalmic Problems | 156 | 2 | 84 | 23 |
| 14 | Imaging Modalities in Ophthalmology | 68 | 2 | 25 | 19 |

---

# PREPARATION PHASES

## PHASE 1: CONTENT EXTRACTION & PARSING

### 1.1 Extract and Parse Chapter Content
- [ ] **Parse all 14 chapters into structured sections**
  - Extract chapter titles and section hierarchy
  - Identify heading levels (H1, H2, H3, H4, H5, H6)
  - Create content blocks for each section
  - Output: `wills_eye_chapters_structured.json`
  - Priority: **HIGH** (Critical for all downstream tasks)

- [ ] **Extract body text and maintain hierarchy**
  - Preserve section-to-subsection relationships
  - Extract paragraph text for entity extraction
  - Maintain reference to parent sections
  - Output: `wills_eye_text_blocks.json`
  - Priority: **HIGH**

### 1.2 Extract and Structure Tables
- [ ] **Parse 21 tables and convert to structured format**
  - Identify table headers and rows
  - Extract table captions/titles
  - Map tables to their parent sections
  - Convert to JSON with schema: `{table_id, title, section, headers[], rows[]}`
  - Chapters with tables: 3, 4, 7, 9, 11, 12, 13, 14
  - Output: `wills_eye_tables.json`
  - Priority: **HIGH** (Tables contain critical medical information)

- [ ] **Create table-to-entity mappings**
  - Link table entities to disease/symptom nodes
  - Identify comparison tables vs. classification tables
  - Flag diagnostic tables for red flag detection
  - Output: `table_entity_mappings.json`
  - Priority: **MEDIUM**

### 1.3 Extract and Structure Lists
- [ ] **Parse 1,086 lists (differential diagnoses, symptoms, treatments)**
  - Extract list items and their context
  - Identify list type: symptoms, differential diagnoses, treatments, etc.
  - Maintain parent-child relationships
  - Map to medical concepts
  - Output: `wills_eye_lists.json`
  - Priority: **HIGH** (Critical for disease hierarchies)

- [ ] **Create specialized differential diagnosis structures**
  - For Chapter 1: symptom-based DDx
  - For Chapter 2: sign-based DDx
  - For each disease chapter: differential lists
  - Output: `differential_diagnoses.json` with schema:
    ```json
    {
      "presenting_complaint": "...",
      "differential_diagnoses": [
        {
          "rank": 1,
          "disease": "...",
          "likelihood": "...",
          "key_features": [],
          "section": "..."
        }
      ]
    }
    ```
  - Priority: **HIGH**

### 1.4 Extract and Process Images
- [ ] **Create image metadata and mapping**
  - Extract image filenames and paths (522 images total)
  - Extract figure captions/labels
  - Map images to their sections and nearby text
  - Output: `image_metadata.json`
  - Priority: **MEDIUM** (Nice to have, can be deferred)

- [ ] **Create cross-reference map**
  - Link images to entities they illustrate
  - Create "image_of_[entity]" relationships
  - Priority: **LOW**

---

## PHASE 2: MEDICAL ENTITY EXTRACTION

### 2.1 Extract Disease Entities
- [ ] **Extract all disease/condition names**
  - Scan all chapters for disease entities
  - Use entity extractor (entity_extractor.py)
  - Normalize disease names (handle synonyms)
  - Extract disease codes if available (ICD-10, SNOMED CT)
  - Output: `diseases.json` with schema:
    ```json
    {
      "entity_id": "disease_001",
      "name": "Keratitis",
      "synonyms": ["corneal inflammation", "..."],
      "icd_10": "H16",
      "snomed_ct": "...",
      "description": "...",
      "chapters": [4, 5],
      "severity": "urgent",
      "red_flag": true
    }
    ```
  - Priority: **CRITICAL**

### 2.2 Extract Symptom/Sign Entities
- [ ] **Extract all symptoms and signs**
  - Focus on Chapter 1 (Symptoms) and Chapter 2 (Signs)
  - Create separate symptom vs. sign distinction
  - Include variations (pain, discomfort, ache)
  - Output: `symptoms.json` and `signs.json`
  - Priority: **CRITICAL**

### 2.3 Extract Treatment/Procedure Entities
- [ ] **Extract treatments, procedures, and interventions**
  - Scan for surgical procedures, non-surgical treatments, medications
  - Extract dosing information if available
  - Output: `treatments.json`
  - Priority: **HIGH**

### 2.4 Extract Diagnostic Test Entities
- [ ] **Extract diagnostic tests and imaging modalities**
  - Use Chapter 14 as reference
  - Include test names, purposes, interpretations
  - Output: `diagnostic_tests.json`
  - Priority: **MEDIUM**

---

## PHASE 3: ENTITY RELATIONSHIP EXTRACTION

### 3.1 Extract Disease-Symptom Relationships
- [ ] **Create "presents_with" relationships**
  - Map: Disease → Symptoms (what symptoms does this disease present with?)
  - Parse symptom lists under disease sections
  - Use relationship_extractor.py
  - Output: relationships with type "presents_with"
  - Priority: **CRITICAL**

- [ ] **Create "associated_with" relationships**
  - Map: Disease → Signs (what signs are observed?)
  - Output: relationships with type "associated_with"
  - Priority: **HIGH**

### 3.2 Extract Disease-Treatment Relationships
- [ ] **Create "treated_with" relationships**
  - Map: Disease → Treatment/Procedure
  - Extract from management/treatment sections
  - Output: relationships with type "treated_with"
  - Priority: **CRITICAL**

### 3.3 Extract Differential Diagnosis Relationships
- [ ] **Create "differential_diagnosis" relationships**
  - Map: Symptom/Sign → Differential Diseases
  - Include likelihood/probability if available
  - Output: relationships with type "differential_diagnosis"
  - Priority: **CRITICAL**

### 3.4 Extract Complication Relationships
- [ ] **Create "can_cause" relationships**
  - Map: Disease → Complications
  - Map: Procedure → Potential Complications
  - Output: relationships with type "can_cause"
  - Priority: **MEDIUM**

### 3.5 Extract Contraindication Relationships
- [ ] **Create "contraindicated_with" relationships**
  - Map: Treatment → Contraindications
  - Extract from safety/warning sections
  - Output: relationships with type "contraindicated_with"
  - Priority: **HIGH**

### 3.6 Extract Cross-Reference Relationships
- [ ] **Create "see_also" relationships**
  - Extract cross-references between sections
  - Link related conditions
  - Output: relationships with type "see_also"
  - Priority: **LOW**

---

## PHASE 4: MEDICAL DOMAIN STANDARDIZATION

### 4.1 Terminology Standardization
- [ ] **Map extracted entities to standard medical codes**
  - ICD-10 codes for diseases
  - SNOMED CT codes for procedures and findings
  - RxNorm codes for medications
  - Create mapping file: `entity_standard_codes.json`
  - Priority: **HIGH** (Required for medical accuracy)

- [ ] **Handle synonym normalization**
  - Identify disease name variants (e.g., "keratitis" vs "corneal inflammation")
  - Create canonical forms
  - Output: `entity_synonyms.json`
  - Priority: **MEDIUM**

### 4.2 Create Urgency/Severity Classifications
- [ ] **Map diseases to urgency levels**
  - Emergent (ER immediately)
  - Urgent (within 24-48 hours)
  - Non-urgent (routine appointment)
  - Use medical domain framework: `docs/medical/framework.md`
  - Output: urgency classifications in disease entities
  - Priority: **CRITICAL** (Required for triage system)

- [ ] **Map symptoms to red flags**
  - Identify which symptoms indicate emergent conditions
  - Use red flags reference: `docs/medical/red-flags.md`
  - Output: flag "red_flag: true" in symptom entities
  - Priority: **CRITICAL**

### 4.3 Create Hierarchical Disease Classifications
- [ ] **Organize diseases by system**
  - Corneal diseases (Chapter 4)
  - Retinal diseases (Chapter 11)
  - Uveal diseases (Chapter 12)
  - Etc.
  - Create hierarchy: `disease_hierarchy.json`
  - Priority: **MEDIUM**

- [ ] **Create severity-based hierarchies**
  - Organize by disease severity within each category
  - Output: `disease_severity_hierarchy.json`
  - Priority: **MEDIUM**

---

## PHASE 5: RED FLAG & SAFETY EXTRACTION

### 5.1 Extract Red Flag Conditions
- [ ] **Identify and extract emergent conditions**
  - Scan all chapters for red flag conditions
  - Extract keywords and identifying features
  - Extract from Chapter 3 (Trauma) especially
  - Output: `red_flags.json` with schema:
    ```json
    {
      "red_flag_id": "rf_001",
      "condition": "Chemical Burn",
      "keywords": ["chemical", "acid", "alkali"],
      "urgency": "emergent",
      "first_aid": "...",
      "referral": "ER immediately",
      "section": "Chapter 3.1"
    }
    ```
  - Priority: **CRITICAL**

### 5.2 Extract Safety Warnings
- [ ] **Extract contraindications and warnings**
  - Find contraindication sections
  - Extract drug interactions if mentioned
  - Extract allergy/hypersensitivity warnings
  - Output: `safety_warnings.json`
  - Priority: **HIGH**

### 5.3 Extract Management Protocols
- [ ] **Extract treatment protocols and algorithms**
  - Find decision trees or treatment algorithms
  - Extract step-by-step management approaches
  - Output: `management_protocols.json`
  - Priority: **MEDIUM**

---

## PHASE 6: GRAPH PREPARATION

### 6.1 Create Node-Link JSON Format
- [ ] **Convert all entities to GraphRAG node format**
  - Schema:
    ```json
    {
      "id": "entity_unique_id",
      "label": "entity_name",
      "type": "Disease|Symptom|Sign|Treatment|Procedure|Test",
      "properties": {
        "description": "...",
        "synonyms": [],
        "medical_code": "ICD-10 or SNOMED",
        "severity": "emergent|urgent|non-urgent",
        "chapters": [1, 2, 3],
        "red_flag": true/false
      }
    }
    ```
  - Output: `graphrag_nodes.json`
  - Priority: **CRITICAL**

- [ ] **Convert all relationships to GraphRAG edge format**
  - Schema:
    ```json
    {
      "source": "entity_id_1",
      "target": "entity_id_2",
      "relationship_type": "presents_with|treated_with|differential_diagnosis|etc",
      "weight": 0.0-1.0,
      "properties": {
        "likelihood": "high|medium|low",
        "context": "...",
        "source_section": "..."
      }
    }
    ```
  - Output: `graphrag_edges.json`
  - Priority: **CRITICAL**

### 6.2 Prepare for Neo4j Ingestion
- [ ] **Create Neo4j Cypher import scripts**
  - Generate CREATE statements for all nodes
  - Generate MATCH-CREATE statements for edges
  - Create indexes for fast lookup
  - Output: `neo4j_import.cypher`
  - Priority: **HIGH**

- [ ] **Prepare CSV format for Neo4j bulk import**
  - Convert nodes to CSV
  - Convert edges to CSV
  - Output: `nodes.csv`, `relationships.csv`
  - Priority: **HIGH**

### 6.3 Create Embedding Metadata
- [ ] **Prepare text for embeddings**
  - Extract description text for each entity
  - Create contextualized text chunks
  - Output: `embeddings_metadata.json`
  - Priority: **MEDIUM** (Will be used for semantic search)

---

## PHASE 7: VALIDATION & TESTING

### 7.1 Data Quality Validation
- [ ] **Validate extracted entities**
  - Check for duplicate entities
  - Verify entity properties are complete
  - Validate medical terminology
  - Report: `entity_validation_report.json`
  - Priority: **HIGH**

- [ ] **Validate extracted relationships**
  - Check for orphaned edges (missing nodes)
  - Verify relationship directionality makes sense
  - Check for circular relationships
  - Report: `relationship_validation_report.json`
  - Priority: **HIGH**

### 7.2 Medical Accuracy Validation
- [ ] **Validate red flags are correct**
  - Cross-check with medical domain experts if available
  - Ensure no false negatives (all true red flags captured)
  - Report: `red_flag_validation_report.json`
  - Priority: **CRITICAL**

- [ ] **Validate urgency classifications**
  - Ensure disease → urgency mappings are medically correct
  - Cross-reference with CLAUDE.md standards
  - Report: `urgency_validation_report.json`
  - Priority: **CRITICAL**

### 7.3 Create Test Scenarios
- [ ] **Build test cases for GraphRAG queries**
  - Create symptom → disease test queries
  - Create treatment → disease test queries
  - Create red flag detection test cases
  - Output: `test_scenarios.json`
  - Priority: **MEDIUM**

- [ ] **Validate triage recommendations**
  - Test that system recommends correct urgency
  - Test red flag detection accuracy
  - Output: `triage_test_results.json`
  - Priority: **HIGH**

### 7.4 Performance Testing
- [ ] **Test query performance on Neo4j**
  - Benchmark common queries
  - Optimize indexes if needed
  - Output: `performance_report.json`
  - Priority: **LOW**

---

## PHASE 8: FINAL DELIVERABLES

### 8.1 Create Indexed Knowledge Graph
- [ ] **Populate Neo4j with all entities and relationships**
  - Import nodes (entities)
  - Import relationships
  - Create indexes
  - Priority: **CRITICAL**

- [ ] **Verify Neo4j import successful**
  - Query sample nodes
  - Verify relationship counts
  - Check index creation
  - Priority: **CRITICAL**

### 8.2 Create Final Export Files
- [ ] **Export complete prepared dataset**
  - `wills_eye_graphrag_complete.json` (all entities + relationships)
  - `neo4j_import.cypher` (ready-to-import Cypher script)
  - `validation_reports/` (all validation reports)
  - Priority: **HIGH**

- [ ] **Create summary documentation**
  - Document entity counts and types
  - Document relationship counts by type
  - Document red flags and urgency classifications
  - Output: `GRAPHRAG_PREPARATION_SUMMARY.md`
  - Priority: **MEDIUM**

### 8.3 Create API/Query Documentation
- [ ] **Document entity schema**
  - Provide schema documentation
  - Document required/optional properties
  - Priority: **MEDIUM**

- [ ] **Document query patterns**
  - Show example queries for common use cases
  - Output: `QUERY_PATTERNS.md`
  - Priority: **MEDIUM**

---

# DEPENDENCY GRAPH

```
Phase 1 (Content Extraction)
    ↓
Phase 2 (Entity Extraction)
    ↓
Phase 3 (Relationship Extraction)
    ↓
Phase 4 (Domain Standardization) [Can run parallel to Phase 3]
    ↓
Phase 5 (Red Flag Extraction) [Can run parallel to Phase 4]
    ↓
Phase 6 (Graph Preparation)
    ↓
Phase 7 (Validation) [Must run after Phase 6]
    ↓
Phase 8 (Final Deliverables) [Must run after Phase 7]
```

---

# RECOMMENDED IMPLEMENTATION ORDER

## Priority 1: CRITICAL (Do First)
1. Phase 1.1: Extract chapter content
2. Phase 2.1: Extract disease entities
3. Phase 2.2: Extract symptom entities
4. Phase 3.1: Disease-symptom relationships
5. Phase 4.2: Urgency classifications
6. Phase 5.1: Red flag extraction
7. Phase 6.1: Create node-link format
8. Phase 7.2: Medical accuracy validation

## Priority 2: HIGH (Do Next)
1. Phase 1.2: Extract and structure tables
2. Phase 1.3: Extract and structure lists
3. Phase 3.2: Disease-treatment relationships
4. Phase 4.1: Terminology standardization
5. Phase 5.2: Safety warnings
6. Phase 6.2: Neo4j preparation

## Priority 3: MEDIUM (Do After)
1. Phase 2.3: Treatment entities
2. Phase 3.3-3.6: Additional relationships
3. Phase 4.3: Disease hierarchies
4. Phase 5.3: Management protocols
5. Phase 1.4: Image processing

## Priority 4: LOW (Nice to Have)
1. Phase 6.3: Embedding metadata
2. Phase 7.4: Performance testing
3. Advanced cross-referencing

---

# ESTIMATED EFFORT

| Phase | Estimated Effort | Priority |
|-------|------------------|----------|
| Phase 1: Content Extraction | 16-24 hours | CRITICAL |
| Phase 2: Entity Extraction | 20-30 hours | CRITICAL |
| Phase 3: Relationship Extraction | 24-36 hours | CRITICAL |
| Phase 4: Domain Standardization | 16-24 hours | HIGH |
| Phase 5: Red Flag & Safety | 12-16 hours | CRITICAL |
| Phase 6: Graph Preparation | 12-16 hours | CRITICAL |
| Phase 7: Validation & Testing | 16-20 hours | HIGH |
| Phase 8: Final Deliverables | 8-12 hours | HIGH |
| **TOTAL** | **124-178 hours** | - |

---

# OUTPUT FILES SUMMARY

## Required Output Files
- `wills_eye_chapters_structured.json` - Structured chapter content
- `wills_eye_tables.json` - Extracted and structured tables
- `wills_eye_lists.json` - Extracted lists and differential diagnoses
- `diseases.json` - Disease entities
- `symptoms.json` - Symptom entities
- `signs.json` - Sign entities
- `treatments.json` - Treatment entities
- `graphrag_nodes.json` - GraphRAG compatible nodes
- `graphrag_edges.json` - GraphRAG compatible edges
- `neo4j_import.cypher` - Neo4j import script
- `red_flags.json` - Red flag conditions with keywords
- `validation_reports/` - All validation reports
- `GRAPHRAG_PREPARATION_SUMMARY.md` - Final summary

---

# Notes & Considerations

1. **Medical Accuracy**: This is medical software. Every extracted entity must be validated for accuracy.
2. **Red Flags**: 100% recall required - no false negatives on emergent conditions.
3. **Terminology**: Use standardized medical codes (ICD-10, SNOMED CT) where possible.
4. **Cross-References**: Manual review may be needed for complex section relationships.
5. **Images**: 522 images are present - decide whether to include image metadata in knowledge graph.
6. **Updates**: Process allows for incremental updates as more content is extracted.

