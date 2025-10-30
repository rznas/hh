"""Embedding service for medical text using OpenAI or BioBERT."""
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
from functools import lru_cache

from openai import OpenAI

from config import (
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    EMBEDDING_BATCH_SIZE,
    OPENAI_EMBEDDING_API_KEY,
    OPENAI_EMBEDDING_BASE_URL,
    SENTENCE_TRANSFORMERS_MODEL,
)

logger = logging.getLogger(__name__)


class MedicalEmbeddingService:
    """Service for generating embeddings of medical text.

    Supports multiple embedding providers:
    - OpenAI (text-embedding-3-small, text-embedding-3-large, ada-002)
    - Sentence Transformers (BioBERT)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        batch_size: int = EMBEDDING_BATCH_SIZE,
    ):
        """Initialize embedding service.

        Args:
            provider: Embedding provider ("openai" or "sentence-transformers")
            model_name: Name of the model
            api_key: API key (for OpenAI)
            base_url: Base URL (for OpenAI)
            batch_size: Batch size for encoding
        """
        self.provider = provider or EMBEDDING_PROVIDER
        self.model_name = model_name or EMBEDDING_MODEL
        self.batch_size = batch_size

        logger.info(f"Initializing embedding service")
        logger.info(f"  Provider: {self.provider}")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Batch size: {self.batch_size}")

        if self.provider == "openai":
            self._init_openai(api_key, base_url)
        elif self.provider == "sentence-transformers":
            self._init_sentence_transformers()
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    def _init_openai(self, api_key: Optional[str], base_url: Optional[str]) -> None:
        """Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key
            base_url: OpenAI API base URL
        """
        self.api_key = api_key or OPENAI_EMBEDDING_API_KEY
        self.base_url = base_url or OPENAI_EMBEDDING_BASE_URL

        if not self.api_key:
            raise ValueError("OpenAI API key is required for OpenAI embeddings")

        logger.info(f"  API Base URL: {self.base_url}")

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # Test connection
            test_response = self.client.embeddings.create(
                model=self.model_name,
                input="test"
            )
            actual_dim = len(test_response.data[0].embedding)
            logger.info(f"  Embedding dimension: {actual_dim}")
            logger.info("OpenAI embedding service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            raise

    def _init_sentence_transformers(self) -> None:
        """Initialize Sentence Transformers (BioBERT)."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            # Auto-detect device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"  Device: {self.device}")

            # Use configured model or default
            model_name = SENTENCE_TRANSFORMERS_MODEL
            logger.info(f"  Loading model: {model_name}")

            self.model = SentenceTransformer(model_name, device=self.device)

            # Verify dimension
            test_embedding = self.model.encode("test", show_progress_bar=False)
            actual_dim = len(test_embedding)
            logger.info(f"  Embedding dimension: {actual_dim}")
            logger.info("Sentence Transformers embedding service initialized successfully")

        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers torch"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Sentence Transformers: {e}")
            raise

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
        normalize: bool = True,
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate embeddings for text(s).

        Args:
            texts: Single text string or list of texts
            show_progress: Show progress bar (only for sentence-transformers)
            normalize: Normalize embeddings to unit length

        Returns:
            Embedding vector(s) as numpy array(s)
        """
        # Handle single string
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False

        try:
            if self.provider == "openai":
                embeddings = self._encode_openai(texts, normalize)
            else:
                embeddings = self._encode_sentence_transformers(texts, show_progress, normalize)

            # Return single embedding if single input
            if single_input:
                return embeddings[0]
            return embeddings

        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise

    def _encode_openai(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> List[np.ndarray]:
        """Encode texts using OpenAI embeddings.

        Args:
            texts: List of texts to encode
            normalize: Normalize embeddings

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )

                batch_embeddings = [
                    np.array(data.embedding, dtype=np.float32)
                    for data in response.data
                ]

                if normalize:
                    batch_embeddings = [
                        emb / np.linalg.norm(emb)
                        for emb in batch_embeddings
                    ]

                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"Error encoding batch {i//self.batch_size + 1}: {e}")
                raise

        return embeddings

    def _encode_sentence_transformers(
        self,
        texts: List[str],
        show_progress: bool,
        normalize: bool,
    ) -> List[np.ndarray]:
        """Encode texts using Sentence Transformers.

        Args:
            texts: List of texts to encode
            show_progress: Show progress bar
            normalize: Normalize embeddings

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )

        return embeddings

    def encode_symptoms(
        self,
        symptoms: List[str],
        show_progress: bool = True,
    ) -> Dict[str, np.ndarray]:
        """Encode a list of symptoms.

        Args:
            symptoms: List of symptom descriptions
            show_progress: Show progress bar

        Returns:
            Dictionary mapping symptom to embedding
        """
        logger.info(f"Encoding {len(symptoms)} symptoms")

        embeddings = self.encode(symptoms, show_progress=show_progress)

        return {
            symptom: embedding
            for symptom, embedding in zip(symptoms, embeddings)
        }

    def encode_conditions(
        self,
        conditions: List[Dict[str, Any]],
        show_progress: bool = True,
    ) -> Dict[str, np.ndarray]:
        """Encode medical conditions with their full context.

        Args:
            conditions: List of condition dictionaries with 'name' and optional context
            show_progress: Show progress bar

        Returns:
            Dictionary mapping condition name to embedding
        """
        logger.info(f"Encoding {len(conditions)} conditions")

        # Build full text for each condition
        texts = []
        names = []

        for condition in conditions:
            name = condition.get("name", "")
            symptoms = condition.get("symptoms", [])
            signs = condition.get("signs", [])

            # Construct context-rich text
            text = f"{name}. "
            if symptoms:
                text += f"Symptoms: {', '.join(symptoms)}. "
            if signs:
                text += f"Signs: {', '.join(signs)}."

            texts.append(text)
            names.append(name)

        # Generate embeddings
        embeddings = self.encode(texts, show_progress=show_progress)

        return {
            name: embedding
            for name, embedding in zip(names, embeddings)
        }

    @lru_cache(maxsize=1000)
    def encode_cached(self, text: str) -> np.ndarray:
        """Encode text with caching for frequently used terms.

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        return self.encode(text, show_progress=False)

    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Ensure embeddings are normalized
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def find_most_similar(
        self,
        query: str,
        candidates: Dict[str, np.ndarray],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[tuple[str, float]]:
        """Find most similar candidates to a query.

        Args:
            query: Query text
            candidates: Dictionary mapping candidate texts to embeddings
            top_k: Number of top results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (candidate_text, similarity_score) tuples, sorted by score
        """
        # Encode query
        query_embedding = self.encode(query, show_progress=False)

        # Compute similarities
        similarities = []
        for candidate_text, candidate_embedding in candidates.items():
            similarity = self.compute_similarity(query_embedding, candidate_embedding)

            if similarity >= threshold:
                similarities.append((candidate_text, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def batch_similarity_search(
        self,
        query_embeddings: List[np.ndarray],
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5,
    ) -> List[List[int]]:
        """Perform batch similarity search.

        Args:
            query_embeddings: List of query embeddings
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results per query

        Returns:
            List of lists containing indices of top k candidates for each query
        """
        query_matrix = np.array(query_embeddings)
        candidate_matrix = np.array(candidate_embeddings)

        # Compute similarity matrix (queries x candidates)
        similarities = np.dot(query_matrix, candidate_matrix.T)

        # Get top k indices for each query
        top_k_indices = []
        for row in similarities:
            # Get indices of top k values
            indices = np.argsort(row)[-top_k:][::-1]
            top_k_indices.append(indices.tolist())

        return top_k_indices

    def semantic_search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 10,
        threshold: float = 0.5,
    ) -> List[tuple[str, float]]:
        """Perform semantic search over a corpus.

        Args:
            query: Search query
            corpus: List of documents to search
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (document, score) tuples
        """
        # Encode query and corpus
        query_embedding = self.encode(query, show_progress=False)
        corpus_embeddings = self.encode(corpus, show_progress=True)

        # Compute similarities
        similarities = []
        for doc, doc_embedding in zip(corpus, corpus_embeddings):
            similarity = self.compute_similarity(query_embedding, doc_embedding)

            if similarity >= threshold:
                similarities.append((doc, similarity))

        # Sort and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension.

        Returns:
            Embedding dimension
        """
        test_embedding = self.encode("test", show_progress=False)
        return len(test_embedding)


class SymptomMatcher:
    """Helper class for matching user input to standardized symptoms."""

    def __init__(self, embedding_service: Optional[MedicalEmbeddingService] = None):
        """Initialize symptom matcher.

        Args:
            embedding_service: Optional pre-configured embedding service
        """
        self.embedding_service = embedding_service or MedicalEmbeddingService()
        self.symptom_embeddings: Dict[str, np.ndarray] = {}

    def add_symptoms(self, symptoms: List[str]) -> None:
        """Add symptoms to the matcher's knowledge base.

        Args:
            symptoms: List of standardized symptom descriptions
        """
        logger.info(f"Adding {len(symptoms)} symptoms to matcher")
        embeddings = self.embedding_service.encode_symptoms(symptoms)
        self.symptom_embeddings.update(embeddings)

    def match(
        self,
        user_input: str,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> List[tuple[str, float]]:
        """Match user input to standardized symptoms.

        Args:
            user_input: User's description of symptoms
            top_k: Number of matches to return
            threshold: Minimum similarity threshold

        Returns:
            List of (symptom, similarity_score) tuples
        """
        if not self.symptom_embeddings:
            logger.warning("No symptoms loaded in matcher")
            return []

        matches = self.embedding_service.find_most_similar(
            query=user_input,
            candidates=self.symptom_embeddings,
            top_k=top_k,
            threshold=threshold,
        )

        logger.debug(f"Matched '{user_input}' to {len(matches)} symptoms")
        return matches

    def get_standardized_symptoms(self, user_inputs: List[str]) -> List[str]:
        """Get standardized symptoms from user inputs.

        Args:
            user_inputs: List of user symptom descriptions

        Returns:
            List of standardized symptom names
        """
        standardized = []

        for user_input in user_inputs:
            matches = self.match(user_input, top_k=1, threshold=0.7)
            if matches:
                standardized.append(matches[0][0])  # Top match

        return standardized


# Example usage
if __name__ == "__main__":
    # Initialize service (will use OpenAI by default if configured)
    service = MedicalEmbeddingService()

    # Test basic encoding
    text = "sudden vision loss in one eye"
    embedding = service.encode(text)
    print(f"Provider: {service.provider}")
    print(f"Model: {service.model_name}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding dimension: {service.get_embedding_dimension()}")

    # Test symptom matching
    matcher = SymptomMatcher(service)

    # Add standardized symptoms
    standard_symptoms = [
        "sudden vision loss",
        "eye pain",
        "red eye",
        "blurry vision",
        "floaters",
        "photophobia",
        "tearing",
    ]
    matcher.add_symptoms(standard_symptoms)

    # Match user inputs
    user_inputs = [
        "I can't see out of my left eye",
        "My eye hurts",
        "I see spots floating",
    ]

    for user_input in user_inputs:
        matches = matcher.match(user_input, top_k=3)
        print(f"\nUser: '{user_input}'")
        print("Matches:")
        for symptom, score in matches:
            print(f"  - {symptom}: {score:.3f}")
