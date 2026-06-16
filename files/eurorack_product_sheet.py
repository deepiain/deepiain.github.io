#!/Users/iain/Documents/Claude/Projects/Sumthing8/venv/bin/python3
"""Generate Eurorack module product PDFs — one per product."""

import os
import urllib.request
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Font registration
FONT_PATH = os.path.join(os.path.dirname(__file__), 'AnjaEliane.ttf')
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('AnjaEliane', FONT_PATH))

# Palette
C_BLACK      = colors.HexColor('#111111')
C_WHITE      = colors.white
C_OFFWHITE   = colors.HexColor('#fafafa')
C_GRAY_DARK  = colors.HexColor('#555555')
C_GRAY_MID   = colors.HexColor('#888888')
C_GRAY_LIGHT = colors.HexColor('#dddddd')
C_RULE       = colors.HexColor('#cccccc')
C_SPEC_BG    = colors.HexColor('#f4f4f4')

PAGE_W, PAGE_H = A4
MARGIN     = 14 * mm
CONTENT_W  = PAGE_W - 2 * MARGIN


def make_styles():
    brand_font = 'AnjaEliane' if os.path.exists(FONT_PATH) else 'Helvetica-Bold'

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
        'feature': ParagraphStyle(
            'feature',
            fontName='Helvetica', fontSize=8.5,
            textColor=C_BLACK, leading=12,
            leftIndent=2, spaceAfter=1.5*mm,
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


def fetch_image(url, max_w, max_h):
    if not url:
        return None
    try:
        if url.startswith('/'):
            img = Image(url, width=max_w, height=max_h, kind='proportional')
        else:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = r.read()
            img = Image(BytesIO(data), width=max_w, height=max_h, kind='proportional')
        return img
    except Exception as e:
        print(f"  Warning: Could not load image {url}: {e}")
        return None


def build_pdf(product, styles, output_dir='.'):
    slug = product['slug']
    # Convert slug to PascalCase: CLOUDS_STANDARD → CloudsStandard
    pdf_name = ''.join(word.capitalize() for word in slug.split('_'))
    path = os.path.join(output_dir, f"{pdf_name}.pdf")

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=12*mm,
    )

    S = styles
    story = []

    # Header bar
    hdr = Table(
        [[Paragraph('Sumthing8 Modular', S['header_brand']),
          Paragraph('sumthing8.local', S['header_web'])]],
        colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45],
    )
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), C_BLACK),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6*mm),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6*mm),
        ('TOPPADDING',    (0, 0), (-1, -1), 5*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
        ('ALIGN',         (1, 0), (1, 0),   'RIGHT'),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 5*mm))

    # Product name and image
    img = fetch_image(product.get('image_url'), 65*mm, 65*mm)

    name_block = [
        Paragraph(product['name'],  S['product_name']),
        Paragraph(product['type'],  S['product_type']),
        Paragraph(f"RRP {product['price']}", S['price_label']),
        Paragraph(f"Wholesale {product.get('wholesale', 'TBC')}", S['wholesale']),
    ]

    if img:
        top_row = Table(
            [[name_block, img]],
            colWidths=[CONTENT_W - 70*mm, 70*mm],
        )
        top_row.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',   (0, 0), (0, 0), 0),
            ('RIGHTPADDING',  (0, 0), (0, 0), 0),
            ('TOPPADDING',    (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0),
            ('LEFTPADDING',   (1, 0), (1, 0), 8*mm),
            ('RIGHTPADDING',  (1, 0), (1, 0), 0),
            ('ALIGN',         (1, 0), (1, 0),   'CENTER'),
        ]))
        story.append(top_row)
    else:
        for el in name_block:
            story.append(el)

    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                             color=C_RULE, spaceAfter=3*mm))

    # Description
    story.append(Paragraph(product['description'], S['body']))

    # Features
    story.append(Paragraph('FEATURES', S['section_head']))
    for feat in product['features']:
        story.append(Paragraph(f'— {feat}', S['feature']))

    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                             color=C_RULE, spaceAfter=1*mm))

    # Specifications
    story.append(Paragraph('SPECIFICATIONS', S['section_head']))

    spec_rows = [
        ('Format',         'Eurorack'),
        ('Width',          product['hp']),
        ('Depth',          product['depth']),
        ('+12V Current',   product['plus12v']),
        ('-12V Current',   product['minus12v']),
    ]
    if product.get('plus5v'):
        spec_rows.append(('+5V Current', product['plus5v']))

    tbl_data = [
        [Paragraph(lbl, S['spec_label']), Paragraph(val, S['spec_value'])]
        for lbl, val in spec_rows
    ]
    spec_tbl = Table(tbl_data, colWidths=[48*mm, CONTENT_W - 48*mm])
    spec_tbl.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4*mm),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4*mm),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS',(0, 0), (-1, -1), [C_WHITE, C_SPEC_BG]),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.25, C_RULE),
    ]))
    story.append(spec_tbl)

    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                             color=C_RULE, spaceAfter=1*mm))

    # Stocking & Availability
    story.append(Paragraph('STOCKING &amp; AVAILABILITY', S['section_head']))
    story.append(Paragraph(
        product.get('about', 'Factory assembled PCB &amp; SMT, THT hand finished and tested. '
        'Brand New. Ships tracked and insured. Enquiries: <b>sumthing8.local</b>'),
        S['about_body']
    ))

    story.append(Spacer(1, 2*mm))

    # Footer
    footer = Table(
        [[Paragraph('sumthing8.local', S['footer_left']),
          Paragraph('Handmade Eurorack', S['footer_right'])]],
        colWidths=[CONTENT_W / 2, CONTENT_W / 2],
    )
    footer.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LINEABOVE',     (0, 0), (-1, -1), 0.5, C_RULE),
    ]))
    story.append(footer)

    doc.build(story)
    print(f"  ✓  {path}")
    return path


