from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in the medical knowledge graph"""
    DISEASE = "disease"
    SYMPTOM = "symptom"
    SIGN = "sign"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    ANATOMY = "anatomy"
    ETIOLOGY = "etiology"
    RISK_FACTOR = "risk_factor"
    DIFFERENTIAL = "differential"
    COMPLICATION = "complication"
    LAB_TEST = "lab_test"
    IMAGING = "imaging"
    CHAPTER = "chapter"
    SECTION = "section"

class EdgeType(str, Enum):
    """Types of relationships in the medical knowledge graph"""
    PRESENTS_WITH = "presents_with"  # Disease -> Symptom
    SHOWS_SIGN = "shows_sign"  # Disease -> Sign
    CAUSED_BY = "caused_by"  # Disease -> Etiology
    TREATED_WITH = "treated_with"  # Disease -> Treatment
    REQUIRES = "requires"  # Disease -> Procedure/Test
    AFFECTS = "affects"  # Disease -> Anatomy
    INDICATES = "indicates"  # Symptom -> Disease (reverse)
    DIFFERENTIATES = "differentiates"  # Disease -> Differential
    INCREASES_RISK = "increases_risk"  # Risk Factor -> Disease
    CONTRAINDICATES = "contraindicates"  # Condition -> Treatment
    COMPLICATES = "complicates"  # Disease -> Complication
    BELONGS_TO = "belongs_to"  # Disease -> Chapter/Section
    SIMILAR_TO = "similar_to"  # Disease -> Disease
    ASSOCIATED_WITH = "associated_with"  # Generic association
    TEMPORAL_FOLLOWS = "temporal_follows"  # For progression
