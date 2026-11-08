"""Verify a finished NELVIS master and fully decode its streams."""
import argparse
import json
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("video")
parser.add_argument("width", type=int)
parser.add_argument("height", type=int)
options = parser.parse_args()
details = json.loads(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", options.video]
))
video = next(s for s in details["streams"] if s["codec_type"] == "video")
audio = next(s for s in details["streams"] if s["codec_type"] == "audio")
assert (video["width"], video["height"]) == (options.width, options.height), video
assert (video["codec_name"], video["r_frame_rate"], int(video["nb_frames"])) == ("h264", "30/1", 360), video
assert audio["codec_name"] == "aac", audio
assert abs(float(details["format"]["duration"]) - 12) < .05, details["format"]
subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", options.video, "-f", "null", "-"], check=True)
print(json.dumps({
    "width": options.width, "height": options.height, "frames": 360,
    "video": video["codec_name"], "audio": audio["codec_name"],
    "duration": details["format"]["duration"],
}))
