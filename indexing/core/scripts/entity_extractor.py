"""Entity extraction from medical text using LLM."""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json

from anthropic import Anthropic
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from graphrag_config import GraphRAGConfig, LLMProvider
from config import NodeType

logger = logging.getLogger(__name__)


class MedicalEntity:
    """Represents a medical entity extracted from text."""

    def __init__(
        self,
        name: str,
        entity_type: NodeType,
        description: Optional[str] = None,
        source_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize medical entity.

        Args:
            name: Entity name
            entity_type: Type of entity
            description: Optional description
            source_text: Source text where entity was found
            metadata: Additional metadata
        """
        self.name = name.strip()
        self.entity_type = entity_type
        self.description = description
        self.source_text = source_text
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "entity_type": self.entity_type.value if isinstance(self.entity_type, NodeType) else self.entity_type,
            "description": self.description,
            "source_text": self.source_text,
            "metadata": self.metadata,
        }


class EntityExtractor:
    """Extracts medical entities from text using LLM."""

    EXTRACTION_PROMPT = """You are a medical knowledge extraction expert specializing in ophthalmology. Extract structured entities from the medical text below.

Extract the following types of entities:
- DISEASE: Medical conditions and diagnoses
- SYMPTOM: Patient-reported symptoms
- SIGN: Clinical findings and signs
- TREATMENT: Treatments and interventions
- MEDICATION: Specific medications
- ANATOMY: Eye structures and anatomical locations
- ETIOLOGY: Causes and risk factors
- PROCEDURE: Medical procedures
- LAB_TEST: Laboratory tests
- IMAGING: Imaging studies

For each entity, provide:
1. name: The entity name (normalized, lowercase)
2. entity_type: One of the types listed above
3. description: Brief description (1 sentence)

Text to analyze:
{text}

Respond with a JSON array of entities. Example format:
[
  {{"name": "acute angle-closure glaucoma", "entity_type": "DISEASE", "description": "Sudden increase in intraocular pressure due to angle closure"}},
  {{"name": "eye pain", "entity_type": "SYMPTOM", "description": "Severe ocular pain"}},
  {{"name": "corneal edema", "entity_type": "SIGN", "description": "Swelling of the cornea"}},
  {{"name": "topical beta-blocker", "entity_type": "MEDICATION", "description": "Medication to lower intraocular pressure"}}
]

IMPORTANT:
- Extract ALL relevant medical entities
- Use standardized medical terminology
- Normalize entity names (lowercase, consistent formatting)
- Be comprehensive but precise
- Focus on entities relevant to ophthalmology

Return ONLY the JSON array, no additional text."""

    def __init__(self, config: GraphRAGConfig):
        """Initialize entity extractor.

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
    async def extract_entities(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[MedicalEntity]:
        """Extract entities from text.

        Args:
            text: Medical text to extract entities from
            context: Optional context (chapter, section, etc.)

        Returns:
            List of extracted medical entities
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for entity extraction")
            return []

        try:
            # Format prompt
            prompt = self.EXTRACTION_PROMPT.format(text=text)

            # Call LLM
            if self.provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(prompt)
            else:
                response = await self._call_openai(prompt)

            # Parse response
            entities = self._parse_entities(response, text, context)

            logger.debug(f"Extracted {len(entities)} entities from text")
            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
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
            max_tokens=self.config.entity_extraction_max_tokens,
            temperature=self.config.entity_extraction_temperature,
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
                {"role": "system", "content": "You are a medical knowledge extraction expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config.entity_extraction_max_tokens,
            temperature=self.config.entity_extraction_temperature,
        )
        return response.choices[0].message.content

    def _parse_entities(
        self,
        response: str,
        source_text: str,
        context: Optional[Dict[str, Any]],
    ) -> List[MedicalEntity]:
        """Parse LLM response to extract entities.

        Args:
            response: LLM response text
            source_text: Original source text
            context: Optional context

        Returns:
            List of medical entities
        """
        try:
            # Extract JSON from response
            response = response.strip()

            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            # Parse JSON
            entities_data = json.loads(response)

            # Convert to MedicalEntity objects
            entities = []
            for entity_dict in entities_data:
                try:
                    # Map entity_type string to NodeType enum
                    entity_type_str = entity_dict.get("entity_type", "").upper()
                    entity_type = NodeType[entity_type_str] if entity_type_str in NodeType.__members__ else None

                    if not entity_type:
                        logger.warning(f"Unknown entity type: {entity_type_str}")
                        continue

                    entity = MedicalEntity(
                        name=entity_dict["name"],
                        entity_type=entity_type,
                        description=entity_dict.get("description"),
                        source_text=source_text[:200],  # Store snippet
                        metadata=context or {},
                    )
                    entities.append(entity)

                except Exception as e:
                    logger.warning(f"Error parsing entity: {e}")
                    continue

            return entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing entities: {e}")
            return []

    async def extract_from_condition(
        self,
        condition_name: str,
        symptoms: List[str],
        signs: List[str],
        treatment: List[str],
        etiology: Optional[List[str]] = None,
        chapter: Optional[str] = None,
        section_id: Optional[str] = None,
    ) -> List[MedicalEntity]:
        """Extract entities from structured condition data.

        Args:
            condition_name: Condition name
            symptoms: List of symptoms
            signs: List of signs
            treatment: List of treatments
            etiology: Optional list of etiologies
            chapter: Optional chapter name
            section_id: Optional section ID

        Returns:
            List of extracted entities
        """
        # Build text representation
        text_parts = [f"Condition: {condition_name}"]

        if symptoms:
            text_parts.append(f"Symptoms: {', '.join(symptoms)}")
        if signs:
            text_parts.append(f"Signs: {', '.join(signs)}")
        if treatment:
            text_parts.append(f"Treatment: {', '.join(treatment)}")
        if etiology:
            text_parts.append(f"Etiology: {', '.join(etiology)}")

        text = ". ".join(text_parts)

        # Context
        context = {
            "condition_name": condition_name,
            "chapter": chapter,
            "section_id": section_id,
        }

        # Extract entities
        return await self.extract_entities(text, context)

    async def batch_extract(
        self,
        texts: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None,
    ) -> List[List[MedicalEntity]]:
        """Extract entities from multiple texts in batch.

        Args:
            texts: List of texts to process
            contexts: Optional list of contexts

        Returns:
            List of entity lists (one per text)
        """
        if contexts is None:
            contexts = [None] * len(texts)

        # Process in batches
        batch_size = self.config.entity_batch_size
        results = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_contexts = contexts[i:i+batch_size]

            # Process batch concurrently
            tasks = [
                self.extract_entities(text, ctx)
                for text, ctx in zip(batch_texts, batch_contexts)
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle errors
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch extraction error: {result}")
                    results.append([])
                else:
                    results.append(result)

            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

        return results


# Example usage
if __name__ == "__main__":
    from graphrag_config import load_config

    async def main():
        config = load_config()
        extractor = EntityExtractor(config)

        # Test extraction
        text = """
        Acute Angle-Closure Glaucoma: Sudden onset of severe eye pain, blurred vision,
        and nausea. Signs include corneal edema, fixed mid-dilated pupil, and elevated
        intraocular pressure. Treatment includes topical beta-blockers, pilocarpine,
        and systemic acetazolamide. This is an ophthalmic emergency.
        """

        entities = await extractor.extract_entities(text)

        print(f"\nExtracted {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity.name} ({entity.entity_type.value}): {entity.description}")

    asyncio.run(main())
