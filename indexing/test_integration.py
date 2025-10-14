#!/usr/bin/env python3
"""Integration test script for knowledge graph indexing.

This script tests the complete pipeline without requiring actual Neo4j/OpenAI connections.
"""
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_parser():
    """Test Wills Eye parser."""
    logger.info("Testing parser...")

    from parsers import WillsEyeParser

    # Check if data file exists
    data_path = Path("../data/wills_eye_structured.json")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return False

    try:
        parser = WillsEyeParser(str(data_path))

        # Get chapters
        chapters = parser.get_chapters()
        logger.info(f"✓ Found {len(chapters)} chapters")

        # Parse Trauma chapter
        if "Trauma" in chapters:
            conditions = parser.parse_chapter("Trauma")
            logger.info(f"✓ Parsed {len(conditions)} conditions from Trauma chapter")

            if conditions:
                sample = conditions[0]
                logger.info(f"  Sample condition: {sample.condition_name}")
                logger.info(f"    Urgency: {sample.urgency_level.value}")
                logger.info(f"    Red flags: {len(sample.red_flags)}")
                logger.info(f"    Entities: {len(sample.entities)}")
                logger.info(f"    Relationships: {len(sample.relationships)}")
        else:
            logger.warning("Trauma chapter not found")

        logger.info("✓ Parser test passed\n")
        return True

    except Exception as e:
        logger.error(f"✗ Parser test failed: {e}")
        return False


def test_embedding_service():
    """Test embedding service."""
    logger.info("Testing embedding service...")

    try:
        from embedding_service import MedicalEmbeddingService, SymptomMatcher

        # Initialize service
        service = MedicalEmbeddingService()
        logger.info(f"✓ Embedding model loaded: {service.model_name}")
        logger.info(f"  Device: {service.device}")
        logger.info(f"  Dimension: {service.get_embedding_dimension()}")

        # Test encoding
        text = "sudden vision loss"
        embedding = service.encode(text)
        logger.info(f"✓ Encoded text: shape={embedding.shape}")

        # Test symptom matching
        matcher = SymptomMatcher(service)
        symptoms = [
            "sudden vision loss",
            "eye pain",
            "red eye",
            "blurry vision",
            "floaters",
        ]
        matcher.add_symptoms(symptoms)
        logger.info(f"✓ Added {len(symptoms)} symptoms to matcher")

        # Test matching
        user_input = "I can't see out of my left eye"
        matches = matcher.match(user_input, top_k=3)
        logger.info(f"✓ Matched '{user_input}':")
        for symptom, score in matches:
            logger.info(f"    - {symptom}: {score:.3f}")

        logger.info("✓ Embedding service test passed\n")
        return True

    except Exception as e:
        logger.error(f"✗ Embedding service test failed: {e}")
        logger.info("  Note: This is expected if BioBERT model not downloaded yet")
        logger.info("  Run: python embedding_service.py to download model")
        return False


def test_config():
    """Test configuration."""
    logger.info("Testing configuration...")

    try:
        from config import (
            NodeType, EdgeType, UrgencyLevel,
            RED_FLAG_KEYWORDS, URGENT_KEYWORDS,
            ANATOMICAL_TERMS
        )

        logger.info(f"✓ Node types: {len([n for n in NodeType])}")
        logger.info(f"✓ Edge types: {len([e for e in EdgeType])}")
        logger.info(f"✓ Red flag keywords: {len(RED_FLAG_KEYWORDS)}")
        logger.info(f"✓ Urgent keywords: {len(URGENT_KEYWORDS)}")
        logger.info(f"✓ Anatomical terms: {len(ANATOMICAL_TERMS)}")

        logger.info("✓ Configuration test passed\n")
        return True

    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


async def test_graphiti_client_mock():
    """Test Graphiti client (without actual connection)."""
    logger.info("Testing Graphiti client structure...")

    try:
        # Just test that we can import and examine the client
        from graphiti_client import GraphitiClient, GraphQueryBuilder

        logger.info("✓ GraphitiClient importable")
        logger.info("✓ GraphQueryBuilder importable")

        # Test query builder
        query = GraphQueryBuilder.get_diseases_by_symptom("eye pain", "EMERGENT")
        logger.info(f"✓ Sample query: {query[:50]}...")

        query = GraphQueryBuilder.check_red_flags(["sudden vision loss"])
        logger.info(f"✓ Red flag query: {query[:50]}...")

        logger.info("✓ Graphiti client structure test passed\n")
        logger.info("  Note: Actual Neo4j connection not tested")
        return True

    except Exception as e:
        logger.error(f"✗ Graphiti client test failed: {e}")
        return False


async def test_graph_builder_mock():
    """Test graph builder structure (without actual graph operations)."""
    logger.info("Testing graph builder structure...")

    try:
        from graph_builder import MedicalGraphBuilder, GraphIndexer

        logger.info("✓ MedicalGraphBuilder importable")
        logger.info("✓ GraphIndexer importable")

        logger.info("✓ Graph builder structure test passed\n")
        logger.info("  Note: Actual graph operations not tested")
        return True

    except Exception as e:
        logger.error(f"✗ Graph builder test failed: {e}")
        return False


def print_summary(results: dict):
    """Print test summary."""
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    print(f"\nTotal tests: {total}")
    print(f"Passed:      {passed} ✓")
    print(f"Failed:      {failed} ✗")

    print("\nDetailed results:")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 70)

    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("  1. Set up environment: cp .env.example .env")
        print("  2. Configure Neo4j and OpenAI credentials")
        print("  3. Run dry run: python index_knowledge_graph.py --data ../data/wills_eye_structured.json --dry-run")
        print("  4. Index Trauma chapter: python index_knowledge_graph.py --data ../data/wills_eye_structured.json --chapter Trauma")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")

    print()


async def main():
    """Run all tests."""
    print("=" * 70)
    print("  Knowledge Graph Integration Tests")
    print("=" * 70)
    print()

    results = {}

    # Run tests
    results["Configuration"] = test_config()
    results["Parser"] = test_parser()
    results["Embedding Service"] = test_embedding_service()
    results["Graphiti Client"] = await test_graphiti_client_mock()
    results["Graph Builder"] = await test_graph_builder_mock()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
