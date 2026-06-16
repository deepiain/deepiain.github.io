#!/Users/iain/Documents/Claude/Projects/Sumthing8/venv/bin/python3
"""
Repository Housekeeping Script
Scans /files/ folders, converts TIFFs to JPGs, fetches product data from
eastcoastmodular.co.uk, and generates PDFs. Uses MD5 hashing to detect changes.
"""

import os
import hashlib
import json
import requests
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Configuration
FILES_DIR = Path("/Users/iain/Documents/GitHub/deepiain.github.io/files")
ECM_BASE_URL = "https://eastcoastmodular.co.uk/products"
COLORS = ["black", "white"]
COLOR_LABELS = {"black": "", "white": " — Arctic White"}

# Font registration
FONT_PATH = Path(__file__).parent / 'AnjaEliane.ttf'
if FONT_PATH.exists():
    pdfmetrics.registerFont(TTFont('AnjaEliane', str(FONT_PATH)))

# Colors (matching eurorack_product_sheet.py exactly)
C_BLACK = colors.HexColor('#111111')
C_WHITE = colors.white
C_GRAY_MID = colors.HexColor('#888888')
C_GRAY_DARK = colors.HexColor('#555555')
C_RULE = colors.HexColor('#cccccc')
C_SPEC_BG = colors.HexColor('#f4f4f4')

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


