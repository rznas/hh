#!/usr/bin/env python3
"""Main script for indexing Wills Eye Manual into knowledge graph.

Usage:
    # Dry run (preview without indexing)
    python index_knowledge_graph.py --data ../data/wills_eye_structured.json --dry-run

    # Index single chapter
    python index_knowledge_graph.py --data ../data/wills_eye_structured.json --chapter "Trauma"

    # Index all chapters
    python index_knowledge_graph.py --data ../data/wills_eye_structured.json

    # With verbose logging
    python index_knowledge_graph.py --data ../data/wills_eye_structured.json --verbose
"""
import argparse
import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from dotenv import load_dotenv

from graph_builder import GraphIndexer
from graphiti_client import GraphitiClient
from config import validate_config, LOG_FILE, LOG_LEVEL

# Load environment variables
load_dotenv()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else getattr(logging, LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def print_banner() -> None:
    """Print startup banner."""
    print("=" * 70)
    print("  Wills Eye Manual - Knowledge Graph Indexing")
    print("  Medical Triage System")
    print("=" * 70)
    print()


def print_summary(result: dict) -> None:
    """Print indexing summary.

    Args:
        result: Indexing result dictionary
    """
    print("\n" + "=" * 70)
    print("  INDEXING SUMMARY")
    print("=" * 70)

    if result.get("success"):
        stats = result.get("stats", {})
        duration = result.get("duration_seconds", 0)

        print(f"\n✓ Success!")
        print(f"\n  Conditions Processed: {stats.get('conditions_processed', 0)}")
        print(f"  Episodes Created:     {stats.get('episodes_created', 0)}")
        print(f"  Errors:               {stats.get('errors', 0)}")
        print(f"  Duration:             {duration:.1f}s ({duration/60:.1f}m)")

        if "chapters_processed" in result:
            print(f"  Chapters Processed:   {result['chapters_processed']}")

    else:
        print(f"\n✗ Failed!")
        print(f"  Error: {result.get('error', 'Unknown error')}")

    print()


async def dry_run(data_path: str, chapters: Optional[List[str]] = None) -> None:
    """Perform dry run (preview without indexing).

    Args:
        data_path: Path to JSON data
        chapters: Optional list of specific chapters to preview
    """
    from parsers import WillsEyeParser

    logger = logging.getLogger(__name__)
    logger.info("Starting dry run...")

    parser = WillsEyeParser(data_path)
    all_chapters = parser.get_chapters()

    # Filter chapters if specified
    chapters_to_process = chapters if chapters else all_chapters

    print("\n" + "-" * 70)
    print("  DRY RUN - Preview Mode")
    print("-" * 70)
    print(f"\nTotal chapters available: {len(all_chapters)}")
    print(f"Chapters to process: {len(chapters_to_process)}\n")

    total_conditions = 0

    for chapter_name in chapters_to_process:
        if chapter_name not in all_chapters:
            logger.warning(f"Chapter '{chapter_name}' not found, skipping")
            continue

        conditions = parser.parse_chapter(chapter_name)
        total_conditions += len(conditions)

        print(f"Chapter: {chapter_name}")
        print(f"  ├─ Conditions: {len(conditions)}")

        # Show sample conditions
        if conditions:
            sample = conditions[0]
            print(f"  ├─ Sample: {sample.condition_name}")
            print(f"  ├─ Urgency: {sample.urgency_level.value}")
            print(f"  ├─ Red Flags: {len(sample.red_flags)}")
            print(f"  ├─ Entities: {len(sample.entities)}")
            print(f"  └─ Relationships: {len(sample.relationships)}")

        print()

    print("-" * 70)
    print(f"Total conditions to index: {total_conditions}")
    print(f"Estimated episodes: {total_conditions}")
    print("-" * 70)
    print("\nDry run complete. Use --no-dry-run to perform actual indexing.\n")


async def index_chapters(
    data_path: str,
    chapters: Optional[List[str]] = None,
    batch_size: int = 10,
    validate: bool = True,
) -> dict:
    """Index chapters to knowledge graph.

    Args:
        data_path: Path to JSON data
        chapters: Optional list of specific chapters to index
        batch_size: Batch size for processing
        validate: Perform validation after indexing

    Returns:
        Indexing result dictionary
    """
    logger = logging.getLogger(__name__)

    # Initialize indexer
    logger.info("Initializing indexer...")
    indexer = GraphIndexer(data_path)

    try:
        # Index specified chapters or all
        if chapters:
            logger.info(f"Indexing {len(chapters)} specified chapter(s)")

            # Index each chapter
            all_stats = {
                "conditions_processed": 0,
                "episodes_created": 0,
                "errors": 0,
            }

            for chapter in chapters:
                logger.info(f"Indexing chapter: {chapter}")
                result = await indexer.index_chapter(chapter, batch_size)

                if result.get("success"):
                    chapter_stats = result.get("stats", {})
                    all_stats["conditions_processed"] += chapter_stats.get("conditions_processed", 0)
                    all_stats["episodes_created"] += chapter_stats.get("episodes_created", 0)
                    all_stats["errors"] += chapter_stats.get("errors", 0)
                else:
                    logger.error(f"Failed to index chapter {chapter}: {result.get('error')}")
                    all_stats["errors"] += 1

            result = {
                "success": True,
                "chapters_processed": len(chapters),
                "stats": all_stats,
            }

        else:
            logger.info("Indexing all chapters")
            result = await indexer.index_all_chapters(batch_size)

        # Validate if requested
        if validate and result.get("success"):
            logger.info("Running validation...")
            validation = await indexer.validate_indexing()

            result["validation"] = validation

            if validation.get("all_passed"):
                logger.info("✓ All validations passed")
            else:
                logger.warning("✗ Some validations failed")
                for v in validation.get("validations", []):
                    if not v.get("passed"):
                        logger.warning(f"  Failed: {v.get('query')} - {v.get('error', 'Unknown')}")

        return result

    except Exception as e:
        logger.error(f"Error during indexing: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }

    finally:
        indexer.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Index Wills Eye Manual into knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  %(prog)s --data ../data/wills_eye_structured.json --dry-run

  # Index Trauma chapter
  %(prog)s --data ../data/wills_eye_structured.json --chapter "Trauma"

  # Index multiple chapters
  %(prog)s --data ../data/wills_eye_structured.json --chapter "Trauma" --chapter "Cornea"

  # Index all chapters
  %(prog)s --data ../data/wills_eye_structured.json

  # Verbose logging
  %(prog)s --data ../data/wills_eye_structured.json --verbose
        """
    )

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to wills_eye_structured.json"
    )

    parser.add_argument(
        "--chapter",
        type=str,
        action="append",
        dest="chapters",
        help="Specific chapter(s) to index (can be specified multiple times)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing (default: 10)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be indexed without actually indexing"
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation after indexing"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )

    return parser.parse_args()


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Print banner
    print_banner()

    # Validate data path
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return 1

    logger.info(f"Data file: {data_path}")

    try:
        # Validate configuration (unless dry run)
        if not args.dry_run:
            logger.info("Validating configuration...")
            validate_config()
            logger.info("✓ Configuration valid")

        # Dry run or actual indexing
        if args.dry_run:
            await dry_run(str(data_path), args.chapters)
            return 0

        else:
            # Perform indexing
            logger.info("Starting indexing...")
            result = await index_chapters(
                data_path=str(data_path),
                chapters=args.chapters,
                batch_size=args.batch_size,
                validate=not args.no_validate,
            )

            # Print summary
            print_summary(result)

            # Save detailed results
            results_file = f"indexing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Detailed results saved to: {results_file}")

            return 0 if result.get("success") else 1

    except KeyboardInterrupt:
        logger.warning("\nIndexing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
