"""Run with GIMP 3's python-fu-eval interpreter to create the layered artwork."""
import os
from pathlib import Path

from gi.repository import Gimp, Gio

assets = Path(os.environ["NELVIS_ASSETS"])
image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE,Gio.File.new_for_path(str(assets/"hero.png")))
image.get_layers()[0].set_name("Blender | VOLT RIFT 01")
logo = Gimp.file_load_layer(Gimp.RunMode.NONINTERACTIVE,image,Gio.File.new_for_path(str(assets/"volt.png")))
image.insert_layer(logo,None,0)
logo.set_name("Inkscape | VOLT mark")
logo.scale(105,105,False)
logo.set_offsets(58,35)
result = Gimp.file_save(Gimp.RunMode.NONINTERACTIVE,image,Gio.File.new_for_path(str(assets/"VOLT_artwork.xcf")))
if not result:
    raise RuntimeError("GIMP XCF export failed")
