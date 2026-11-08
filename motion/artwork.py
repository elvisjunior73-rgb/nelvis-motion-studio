"""Write a portable layered OpenRaster project for Krita."""
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile, ZIP_STORED

from PIL import Image

assets = Path(__file__).resolve().parent / "assets"
shoe = Image.open(assets / "hero.png").convert("RGBA")
logo = Image.open(assets / "volt.png").convert("RGBA").resize((105, 105))
merged = shoe.copy()
merged.alpha_composite(logo, (58, 35))
root = ElementTree.Element("image", w=str(shoe.width), h=str(shoe.height), name="VOLT")
stack = ElementTree.SubElement(root, "stack")
layers = [
    ("Logo Inkscape", "data/logo.png", 58, 35, logo),
    ("Produit Blender", "data/produit.png", 0, 0, shoe),
]
with ZipFile(assets / "VOLT.ora", "w") as archive:
    archive.writestr("mimetype", "image/openraster", compress_type=ZIP_STORED)
    for name, path, x, y, image in layers:
        ElementTree.SubElement(stack, "layer", {
            "name": name, "src": path, "x": str(x), "y": str(y), "opacity": "1.0",
            "visibility": "visible", "composite-op": "svg:src-over",
        })
        content = BytesIO()
        image.save(content, format="PNG")
        archive.writestr(path, content.getvalue())
    archive.writestr("stack.xml", ElementTree.tostring(root, encoding="utf-8"))
    content = BytesIO()
    merged.save(content, format="PNG")
    archive.writestr("mergedimage.png", content.getvalue())
