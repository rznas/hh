#!/usr/bin/env python3
"""
Shared utilities for LLM schema validation and error handling.

This module provides common functionality for:
- JSON schema validation
- Recording invalid outputs for manual review
- Structured error reporting
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
import jsonschema


class SchemaValidationError(Exception):
    """Raised when LLM output fails schema validation."""
    pass


class InvalidResponseHandler:
    """Handles LLM responses that don't match the expected schema and connection errors."""

    def __init__(self, output_dir: Path, entity_type: str):
        """
        Initialize the handler.

        Args:
            output_dir: Directory to save invalid responses
            entity_type: Type of entity being extracted (e.g., 'anatomy', 'etiology')
        """
        self.output_dir = Path(output_dir)
        self.entity_type = entity_type
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.invalid_file = self.output_dir / f"invalid_{entity_type}_{timestamp}.json"
        self.summary_file = self.output_dir / f"invalid_{entity_type}_summary.json"
        self.connection_errors_file = self.output_dir / f"connection_errors_{entity_type}_{timestamp}.json"

        self.invalid_responses = []
        self.connection_errors = []
        self.summary = {
            "entity_type": entity_type,
            "timestamp": timestamp,
            "total_invalid": 0,
            "total_connection_errors": 0,
            "errors_by_type": {},
            "connection_errors_by_type": {},
            "file_path": str(self.invalid_file),
            "connection_errors_file_path": str(self.connection_errors_file)
        }

    def record_invalid_response(
        self,
        text_block: Dict[str, Any],
        prompt: str,
        llm_response: str,
        error: str,
        schema: Dict[str, Any]
    ) -> None:
        """
        Record an LLM response that failed validation.

        Args:
            text_block: Original text block that was processed
            prompt: The prompt sent to the LLM
            llm_response: The raw response from the LLM
            error: Error message or validation failure reason
            schema: The expected JSON schema
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "chapter": text_block.get("chapter_number"),
            "section": text_block.get("section_title"),
            "text_block_id": text_block.get("id"),
            "text_preview": text_block.get("text", "")[:200],
            "prompt": prompt,
            "llm_response": llm_response,
            "error": error,
            "error_category": "schema_validation",
            "expected_schema": schema,
            "entity_type": self.entity_type
        }

        self.invalid_responses.append(record)

        # Update summary
        error_type = error.split(":")[0] if ":" in error else error
        self.summary["errors_by_type"][error_type] = \
            self.summary["errors_by_type"].get(error_type, 0) + 1
        self.summary["total_invalid"] += 1

    def record_connection_error(
        self,
        text_block: Dict[str, Any],
        prompt: str,
        error: Exception,
        error_message: str,
        retry_count: int = 0
    ) -> None:
        """
        Record a connection error or other exception during LLM API call.

        Args:
            text_block: Original text block that was being processed
            prompt: The prompt that was being sent
            error: The exception object
            error_message: Human-readable error message
            retry_count: Number of retries attempted
        """
        error_type = type(error).__name__
        record = {
            "timestamp": datetime.now().isoformat(),
            "chapter": text_block.get("chapter_number"),
            "section": text_block.get("section_title"),
            "text_block_id": text_block.get("id"),
            "text_preview": text_block.get("text", "")[:200],
            "prompt": prompt,
            "error_type": error_type,
            "error_message": error_message,
            "full_error": str(error),
            "error_category": "connection_error",
            "retry_count": retry_count,
            "entity_type": self.entity_type,
            "action_needed": "Retry the extraction for this text block"
        }

        self.connection_errors.append(record)

        # Update summary
        self.summary["connection_errors_by_type"][error_type] = \
            self.summary["connection_errors_by_type"].get(error_type, 0) + 1
        self.summary["total_connection_errors"] += 1

    def save_invalid_responses(self) -> Tuple[int, str]:
        """
        Save all invalid responses and connection errors to JSON files for manual review.

        Returns:
            Tuple of (total_error_count, summary_file_path)
        """
        saved_count = 0
        saved_files = []

        # Save schema validation failures
        if self.invalid_responses:
            with open(self.invalid_file, "w", encoding="utf-8") as f:
                json.dump(self.invalid_responses, f, indent=2, ensure_ascii=False)
            saved_files.append(str(self.invalid_file))
            saved_count += len(self.invalid_responses)

        # Save connection errors
        if self.connection_errors:
            with open(self.connection_errors_file, "w", encoding="utf-8") as f:
                json.dump(self.connection_errors, f, indent=2, ensure_ascii=False)
            saved_files.append(str(self.connection_errors_file))
            saved_count += len(self.connection_errors)

        # Save summary
        if self.invalid_responses or self.connection_errors:
            self.summary["saved_files"] = saved_files
            self.summary["total_errors"] = saved_count
            with open(self.summary_file, "w", encoding="utf-8") as f:
                json.dump(self.summary, f, indent=2, ensure_ascii=False)

        return saved_count, str(self.summary_file)

    def get_summary(self) -> Dict[str, Any]:
        """Get the summary of invalid responses."""
        return self.summary


class SchemaValidator:
    """Validates JSON responses against expected schemas."""

    @staticmethod
    def validate(
        response_text: str,
        schema: Dict[str, Any],
        strict: bool = True
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Validate a JSON response against a schema.

        Args:
            response_text: The JSON string to validate
            schema: The JSON schema to validate against
            strict: If True, use strict validation; if False, be more lenient

        Returns:
            Tuple of (is_valid, parsed_json, error_message)
        """
        try:
            # Try to parse JSON
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError as e:
                return False, None, f"JSON parsing error: {str(e)}"

            # Validate against schema
            try:
                jsonschema.validate(instance=parsed, schema=schema)
                return True, parsed, ""
            except jsonschema.ValidationError as e:
                error_msg = f"Schema validation error: {e.message}"
                if not strict:
                    # In lenient mode, accept if the required fields are present
                    required_fields = schema.get("required", [])
                    if all(field in parsed for field in required_fields):
                        return True, parsed, ""
                return False, parsed, error_msg

        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"

    @staticmethod
    def extract_with_fallback(
        parsed_json: Dict[str, Any],
        primary_key: str,
        fallback_keys: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Extract data from parsed JSON with fallback keys.

        Args:
            parsed_json: The parsed JSON object
            primary_key: Primary key to look for
            fallback_keys: List of fallback keys to try

        Returns:
            List of extracted items
        """
        # Try primary key
        if primary_key in parsed_json:
            items = parsed_json[primary_key]
            if isinstance(items, list):
                return items
            return [items] if items else []

        # Try fallback keys
        if fallback_keys:
            for key in fallback_keys:
                if key in parsed_json:
                    items = parsed_json[key]
                    if isinstance(items, list):
                        return items
                    return [items] if items else []

        # If nothing found, return empty list
        return []


def create_error_summary_report(
    invalid_handlers: Dict[str, InvalidResponseHandler],
    output_dir: Path
) -> str:
    """
    Create a consolidated error summary report.

    Args:
        invalid_handlers: Dictionary of entity_type -> InvalidResponseHandler
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_entity_types": len(invalid_handlers),
        "entity_summaries": {},
        "total_invalid_responses": 0,
        "common_error_types": {}
    }

    for entity_type, handler in invalid_handlers.items():
        summary = handler.get_summary()
        report["entity_summaries"][entity_type] = summary
        report["total_invalid_responses"] += summary.get("total_invalid", 0)

        # Aggregate error types
        for error_type, count in summary.get("errors_by_type", {}).items():
            report["common_error_types"][error_type] = \
                report["common_error_types"].get(error_type, 0) + count

    # Sort error types by frequency
    report["common_error_types"] = dict(
        sorted(report["common_error_types"].items(), key=lambda x: x[1], reverse=True)
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "invalid_responses_summary.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(report_file)
