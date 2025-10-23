# Urgency Level Classification

> **IMPORTANT**: This document provides example urgency classifications for reference, but the **authoritative source** for urgency levels is **The Wills Eye Manual (7th Edition)**.
>
> All urgency classifications used in the triage system **MUST be extracted directly from the textbook** via the GraphRAG preparation pipeline (Phase 4.2). Do NOT use hardcoded urgency levels in production.
>
> **Extraction Source**: `indexing/output/phase4/urgency_classifications.json` (to be created via GraphRAG pipeline)

## Three-Tier System

The Wills Eye Manual categorizes conditions by urgency. These categories guide appropriate timing for medical evaluation.

### Emergent (ER Immediately)
**Definition**: Condition that may result in permanent vision loss or systemic complication if not treated within hours.

**Example conditions** (for reference only - extract from textbook):
- Central Retinal Artery Occlusion
- Acute Angle-Closure Glaucoma
- Endophthalmitis
- Orbital Cellulitis
- Retinal Detachment
- Chemical Burns
- Penetrating Trauma

**Timeframe**: Minutes to hours
**Disposition**: Emergency Department
**Typical keywords** (extracted from textbook): "sudden", "severe", "trauma", "chemical"

### Urgent (Within 24-48 hours)
**Definition**: Condition requiring prompt treatment to prevent complications, but not immediately sight-threatening.

**Example conditions** (for reference only - extract from textbook):
- Bacterial Keratitis
- Corneal Ulcer
- Anterior Uveitis
- Herpes Zoster Ophthalmicus
- Severe Bacterial Conjunctivitis (contact lens wearer)

**Timeframe**: 24-48 hours
**Disposition**: Urgent care or ophthalmologist same/next day
**Typical keywords** (extracted from textbook): "pain", "contact lens", "worsening"

### Non-Urgent (Schedule Appointment)
**Definition**: Condition that can be managed with routine appointment.

**Example conditions** (for reference only - extract from textbook):
- Viral Conjunctivitis
- Allergic Conjunctivitis
- Dry Eye Syndrome
- Chalazion/Hordeolum (simple)
- Pinguecula

**Timeframe**: Days to weeks
**Disposition**: Routine ophthalmologist appointment
**Typical keywords** (extracted from textbook): "itchy", "gritty", "watery", "chronic"

## Decision Tree
```
Chief Complaint
│
├─ Contains Red Flag Keywords? ──YES──> EMERGENT
│
├─ NO
│   │
│   ├─ Vision Loss Present? ──YES──> EMERGENT
│   │
│   ├─ Severe Pain + Red Eye? ──YES──> URGENT/EMERGENT
│   │
│   ├─ Contact Lens Wearer + Red Eye? ──YES──> URGENT
│   │
│   ├─ Moderate Pain? ──YES──> URGENT
│   │
│   └─ Mild Symptoms? ──YES──> NON-URGENT
```

## Implementation in Code

Location: `backend/apps/triage/services/risk_assessment.py`
```python
class UrgencyClassifier:
    """Determine urgency level based on symptoms"""
    
    def classify(
        self,
        symptoms: List[str],
        red_flags: List[str],
        vision_affected: bool,
        pain_level: int  # 0-10
    ) -> str:
        # Implementation here
        pass
```