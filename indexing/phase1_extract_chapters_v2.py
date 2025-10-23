#!/usr/bin/env python3
"""
Phase 1.1: Extract and Parse Chapter Content from Wills Eye Manual EPUB (V2)

Improved version that properly handles the XHTML structure where content
follows headings in subsequent div elements.
"""

import json
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from xml.etree import ElementTree as ET

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Namespace map for XHTML
NS = {'xhtml': 'http://www.w3.org/1999/xhtml'}

def get_tag(elem) -> str:
    """Get tag name without namespace."""
    tag = elem.tag
    return tag.split('}')[1] if '}' in tag else tag

def get_text(elem, recursive=True) -> str:
    """Extract text from element."""
    if recursive:
        return ''.join(elem.itertext()).strip()
    return (elem.text or '').strip()

def is_heading(tag: str) -> bool:
    """Check if tag is a heading."""
    return tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def get_heading_level(tag: str) -> int:
    """Get heading level (1-6)."""
    if is_heading(tag):
        return int(tag[1])
    return 0

def extract_list_items(elem) -> List[str]:
    """Extract list items from ul/ol element."""
    items = []
    for li in elem.findall('.//xhtml:li', NS):
        text = get_text(li)
        if text:
            items.append(text)
    return items

def extract_chapter_sections(chapter_html: str, chapter_num: int, chapter_title: str) -> Dict[str, Any]:
    """Extract structured sections from chapter HTML."""
    root = ET.fromstring(chapter_html)
    body = root.find('.//xhtml:body', NS)

    if body is None:
        return {'chapter_number': chapter_num, 'title': chapter_title, 'sections': []}

    # Convert to list for indexed access
    children = list(body)
    sections = []
    section_stack = []

    i = 0
    while i < len(children):
        elem = children[i]
        tag = get_tag(elem)

        # Process headings
        if is_heading(tag):
            level = get_heading_level(tag)
            heading = get_text(elem)

            if not heading:
                i += 1
                continue

            # Create new section
            section = {
                'heading': heading,
                'level': level,
                'content_blocks': [],
                'subsections': []
            }

            # Collect content until next heading of same or higher level
            j = i + 1
            while j < len(children):
                next_elem = children[j]
                next_tag = get_tag(next_elem)

                # Stop at next heading of same or higher level
                if is_heading(next_tag) and get_heading_level(next_tag) <= level:
                    break

                # Process content
                if next_tag == 'div':
                    # Extract content from div
                    for child in next_elem:
                        child_tag = get_tag(child)

                        if child_tag == 'p':
                            text = get_text(child)
                            if text and len(text) > 5:
                                section['content_blocks'].append({
                                    'type': 'paragraph',
                                    'text': text
                                })
                        elif child_tag in ['ul', 'ol']:
                            items = extract_list_items(child)
                            if items:
                                section['content_blocks'].append({
                                    'type': 'list',
                                    'list_type': child_tag,
                                    'items': items
                                })
                        elif child_tag == 'span':
                            # Sometimes spans contain important text
                            text = get_text(child)
                            if text and len(text) > 10:
                                section['content_blocks'].append({
                                    'type': 'text',
                                    'text': text
                                })

                    # Also check for direct text in div
                    div_text = get_text(next_elem, recursive=False)
                    if div_text and len(div_text) > 5:
                        section['content_blocks'].append({
                            'type': 'text',
                            'text': div_text
                        })

                elif next_tag == 'p':
                    text = get_text(next_elem)
                    if text and len(text) > 5:
                        section['content_blocks'].append({
                            'type': 'paragraph',
                            'text': text
                        })

                elif next_tag in ['ul', 'ol']:
                    items = extract_list_items(next_elem)
                    if items:
                        section['content_blocks'].append({
                            'type': 'list',
                            'list_type': next_tag,
                            'items': items
                        })

                j += 1

            # Maintain hierarchy
            while section_stack and section_stack[-1]['level'] >= level:
                section_stack.pop()

            if section_stack:
                section_stack[-1]['subsections'].append(section)
            else:
                sections.append(section)

            section_stack.append(section)
            i = j  # Jump to next unprocessed element
        else:
            i += 1

    return {
        'chapter_number': chapter_num,
        'title': chapter_title,
        'sections': sections
    }

