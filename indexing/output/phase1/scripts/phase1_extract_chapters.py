#!/usr/bin/env python3
"""
Phase 1.1: Extract and Parse Chapter Content from Wills Eye Manual EPUB

This script extracts structured chapter content including:
- Chapter titles and section hierarchy
- Heading levels (H1-H6)
- Content blocks for each section
- Body text with maintained hierarchy

Output files:
- wills_eye_chapters_structured.json
- wills_eye_text_blocks.json
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from xml.etree import ElementTree as ET
from collections import defaultdict

# Namespace map for XHTML
XHTML_NS = {'xhtml': 'http://www.w3.org/1999/xhtml'}

def extract_epub_content(epub_path: Path) -> Dict[str, str]:
    """Extract XHTML content from EPUB file."""
    content = {}
    with zipfile.ZipFile(epub_path, 'r') as epub:
        # Get all XHTML files
        for item in epub.namelist():
            if item.endswith('.xhtml'):
                content[item] = epub.read(item).decode('utf-8')
    return content

def get_heading_level(tag: str) -> int:
    """Get heading level from tag name (h1->1, h2->2, etc.)."""
    if tag.startswith('{'):
        # Strip namespace
        tag = tag.split('}')[1]
    if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
        return int(tag[1])
    return 0

def extract_text_recursive(element) -> str:
    """Recursively extract text from element and children."""
    text_parts = []
    if element.text:
        text_parts.append(element.text.strip())
    for child in element:
        text_parts.append(extract_text_recursive(child))
        if child.tail:
            text_parts.append(child.tail.strip())
    return ' '.join(filter(None, text_parts))

def parse_chapter_structure(chapter_html: str, chapter_num: int, chapter_title: str) -> Dict[str, Any]:
    """Parse a chapter's HTML into structured sections."""
    root = ET.fromstring(chapter_html)
    body = root.find('.//xhtml:body', XHTML_NS)

    if body is None:
        return {
            'chapter_number': chapter_num,
            'title': chapter_title,
            'sections': []
        }

    sections = []
    current_section = None
    section_stack = []  # Track hierarchy

    # Process all children of body sequentially
    for elem in body:
        tag = elem.tag.split('}')[1] if '}' in elem.tag else elem.tag

        # Process headings
        level = get_heading_level(elem.tag)
        if level > 0:
            heading_text = extract_text_recursive(elem)
            if not heading_text:
                continue

            # Create new section
            section = {
                'heading': heading_text,
                'level': level,
                'content_blocks': [],
                'subsections': []
            }

            # Maintain hierarchy
            while section_stack and section_stack[-1]['level'] >= level:
                section_stack.pop()

            if section_stack:
                # Add as subsection to parent
                section_stack[-1]['subsections'].append(section)
            else:
                # Top-level section
                sections.append(section)

            section_stack.append(section)
            current_section = section

        # Process divs (may contain paragraphs or lists)
        elif tag == 'div' and current_section is not None:
            # Process children of div
            for child in elem:
                child_tag = child.tag.split('}')[1] if '}' in child.tag else child.tag

                if child_tag == 'p':
                    text = extract_text_recursive(child)
                    if text and len(text.strip()) > 0:
                        current_section['content_blocks'].append({
                            'type': 'paragraph',
                            'text': text.strip()
                        })
                elif child_tag in ['ul', 'ol']:
                    # Extract list items
                    items = []
                    for li in child.findall('.//xhtml:li', XHTML_NS):
                        li_text = extract_text_recursive(li)
                        if li_text:
                            items.append(li_text.strip())
                    if items:
                        current_section['content_blocks'].append({
                            'type': 'list',
                            'items': items
                        })

        # Process direct paragraphs
        elif tag == 'p' and current_section is not None:
            text = extract_text_recursive(elem)
            if text and len(text.strip()) > 0:
                current_section['content_blocks'].append({
                    'type': 'paragraph',
                    'text': text.strip()
                })

    return {
        'chapter_number': chapter_num,
        'title': chapter_title,
        'sections': sections
    }

def extract_text_blocks(chapters_data: List[Dict]) -> List[Dict[str, Any]]:
    """Extract flat text blocks with hierarchy references."""
    text_blocks = []
    block_id = 0

    def process_section(section: Dict, chapter_num: int, chapter_title: str, parent_path: str = ""):
        nonlocal block_id

        # Create path for this section
        section_path = f"{parent_path}/{section['heading']}" if parent_path else section['heading']

        # Add text blocks from this section
        for block in section.get('content_blocks', []):
            if block['type'] == 'paragraph' and len(block['text']) > 20:  # Filter very short blocks
                text_blocks.append({
                    'block_id': f"block_{block_id:05d}",
                    'chapter_number': chapter_num,
                    'chapter_title': chapter_title,
                    'section_path': section_path,
                    'heading_level': section['level'],
                    'text': block['text']
                })
                block_id += 1

        # Process subsections recursively
        for subsection in section.get('subsections', []):
            process_section(subsection, chapter_num, chapter_title, section_path)

    for chapter in chapters_data:
        for section in chapter['sections']:
            process_section(section, chapter['chapter_number'], chapter['title'])

    return text_blocks

def main():
    # Paths
    base_dir = Path(__file__).parent.parent
    epub_path = base_dir / "data" / "The Wills Eye Manual - Kalla Gervasio.epub"
    structure_summary = base_dir / "data" / "epub_structure_summary.json"
    output_dir = base_dir / "indexing" / "output" / "phase1"

    # Load chapter metadata
    with open(structure_summary, 'r') as f:
        chapter_metadata = json.load(f)

    print("Phase 1.1: Extracting Chapter Content")
    print(f"Processing EPUB: {epub_path}")

    # Extract EPUB content
    epub_content = extract_epub_content(epub_path)
    print(f"Extracted {len(epub_content)} XHTML files")

    # Parse chapters
    chapters_structured = []
    for meta in chapter_metadata[:5]:  # Limit to first 5 chapters for initial run
        chapter_file = f"OEBPS/XHTML/{meta['file']}"
        if chapter_file not in epub_content:
            print(f"Warning: {chapter_file} not found")
            continue

        print(f"Processing Chapter {meta['number']}: {meta['title']}")
        chapter_data = parse_chapter_structure(
            epub_content[chapter_file],
            meta['number'],
            meta['title']
        )
        chapters_structured.append(chapter_data)
        print(f"  - Extracted {len(chapter_data['sections'])} top-level sections")

    # Save structured chapters
    output_file = output_dir / "wills_eye_chapters_structured.json"
    with open(output_file, 'w') as f:
        json.dump(chapters_structured, f, indent=2)
    print(f"\nSaved: {output_file}")

    # Extract text blocks
    print("\nExtracting text blocks...")
    text_blocks = extract_text_blocks(chapters_structured)

    output_file = output_dir / "wills_eye_text_blocks.json"
    with open(output_file, 'w') as f:
        json.dump(text_blocks, f, indent=2)
    print(f"Saved: {output_file}")
    print(f"Total text blocks: {len(text_blocks)}")

    # Generate summary report
    report = {
        'phase': 'Phase 1.1 - Chapter Content Extraction',
        'chapters_processed': len(chapters_structured),
        'total_sections': sum(len(ch['sections']) for ch in chapters_structured),
        'total_text_blocks': len(text_blocks),
        'output_files': [
            'wills_eye_chapters_structured.json',
            'wills_eye_text_blocks.json'
        ]
    }

    report_file = output_dir / "phase1_1_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {report_file}")

if __name__ == '__main__':
    main()
