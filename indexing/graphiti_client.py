"""Graphiti client wrapper for medical knowledge graph operations."""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from graphiti_core import Graphiti
from openai import OpenAI

from config import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    CUSTOM_OPENAI_BASE_URL,
    CUSTOM_OPENAI_API_KEY,
    CUSTOM_OPENAI_MODEL,
    NodeType,
    EdgeType,
    validate_config,
)

logger = logging.getLogger(__name__)


class GraphitiClient:
    """Wrapper for Graphiti with custom OpenAI client configuration.

    Provides high-level interface for medical knowledge graph operations
    including node creation, relationship management, and querying.
    """

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
    ):
        """Initialize Graphiti client with custom configurations.

        Args:
            neo4j_uri: Neo4j database URI (defaults to config)
            neo4j_user: Neo4j username (defaults to config)
            neo4j_password: Neo4j password (defaults to config)
            openai_base_url: Custom OpenAI API base URL (defaults to config)
            openai_api_key: Custom OpenAI API key (defaults to config)
            openai_model: Custom OpenAI model name (defaults to config)
        """
        # Validate configuration
        validate_config()

        # Use provided values or fall back to config
        self.neo4j_uri = neo4j_uri or NEO4J_URI
        self.neo4j_user = neo4j_user or NEO4J_USER
        self.neo4j_password = neo4j_password or NEO4J_PASSWORD
        self.openai_base_url = openai_base_url or CUSTOM_OPENAI_BASE_URL
        self.openai_api_key = openai_api_key or CUSTOM_OPENAI_API_KEY
        self.openai_model = openai_model or CUSTOM_OPENAI_MODEL

        logger.info(f"Initializing Graphiti client")
        logger.info(f"  Neo4j URI: {self.neo4j_uri}")
        logger.info(f"  OpenAI Base URL: {self.openai_base_url}")
        logger.info(f"  OpenAI Model: {self.openai_model}")

        # Initialize custom OpenAI client
        self.openai_client = OpenAI(
            base_url=self.openai_base_url,
            api_key=self.openai_api_key,
        )

        # Initialize Graphiti with Neo4j and custom OpenAI client
        try:
            self.graphiti = Graphiti(
                self.neo4j_uri,
                self.neo4j_user,
                self.neo4j_password,
            )

            # Set custom OpenAI client and model in Graphiti
            # Note: This depends on Graphiti's API - adjust if needed
            if hasattr(self.graphiti, 'llm_client'):
                self.graphiti.llm_client = self.openai_client
            if hasattr(self.graphiti, 'llm_model'):
                self.graphiti.llm_model = self.openai_model

            logger.info("Graphiti client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise

        # Track statistics
        self.stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "queries_executed": 0,
            "errors": 0,
        }

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: Optional[datetime] = None,
    ) -> Any:
        """Add an episode to the knowledge graph.

        Graphiti uses episodes as the primary way to add information.
        An episode represents a piece of knowledge with context.

        Args:
            name: Episode name/identifier
            episode_body: The actual content to be processed
            source_description: Description of the source
            reference_time: Timestamp for the episode

        Returns:
            Episode processing result
        """
        try:
            result = await self.graphiti.add_episode(
                name=name,
                episode_body=episode_body,
                source_description=source_description,
                reference_time=reference_time or datetime.now(),
            )
            logger.debug(f"Added episode: {name}")
            return result
        except Exception as e:
            logger.error(f"Error adding episode {name}: {e}")
            self.stats["errors"] += 1
            raise

    async def add_medical_condition(
        self,
        condition_name: str,
        chapter: str,
        section_id: str,
        symptoms: List[str],
        signs: List[str],
        treatment: List[str],
        urgency_level: str,
        red_flags: List[str],
        etiology: Optional[List[str]] = None,
        differential: Optional[List[str]] = None,
    ) -> Any:
        """Add a complete medical condition to the knowledge graph.

        This is a high-level method that constructs an episode from
        structured medical data.

        Args:
            condition_name: Name of the medical condition
            chapter: Chapter it belongs to
            section_id: Wills Eye Manual section ID
            symptoms: List of symptoms
            signs: List of clinical signs
            treatment: List of treatments
            urgency_level: EMERGENT, URGENT, or NON_URGENT
            red_flags: List of red flag keywords
            etiology: Optional list of causes
            differential: Optional list of differential diagnoses

        Returns:
            Episode processing result
        """
        # Construct episode body from structured data
        episode_body = self._construct_medical_episode(
            condition_name=condition_name,
            chapter=chapter,
            section_id=section_id,
            symptoms=symptoms,
            signs=signs,
            treatment=treatment,
            urgency_level=urgency_level,
            red_flags=red_flags,
            etiology=etiology,
            differential=differential,
        )

        # Add as episode
        result = await self.add_episode(
            name=f"{section_id}: {condition_name}",
            episode_body=episode_body,
            source_description=f"Wills Eye Manual - {chapter} - {section_id}",
        )

        self.stats["nodes_created"] += 1
        return result

    def _construct_medical_episode(
        self,
        condition_name: str,
        chapter: str,
        section_id: str,
        symptoms: List[str],
        signs: List[str],
        treatment: List[str],
        urgency_level: str,
        red_flags: List[str],
        etiology: Optional[List[str]] = None,
        differential: Optional[List[str]] = None,
    ) -> str:
        """Construct natural language episode from structured medical data.

        Graphiti works best with natural language text, so we convert
        structured medical data into a narrative format.

        Args:
            condition_name: Condition name
            chapter: Chapter
            section_id: Section ID
            symptoms: Symptoms
            signs: Signs
            treatment: Treatments
            urgency_level: Urgency level
            red_flags: Red flags
            etiology: Causes
            differential: Differential diagnoses

        Returns:
            Natural language episode body
        """
        parts = [
            f"Medical Condition: {condition_name} (Section {section_id})",
            f"Chapter: {chapter}",
            f"Urgency Level: {urgency_level}",
        ]

        if red_flags:
            parts.append(f"Red Flags: {', '.join(red_flags)}")

        if symptoms:
            parts.append(f"Symptoms: {'; '.join(symptoms)}")

        if signs:
            parts.append(f"Clinical Signs: {'; '.join(signs)}")

        if etiology:
            parts.append(f"Etiology: {'; '.join(etiology)}")

        if treatment:
            parts.append(f"Treatment: {'; '.join(treatment[:3])}")  # Limit for brevity

        if differential:
            parts.append(f"Differential Diagnosis: {', '.join(differential)}")

        return ". ".join(parts) + "."

    async def search(
        self,
        query: str,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search the knowledge graph using natural language.

        Args:
            query: Natural language search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        try:
            results = await self.graphiti.search(query, num_results=num_results)
            self.stats["queries_executed"] += 1
            logger.debug(f"Search query executed: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            self.stats["errors"] += 1
            raise

    async def retrieve_episodes(
        self,
        name: Optional[str] = None,
        reference_time_start: Optional[datetime] = None,
        reference_time_end: Optional[datetime] = None,
    ) -> List[Any]:
        """Retrieve episodes from the knowledge graph.

        Args:
            name: Episode name to filter by
            reference_time_start: Start time filter
            reference_time_end: End time filter

        Returns:
            List of episodes
        """
        try:
            episodes = await self.graphiti.retrieve_episodes(
                name=name,
                reference_time_start=reference_time_start,
                reference_time_end=reference_time_end,
            )
            logger.debug(f"Retrieved {len(episodes)} episodes")
            return episodes
        except Exception as e:
            logger.error(f"Error retrieving episodes: {e}")
            self.stats["errors"] += 1
            raise

    async def get_graph_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge graph.

        Returns:
            Dictionary with graph statistics
        """
        # This would require custom Cypher queries through Graphiti's driver
        # Implementation depends on Graphiti's API
        return {
            **self.stats,
            "message": "Full graph stats require custom Cypher queries"
        }

    def close(self) -> None:
        """Close Graphiti connection."""
        try:
            if hasattr(self.graphiti, 'close'):
                self.graphiti.close()
            logger.info("Graphiti client closed")
        except Exception as e:
            logger.error(f"Error closing Graphiti client: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class GraphQueryBuilder:
    """Helper class for building medical knowledge graph queries."""

    @staticmethod
    def get_diseases_by_symptom(symptom: str, urgency_filter: Optional[str] = None) -> str:
        """Build query to find diseases by symptom.

        Args:
            symptom: Symptom to search for
            urgency_filter: Optional urgency level filter

        Returns:
            Natural language query string
        """
        query = f"What diseases present with {symptom}?"
        if urgency_filter:
            query += f" Focus on {urgency_filter.lower()} conditions."
        return query

    @staticmethod
    def get_treatment_for_disease(disease: str) -> str:
        """Build query to find treatments for a disease.

        Args:
            disease: Disease name

        Returns:
            Natural language query string
        """
        return f"What is the treatment for {disease}?"

    @staticmethod
    def get_differential_diagnosis(symptoms: List[str]) -> str:
        """Build query for differential diagnosis.

        Args:
            symptoms: List of symptoms

        Returns:
            Natural language query string
        """
        symptom_str = ", ".join(symptoms)
        return f"What are the differential diagnoses for a patient with {symptom_str}?"

    @staticmethod
    def check_red_flags(symptoms: List[str]) -> str:
        """Build query to check for emergent conditions.

        Args:
            symptoms: List of symptoms

        Returns:
            Natural language query string
        """
        symptom_str = ", ".join(symptoms)
        return (
            f"Are any of these symptoms red flags requiring emergency care: {symptom_str}? "
            "List any emergent conditions."
        )


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize client
        client = GraphitiClient()

        try:
            # Example: Add a medical condition
            await client.add_medical_condition(
                condition_name="Chemical Burn",
                chapter="Trauma",
                section_id="3.1",
                symptoms=["eye pain", "vision loss", "tearing"],
                signs=["corneal opacity", "conjunctival injection"],
                treatment=["copious irrigation", "topical antibiotics"],
                urgency_level="EMERGENT",
                red_flags=["chemical burn", "chemical splash"],
                etiology=["alkali exposure", "acid exposure"],
            )

            # Example: Search for related conditions
            results = await client.search("What causes sudden vision loss?")
            print(f"Search results: {len(results)}")

            # Get stats
            stats = await client.get_graph_stats()
            print(f"Graph stats: {stats}")

        finally:
            client.close()

    # Run async main
    asyncio.run(main())
