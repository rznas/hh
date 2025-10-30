"""Configuration for Microsoft GraphRAG implementation."""
import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """LLM provider options."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class EmbeddingProvider(str, Enum):
    """Embedding provider options."""
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"


class GraphRAGConfig(BaseModel):
    """GraphRAG configuration."""

    # Neo4j Configuration
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "password"))

    # LLM Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))
    openai_model: str = Field(default="gpt-4o")
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")

    # Embedding Configuration
    embedding_provider: EmbeddingProvider = Field(default=EmbeddingProvider.OPENAI)
    embedding_model: str = Field(default="text-embedding-3-large")
    embedding_dimensions: int = Field(default=1536)
    biobert_model: str = Field(default="dmis-lab/biobert-v1.1")

    # Entity Extraction Configuration
    entity_extraction_temperature: float = Field(default=0.1)
    entity_extraction_max_tokens: int = Field(default=4000)
    entity_batch_size: int = Field(default=5)

    # Relationship Extraction Configuration
    relationship_extraction_temperature: float = Field(default=0.1)
    relationship_extraction_max_tokens: int = Field(default=2000)

    # Community Detection Configuration
    community_algorithm: str = Field(default="leiden")  # leiden or louvain
    community_resolution: float = Field(default=1.0)
    max_community_levels: int = Field(default=3)
    min_community_size: int = Field(default=3)

    # Community Summarization Configuration
    summary_temperature: float = Field(default=0.3)
    summary_max_tokens: int = Field(default=500)

    # Search Configuration
    local_search_top_k: int = Field(default=10)
    global_search_top_k: int = Field(default=5)
    max_context_tokens: int = Field(default=8000)

    # Performance Configuration
    max_concurrent_requests: int = Field(default=5)
    retry_attempts: int = Field(default=3)
    retry_delay_seconds: float = Field(default=1.0)

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="graphrag_indexing.log")

    class Config:
        """Pydantic config."""
        use_enum_values = True


def load_config() -> GraphRAGConfig:
    """Load configuration from environment variables.

    Returns:
        GraphRAG configuration
    """
    return GraphRAGConfig()


def validate_config(config: Optional[GraphRAGConfig] = None) -> None:
    """Validate configuration.

    Args:
        config: Optional configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if config is None:
        config = load_config()

    # Validate Neo4j
    if not config.neo4j_uri:
        raise ValueError("NEO4J_URI is required")
    if not config.neo4j_user:
        raise ValueError("NEO4J_USER is required")
    if not config.neo4j_password:
        raise ValueError("NEO4J_PASSWORD is required")

    # Validate LLM
    if config.llm_provider == LLMProvider.OPENAI:
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI")
    elif config.llm_provider == LLMProvider.ANTHROPIC:
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic")

    # Validate Embedding
    if config.embedding_provider == EmbeddingProvider.OPENAI:
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
