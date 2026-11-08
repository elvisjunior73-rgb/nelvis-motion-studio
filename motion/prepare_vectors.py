"""Generate portable SVG and Lottie sources for the motion package."""
import json
from pathlib import Path

assets = Path(__file__).resolve().parent / "assets"
assets.joinpath("volt.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
<path fill="#dcfa4c" d="M38 132h67l52 92L298 74h68L145 319z"/>
<path fill="#dcfa4c" d="M203 280h147v24H180z"/>
</svg>""")

def prop(value):
    return {"a": 0, "k": value}

frames = [{"t":0,"s":[64,140,0],"o":{"x":[.2],"y":[.2]},"i":{"x":[.6],"y":[1]}},
          {"t":12,"s":[172,108,0],"o":{"x":[.4],"y":[0]},"i":{"x":[.6],"y":[1]}},
          {"t":35,"s":[270,80,0]}]
shape = {"ty":"el","nm":"Orbit","p":prop([0,0]),"s":prop([130,130])}
stroke = {"ty":"st","nm":"Acid","c":prop([.83,1,.21,1]),"o":prop(100),"w":prop(5),"lc":2,"lj":2}
layer = {"ddd":0,"ind":1,"ty":4,"nm":"Orbit","sr":1,"ip":0,"op":36,"st":0,"bm":0,
         "ks":{"o":prop(100),"r":prop(0),"p":{"a":1,"k":frames},"a":prop([0,0,0]),"s":prop([100,100,100])},
         "shapes":[shape,stroke]}
data = {"v":"5.7.4","fr":30,"ip":0,"op":36,"w":360,"h":240,"nm":"VOLT Orbit","ddd":0,"assets":[],"layers":[layer]}
assets.joinpath("orbit.json").write_text(json.dumps(data, indent=2))
