#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

mkdir -p assets/{fonts,orbit}
for file in LiberationSans-Bold LiberationSans-BoldItalic LiberationMono-Bold; do
  location=$(find /usr/share/fonts/truetype -name "$file.ttf" -print -quit)
  cp "$location" assets/fonts/
done
if [[ -f /usr/share/doc/fonts-liberation/copyright ]]; then
  cp /usr/share/doc/fonts-liberation/copyright assets/fonts/LICENSE.txt
fi
blender -b -t 4 --python-exit-code 1 --python blender_shoe.py -- "$PWD/assets" --orbit
python prepare_vectors.py
inkscape assets/volt.svg --export-filename=assets/volt.png --export-width=360

# MLT's Glaxnimate module requires a display even when exporting offline.
xvfb-run -a melt -profile atsc_720p_30 glaxnimate:assets/orbit.json in=0 out=35 \
  -consumer avformat:assets/orbit-preview.mp4 vcodec=libx264 pix_fmt=yuv420p an=1 real_time=-1 terminate_on_pause=1
ffmpeg -v error -y -i assets/orbit-preview.mp4 -vf 'crop=1080:720,scale=360:240' assets/orbit/%02d.png
test -s assets/orbit/36.png
