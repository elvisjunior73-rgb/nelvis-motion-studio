"""Transcribe a narration to SRT with the pinned Whisper-based AutoSub CLI."""
import argparse
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("media", type=Path)
parser.add_argument("output_dir", type=Path)
parser.add_argument("--language", default="auto")
parser.add_argument("--model", default="tiny")
options = parser.parse_args()
options.output_dir.mkdir(parents=True, exist_ok=True)
cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "whisper"
subprocess.run([
    "autosub", "--cpu", "--overwrite", "--model", options.model,
    "--language", options.language, "--output-dir", str(options.output_dir.resolve()),
    "--whisper-root", str(cache),
    str(options.media.resolve()),
], check=True)
generated = options.output_dir / f"{options.media.stem}.srt"
if not generated.is_file() or not generated.stat().st_size:
    raise RuntimeError("AutoSub n’a pas produit de fichier SRT.")
print(generated)
