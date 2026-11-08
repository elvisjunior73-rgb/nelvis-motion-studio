"""Run an explicitly selected Auto-Sub CLI and return its generated SRT."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("media", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--language", default="fr")
parser.add_argument("--binary", default="autosub")
options = parser.parse_args()
if options.output.suffix.lower() != ".srt":
    parser.error("La sortie doit porter l’extension .srt.")
options.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [options.binary, "-S", options.language, "-D", options.language, "-F", "srt",
     "-o", str(options.output.resolve()), str(options.media.resolve())],
    check=True,
)
if not options.output.is_file() or not options.output.stat().st_size:
    raise RuntimeError("Auto-Sub n’a pas produit de fichier SRT.")
