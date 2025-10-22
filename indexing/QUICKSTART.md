# Quick Start Guide - Microsoft GraphRAG Indexing

This quick start guide has been deprecated in favor of the **Microsoft GraphRAG implementation**.

## Current Implementation

Please refer to **[QUICKSTART_GRAPHRAG.md](./QUICKSTART_GRAPHRAG.md)** for the current GraphRAG setup and usage guide.

## Overview

The knowledge graph indexing pipeline uses **Microsoft GraphRAG** to:
1. Extract entities from Wills Eye Manual JSON
2. Build relationships between medical concepts
3. Detect communities of related conditions
4. Enable both local (entity-specific) and global (theme-based) searches

## Quick Links

- **[QUICKSTART_GRAPHRAG.md](./QUICKSTART_GRAPHRAG.md)** - Complete GraphRAG setup guide
- **[../docs/GRAPHRAG_ARCHITECTURE.md](../docs/GRAPHRAG_ARCHITECTURE.md)** - Architecture details
- **[README.md](./README.md)** - Indexing module documentation

## Setup (Quick Steps)

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: `cp .env.example .env`
3. Run indexing: `python graphrag_indexer.py --data ../data/wills_eye_structured.json --dry-run`

For detailed instructions, see **QUICKSTART_GRAPHRAG.md**.
