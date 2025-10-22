#!/usr/bin/env python3
"""
Phase 1.2: Extract and Structure Tables from Wills Eye Manual

Extracts tables from chapters and converts them to structured JSON format.
Tables are found in chapters: 3, 4, 7, 9, 11, 12, 13, 14
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from xml.etree import ElementTree as ET

NS = {'xhtml': 'http://www.w3.org/1999/xhtml'}

def get_tag(elem) -> str:
    """Get tag name without namespace."""
    tag = elem.tag
    return tag.split('}')[1] if '}' in tag else tag

def get_text(elem) -> str:
    """Extract all text from element."""
    return ''.join(elem.itertext()).strip()

def extract_table_data(table_elem) -> Dict[str, Any]:
    """Extract structured data from a table element."""
    headers = []
    rows = []

    # Extract headers from thead or first tr
    thead = table_elem.find('.//xhtml:thead', NS)
    if thead is not None:
        for th in thead.findall('.//xhtml:th', NS):
            headers.append(get_text(th))

    # If no thead, check first row
    if not headers:
        first_tr = table_elem.find('.//xhtml:tr', NS)
        if first_tr is not None:
            for th in first_tr.findall('.//xhtml:th', NS):
                headers.append(get_text(th))
            # Also try td in first row if no th
            if not headers:
                for td in first_tr.findall('.//xhtml:td', NS):
                    headers.append(get_text(td))

    # Extract data rows from tbody or all tr elements
    tbody = table_elem.find('.//xhtml:tbody', NS)
    tr_elements = tbody.findall('.//xhtml:tr', NS) if tbody is not None else table_elem.findall('.//xhtml:tr', NS)

    # Skip first row if it was used for headers
    start_idx = 1 if not thead and headers else 0

    for tr in tr_elements[start_idx:]:
        row_data = []
        for td in tr.findall('.//xhtml:td', NS):
            row_data.append(get_text(td))

        # Also check for th in data rows
        for th in tr.findall('.//xhtml:th', NS):
            row_data.append(get_text(th))

        if row_data:
            rows.append(row_data)

    return {
        'headers': headers,
        'rows': rows
    }

def find_table_context(table_elem, body_elements: List) -> str:
    """Find the nearest heading or context for a table."""
    # Find the table's position in body
    table_index = -1
    for i, elem in enumerate(body_elements):
        if elem == table_elem:
            table_index = i
            break

    # Look backwards for nearest heading
    if table_index > 0:
        for i in range(table_index - 1, -1, -1):
            elem = body_elements[i]
            tag = get_tag(elem)
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                return get_text(elem)

            # Also check divs for headings
            if tag == 'div':
                for child in elem:
                    child_tag = get_tag(child)
                    if child_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        return get_text(child)

    return "Unknown section"

def extract_tables_from_chapter(html_content: str, chapter_num: int, chapter_title: str) -> List[Dict]:
    """Extract all tables from a chapter."""
    root = ET.fromstring(html_content)
    body = root.find('.//xhtml:body', NS)

    if body is None:
        return []

    body_elements = list(body.iter())
    tables = []
    table_id = 0

    for elem in body.findall('.//xhtml:table', NS):
        # Extract table data
        table_data = extract_table_data(elem)

        # Skip empty tables
        if not table_data['rows'] and not table_data['headers']:
            continue

        # Find context/caption
        context = find_table_context(elem, body_elements)

        # Look for caption element
        caption_elem = elem.find('.//xhtml:caption', NS)
        caption = get_text(caption_elem) if caption_elem is not None else ""

        tables.append({
            'table_id': f"ch{chapter_num}_table_{table_id}",
            'chapter_number': chapter_num,
            'chapter_title': chapter_title,
            'section': context,
            'caption': caption,
            'headers': table_data['headers'],
            'rows': table_data['rows'],
            'num_rows': len(table_data['rows']),
            'num_columns': len(table_data['headers']) if table_data['headers'] else (len(table_data['rows'][0]) if table_data['rows'] else 0)
        })

        table_id += 1

    return tables

def main():
    base_dir = Path(__file__).parent.parent
    epub_path = base_dir / "data" / "The Wills Eye Manual - Kalla Gervasio.epub"
    structure_file = base_dir / "data" / "epub_structure_summary.json"
    output_dir = base_dir / "indexing" / "output" / "phase1"

    print("=" * 60)
    print("Phase 1.2: Table Extraction")
    print("=" * 60)

    # Load chapter metadata
    with open(structure_file) as f:
        metadata = json.load(f)

    # Chapters with tables: 3, 4, 7, 9, 11, 12, 13, 14
    chapters_with_tables = [3, 4, 7, 9, 11, 12, 13, 14]

    # Extract EPUB content
    print(f"\nExtracting from: {epub_path.name}")
    epub_content = {}
    with zipfile.ZipFile(epub_path) as epub:
        for item in epub.namelist():
            if item.endswith('.xhtml'):
                epub_content[item] = epub.read(item).decode('utf-8')

    # Extract tables
    all_tables = []
    for meta in metadata:
        if meta['number'] not in chapters_with_tables:
            continue

        chapter_file = f"OEBPS/XHTML/{meta['file']}"
        if chapter_file not in epub_content:
            continue

        print(f"\n📊 Chapter {meta['number']}: {meta['title']}")
        tables = extract_tables_from_chapter(
            epub_content[chapter_file],
            meta['number'],
            meta['title']
        )

        print(f"   Found {len(tables)} table(s)")
        for table in tables:
            print(f"     - {table['table_id']}: {table['num_rows']} rows × {table['num_columns']} cols")
            if table['caption']:
                print(f"       Caption: {table['caption'][:60]}...")

        all_tables.extend(tables)

    # Save tables
    output_file = output_dir / "wills_eye_tables.json"
    with open(output_file, 'w') as f:
        json.dump(all_tables, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved: {output_file.name}")
    print(f"  Total tables extracted: {len(all_tables)}")

    # Generate report
    report = {
        'phase': '1.2 - Table Extraction',
        'total_tables': len(all_tables),
        'chapters_processed': len(chapters_with_tables),
        'tables_by_chapter': {}
    }

    for ch_num in chapters_with_tables:
        ch_tables = [t for t in all_tables if t['chapter_number'] == ch_num]
        if ch_tables:
            report['tables_by_chapter'][f"chapter_{ch_num}"] = {
                'count': len(ch_tables),
                'table_ids': [t['table_id'] for t in ch_tables]
            }

    report_file = output_dir / "phase1_2_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Report: {report_file.name}")
    print("\n" + "=" * 60)
    print("Phase 1.2 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
