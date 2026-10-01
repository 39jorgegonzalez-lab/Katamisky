#!/usr/bin/env python3
"""Recreate the original typographic social card; never a historical image.

Optional asset-authoring dependencies: Pillow and fontTools with Brotli support.
The normal website build uses the committed PNG and needs Python stdlib only.
"""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parents[1]
def font(filename, size):
    face = TTFont(root/'assets/fonts'/filename)
    face.flavor = None
    data = BytesIO(); face.save(data); data.seek(0)
    return ImageFont.truetype(data, size)

image = Image.new('RGB', (1200,630), '#f8f5f1')
draw = ImageDraw.Draw(image)
draw.rectangle((30,30,1170,600), outline='#dfd2c2', width=2)
draw.rectangle((70,70,1130,560), fill='#f6eddf')
draw.line((170,195,1030,195), fill='#b98a52', width=2)
draw.text((600,290), 'KATAMISKY', font=font('playfair-display-normal-500.woff2',92), fill='#34271f', anchor='mm')
draw.text((600,375), 'A Serialized Illustrated Memoir', font=font('source-serif-4-normal-400.woff2',34), fill='#34271f', anchor='mm')
draw.text((600,440), 'By Henry', font=font('inter-normal-400.woff2',23), fill='#756457', anchor='mm')
draw.line((170,490,1030,490), fill='#b98a52', width=2)
image.save(root/'assets/images/site/katamisky-share.png', optimize=True)
