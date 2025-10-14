"""Configuration for knowledge graph indexing."""
import os
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


class UrgencyLevel(str, Enum):
    """Medical urgency classification"""
    EMERGENT = "EMERGENT"  # ER immediately
    URGENT = "URGENT"  # Within 24-48 hours
    NON_URGENT = "NON_URGENT"  # Schedule appointment


# Neo4j Configuration (for Graphiti)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Custom OpenAI Configuration (for Graphiti LLM operations)
CUSTOM_OPENAI_BASE_URL = os.getenv("CUSTOM_OPENAI_BASE_URL", "https://api.openai.com/v1")
CUSTOM_OPENAI_API_KEY = os.getenv("CUSTOM_OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
CUSTOM_OPENAI_MODEL = os.getenv("CUSTOM_OPENAI_MODEL", "gpt-4")

# Embedding Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # "openai" or "sentence-transformers"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # OpenAI default

# OpenAI Embedding Configuration
OPENAI_EMBEDDING_API_KEY = os.getenv("OPENAI_EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY"))
OPENAI_EMBEDDING_BASE_URL = os.getenv("OPENAI_EMBEDDING_BASE_URL", "https://api.openai.com/v1")

# Sentence Transformers (BioBERT) - Fallback
SENTENCE_TRANSFORMERS_MODEL = os.getenv(
    "SENTENCE_TRANSFORMERS_MODEL",
    "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb"
)

# Embedding dimensions (auto-detected, but can be overridden)
EMBEDDING_DIMENSION_MAP = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))  # OpenAI default
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))  # OpenAI supports larger batches

# Indexing Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Medical Safety Configuration
TRIAGE_THRESHOLD = 0.2  # 20% likelihood threshold for referral
RED_FLAG_SIMILARITY_THRESHOLD = 0.85  # For semantic red flag detection

# Red Flag Keywords (Emergent Conditions)
# Source: docs/medical/red-flags.md
RED_FLAG_KEYWORDS = [
    # Vision Loss
    "sudden vision loss",
    "sudden loss of vision",
    "can't see",
    "cannot see",
    "went blind",
    "lost vision",
    "vision went dark",
    "painless vision loss",

    # Trauma
    "chemical burn",
    "chemical splash",
    "chemical in eye",
    "acid in eye",
    "alkali burn",
    "penetrating trauma",
    "penetrating injury",
    "something stuck in eye",
    "puncture wound",
    "eye rupture",
    "ruptured globe",

    # Severe Symptoms
    "severe eye pain",
    "worst pain",
    "excruciating pain",
    "severe headache with eye pain",
    "nausea with eye pain",
    "vomiting with eye pain",

    # Neurological
    "new floaters with flashes",
    "curtain over vision",
    "sudden double vision",
    "sudden drooping eyelid",
    "pupil not reacting",

    # Infection
    "eye surgery infection",
    "severe infection",
    "pus from eye",

    # Other Emergent
    "eye popped out",
    "proptosis",
    "orbital cellulitis",
]

# Urgency Keywords
URGENT_KEYWORDS = [
    "contact lens pain",
    "contact lens red eye",
    "worsening vision",
    "moderate pain",
    "photophobia",
    "light sensitivity",
    "herpes",
    "shingles",
]

NON_URGENT_KEYWORDS = [
    "itchy eyes",
    "watery eyes",
    "gritty sensation",
    "mild redness",
    "chronic",
    "dry eyes",
]

# Anatomical Terms (for ANATOMY nodes)
ANATOMICAL_TERMS = [
    "cornea", "conjunctiva", "sclera", "iris", "pupil",
    "lens", "retina", "macula", "optic nerve", "vitreous",
    "anterior chamber", "posterior chamber", "eyelid",
    "orbit", "lacrimal gland", "tear duct"
]

# Section Key Mappings
# Maps JSON field names to node types
FIELD_TO_NODE_TYPE = {
    "Symptoms": NodeType.SYMPTOM,
    "Signs": NodeType.SIGN,
    "Treatment": NodeType.TREATMENT,
    "Etiology": NodeType.ETIOLOGY,
    "Differential Diagnosis": NodeType.DIFFERENTIAL,
    "Work Up": NodeType.PROCEDURE,
    "Complications": NodeType.COMPLICATION,
}

# Logging
LOG_FILE = "knowledge_graph_indexing.log"
ERROR_LOG_FILE = "indexing_errors.json"

# Validation
REQUIRED_EMERGENT_CONDITIONS = [
    "3.1 Chemical Burn",
    "Central Retinal Artery Occlusion",
    "Acute Angle-Closure Glaucoma",
    "Endophthalmitis",
    "Retinal Detachment",
    "Orbital Cellulitis",
]

def validate_config() -> None:
    """Validate required configuration."""
    if not NEO4J_PASSWORD:
        raise ValueError(
            "NEO4J_PASSWORD environment variable is required. "
            "Set it with: export NEO4J_PASSWORD='your_password'"
        )

    if not CUSTOM_OPENAI_API_KEY:
        raise ValueError(
            "CUSTOM_OPENAI_API_KEY (or OPENAI_API_KEY) environment variable is required. "
            "Set it with: export CUSTOM_OPENAI_API_KEY='your_api_key'"
        )

    if EMBEDDING_PROVIDER == "openai" and not OPENAI_EMBEDDING_API_KEY:
        raise ValueError(
            "OPENAI_EMBEDDING_API_KEY (or OPENAI_API_KEY) environment variable is required for OpenAI embeddings. "
            "Set it with: export OPENAI_EMBEDDING_API_KEY='your_api_key'"
        )

    if not os.path.exists("../data/wills_eye_structured.json"):
        raise FileNotFoundError(
            "Wills Eye Manual JSON not found. "
            "Expected path: ../data/wills_eye_structured.json"
        )
