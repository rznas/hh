"""Parser for Wills Eye Manual structured JSON."""
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    NodeType, EdgeType, UrgencyLevel,
    RED_FLAG_KEYWORDS, URGENT_KEYWORDS, NON_URGENT_KEYWORDS,
    ANATOMICAL_TERMS, FIELD_TO_NODE_TYPE
)


@dataclass
class MedicalEntity:
    """Represents a medical entity (node) in the knowledge graph."""
    name: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    source_section: Optional[str] = None


@dataclass
class MedicalRelationship:
    """Represents a relationship (edge) between entities."""
    source: MedicalEntity
    target: MedicalEntity
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedCondition:
    """Complete parsed medical condition with entities and relationships."""
    condition_name: str
    chapter: str
    section_id: str
    urgency_level: UrgencyLevel
    entities: List[MedicalEntity] = field(default_factory=list)
    relationships: List[MedicalRelationship] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)


class WillsEyeParser:
    """Parser for extracting medical entities from Wills Eye Manual JSON."""

    def __init__(self, json_path: str):
        """Initialize parser with path to structured JSON.

        Args:
            json_path: Path to wills_eye_structured.json
        """
        self.json_path = json_path
        self.data: Dict[str, Any] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load and validate JSON data."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {self.json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    def get_chapters(self) -> List[str]:
        """Get list of all chapter names.

        Returns:
            List of chapter names
        """
        return list(self.data.keys())

    def parse_chapter(self, chapter_name: str) -> List[ParsedCondition]:
        """Parse all conditions in a chapter.

        Args:
            chapter_name: Name of the chapter (e.g., "Trauma")

        Returns:
            List of parsed conditions
        """
        if chapter_name not in self.data:
            raise ValueError(f"Chapter not found: {chapter_name}")

        chapter_data = self.data[chapter_name]
        conditions = []

        for section_id, content in chapter_data.items():
            if isinstance(content, dict):
                parsed = self._parse_condition(
                    condition_name=section_id,
                    chapter=chapter_name,
                    content=content
                )
                conditions.append(parsed)

        return conditions

    def _parse_condition(
        self,
        condition_name: str,
        chapter: str,
        content: Dict[str, Any]
    ) -> ParsedCondition:
        """Parse a single medical condition.

        Args:
            condition_name: Name/ID of the condition
            chapter: Chapter it belongs to
            content: Condition content dictionary

        Returns:
            Parsed condition with entities and relationships
        """
        # Create main disease entity
        disease_entity = MedicalEntity(
            name=condition_name,
            node_type=NodeType.DISEASE,
            source_section=condition_name,
            properties={"chapter": chapter}
        )

        entities = [disease_entity]
        relationships = []

        # Extract urgency level
        urgency = self._extract_urgency(content)
        disease_entity.properties["urgency_level"] = urgency.value

        # Extract red flags
        red_flags = self._extract_red_flags(content)
        disease_entity.properties["red_flags"] = red_flags

        # Parse symptoms
        symptom_entities, symptom_rels = self._parse_symptoms(
            content, disease_entity
        )
        entities.extend(symptom_entities)
        relationships.extend(symptom_rels)

        # Parse signs
        sign_entities, sign_rels = self._parse_signs(content, disease_entity)
        entities.extend(sign_entities)
        relationships.extend(sign_rels)

        # Parse treatment
        treatment_entities, treatment_rels = self._parse_treatment(
            content, disease_entity
        )
        entities.extend(treatment_entities)
        relationships.extend(treatment_rels)

        # Parse etiology
        etiology_entities, etiology_rels = self._parse_etiology(
            content, disease_entity
        )
        entities.extend(etiology_entities)
        relationships.extend(etiology_rels)

        # Parse differential diagnosis
        ddx_entities, ddx_rels = self._parse_differential(
            content, disease_entity
        )
        entities.extend(ddx_entities)
        relationships.extend(ddx_rels)

        # Parse anatomical references
        anatomy_entities, anatomy_rels = self._extract_anatomy(
            content, disease_entity
        )
        entities.extend(anatomy_entities)
        relationships.extend(anatomy_rels)

        return ParsedCondition(
            condition_name=condition_name,
            chapter=chapter,
            section_id=condition_name,
            urgency_level=urgency,
            entities=entities,
            relationships=relationships,
            red_flags=red_flags
        )

    def _extract_urgency(self, content: Dict[str, Any]) -> UrgencyLevel:
        """Classify urgency level from content.

        Args:
            content: Condition content dictionary

        Returns:
            Urgency level classification
        """
        text = self._get_full_text(content).lower()

        # Check for red flag keywords (EMERGENT)
        for keyword in RED_FLAG_KEYWORDS:
            if keyword.lower() in text:
                return UrgencyLevel.EMERGENT

        # Check for specific urgency indicators
        emergent_indicators = [
            "emergency", "immediately", "urgent care", "er immediately",
            "call 911", "life-threatening", "sight-threatening"
        ]
        for indicator in emergent_indicators:
            if indicator in text:
                return UrgencyLevel.EMERGENT

        # Check for urgent keywords
        for keyword in URGENT_KEYWORDS:
            if keyword.lower() in text:
                return UrgencyLevel.URGENT

        # Check for time-based indicators
        if any(phrase in text for phrase in ["24 hours", "24-48 hours", "same day"]):
            return UrgencyLevel.URGENT

        # Default to non-urgent if no indicators found
        return UrgencyLevel.NON_URGENT

    def _extract_red_flags(self, content: Dict[str, Any]) -> List[str]:
        """Extract red flag keywords present in content.

        Args:
            content: Condition content dictionary

        Returns:
            List of red flag keywords found
        """
        text = self._get_full_text(content).lower()
        found_flags = []

        for keyword in RED_FLAG_KEYWORDS:
            if keyword.lower() in text:
                found_flags.append(keyword)

        return found_flags

    def _parse_symptoms(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract symptom entities and relationships.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (symptom entities, relationships)
        """
        entities = []
        relationships = []

        symptoms = content.get("Symptoms", [])
        if not symptoms:
            return entities, relationships

        # Handle both list and dict formats
        if isinstance(symptoms, dict):
            symptoms = list(symptoms.values())
        elif not isinstance(symptoms, list):
            symptoms = [symptoms]

        for symptom in symptoms:
            symptom_text = self._clean_text(symptom)
            if not symptom_text:
                continue

            symptom_entity = MedicalEntity(
                name=symptom_text,
                node_type=NodeType.SYMPTOM,
                source_section=disease.source_section
            )
            entities.append(symptom_entity)

            # Create PRESENTS_WITH relationship
            relationships.append(MedicalRelationship(
                source=disease,
                target=symptom_entity,
                edge_type=EdgeType.PRESENTS_WITH,
                properties={"confidence": 0.8}  # Default confidence
            ))

            # Create reverse INDICATES relationship
            relationships.append(MedicalRelationship(
                source=symptom_entity,
                target=disease,
                edge_type=EdgeType.INDICATES,
                properties={"confidence": 0.6}  # Lower for reverse
            ))

        return entities, relationships

    def _parse_signs(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract sign entities and relationships.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (sign entities, relationships)
        """
        entities = []
        relationships = []

        signs = content.get("Signs", [])
        if not signs:
            return entities, relationships

        # Handle nested structure (e.g., Critical/Other subsections)
        if isinstance(signs, dict):
            all_signs = []
            for key, value in signs.items():
                if isinstance(value, list):
                    all_signs.extend(value)
                else:
                    all_signs.append(value)
            signs = all_signs

        for sign in signs:
            sign_text = self._clean_text(sign)
            if not sign_text:
                continue

            sign_entity = MedicalEntity(
                name=sign_text,
                node_type=NodeType.SIGN,
                source_section=disease.source_section
            )
            entities.append(sign_entity)

            relationships.append(MedicalRelationship(
                source=disease,
                target=sign_entity,
                edge_type=EdgeType.SHOWS_SIGN,
                properties={"confidence": 0.85}
            ))

        return entities, relationships

    def _parse_treatment(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract treatment entities and relationships.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (treatment entities, relationships)
        """
        entities = []
        relationships = []

        treatment = content.get("Treatment", [])
        if not treatment:
            return entities, relationships

        # Flatten nested treatment structures
        treatments = self._flatten_list(treatment)

        for t in treatments:
            treatment_text = self._clean_text(t)
            if not treatment_text or len(treatment_text) < 10:
                continue

            # Determine if it's a medication or procedure
            node_type = self._classify_treatment_type(treatment_text)

            treatment_entity = MedicalEntity(
                name=treatment_text,
                node_type=node_type,
                source_section=disease.source_section
            )
            entities.append(treatment_entity)

            relationships.append(MedicalRelationship(
                source=disease,
                target=treatment_entity,
                edge_type=EdgeType.TREATED_WITH
            ))

        return entities, relationships

    def _parse_etiology(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract etiology entities and relationships.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (etiology entities, relationships)
        """
        entities = []
        relationships = []

        etiology = content.get("Etiology", [])
        if not etiology:
            return entities, relationships

        etiologies = self._flatten_list(etiology)

        for e in etiologies:
            etiology_text = self._clean_text(e)
            if not etiology_text:
                continue

            etiology_entity = MedicalEntity(
                name=etiology_text,
                node_type=NodeType.ETIOLOGY,
                source_section=disease.source_section
            )
            entities.append(etiology_entity)

            relationships.append(MedicalRelationship(
                source=disease,
                target=etiology_entity,
                edge_type=EdgeType.CAUSED_BY
            ))

        return entities, relationships

    def _parse_differential(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract differential diagnosis entities.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (differential entities, relationships)
        """
        entities = []
        relationships = []

        ddx = content.get("Differential Diagnosis", [])
        if not ddx:
            return entities, relationships

        differentials = self._flatten_list(ddx)

        for d in differentials:
            ddx_text = self._clean_text(d)
            if not ddx_text:
                continue

            ddx_entity = MedicalEntity(
                name=ddx_text,
                node_type=NodeType.DIFFERENTIAL,
                source_section=disease.source_section
            )
            entities.append(ddx_entity)

            relationships.append(MedicalRelationship(
                source=disease,
                target=ddx_entity,
                edge_type=EdgeType.DIFFERENTIATES
            ))

        return entities, relationships

    def _extract_anatomy(
        self,
        content: Dict[str, Any],
        disease: MedicalEntity
    ) -> Tuple[List[MedicalEntity], List[MedicalRelationship]]:
        """Extract anatomical structures mentioned.

        Args:
            content: Condition content
            disease: Parent disease entity

        Returns:
            Tuple of (anatomy entities, relationships)
        """
        entities = []
        relationships = []

        text = self._get_full_text(content).lower()

        for anatomy_term in ANATOMICAL_TERMS:
            if anatomy_term.lower() in text:
                anatomy_entity = MedicalEntity(
                    name=anatomy_term,
                    node_type=NodeType.ANATOMY
                )
                entities.append(anatomy_entity)

                relationships.append(MedicalRelationship(
                    source=disease,
                    target=anatomy_entity,
                    edge_type=EdgeType.AFFECTS
                ))

        return entities, relationships

    def _classify_treatment_type(self, text: str) -> NodeType:
        """Classify treatment as medication, procedure, or generic treatment.

        Args:
            text: Treatment description

        Returns:
            Appropriate NodeType
        """
        text_lower = text.lower()

        # Medication indicators
        medication_keywords = [
            "mg", "ml", "drop", "ointment", "tablet", "topical",
            "oral", "i.v.", "steroid", "antibiotic", "antiviral"
        ]
        if any(kw in text_lower for kw in medication_keywords):
            return NodeType.MEDICATION

        # Procedure indicators
        procedure_keywords = [
            "surgery", "excision", "repair", "graft", "laser",
            "injection", "irrigation", "debridement"
        ]
        if any(kw in text_lower for kw in procedure_keywords):
            return NodeType.PROCEDURE

        return NodeType.TREATMENT

    def _clean_text(self, text: Any) -> str:
        """Clean and normalize text.

        Args:
            text: Raw text (can be string, list, or dict)

        Returns:
            Cleaned string
        """
        if isinstance(text, str):
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            # Remove special markers like "NOTE:", "Critical."
            text = re.sub(r'^(NOTE|Critical|Other):\s*', '', text, flags=re.IGNORECASE)
            return text
        elif isinstance(text, (list, dict)):
            return self._get_full_text(text)
        else:
            return str(text)

    def _flatten_list(self, data: Any) -> List[str]:
        """Recursively flatten nested lists/dicts into list of strings.

        Args:
            data: Nested data structure

        Returns:
            Flattened list of strings
        """
        result = []

        if isinstance(data, str):
            result.append(data)
        elif isinstance(data, list):
            for item in data:
                result.extend(self._flatten_list(item))
        elif isinstance(data, dict):
            for value in data.values():
                result.extend(self._flatten_list(value))

        return result

    def _get_full_text(self, data: Any) -> str:
        """Extract all text content from nested structure.

        Args:
            data: Nested data structure

        Returns:
            Concatenated text
        """
        flattened = self._flatten_list(data)
        return " ".join(flattened)


# Example usage
if __name__ == "__main__":
    parser = WillsEyeParser("../data/wills_eye_structured.json")

    print("Available chapters:")
    for chapter in parser.get_chapters():
        print(f"  - {chapter}")

    # Parse Trauma chapter
    print("\nParsing Trauma chapter...")
    conditions = parser.parse_chapter("Trauma")

    for condition in conditions[:3]:  # Show first 3
        print(f"\nCondition: {condition.condition_name}")
        print(f"  Urgency: {condition.urgency_level.value}")
        print(f"  Red Flags: {condition.red_flags}")
        print(f"  Entities: {len(condition.entities)}")
        print(f"  Relationships: {len(condition.relationships)}")
