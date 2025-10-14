# Urgency Level Classification

Comprehensive guide for classifying conditions by urgency.

## Three-Tier System

### Emergent (ER Immediately)
**Definition**: Condition that may result in permanent vision loss or systemic complication if not treated within hours.

**Examples**:
- Central Retinal Artery Occlusion
- Acute Angle-Closure Glaucoma  
- Endophthalmitis
- Orbital Cellulitis
- Retinal Detachment
- Chemical Burns
- Penetrating Trauma

**Timeframe**: Minutes to hours  
**Disposition**: Emergency Department  
**Keywords**: "sudden", "severe", "trauma", "chemical"

### Urgent (Within 24-48 hours)
**Definition**: Condition requiring prompt treatment to prevent complications, but not immediately sight-threatening.

**Examples**:
- Bacterial Keratitis
- Corneal Ulcer
- Anterior Uveitis
- Herpes Zoster Ophthalmicus
- Severe Bacterial Conjunctivitis (contact lens wearer)

**Timeframe**: 24-48 hours  
**Disposition**: Urgent care or ophthalmologist same/next day  
**Keywords**: "pain", "contact lens", "worsening"

### Non-Urgent (Schedule Appointment)
**Definition**: Condition that can be managed with routine appointment.

**Examples**:
- Viral Conjunctivitis
- Allergic Conjunctivitis
- Dry Eye Syndrome
- Chalazion/Hordeolum (simple)
- Pinguecula

**Timeframe**: Days to weeks  
**Disposition**: Routine ophthalmologist appointment  
**Keywords**: "itchy", "gritty", "watery", "chronic"

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