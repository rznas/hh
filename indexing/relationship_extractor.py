"""Relationship extraction between medical entities using LLM."""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import json

from anthropic import Anthropic
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from graphrag_config import GraphRAGConfig, LLMProvider
from config import EdgeType
from entity_extractor import MedicalEntity

logger = logging.getLogger(__name__)


class MedicalRelationship:
    """Represents a relationship between two medical entities."""

    def __init__(
        self,
        source_entity: str,
        target_entity: str,
        relationship_type: EdgeType,
        description: Optional[str] = None,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize medical relationship.

        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            relationship_type: Type of relationship
            description: Optional description
            weight: Relationship weight/strength (0-1)
            metadata: Additional metadata
        """
        self.source_entity = source_entity.strip()
        self.target_entity = target_entity.strip()
        self.relationship_type = relationship_type
        self.description = description
        self.weight = weight
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "relationship_type": self.relationship_type.value if isinstance(self.relationship_type, EdgeType) else self.relationship_type,
            "description": self.description,
            "weight": self.weight,
            "metadata": self.metadata,
        }


class RelationshipExtractor:
    """Extracts relationships between medical entities using LLM."""

    EXTRACTION_PROMPT = """You are a medical knowledge expert specializing in ophthalmology. Extract relationships between the medical entities provided.

Entities:
{entities}

Source Text:
{text}

Extract relationships between these entities using the following types:
- PRESENTS_WITH: Disease → Symptom (disease presents with symptom)
- SHOWS_SIGN: Disease → Sign (disease shows clinical sign)
- CAUSED_BY: Disease → Etiology (disease caused by etiology)
- TREATED_WITH: Disease → Treatment/Medication (disease treated with treatment)
- AFFECTS: Disease → Anatomy (disease affects anatomical structure)
- INDICATES: Symptom → Disease (symptom indicates disease)
- DIFFERENTIATES: Disease → Disease (differential diagnosis)
- ASSOCIATED_WITH: Generic association between any entities

For each relationship, provide:
1. source: Source entity name (exact match from entity list)
2. target: Target entity name (exact match from entity list)
3. relationship_type: One of the types above
4. description: Brief explanation (1 sentence)
5. weight: Strength of relationship (0.0 to 1.0, where 1.0 is strongest)

Respond with a JSON array of relationships. Example format:
[
  {{
    "source": "acute angle-closure glaucoma",
    "target": "eye pain",
    "relationship_type": "PRESENTS_WITH",
    "description": "This condition commonly presents with severe eye pain",
    "weight": 0.9
  }},
  {{
    "source": "acute angle-closure glaucoma",
    "target": "corneal edema",
    "relationship_type": "SHOWS_SIGN",
    "description": "Corneal edema is a clinical sign of this condition",
    "weight": 0.95
  }}
]

IMPORTANT:
- Only create relationships between entities in the provided list
- Use exact entity names from the list
- Be selective - only extract clear, medically meaningful relationships
- Weight stronger/more specific relationships higher
- Focus on direct relationships, not transitive ones

Return ONLY the JSON array, no additional text."""

    def __init__(self, config: GraphRAGConfig):
        """Initialize relationship extractor.

        Args:
            config: GraphRAG configuration
        """
        self.config = config

        # Initialize LLM client
        if config.llm_provider == LLMProvider.ANTHROPIC:
            self.client = Anthropic(api_key=config.anthropic_api_key)
            self.model = config.anthropic_model
        else:
            self.client = OpenAI(api_key=config.openai_api_key)
            self.model = config.openai_model

        self.provider = config.llm_provider

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def extract_relationships(
        self,
        entities: List[MedicalEntity],
        source_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[MedicalRelationship]:
        """Extract relationships between entities.

        Args:
            entities: List of medical entities
            source_text: Original source text
            context: Optional context

        Returns:
            List of medical relationships
        """
        if len(entities) < 2:
            logger.debug("Not enough entities for relationship extraction")
            return []

        try:
            # Format entity list
            entity_list = "\n".join([
                f"- {e.name} ({e.entity_type.value})"
                for e in entities
            ])

            # Format prompt
            prompt = self.EXTRACTION_PROMPT.format(
                entities=entity_list,
                text=source_text
            )

            # Call LLM
            if self.provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(prompt)
            else:
                response = await self._call_openai(prompt)

            # Parse response
            relationships = self._parse_relationships(response, context)

            logger.debug(f"Extracted {len(relationships)} relationships")
            return relationships

        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            raise

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API.

        Args:
            prompt: Prompt text

        Returns:
            Response text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config.relationship_extraction_max_tokens,
            temperature=self.config.relationship_extraction_temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API.

        Args:
            prompt: Prompt text

        Returns:
            Response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical knowledge expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config.relationship_extraction_max_tokens,
            temperature=self.config.relationship_extraction_temperature,
        )
        return response.choices[0].message.content

    def _parse_relationships(
        self,
        response: str,
        context: Optional[Dict[str, Any]],
    ) -> List[MedicalRelationship]:
        """Parse LLM response to extract relationships.

        Args:
            response: LLM response text
            context: Optional context

        Returns:
            List of medical relationships
        """
        try:
            # Extract JSON from response
            response = response.strip()

            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            # Parse JSON
            relationships_data = json.loads(response)

            # Convert to MedicalRelationship objects
            relationships = []
            for rel_dict in relationships_data:
                try:
                    # Map relationship_type string to EdgeType enum
                    rel_type_str = rel_dict.get("relationship_type", "").upper()
                    rel_type = EdgeType[rel_type_str] if rel_type_str in EdgeType.__members__ else None

                    if not rel_type:
                        logger.warning(f"Unknown relationship type: {rel_type_str}")
                        continue

                    relationship = MedicalRelationship(
                        source_entity=rel_dict["source"],
                        target_entity=rel_dict["target"],
                        relationship_type=rel_type,
                        description=rel_dict.get("description"),
                        weight=float(rel_dict.get("weight", 1.0)),
                        metadata=context or {},
                    )
                    relationships.append(relationship)

                except Exception as e:
                    logger.warning(f"Error parsing relationship: {e}")
                    continue

            return relationships

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing relationships: {e}")
            return []

    async def extract_from_condition(
        self,
        condition_entity: MedicalEntity,
        related_entities: List[MedicalEntity],
        source_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[MedicalRelationship]:
        """Extract relationships for a specific condition.

        This method focuses on extracting relationships between a condition
        and its related entities (symptoms, signs, treatments, etc.)

        Args:
            condition_entity: The main condition entity
            related_entities: Related entities
            source_text: Source text
            context: Optional context

        Returns:
            List of relationships
        """
        # Combine condition with related entities
        all_entities = [condition_entity] + related_entities

        return await self.extract_relationships(all_entities, source_text, context)

    async def batch_extract(
        self,
        entity_groups: List[List[MedicalEntity]],
        source_texts: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[List[MedicalRelationship]]:
        """Extract relationships from multiple entity groups in batch.

        Args:
            entity_groups: List of entity groups
            source_texts: List of source texts
            contexts: Optional list of contexts

        Returns:
            List of relationship lists (one per entity group)
        """
        if contexts is None:
            contexts = [None] * len(entity_groups)

        # Process concurrently with rate limiting
        tasks = [
            self.extract_relationships(entities, text, ctx)
            for entities, text, ctx in zip(entity_groups, source_texts, contexts)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle errors
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch extraction error: {result}")
                final_results.append([])
            else:
                final_results.append(result)

        return final_results


# Example usage
if __name__ == "__main__":
    from graphrag_config import load_config
    from config import NodeType

    async def main():
        config = load_config()
        extractor = RelationshipExtractor(config)

        # Test entities
        entities = [
            MedicalEntity("acute angle-closure glaucoma", NodeType.DISEASE),
            MedicalEntity("eye pain", NodeType.SYMPTOM),
            MedicalEntity("corneal edema", NodeType.SIGN),
            MedicalEntity("topical beta-blocker", NodeType.MEDICATION),
        ]

        text = """
        Acute angle-closure glaucoma presents with severe eye pain and shows
        corneal edema on examination. It is treated with topical beta-blockers.
        """

        relationships = await extractor.extract_relationships(entities, text)

        print(f"\nExtracted {len(relationships)} relationships:")
        for rel in relationships:
            print(f"  - {rel.source_entity} --[{rel.relationship_type.value}]--> {rel.target_entity}")
            print(f"    Description: {rel.description}")
            print(f"    Weight: {rel.weight}")

    asyncio.run(main())
