"""Split a completed VOLT-style master into editable shots and an MLT playlist."""
import subprocess
import sys

import opentimelineio as otio
from pathlib import Path
from xml.etree import ElementTree as XML

root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent
root.mkdir(parents=True, exist_ok=True)
source = Path(sys.argv[1]).resolve()
dimensions = subprocess.check_output(
    ["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height",
     "-of","csv=p=0:s=x",str(source)],text=True
).strip().split("x")
width,height = dimensions
mlt = XML.Element("mlt",producer="main",version="7.30.0")
XML.SubElement(mlt,"profile",description="NELVIS 30p",width=width,height=height,
               progressive="1",frame_rate_num="30",frame_rate_den="1",sample_aspect_num="1",
               sample_aspect_den="1",display_aspect_num="9" if int(width)<int(height) else "16",
               display_aspect_den="16" if int(width)<int(height) else "9",colorspace="709")
for index in range(4):
    name = f"{index+1:02d}.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(index*3),"-i",str(source),"-t","3",
                    "-c:v","libx264","-crf","17","-threads","3","-preset","veryfast","-c:a","aac",
                    "-b:a","192k",str(root/name)],check=True)
    node = XML.SubElement(mlt,"chain",id=f"shot{index}",out="89")
    XML.SubElement(node,"property",name="resource").text = name
    XML.SubElement(node,"property",name="mlt_service").text = "avformat"
playlist = XML.SubElement(mlt,"playlist",id="main")
for index in range(4):
    XML.SubElement(playlist,"entry",{"producer":f"shot{index}","in":"0","out":"89"})
XML.indent(mlt)
XML.ElementTree(mlt).write(root/"VOLT.mlt",encoding="UTF-8",xml_declaration=True)

timeline = otio.schema.Timeline(name="NELVIS — quatre plans")
for kind in (otio.schema.TrackKind.Video, otio.schema.TrackKind.Audio):
    track = otio.schema.Track(name=kind, kind=kind)
    for index in range(4):
        shot = f"{index + 1:02d}.mp4"
        time_range = otio.opentime.TimeRange(
            otio.opentime.RationalTime(0, 30), otio.opentime.RationalTime(90, 30)
        )
        track.append(otio.schema.Clip(
            name=shot,
            media_reference=otio.schema.ExternalReference(target_url=shot, available_range=time_range),
            source_range=time_range,
        ))
    timeline.tracks.append(track)
otio.adapters.write_to_file(timeline, str(root / "VOLT.otio"))
check = otio.adapters.read_from_file(str(root / "VOLT.otio"))
assert len(check.tracks) == 2 and all(len(track) == 4 for track in check.tracks)