PRODUCTS = [
    {
        'slug': 'MONSOON',
        'name': 'MONSOON',
        'type': 'Granular Texture Synthesizer',
        'price': '£189',
        'wholesale': '£105',
        'hp': '18HP',
        'depth': '25mm',
        'plus12v': '120mA',
        'minus12v': '10mA',
        'image_url': None,
        'description': (
            'Monsoon is a granular texture synthesizer that captures and transforms audio '
            'into shimmering clouds of sound. Feed it anything — a drone, a voice, a drum hit '
            '— and it returns lush, evolving textures. Granular reverb, pitch shifting, '
            'time stretching, or abstract texture generation.'
        ),
        'features': [
            'Real-time granular processing with multiple simultaneous grains',
            'Position, Size, Pitch, Density and Texture controls',
            'Stereo in and out with blend control',
            'Freeze input for capturing and looping grains indefinitely',
            'Multiple alternate firmware modes available',
        ],
        'about': 'Factory assembled PCB &amp; SMT, THT hand finished and tested. Brand New. Ships tracked and insured. Enquiries: <b>sumthing8.local</b>',
    },
    {
        'slug': 'CLOUDS_STANDARD',
        'name': 'CLOUDS',
        'type': 'Granular Texture Synthesizer',
        'price': '£169',
        'wholesale': '£95',
        'hp': '18HP',
        'depth': '25mm',
        'plus12v': '120mA',
        'minus12v': '10mA',
        'image_url': None,
        'description': (
            'Clouds is a granular texture synthesizer inspired by Mutable Instruments\' '
            'legendary design. Capture, freeze, and reshape audio into evolving textures — '
            'from ethereal ambience to dense, saturated soundscapes.'
        ),
        'features': [
            'Real-time granular processing with up to 8 simultaneous grains',
            'Position, Size, Pitch, Density and Texture controls',
            'Stereo in and out with blend control',
            'Freeze input to capture and loop audio indefinitely',
            'Multiple firmware variants available',
        ],
        'about': 'Factory assembled PCB &amp; SMT, THT hand finished and tested. Brand New. Ships tracked and insured. Enquiries: <b>sumthing8.local</b>',
    },
    {
        'slug': 'CLOUDS_ARCTIC_WHITE',
        'name': 'CLOUDS',
        'type': 'Granular Texture Synthesizer — Arctic White',
        'price': '£169',
        'wholesale': '£95',
        'hp': '18HP',
        'depth': '25mm',
        'plus12v': '120mA',
        'minus12v': '10mA',
        'image_url': None,
        'description': (
            'Clouds is a granular texture synthesizer inspired by Mutable Instruments\' '
            'legendary design. Capture, freeze, and reshape audio into evolving textures — '
            'from ethereal ambience to dense, saturated soundscapes. Arctic White panel edition.'
        ),
        'features': [
            'Real-time granular processing with up to 8 simultaneous grains',
            'Position, Size, Pitch, Density and Texture controls',
            'Stereo in and out with blend control',
            'Freeze input to capture and loop audio indefinitely',
            'Multiple firmware variants available',
        ],
        'about': 'Factory assembled PCB &amp; SMT, THT hand finished and tested. Brand New. Ships tracked and insured. Enquiries: <b>sumthing8.local</b>',
    },
]


if __name__ == '__main__':
    output_dir = '.'
    styles = make_styles()
    print(f"\nGenerating {len(PRODUCTS)} Eurorack product PDFs...\n")
    files = []
    for p in PRODUCTS:
        files.append(build_pdf(p, styles, output_dir))
    print(f"\nDone — {len(files)} PDFs written to {output_dir}\n")