def extract_text_blocks(chapters: List[Dict]) -> List[Dict]:
    """Extract flat text blocks for GraphRAG processing."""
    blocks = []
    block_id = 0

    def process_section(sec, ch_num, ch_title, path=""):
        nonlocal block_id

        section_path = f"{path}/{sec['heading']}" if path else sec['heading']

        # Add content blocks
        for block in sec['content_blocks']:
            if block['type'] in ['paragraph', 'text']:
                text = block['text']
                if len(text) > 20:  # Filter very short blocks
                    blocks.append({
                        'block_id': f"block_{block_id:05d}",
                        'chapter_number': ch_num,
                        'chapter_title': ch_title,
                        'section_path': section_path,
                        'heading_level': sec['level'],
                        'text': text
                    })
                    block_id += 1

            elif block['type'] == 'list':
                # Combine list items into text block
                list_text = '; '.join(block['items'])
                if len(list_text) > 20:
                    blocks.append({
                        'block_id': f"block_{block_id:05d}",
                        'chapter_number': ch_num,
                        'chapter_title': ch_title,
                        'section_path': section_path,
                        'heading_level': sec['level'],
                        'text': f"List: {list_text}",
                        'is_list': True
                    })
                    block_id += 1

        # Process subsections
        for subsec in sec['subsections']:
            process_section(subsec, ch_num, ch_title, section_path)

    for chapter in chapters:
        for section in chapter['sections']:
            process_section(section, chapter['chapter_number'], chapter['title'])

    return blocks

def main():
    base_dir = Path(__file__).parent.parent
    epub_path = base_dir / "data" / "The Wills Eye Manual - Kalla Gervasio.epub"
    structure_file = base_dir / "data" / "epub_structure_summary.json"
    output_dir = base_dir / "indexing" / "output" / "phase1"

    print("=" * 60)
    print("Phase 1.1: Chapter Content Extraction")
    print("=" * 60)

    # Load chapter metadata
    with open(structure_file) as f:
        metadata = json.load(f)

    # Extract EPUB content
    print(f"\nExtracting from: {epub_path.name}")
    epub_content = {}
    with zipfile.ZipFile(epub_path) as epub:
        for item in epub.namelist():
            if item.endswith('.xhtml'):
                epub_content[item] = epub.read(item).decode('utf-8')
    print(f"Found {len(epub_content)} XHTML files")

    # Process all chapters
    chapters = []
    for meta in metadata:
        chapter_file = f"OEBPS/XHTML/{meta['file']}"

        if chapter_file not in epub_content:
            print(f"⚠ Skipping Chapter {meta['number']}: file not found")
            continue

        print(f"\n📖 Chapter {meta['number']}: {meta['title']}")
        chapter = extract_chapter_sections(
            epub_content[chapter_file],
            meta['number'],
            meta['title']
        )

        total_sections = len(chapter['sections'])
        total_subsections = sum(len(s.get('subsections', [])) for s in chapter['sections'])
        total_blocks = sum(len(s.get('content_blocks', [])) for s in chapter['sections'])

        print(f"   Sections: {total_sections}")
        print(f"   Subsections: {total_subsections}")
        print(f"   Content blocks: {total_blocks}")

        chapters.append(chapter)

    # Save structured chapters
    output_file = output_dir / "wills_eye_chapters_structured.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chapters, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved: {output_file.name}")

    # Extract text blocks
    print("\n" + "=" * 60)
    print("Extracting text blocks...")
    blocks = extract_text_blocks(chapters)

    output_file = output_dir / "wills_eye_text_blocks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {output_file.name}")
    print(f"  Total blocks: {len(blocks)}")

    # Generate report
    report = {
        'phase': '1.1 - Chapter Content Extraction',
        'chapters_processed': len(chapters),
        'total_top_level_sections': sum(len(ch['sections']) for ch in chapters),
        'total_text_blocks': len(blocks),
        'chapters': [
            {
                'number': ch['chapter_number'],
                'title': ch['title'],
                'sections': len(ch['sections']),
                'blocks': len([b for b in blocks if b['chapter_number'] == ch['chapter_number']])
            }
            for ch in chapters
        ]
    }

    report_file = output_dir / "phase1_1_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Report: {report_file.name}")
    print("\n" + "=" * 60)
    print("Phase 1.1 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
