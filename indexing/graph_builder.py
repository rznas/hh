"""Graph builder service for populating medical knowledge graph using Microsoft GraphRAG."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from parsers import WillsEyeParser, ParsedCondition, MedicalEntity, MedicalRelationship
from config import NodeType, EdgeType, UrgencyLevel

logger = logging.getLogger(__name__)


class MedicalGraphBuilder:
    """Service for building medical knowledge graph from parsed Wills Eye data using GraphRAG."""

    def __init__(self):
        """Initialize graph builder with GraphRAG backend."""
        # TODO: Initialize GraphRAG client when implementation is complete
        # Currently structured to receive GraphRAG client from indexing pipeline
        self.batch_buffer: List[ParsedCondition] = []
        self.stats = {
            "conditions_processed": 0,
            "episodes_created": 0,
            "errors": 0,
        }

    async def build_from_chapter(
        self,
        chapter_name: str,
        parser: WillsEyeParser,
        batch_size: int = 10,
    ) -> Dict[str, int]:
        """Build knowledge graph from a chapter.

        Args:
            chapter_name: Name of the chapter to process
            parser: WillsEyeParser instance
            batch_size: Number of conditions to batch before processing

        Returns:
            Statistics dictionary
        """
        logger.info(f"Building knowledge graph for chapter: {chapter_name}")

        try:
            # Parse chapter
            conditions = parser.parse_chapter(chapter_name)
            logger.info(f"Parsed {len(conditions)} conditions from {chapter_name}")

            # Process conditions in batches
            for i in range(0, len(conditions), batch_size):
                batch = conditions[i:i + batch_size]
                await self._process_batch(batch)

                logger.info(
                    f"Processed batch {i//batch_size + 1}/{(len(conditions)-1)//batch_size + 1}"
                )

            logger.info(f"Completed processing chapter: {chapter_name}")
            return self.stats

        except Exception as e:
            logger.error(f"Error building graph for chapter {chapter_name}: {e}")
            self.stats["errors"] += 1
            raise

    async def build_from_all_chapters(
        self,
        parser: WillsEyeParser,
        batch_size: int = 10,
    ) -> Dict[str, int]:
        """Build knowledge graph from all chapters.

        Args:
            parser: WillsEyeParser instance
            batch_size: Batch size for processing

        Returns:
            Statistics dictionary
        """
        chapters = parser.get_chapters()
        logger.info(f"Building knowledge graph for {len(chapters)} chapters")

        for idx, chapter in enumerate(chapters, 1):
            logger.info(f"Processing chapter {idx}/{len(chapters)}: {chapter}")
            await self.build_from_chapter(chapter, parser, batch_size)

        logger.info("Completed building knowledge graph for all chapters")
        return self.stats

    async def _process_batch(self, conditions: List[ParsedCondition]) -> None:
        """Process a batch of conditions.

        Args:
            conditions: List of parsed conditions to process
        """
        tasks = []
        for condition in conditions:
            task = self._add_condition_to_graph(condition)
            tasks.append(task)

        # Process batch concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _add_condition_to_graph(self, condition: ParsedCondition) -> None:
        """Add a single medical condition to the knowledge graph.

        Args:
            condition: Parsed medical condition

        Note:
            This method extracts and structures medical data from parsed conditions.
            The actual GraphRAG indexing is handled by the indexing pipeline.
        """
        try:
            # Extract data from parsed condition
            symptoms = self._extract_entities_by_type(
                condition.entities, NodeType.SYMPTOM
            )
            signs = self._extract_entities_by_type(
                condition.entities, NodeType.SIGN
            )
            treatments = self._extract_entities_by_type(
                condition.entities, NodeType.TREATMENT
            )
            treatments.extend(
                self._extract_entities_by_type(condition.entities, NodeType.MEDICATION)
            )
            etiologies = self._extract_entities_by_type(
                condition.entities, NodeType.ETIOLOGY
            )
            differentials = self._extract_entities_by_type(
                condition.entities, NodeType.DIFFERENTIAL
            )

            # TODO: Send structured data to GraphRAG indexing pipeline
            # For now, just track processing statistics
            # GraphRAG indexing is handled by graphrag_indexer.py

            self.stats["conditions_processed"] += 1
            self.stats["episodes_created"] += 1

            logger.debug(f"Processed condition for GraphRAG: {condition.condition_name}")

        except Exception as e:
            logger.error(
                f"Error processing condition {condition.condition_name}: {e}"
            )
            self.stats["errors"] += 1

    def _extract_entities_by_type(
        self,
        entities: List[MedicalEntity],
        node_type: NodeType,
    ) -> List[str]:
        """Extract entity names of a specific type.

        Args:
            entities: List of medical entities
            node_type: Type of node to extract

        Returns:
            List of entity names
        """
        return [
            entity.name
            for entity in entities
            if entity.node_type == node_type
        ]

    async def search_conditions_by_symptom(
        self,
        symptom: str,
        urgency_filter: Optional[str] = None,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for conditions by symptom using GraphRAG.

        Args:
            symptom: Symptom to search for
            urgency_filter: Optional urgency level filter
            num_results: Number of results to return

        Returns:
            List of matching conditions
        """
        # TODO: Implement GraphRAG search when backend is ready
        # This would use GraphRAG's local/global search capabilities
        logger.info(f"GraphRAG search for symptom: {symptom}")
        return []

    async def get_treatment_recommendations(
        self,
        disease: str,
        num_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get treatment recommendations for a disease using GraphRAG.

        Args:
            disease: Disease name
            num_results: Number of results to return

        Returns:
            List of treatment recommendations
        """
        # TODO: Implement GraphRAG search when backend is ready
        logger.info(f"GraphRAG search for treatments: {disease}")
        return []

    async def get_differential_diagnosis(
        self,
        symptoms: List[str],
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get differential diagnosis based on symptoms using GraphRAG.

        Args:
            symptoms: List of symptoms
            num_results: Number of results to return

        Returns:
            List of potential diagnoses
        """
        # TODO: Implement GraphRAG search when backend is ready
        logger.info(f"GraphRAG search for differential diagnosis: {symptoms}")
        return []

    async def check_for_red_flags(
        self,
        symptoms: List[str],
        num_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Check if symptoms indicate emergent conditions using GraphRAG.

        Args:
            symptoms: List of symptoms to check
            num_results: Number of results to return

        Returns:
            List of potential emergent conditions
        """
        # TODO: Implement GraphRAG red flag detection when backend is ready
        logger.info(f"GraphRAG red flag check: {symptoms}")
        return []

    def get_stats(self) -> Dict[str, int]:
        """Get builder statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats

    def close(self) -> None:
        """Close graph builder."""
        logger.info("Graph builder closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class GraphIndexer:
    """High-level indexing service orchestrator for GraphRAG."""

    def __init__(self, json_path: str):
        """Initialize indexer.

        Args:
            json_path: Path to wills_eye_structured.json
        """
        self.parser = WillsEyeParser(json_path)
        self.builder = MedicalGraphBuilder()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def index_chapter(
        self,
        chapter_name: str,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """Index a single chapter.

        Args:
            chapter_name: Name of chapter to index
            batch_size: Batch size for processing

        Returns:
            Indexing results with statistics
        """
        self.start_time = datetime.now()
        logger.info(f"Starting indexing of chapter: {chapter_name}")

        try:
            stats = await self.builder.build_from_chapter(
                chapter_name, self.parser, batch_size
            )

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            return {
                "chapter": chapter_name,
                "stats": stats,
                "duration_seconds": duration,
                "success": True,
            }

        except Exception as e:
            self.end_time = datetime.now()
            logger.error(f"Error indexing chapter {chapter_name}: {e}")
            return {
                "chapter": chapter_name,
                "error": str(e),
                "success": False,
            }

    async def index_all_chapters(
        self,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """Index all chapters.

        Args:
            batch_size: Batch size for processing

        Returns:
            Indexing results with statistics
        """
        self.start_time = datetime.now()
        chapters = self.parser.get_chapters()
        logger.info(f"Starting indexing of {len(chapters)} chapters")

        try:
            stats = await self.builder.build_from_all_chapters(
                self.parser, batch_size
            )

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()

            return {
                "chapters_processed": len(chapters),
                "stats": stats,
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "success": True,
            }

        except Exception as e:
            self.end_time = datetime.now()
            logger.error(f"Error indexing all chapters: {e}")
            return {
                "error": str(e),
                "success": False,
            }

    async def validate_indexing(self) -> Dict[str, Any]:
        """Validate that critical conditions are indexed correctly.

        Returns:
            Validation results
        """
        logger.info("Validating indexing...")

        validations = []

        # Test 1: Check for emergent red flags
        test_queries = [
            ("sudden vision loss", "EMERGENT"),
            ("chemical burn", "EMERGENT"),
            ("mild allergic conjunctivitis", "NON_URGENT"),
        ]

        for query, expected_urgency in test_queries:
            try:
                results = await self.builder.search_conditions_by_symptom(
                    query, urgency_filter=None, num_results=5
                )

                validations.append({
                    "query": query,
                    "expected_urgency": expected_urgency,
                    "results_found": len(results),
                    "passed": len(results) > 0,
                })

            except Exception as e:
                validations.append({
                    "query": query,
                    "error": str(e),
                    "passed": False,
                })

        return {
            "validations": validations,
            "all_passed": all(v.get("passed", False) for v in validations),
        }

    def close(self) -> None:
        """Close indexer."""
        self.builder.close()


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        # Initialize indexer
        indexer = GraphIndexer("../data/wills_eye_structured.json")

        try:
            # Index Trauma chapter (pilot)
            result = await indexer.index_chapter("Trauma", batch_size=5)
            print(f"Indexing result: {result}")

            # Validate
            validation = await indexer.validate_indexing()
            print(f"Validation: {validation}")

            # Test search
            results = await indexer.builder.search_conditions_by_symptom(
                "eye pain", urgency_filter="EMERGENT"
            )
            print(f"Search results for 'eye pain': {len(results)} found")

        finally:
            indexer.close()

    # Run async main
    asyncio.run(main())