def get_md5(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_md5_record(filepath, hash_value):
    """Save MD5 hash to .md5 file."""
    md5_file = filepath.with_suffix('.md5')
    with open(md5_file, 'w') as f:
        f.write(hash_value)


def load_md5_record(filepath):
    """Load MD5 hash from .md5 file."""
    md5_file = filepath.with_suffix('.md5')
    if md5_file.exists():
        with open(md5_file, 'r') as f:
            return f.read().strip()
    return None


def convert_tiff_to_jpg(tiff_path, jpg_path, quality=90):
    """Convert TIFF to JPG."""
    try:
        print(f"    Converting {tiff_path.name}...", end=" ")
        img = Image.open(tiff_path)
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        img.save(jpg_path, 'JPEG', quality=quality)
        print(f"✓ {jpg_path.name}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def find_product_url(module_name):
    """Search eastcoastmodular.co.uk for the product URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Try direct search
        search_url = f"https://eastcoastmodular.co.uk/products"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find product links that match the module name
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            module_lower = module_name.lower()

            if module_lower in link_text and '/products/' in href:
                return href if href.startswith('http') else f"https://eastcoastmodular.co.uk{href}"

        return None
    except Exception as e:
        print(f"    (Search failed: {e})")
        return None


def fetch_product_data(module_name):
    """Fetch product data from eastcoastmodular.co.uk."""
    try:
        # Find the correct product URL
        product_url = find_product_url(module_name)
        if not product_url:
            print(f"    ⚠ Could not find {module_name} on website")
            # Return basic data if website lookup fails
            return {
                'name': module_name.upper(),
                'type': 'Eurorack Module',
                'price': 'TBC',
                'wholesale': 'TBC',
                'description': f"{module_name} is a professional Eurorack module.",
                'hp': '8HP',
                'depth': '25mm',
                'plus12v': 'TBC',
                'minus12v': 'TBC',
            }

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract data from page
        name = module_name.upper()
        product_type = "Eurorack Module"
        price = "TBC"
        wholesale = "TBC"
        description = ""

        # Try to find product type (look in common locations)
        for selector in ['span.product-type', 'h2.product-type', '.product-subtitle', 'span[data-type]']:
            elem = soup.select_one(selector)
            if elem:
                product_type = elem.get_text(strip=True)
                break

        # Try to find price
        for selector in ['span.price', 'p.price', '[data-price]']:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                if '£' in price_text or '$' in price_text:
                    price = price_text
                    break

        # Try to find description
        for selector in ['div.product-description', 'div.description', '[data-description]']:
            elem = soup.select_one(selector)
            if elem:
                description = elem.get_text(strip=True)[:500]
                break

        return {
            'name': name,
            'type': product_type,
            'price': price,
            'wholesale': wholesale,
            'description': description or f"{name} is a professional Eurorack module.",
            'hp': '8HP',
            'depth': '25mm',
            'plus12v': 'TBC',
            'minus12v': 'TBC',
        }
    except Exception as e:
        print(f"    ⚠ Error fetching data: {e}")
        return None


def make_styles():
    """Create reportlab paragraph styles (matching eurorack_product_sheet.py)."""
    brand_font = 'AnjaEliane' if FONT_PATH.exists() else 'Helvetica-Bold'

    return {
        'header_brand': ParagraphStyle(
            'header_brand',
            fontName=brand_font, fontSize=14,
            textColor=C_WHITE, leading=17,
        ),
        'header_web': ParagraphStyle(
            'header_web',
            fontName='Helvetica', fontSize=7.5,
            textColor=colors.HexColor('#aaaaaa'),
            leading=10, alignment=TA_RIGHT,
        ),
        'product_name': ParagraphStyle(
            'product_name',
            fontName=brand_font, fontSize=36,
            textColor=C_BLACK, leading=36, spaceAfter=0,
        ),
        'product_type': ParagraphStyle(
            'product_type',
            fontName='Helvetica', fontSize=12,
            textColor=C_GRAY_MID, leading=15, spaceAfter=6*mm,
        ),
        'price_label': ParagraphStyle(
            'price_label',
            fontName=brand_font, fontSize=24,
            textColor=C_BLACK, leading=28, spaceAfter=2,
        ),
        'wholesale': ParagraphStyle(
            'wholesale',
            fontName='Helvetica', fontSize=9,
            textColor=C_GRAY_DARK, leading=12, spaceAfter=6*mm,
        ),
        'section_head': ParagraphStyle(
            'section_head',
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_GRAY_MID, leading=9,
            spaceBefore=3*mm, spaceAfter=2*mm,
            charSpace=1.8,
        ),
        'body': ParagraphStyle(
            'body',
            fontName='Helvetica', fontSize=9,
            textColor=C_BLACK, leading=13.5, spaceAfter=2*mm,
            alignment=TA_LEFT,
        ),
        'spec_label': ParagraphStyle(
            'spec_label',
            fontName='Helvetica-Bold', fontSize=8,
            textColor=C_GRAY_DARK, leading=11,
        ),
        'spec_value': ParagraphStyle(
            'spec_value',
            fontName='Helvetica', fontSize=8,
            textColor=C_BLACK, leading=11,
        ),
        'about_body': ParagraphStyle(
            'about_body',
            fontName='Helvetica', fontSize=8,
            textColor=C_GRAY_DARK, leading=12, spaceAfter=1.5*mm,
        ),
        'footer_left': ParagraphStyle(
            'footer_left',
            fontName='Helvetica', fontSize=7.5,
            textColor=C_GRAY_MID, leading=10,
        ),
        'footer_right': ParagraphStyle(
            'footer_right',
            fontName='Helvetica', fontSize=7.5,
            textColor=C_GRAY_MID, leading=10, alignment=TA_RIGHT,
        ),
    }


def generate_pdf(product_data, image_path, output_path, color_label=""):
    """Generate PDF with front image only."""
    try:
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN, bottomMargin=12*mm,
        )

        S = make_styles()
        story = []

        # Header
        hdr = Table(
            [[Paragraph('Sumthing8 Modular', S['header_brand']),
              Paragraph('sumthing8.local', S['header_web'])]],
            colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45],
        )
        hdr.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C_BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(hdr)
        story.append(Spacer(1, 5*mm))

        # Product image
        try:
            img = RLImage(str(image_path), width=65*mm, height=65*mm, kind='proportional')
        except:
            img = None

        # Product info
        name_block = [
            Paragraph(product_data['name'], S['product_name']),
            Paragraph(product_data['type'] + color_label, S['product_type']),
            Paragraph(f"RRP {product_data['price']}", S['price_label']),
            Paragraph(f"Wholesale {product_data['wholesale']}", S['wholesale']),
        ]

        if img:
            top_row = Table(
                [[name_block, img]],
                colWidths=[CONTENT_W - 70*mm, 70*mm],
            )
            top_row.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (0, 0), (0, 0), 0),
                ('TOPPADDING', (0, 0), (0, 0), 0),
                ('BOTTOMPADDING', (0, 0), (0, 0), 0),
                ('LEFTPADDING', (1, 0), (1, 0), 8*mm),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ]))
            story.append(top_row)
        else:
            for el in name_block:
                story.append(el)

        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                                 color=C_RULE, spaceAfter=3*mm))

        # Description
        story.append(Paragraph(product_data['description'], S['body']))
        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                                 color=C_RULE, spaceAfter=1*mm))

        # Specs
        story.append(Paragraph('SPECIFICATIONS', S['section_head']))

        spec_rows = [
            ('Format', 'Eurorack'),
            ('Width', product_data['hp']),
            ('Depth', product_data['depth']),
            ('+12V Current', product_data['plus12v']),
            ('-12V Current', product_data['minus12v']),
        ]

        tbl_data = [
            [Paragraph(lbl, S['spec_label']), Paragraph(val, S['spec_value'])]
            for lbl, val in spec_rows
        ]
        spec_tbl = Table(tbl_data, colWidths=[48*mm, CONTENT_W - 48*mm])
        spec_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [C_WHITE, C_SPEC_BG]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.25, C_RULE),
        ]))
        story.append(spec_tbl)

        story.append(Spacer(1, 3*mm))
        story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                                 color=C_RULE, spaceAfter=1*mm))

        # Footer
        footer = Table(
            [[Paragraph('sumthing8.local', S['footer_left']),
              Paragraph('Handmade Eurorack', S['footer_right'])]],
            colWidths=[CONTENT_W / 2, CONTENT_W / 2],
        )
        footer.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, C_RULE),
        ]))
        story.append(footer)

        doc.build(story)
        return True
    except Exception as e:
        print(f"  ✗ Error generating PDF: {e}")
        return False


def housekeep():
    """Main housekeeping function."""
    print(f"\n{'='*60}")
    print(f"Repository Housekeeping - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if not FILES_DIR.exists():
        print(f"✗ Files directory not found: {FILES_DIR}")
        return

    stats = {'updated': 0, 'skipped': 0, 'errors': 0}

    # Scan all module folders
    for module_folder in sorted(FILES_DIR.iterdir()):
        if not module_folder.is_dir() or module_folder.name.startswith('.'):
            continue

        module_name = module_folder.name
        print(f"\n📦 {module_name}")

        # Find TIFF files with flexible naming (case-insensitive)
        front_tiff = None
        back_tiff = None

        for file in module_folder.iterdir():
            if not file.is_file():
                continue
            name_lower = file.name.lower()
            if name_lower.endswith('.tiff') or name_lower.endswith('.tif'):
                if 'front' in name_lower:
                    front_tiff = file
                if 'back' in name_lower:
                    back_tiff = file

        # Skip if no front TIFF
        if not front_tiff:
            print(f"  ⊘ No front TIFF found, skipping")
            stats['skipped'] += 1
            continue

        print(f"  🎨 Processing:", end=" ")

        # Check MD5 hash
        current_hash = get_md5(front_tiff)
        stored_hash = load_md5_record(front_tiff)

        # Determine if we need to regenerate
        need_regen = current_hash != stored_hash

        # Create output JPG paths (use TIFF stem directly)
        front_jpg = module_folder / f"{front_tiff.stem}.jpg"
        back_jpg = module_folder / f"{back_tiff.stem}.jpg" if back_tiff else None

        # Check if we need to regenerate JPGs (based on TIFF change)
        if not need_regen:
            print("✓ JPEGs up to date")
            continue

        # Convert TIFFs to JPGs
        if not convert_tiff_to_jpg(front_tiff, front_jpg):
            stats['errors'] += 1
            continue

        if back_tiff:
            convert_tiff_to_jpg(back_tiff, back_jpg)

        # Save MD5 record
        save_md5_record(front_tiff, current_hash)
        print(f"✓ JPEGs updated")
        stats['updated'] += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {stats['updated']} updated, {stats['skipped']} skipped, {stats['errors']} errors")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    housekeep()
