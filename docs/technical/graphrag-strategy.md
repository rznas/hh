# GraphRAG Strategy for Wills Eye Manual Knowledge Base

## Executive Summary

This document outlines the optimal GraphRAG approach for transforming the Wills Eye Manual structured JSON into a queryable knowledge graph using Zep Graphiti. The strategy prioritizes medical safety, efficient retrieval, and accurate triage recommendations.

## Data Structure Analysis

### Current JSON Structure
```
{
  "Chapter Name": {
    "Section/Condition Name": {
      "_content": [...],
      "Symptoms": [...],
      "Signs": {...},
      "Treatment": {...},
      "Follow Up": [...],
      ...
    }
  }
}
```

**Key Characteristics:**
- 14 top-level chapters (Trauma, Cornea, Glaucoma, etc.)
- Hierarchical nested structure with subsections
- Mixed data types (lists, dicts, strings)
- Contains critical medical metadata (urgency, differential diagnoses)
- References between sections (e.g., "See 4.3, Dry Eye Syndrome")

## Recommended GraphRAG Architecture

### 1. **Hybrid Approach: Structured Graph + Vector Embeddings**

**Why Hybrid?**
- **Structured relationships** for rule-based triage (e.g., Disease → Symptoms → Urgency)
- **Vector embeddings** for semantic similarity (user's free-text → standardized chief complaint)
- **Best of both worlds**: Deterministic red flag detection + flexible symptom matching

### 2. **Node Schema** (Based on `backend/schema/knowladge_base.py`)

```python
# Primary Medical Entities
NODE_TYPES = {
    "DISEASE": "Bacterial Keratitis",
    "SYMPTOM": "eye pain",
    "SIGN": "corneal ulcer",
    "TREATMENT": "topical fluoroquinolone",
    "ANATOMY": "cornea",
    "DIFFERENTIAL": "viral keratitis",
    "CHAPTER": "Cornea",
    "SECTION": "4.11 Bacterial Keratitis",
    "ETIOLOGY": "Pseudomonas aeruginosa",
    "RISK_FACTOR": "contact lens wear",
    "COMPLICATION": "corneal perforation",
    "LAB_TEST": "corneal culture",
    "IMAGING": "OCT",
    "MEDICATION": "ciprofloxacin 0.3%",
    "PROCEDURE": "corneal debridement"
}
```

**Critical Metadata for Each Disease Node:**
```python
{
    "urgency_level": "EMERGENT | URGENT | NON_URGENT",
    "triage_threshold": 0.2,  # Likelihood threshold for referral
    "red_flag_keywords": ["sudden vision loss", "severe pain"],
    "wills_eye_section": "4.11",
    "chapter": "Cornea",
    "requires_emergency": true/false
}
```

### 3. **Edge Schema** (Relationship Types)

```python
EDGE_TYPES = {
    # Symptom-Disease Relationships
    "PRESENTS_WITH": Disease → Symptom (e.g., "Keratitis PRESENTS_WITH eye pain")
    "SHOWS_SIGN": Disease → Sign (e.g., "Keratitis SHOWS_SIGN corneal infiltrate")

    # Diagnostic Relationships
    "INDICATES": Symptom → Disease (reverse, with confidence weight)
    "DIFFERENTIATES": Disease → Differential (e.g., "Bacterial vs Viral Keratitis")

    # Treatment Relationships
    "TREATED_WITH": Disease → Treatment/Medication
    "REQUIRES": Disease → Procedure/Test
    "CONTRAINDICATES": Condition → Treatment (safety)

    # Anatomical & Causal
    "AFFECTS": Disease → Anatomy
    "CAUSED_BY": Disease → Etiology
    "INCREASES_RISK": Risk Factor → Disease

    # Temporal & Hierarchical
    "COMPLICATES": Disease → Complication
    "TEMPORAL_FOLLOWS": Stage1 → Stage2 (progression)
    "BELONGS_TO": Disease → Chapter/Section
    "SIMILAR_TO": Disease → Disease (for DDx)
}
```

**Edge Properties:**
```python
{
    "confidence": 0.0-1.0,  # How strong is this relationship?
    "frequency": "common" | "rare",
    "time_course": "acute" | "chronic",
    "severity": "mild" | "moderate" | "severe"
}
```

### 4. **Multi-Level Indexing Strategy**

#### Level 1: Chief Complaint Vectorization
```python
# Index all symptoms/signs with embeddings for semantic search
symptoms = [
    "red eye", "eye pain", "blurry vision", "discharge",
    "sudden vision loss", "floaters", "photophobia"
]
# Vector DB: User query → Top N matching standardized symptoms
```

#### Level 2: Differential Diagnosis Graph Traversal
```python
# Given matched symptoms, traverse graph to find diseases
query = """
MATCH (symptom:SYMPTOM {name: "eye pain"})<-[r:PRESENTS_WITH]-(disease:DISEASE)
WHERE disease.urgency_level IN ["EMERGENT", "URGENT"]
RETURN disease, r.confidence
ORDER BY disease.urgency_level DESC, r.confidence DESC
"""
```

#### Level 3: Rule-Based Red Flag Detection
```python
# Bypass graph for immediate referral
RED_FLAGS = {
    "sudden painless vision loss": "EMERGENT",
    "chemical burn": "EMERGENT",
    "penetrating trauma": "EMERGENT",
    "new floaters + flashes": "URGENT",
}
# Keyword matching + semantic similarity (threshold: 0.85)
```

## Implementation Phases

### Phase 1: Schema Definition & Extraction
**Goal:** Parse JSON → Extract entities & relationships

**Tasks:**
1. Define Zep Graphiti schema (nodes, edges, properties)
2. Write parsers for different JSON structures:
   - Flat lists (symptoms, signs)
   - Nested dicts (treatment protocols)
   - Cross-references (section links)
3. Extract urgency metadata from content
4. Identify red flags per condition

**Output:**
- `backend/knowledge_graph/schema.py`
- `indexing/parsers/wills_eye_parser.py`

### Phase 2: Graph Population
**Goal:** Transform parsed data → Zep Graphiti nodes/edges

**Strategy:**
```python
# For each condition in JSON
for chapter, sections in wills_eye_data.items():
    # Create Chapter node
    chapter_node = create_node(type="CHAPTER", name=chapter)

    for section_id, content in sections.items():
        # Create Disease node
        disease = create_node(
            type="DISEASE",
            name=section_id,
            urgency=extract_urgency(content),
            red_flags=extract_red_flags(content)
        )
        create_edge(disease, chapter_node, type="BELONGS_TO")

        # Create Symptom nodes & edges
        for symptom in content.get("Symptoms", []):
            symptom_node = get_or_create_node(type="SYMPTOM", name=symptom)
            create_edge(disease, symptom_node, type="PRESENTS_WITH")
            create_edge(symptom_node, disease, type="INDICATES",
                        confidence=calculate_specificity(symptom, disease))

        # Create Treatment nodes
        for treatment in content.get("Treatment", []):
            treatment_node = create_node(type="TREATMENT", content=treatment)
            create_edge(disease, treatment_node, type="TREATED_WITH")
```

**Critical:** Handle cross-references
```python
# "See 4.3, Dry Eye Syndrome" → Create edge to referenced section
references = extract_references(content)
for ref in references:
    target_disease = find_node_by_section(ref)
    create_edge(disease, target_disease, type="SIMILAR_TO")
```

### Phase 3: Embedding & Vectorization
**Goal:** Enable semantic search for symptom matching

**Approach:**
1. **Symptom Embeddings:** Use medical BERT (e.g., BioBERT, PubMedBERT)
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb')

   for symptom_node in graph.nodes(type="SYMPTOM"):
       embedding = model.encode(symptom_node.name)
       symptom_node.embedding = embedding
   ```

2. **Chief Complaint → Symptom Matching:**
   ```python
   user_input = "My eye is red and painful"
   user_embedding = model.encode(user_input)

   # Cosine similarity search
   matched_symptoms = vector_search(user_embedding, top_k=5, threshold=0.7)
   # Returns: ["eye pain" (0.92), "red eye" (0.88), ...]
   ```

3. **Differential Diagnosis Embeddings:**
   ```python
   # Embed full condition descriptions for context
   for disease_node in graph.nodes(type="DISEASE"):
       full_context = f"{disease_node.name}. Symptoms: {symptoms}. Signs: {signs}."
       disease_node.context_embedding = model.encode(full_context)
   ```

### Phase 4: Query Optimization
**Goal:** Fast, accurate retrieval for triage

**Query Types:**

#### 1. Red Flag Check (< 200ms)
```python
def check_red_flags(user_input: str) -> tuple[bool, str]:
    # Keyword matching
    for flag, urgency in RED_FLAG_KEYWORDS.items():
        if flag in user_input.lower():
            return True, urgency

    # Semantic check for edge cases
    flag_embeddings = [model.encode(f) for f in RED_FLAG_KEYWORDS.keys()]
    user_embedding = model.encode(user_input)
    max_similarity = max(cosine_similarity(user_embedding, flag_embeddings))

    if max_similarity > 0.85:
        return True, "EMERGENT"
    return False, None
```

#### 2. Differential Diagnosis Retrieval (< 1s)
```python
def get_differential_diagnosis(symptoms: list[str]) -> list[dict]:
    # Graph traversal query
    query = """
    MATCH (s:SYMPTOM)<-[:PRESENTS_WITH]-(d:DISEASE)
    WHERE s.name IN $symptoms
    WITH d, COUNT(s) as symptom_matches
    MATCH (d)-[:SHOWS_SIGN]->(sign:SIGN)
    OPTIONAL MATCH (d)-[:CAUSED_BY]->(etiology:ETIOLOGY)
    RETURN d.name, d.urgency_level, symptom_matches,
           COLLECT(sign.name) as signs,
           COLLECT(etiology.name) as causes
    ORDER BY d.urgency_level DESC, symptom_matches DESC
    LIMIT 10
    """
    return zep_client.query(query, symptoms=symptoms)
```

#### 3. Contextual Follow-Up Questions
```python
def generate_clarifying_questions(candidate_diseases: list[str]) -> list[str]:
    # Find discriminating symptoms/signs
    query = """
    MATCH (d:DISEASE)-[:PRESENTS_WITH]->(s:SYMPTOM)
    WHERE d.name IN $diseases
    WITH s, COLLECT(d.name) as associated_diseases
    WHERE SIZE(associated_diseases) = 1  // Unique to one disease
    RETURN s.name, associated_diseases[0]
    LIMIT 3
    """
    discriminators = zep_client.query(query, diseases=candidate_diseases)

    questions = [
        f"Do you have {symptom}?"
        for symptom, _ in discriminators
    ]
    return questions
```

## Advanced Features

### 1. Probabilistic Triage
```python
# Bayesian updating based on user responses
initial_priors = {
    "Bacterial Keratitis": 0.15,
    "Viral Conjunctivitis": 0.40,
    "Allergic Conjunctivitis": 0.30,
}

# Update after each answer
def update_probabilities(priors: dict, symptom: str, present: bool):
    # P(Disease | Symptom) ∝ P(Symptom | Disease) * P(Disease)
    for disease, prior in priors.items():
        likelihood = get_likelihood(disease, symptom, present)
        priors[disease] *= likelihood

    # Normalize
    total = sum(priors.values())
    return {d: p/total for d, p in priors.items()}
```

### 2. Treatment Contraindication Checking
```python
query = """
MATCH (disease:DISEASE)-[:TREATED_WITH]->(treatment:TREATMENT)
MATCH (patient_condition:DISEASE)-[:CONTRAINDICATES]->(treatment)
WHERE disease.name = $disease AND patient_condition.name IN $patient_history
RETURN treatment.name, patient_condition.name
"""
# Ensure no dangerous recommendations
```

### 3. Multi-Hop Reasoning
```python
# "Patient has diabetes" → Check for diabetic retinopathy risk
query = """
MATCH path = (risk:RISK_FACTOR {name: "diabetes"})-[:INCREASES_RISK]->(d:DISEASE)
          -[:COMPLICATES]->(complication:COMPLICATION)
WHERE complication.urgency_level = "EMERGENT"
RETURN path
"""
```

## Performance Optimization

### Caching Strategy
```python
# Cache common queries
@lru_cache(maxsize=1000)
def get_condition_details(condition_name: str):
    return zep_client.get_node(type="DISEASE", name=condition_name)

# Pre-compute embeddings for all symptoms (done at indexing time)
SYMPTOM_EMBEDDINGS = load_precomputed_embeddings()
```

### Indexing Best Practices
1. **Batch Processing:** Index in chunks (100-500 nodes/edges per batch)
2. **Idempotency:** Check for existing nodes before creating duplicates
3. **Logging:** Track indexing progress, errors, skipped entries
4. **Validation:** Verify graph integrity after indexing

## Safety & Compliance

### Medical Accuracy Verification
```python
# After indexing, run validation queries
validation_checks = [
    ("Sudden vision loss", "EMERGENT"),  # Should always be emergent
    ("Mild allergic conjunctivitis", "NON_URGENT"),
    ("Penetrating trauma", "EMERGENT"),
]

for symptom, expected_urgency in validation_checks:
    result = query_urgency(symptom)
    assert result == expected_urgency, f"Failed: {symptom}"
```

### Audit Trail
```python
# Log all graph queries for medical audits
def query_with_audit(query: str, params: dict, user_id: str):
    result = zep_client.query(query, **params)

    # Log to Langfuse
    langfuse.log_event(
        name="graph_query",
        user_id=user_id,
        input={"query": query, "params": params},
        output=result,
        metadata={"timestamp": datetime.now()}
    )
    return result
```

## Cost & Scalability

### Zep Graphiti Considerations
- **Nodes:** ~5,000-10,000 (diseases, symptoms, signs, treatments)
- **Edges:** ~50,000-100,000 (relationships)
- **Embeddings:** 768-dim vectors (BioBERT) × 10,000 entities ≈ 30 MB
- **Query Cost:** <$0.001 per triage session (assuming cached embeddings)

### Incremental Updates
```python
# For updating knowledge graph when Wills Eye Manual updates
def incremental_update(new_content: dict, section: str):
    # Find existing nodes
    existing = zep_client.get_node(type="SECTION", name=section)

    # Compare and update only changed entities
    diff = compute_diff(existing, new_content)

    for change in diff:
        if change.type == "ADD":
            create_node(change.entity)
        elif change.type == "UPDATE":
            update_node(change.entity)
        elif change.type == "DELETE":
            delete_node(change.entity)
```

## Testing Strategy

### Unit Tests
```python
# Test entity extraction
def test_extract_symptoms():
    content = {"Symptoms": ["eye pain", "photophobia"]}
    symptoms = extract_symptoms(content)
    assert len(symptoms) == 2
    assert "eye pain" in symptoms

# Test urgency classification
def test_urgency_extraction():
    content = {"_content": ["This is an EMERGENCY condition"]}
    urgency = extract_urgency(content)
    assert urgency == "EMERGENT"
```

### Integration Tests
```python
# Test end-to-end graph query
def test_red_flag_detection():
    user_input = "I suddenly can't see out of my left eye"
    result = triage_agent.process(user_input)
    assert result.urgency == "EMERGENT"
    assert "emergency" in result.recommendation.lower()
```

### Medical Validation Tests
```python
# Test against known scenarios from test_scenarios/
def test_bacterial_keratitis_scenario():
    scenario = load_scenario("bacterial_keratitis_contact_lens.json")
    result = triage_agent.process(scenario.input)
    assert result.likely_condition == "Bacterial Keratitis"
    assert result.urgency == "URGENT"
```

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Schema Design | 1 week | `schema.py`, data model diagrams |
| Parser Development | 2 weeks | `wills_eye_parser.py`, unit tests |
| Graph Population | 2 weeks | Fully indexed knowledge graph |
| Embedding Integration | 1 week | Vector search functionality |
| Query Optimization | 2 weeks | Optimized retrieval, caching |
| Validation & Testing | 2 weeks | Test suite, medical accuracy checks |
| **Total** | **10 weeks** | Production-ready GraphRAG system |

## Next Steps

1. **Create `indexing/` module structure:**
   ```
   indexing/
   ├── __init__.py
   ├── parsers/
   │   ├── wills_eye_parser.py
   │   └── entity_extractor.py
   ├── graph_builder.py
   ├── embedding_service.py
   ├── index_knowledge_graph.py (main script)
   └── tests/
       └── test_indexing.py
   ```

2. **Define Zep Graphiti connection:**
   ```python
   # backend/knowledge_graph/client.py
   from graphiti import ZepGraphitiClient

   client = ZepGraphitiClient(
       api_key=os.getenv("ZEP_API_KEY"),
       graph_name="wills_eye_medical_kg"
   )
   ```

3. **Start with pilot chapter:**
   - Index "Trauma" chapter first (well-defined, critical urgency)
   - Validate accuracy before scaling to all 14 chapters

4. **Iterate on query performance:**
   - Benchmark red flag detection (<200ms)
   - Optimize differential diagnosis retrieval (<1s)
   - Test with real user queries from test scenarios

## References

- Wills Eye Manual 7th Edition (authoritative source)
- `backend/schema/knowladge_base.py` (node/edge types)
- `docs/medical/framework.md` (triage logic)
- `docs/medical/urgency-levels.md` (classification system)
- Zep Graphiti Documentation: https://docs.getzep.com/graphiti/
