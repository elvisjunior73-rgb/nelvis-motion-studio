#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

brief=${1:-examples/volt.json}
format=${2:-both}
variant=${3:-full}
output="$PWD/output"
mkdir -p "$output"
case "$format" in both|9:16|16:9) ;; *) echo "Format inconnu." >&2; exit 2 ;; esac
case "$variant" in full|core) ;; *) echo "Variante inconnue." >&2; exit 2 ;; esac
brief=$(realpath -- "$brief")
case "$brief" in "$PWD"/*.json) ;; *) echo "Placez le brief JSON dans motion/." >&2; exit 2 ;; esac
test -f "$brief"
bash bootstrap.sh

# A custom brief can provide its own narration or captions beside the JSON.
voice="${brief%.json}.wav"
captions="${brief%.json}.ass"
if [[ ! -s "$captions" && -s "${brief%.json}.srt" ]]; then captions="${brief%.json}.srt"; fi
if [[ "$brief" == "$PWD/examples/volt.json" && "$variant" == full ]]; then
  voice="$output/VOLT-voix.wav"
  espeak-ng -v fr-fr -s 154 -w "$voice" 'Prends ton élan. Découvre Volt Rift. À toi la rue.'
fi

if [[ "$variant" == full ]]; then
  python artwork.py
  NELVIS_ASSETS="$PWD/assets" NELVIS_GIMP_SCRIPT="$PWD/gimp_project.py" \
    gimp-console -n -idf --batch-interpreter=python-fu-eval \
    -b 'import os; exec(open(os.environ["NELVIS_GIMP_SCRIPT"]).read())' --quit
  xvfb-run -a krita assets/VOLT.ora --export --export-filename "$PWD/assets/VOLT-krita.png"
  test -s assets/VOLT_artwork.xcf
  test -s assets/VOLT-krita.png
  if [[ -n "${NELVIS_NATRON:-}" ]]; then
    NELVIS_NATRON_SOURCE="$PWD/assets/detail.png" NELVIS_NATRON_OUTPUT="$PWD/assets/detail-natron.png" \
      xvfb-run -a "$NELVIS_NATRON" "$PWD/natron_project.py" -w WriteNelvis "$PWD/assets/detail-natron.png" 1-1
    test -s assets/detail-natron.png
    if [[ "$brief" == "$PWD/examples/volt.json" ]]; then
      cp assets/detail-natron.png assets/detail.png
    fi
  fi
  if [[ -s "$voice" ]]; then
    python autosub_import.py "$voice" "$output/autosub"
  fi
  cp assets/{VOLT.ora,VOLT-krita.png,VOLT_artwork.xcf} "$output/"
  if [[ -s assets/detail-natron.png ]]; then cp assets/detail-natron.png "$output/"; fi
fi

for size in 9:16 16:9; do
  if [[ "$format" != both && "$format" != "$size" ]]; then continue; fi
  args=()
  suffix=9x16
  width=1080
  height=1920
  if [[ "$size" == 16:9 ]]; then
    suffix=16x9
    width=1920
    height=1080
  fi
  if [[ -s "$voice" ]]; then args+=(--voice "$voice" --whisper-model tiny); fi
  if [[ -s "$captions" ]]; then args+=(--captions "$captions"); fi
  if [[ "$variant" == full && "$brief" == "$PWD/examples/volt.json" ]]; then
    composition=NelvisTitre
    if [[ "$size" == 16:9 ]]; then composition=NelvisTitreHorizontal; fi
    (cd remotion && npx --no-install remotion render index.jsx "$composition" "$output/carton-$suffix.mp4" --concurrency=2)
    args+=(--end-card "$output/carton-$suffix.mp4")
  fi
  target="$output/NELVIS-$suffix.mp4"
  python render.py "$brief" --format "$size" -o "$target" "${args[@]}"
  python probe.py "$target" "$width" "$height" | tee "$output/NELVIS-$suffix-qc.json"
  if [[ -s "$output/NELVIS-$suffix.srt" && -n "${NELVIS_SECONV:-}" ]]; then
    "$NELVIS_SECONV" "$output/NELVIS-$suffix.srt" webvtt \
      "--output-folder:$output" --overwrite
    test -s "$output/NELVIS-$suffix.vtt"
  fi
  python montage/prepare_mlt.py "$target" "$output/montage-$suffix"
  (cd "$output/montage-$suffix" && melt VOLT.mlt -consumer "avformat:$output/MLT-$suffix.mp4" \
    vcodec=libx264 acodec=aac real_time=-1 terminate_on_pause=1)
  python probe.py "$output/MLT-$suffix.mp4" "$width" "$height"
done
cp assets/{VOLT.blend,volt.svg,orbit.json} "$output/"
