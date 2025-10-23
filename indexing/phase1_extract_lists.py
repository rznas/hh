#!/usr/bin/env python3
"""
Phase 1.3: Extract and Structure Lists from Wills Eye Manual

Extracts lists (differential diagnoses, symptoms, treatments, etc.)
and creates structured JSON with medical concept mapping.
"""

import json
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from xml.etree import ElementTree as ET

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

NS = {'xhtml': 'http://www.w3.org/1999/xhtml'}

def get_tag(elem) -> str:
    """Get tag name without namespace."""
    tag = elem.tag
    return tag.split('}')[1] if '}' in tag else tag

def get_text(elem) -> str:
    """Extract all text from element."""
    return ''.join(elem.itertext()).strip()

def extract_list_items(list_elem) -> List[str]:
    """Extract items from ul/ol element."""
    items = []
    for li in list_elem.findall('.//xhtml:li', NS):
        text = get_text(li)
        if text:
            items.append(text)
    return items

def find_list_context(list_elem, body_elements: List) -> Dict[str, str]:
    """Find the heading and context for a list."""
    list_index = -1
    for i, elem in enumerate(body_elements):
        if elem == list_elem:
            list_index = i
            break

    heading = "Unknown"
    level = 0

    # Look backwards for nearest heading
    if list_index > 0:
        for i in range(list_index - 1, max(0, list_index - 20), -1):
            elem = body_elements[i]
            tag = get_tag(elem)
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading = get_text(elem)
                level = int(tag[1])
                break

    return {'heading': heading, 'level': level}

def classify_list_type(heading: str, items: List[str]) -> str:
    """Classify list based on heading and content."""
    heading_lower = heading.lower()

    # Differential diagnosis lists
    if 'differential' in heading_lower or 'diagnosis' in heading_lower or 'etiology' in heading_lower:
        return 'differential_diagnosis'

    # Symptom lists
    if 'symptom' in heading_lower or 'sign' in heading_lower:
        return 'symptoms_signs'

    # Treatment/management lists
    if 'treatment' in heading_lower or 'management' in heading_lower or 'workup' in heading_lower:
        return 'treatment'

    # Examination/findings lists
    if 'exam' in heading_lower or 'finding' in heading_lower or 'evaluation' in heading_lower:
        return 'examination'

    # Check items for medication/procedure indicators
    items_text = ' '.join(items).lower()
    if any(med in items_text for med in ['mg', 'drops', 'topical', 'oral', 'injection']):
        return 'medication'
    if any(proc in items_text for proc in ['surgery', 'laser', 'repair', 'removal']):
        return 'procedure'

    return 'general'

def extract_lists_from_chapter(html_content: str, chapter_num: int, chapter_title: str) -> List[Dict]:
    """Extract all lists from a chapter."""
    root = ET.fromstring(html_content)
    body = root.find('.//xhtml:body', NS)

    if body is None:
        return []

    body_elements = list(body.iter())
    lists = []
    list_id = 0

    for elem in body.findall('.//xhtml:ul', NS) + body.findall('.//xhtml:ol', NS):
        # Extract list items
        items = extract_list_items(elem)

        # Skip empty or very small lists
        if len(items) < 2:
            continue

        # Find context
        context = find_list_context(elem, body_elements)

        # Classify list type
        list_type = classify_list_type(context['heading'], items)

        lists.append({
            'list_id': f"ch{chapter_num}_list_{list_id}",
            'chapter_number': chapter_num,
            'chapter_title': chapter_title,
            'section': context['heading'],
            'heading_level': context['level'],
            'list_type': list_type,
            'ordered': get_tag(elem) == 'ol',
            'items': items,
            'item_count': len(items)
        })

        list_id += 1

    return lists

def main():
    base_dir = Path(__file__).parent.parent
    epub_path = base_dir / "data" / "The Wills Eye Manual - Kalla Gervasio.epub"
    structure_file = base_dir / "data" / "epub_structure_summary.json"
    output_dir = base_dir / "indexing" / "output" / "phase1"

    print("=" * 60)
    print("Phase 1.3: List Extraction")
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

    # Extract lists from all chapters
    all_lists = []
    for meta in metadata:
        chapter_file = f"OEBPS/XHTML/{meta['file']}"
        if chapter_file not in epub_content:
            continue

        print(f"\n📋 Chapter {meta['number']}: {meta['title']}")
        lists = extract_lists_from_chapter(
            epub_content[chapter_file],
            meta['number'],
            meta['title']
        )

        print(f"   Found {len(lists)} list(s)")

        # Show type distribution
        type_counts = {}
        for lst in lists:
            type_counts[lst['list_type']] = type_counts.get(lst['list_type'], 0) + 1

        for list_type, count in sorted(type_counts.items()):
            print(f"     - {list_type}: {count}")

        all_lists.extend(lists)

    # Save lists
    output_file = output_dir / "wills_eye_lists.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_lists, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved: {output_file.name}")
    print(f"  Total lists extracted: {len(all_lists)}")

    # Generate report
    type_distribution = {}
    for lst in all_lists:
        type_distribution[lst['list_type']] = type_distribution.get(lst['list_type'], 0) + 1

    report = {
        'phase': '1.3 - List Extraction',
        'total_lists': len(all_lists),
        'chapters_processed': len(metadata),
        'type_distribution': type_distribution,
        'avg_items_per_list': sum(lst['item_count'] for lst in all_lists) / len(all_lists) if all_lists else 0
    }

    report_file = output_dir / "phase1_3_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Report: {report_file.name}")
    print("\n" + "=" * 60)
    print("Phase 1.3 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
