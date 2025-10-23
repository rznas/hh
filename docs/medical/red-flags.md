# Red Flag Conditions - Immediate Referral Required

> **⚠️ DEPRECATED - FOR REFERENCE ONLY**
>
> **This file contains hardcoded red flags and should NOT be used as the authoritative source.**
>
> **Correct approach**: Red flags must be extracted from the Wills Eye Manual textbook via the GraphRAG preparation pipeline (Phase 5.1).
>
> **See**: `docs/GRAPHRAG_PREPARATION_TODO.md` Phase 5.1 for extraction process
>
> **Output file**: `indexing/output/phase5/red_flags.json`
>
> This file remains for reference purposes only and to illustrate the expected structure of red flag data.

---

## Immediate Emergency Department Referral

### 1. Sudden Vision Loss
- **Description**: Painless or painful sudden decrease in vision
- **Examples**: 
  - Central Retinal Artery Occlusion (CRAO)
  - Retinal Detachment
  - Vitreous Hemorrhage
- **Keywords**: "sudden", "can't see", "went blind", "lost vision"
- **Action**: ER immediately

### 2. Chemical Exposure
- **Description**: Any chemical splash to eye
- **Examples**: Acid, alkali, cleaning products
- **Keywords**: "chemical", "splash", "cleaner", "acid", "bleach"
- **Action**: Irrigate immediately, then ER
- **Special**: Start irrigation before transport

### 3. Penetrating Trauma
- **Description**: Object penetrated globe
- **Examples**: Metal fragment, glass, sharp object
- **Keywords**: "stuck", "penetrated", "inside eye", "metal", "glass"
- **Action**: Shield eye (do NOT remove object), ER immediately

[Continue with all red flags...]

## Detection Logic
```python
# Pseudo-code for red flag detection
RED_FLAG_KEYWORDS = {
    "sudden_vision_loss": [
        "sudden vision loss",
        "suddenly blind",
        "can't see suddenly",
        "vision went black"
    ],
    "chemical_burn": [
        "chemical in eye",
        "splash",
        "cleaner in eye",
        "acid",
        "alkali"
    ],
    # ...
}

def contains_red_flag(text: str) -> tuple[bool, str]:
    """
    Check if patient text contains red flag keywords
    Returns: (is_red_flag, flag_type)
    """
    text_lower = text.lower()
    for flag_type, keywords in RED_FLAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return True, flag_type
    return False, None
```

## Testing Red Flag Detection

See: `tests/medical/test_red_flag_detection.py`