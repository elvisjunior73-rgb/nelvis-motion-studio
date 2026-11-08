"""Render an original product teaser from three visuals and a JSON brief."""
import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FPS = 30
DURATION = 12
CUTS = (0, 3, 6, 9, 12)
PALE = (238, 242, 247)
INK = (10, 19, 34)
FONT_DIR = ASSETS / "fonts"

def execute(args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or str(args[0]))
    return result.stdout

def checked_brief(raw):
    brief = dict(raw)
    for key, limit in (("brand", 18), ("model", 22), ("tagline", 36)):
        value = brief.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"{key} doit contenir de 1 à {limit} caractères.")
        brief[key] = value.strip()
    for key in ("hook", "detail"):
        lines = brief.get(key)
        if not isinstance(lines, list) or not 1 <= len(lines) <= 2 or any(
            not isinstance(line, str) or not line.strip() or len(line) > 24 for line in lines
        ):
            raise ValueError(f"{key} doit contenir une ou deux lignes de 24 caractères maximum.")
    if brief.get("format") not in ("9:16", "16:9"):
        raise ValueError("Formats acceptés : 9:16 et 16:9.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(brief.get("accent", ""))):
        raise ValueError("La couleur doit être au format #RRGGBB.")
    if not isinstance(brief.get("images"), list) or len(brief["images"]) != 3:
        raise ValueError("Il faut exactement trois visuels.")
    return brief

@lru_cache(maxsize=128)
def font(size, variant="bold"):
    names = {"bold":"LiberationSans-Bold.ttf","italic":"LiberationSans-BoldItalic.ttf",
             "mono":"LiberationMono-Bold.ttf"}
    return ImageFont.truetype(str(FONT_DIR / names[variant]), size)

def label(draw, xy, text, size, color, width, variant="bold", anchor="lt", stroke=0):
    face = font(size, variant)
    while draw.textlength(text, font=face) > width and size > 8:
        size -= 1
        face = font(size, variant)
    draw.text(xy, text, font=face, fill=color, anchor=anchor, stroke_width=stroke,
              stroke_fill=PALE)

def interpolate(value):
    value = min(1, max(0, value))
    return 1-(1-value)**3

def load_image(path):
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")
    image.thumbnail((1500, 1500), Image.Resampling.LANCZOS)
    return image

def trim(image):
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError("Un des visuels est entièrement transparent.")
    return image.crop(bounds)

class Spot:
    def __init__(self, brief):
        self.brief = brief
        self.vertical = brief["format"] == "9:16"
        self.width, self.height = (720,1280) if self.vertical else (1280,720)
        self.accent = ImageColor.getrgb(brief["accent"])
        self.products = [trim(load_image(path)) for path in brief["images"]]
        self.turn = []
        self.orbits = []
        self.logo = None
        if brief.get("demo_orbit"):
            self.logo = load_image(ASSETS/"volt.png").resize((62,62))
        turn_dir = brief.get("turn_frames") or (ASSETS/"turn" if brief.get("demo_orbit") else None)
        if turn_dir:
            paths = sorted(Path(turn_dir).glob("*.png"))
            if not 1 <= len(paths) <= 120:
                raise ValueError("La séquence 3D doit contenir entre 1 et 120 PNG.")
            self.turn = [load_image(path) for path in paths]
            if len({image.size for image in self.turn}) != 1:
                raise ValueError("Les images de la séquence doivent avoir les mêmes dimensions.")
            bounds = [frame.getchannel("A").getbbox() for frame in self.turn]
            bounds = [box for box in bounds if box]
            if not bounds:
                raise ValueError("La séquence 3D est transparente.")
            union = (min(b[0] for b in bounds),min(b[1] for b in bounds),
                     max(b[2] for b in bounds),max(b[3] for b in bounds))
            self.turn = [frame.crop(union) for frame in self.turn]
        overlay_dir = brief.get("vector_frames") or (ASSETS/"orbit" if brief.get("demo_orbit") else None)
        if overlay_dir:
            paths = sorted(Path(overlay_dir).glob("*.png"))
            if not 1 <= len(paths) <= 120:
                raise ValueError("L’animation vectorielle doit contenir entre 1 et 120 PNG.")
            for path in paths:
                layer = np.array(load_image(path))
                if not brief.get("vector_frames"):
                    layer[:,:,3] = np.clip(layer[:,:,1].astype(float)*.55-6,0,255).astype("uint8")
                self.orbits.append(Image.fromarray(layer))
        self.backgrounds = [self.background(i) for i in range(4)]

    def background(self, index):
        width,height = self.width,self.height
        y,x = np.mgrid[:height,:width].astype("float32")
        x /= width
        y /= height
        halo = np.exp(-((x-.61)**2*5+(y-.43)**2*8))
        noise = np.random.default_rng(35+index).normal(0,1.35,(height,width))
        base = self.accent if index == 1 else (8,14,28)
        light = (-34,-34,-23) if index == 1 else (19,37,63)
        pixels = np.stack([base[i] + halo*light[i] + noise for i in range(3)],axis=2)
        frame = Image.fromarray(np.clip(pixels,0,255).astype("uint8")).convert("RGBA")
        draw = ImageDraw.Draw(frame)
        low = (160,183,48) if index == 1 else (34,51,72)
        if index != 3:
            for k in range(-3,10):
                x0 = k*width//7
                draw.line((x0,height,x0+height//2,0), fill=low, width=1)
        for k in range(12):
            y0 = int((.22 + k*.047)*height)
            draw.line((24,y0,34 if k%3 else 44,y0),fill=low,width=2)
        return frame

    def product(self, frame, image, center, width, height, angle=0):
        ratio = min(width/image.width,height/image.height)
        image = image.resize((round(image.width*ratio),round(image.height*ratio)), Image.Resampling.BICUBIC)
        if angle:
            image = image.rotate(angle,Image.Resampling.BICUBIC,expand=True)
        frame.alpha_composite(image,(round(center[0]-image.width/2),round(center[1]-image.height/2)))

    def frame(self, number):
        time = number / FPS
        i = min(3, int(time//3))
        local = time - CUTS[i]
        p = local/3
        entry = interpolate(local/.44)
        width,height = self.width,self.height
        accent = self.accent
        brand,model = self.brief["brand"],self.brief["model"]
        frame = self.backgrounds[i].copy()
        draw = ImageDraw.Draw(frame)
        x = 58 if self.vertical else 79
        y = 145 if self.vertical else 88
        text_width = width-2*x-30 if self.vertical else 490
        brightness = sum(channel * weight for channel,weight in zip(accent,(.2126,.7152,.0722)))
        figure_color = (INK if brightness >= 145 else PALE) if i == 1 else PALE
        mark_color = figure_color if i == 1 else (accent if brightness >= 110 else PALE)
        if self.logo and i != 1:
            frame.alpha_composite(self.logo,(x-9,y-20))
            micro_x = x+54
        else:
            micro_x = x
        label(draw,(micro_x,y),f"{brand}  /  {model}",23,figure_color,text_width,"mono")
        if i == 0:
            lines = self.brief["hook"]
            image = self.products[0]
        elif i == 1:
            lines = [model]
            image = self.turn[min(len(self.turn)-1,round(p*(len(self.turn)-1)))] if self.turn else self.products[1]
        elif i == 2:
            lines = self.brief["detail"]
            image = self.products[1]
        else:
            lines = [brand]
            image = self.products[2]

        if self.vertical:
            title_y = y+110 + (1-entry)*40
            center = (width*.49 + (1-entry)*103, height*(.57 if i in (0,2) else .52))
            max_width = (660 if i != 2 else 790)*(1+.06*p)
            max_height = 445
            foot_y = 968 if i == 3 else 1004
            size = 114 if i != 3 else 161
        else:
            title_y = y+140 + (1-entry)*40
            center = (width*.68 + (1-entry)*103,height*.52)
            max_width,max_height = (780 if i == 2 else 715)*(1+.06*p),485
            foot_y = 572
            size = 100 if i != 3 else 141

        if i == 0 and self.orbits and local < 1.18:
            layer = self.orbits[min(len(self.orbits)-1,int(local*FPS))]
            layer = layer.resize((520,346),Image.Resampling.BICUBIC)
            frame.alpha_composite(layer,(round(center[0]-260),round(center[1]-180)))

        if i == 1:
            if self.vertical:
                draw.arc((64,330,width-64,954),198,350,fill=figure_color,width=3)
                draw.arc((93,361,width-93,921),12,157,fill=figure_color,width=3)
            else:
                draw.arc((470,120,1220,650),198,350,fill=figure_color,width=3)
                draw.arc((510,150,1190,610),12,157,fill=figure_color,width=3)
        if i == 2:
            cy = round(center[1])
            dx = round(center[0])
            draw.line((dx-180,cy+65,dx+200,cy-130),fill=accent,width=2)
            draw.ellipse((dx+194,cy-136,dx+206,cy-124),fill=accent)
        angle = (-6 + p*8) if i == 0 else (5-p*9 if i == 2 else 0)
        self.product(frame,image,center,max_width,max_height,angle)
        for line_index, line in enumerate(lines):
            color = mark_color if line_index == len(lines)-1 else figure_color
            label(draw,(x,round(title_y+line_index*(size*.9))),line,size,color,text_width,"italic")
        if i == 3:
            label(draw,(x,foot_y),self.brief["tagline"],48,PALE,text_width)
        else:
            kicker = ("01   /   LANCEMENT","02   /   SILHOUETTE","03   /   GROS PLAN")[i]
            label(draw,(x,foot_y),kicker,22,figure_color,text_width,"mono")
        line_y = foot_y+65
        draw.rectangle((x,line_y,x+128,line_y+4),fill=mark_color)
        for k in range(4):
            draw.rectangle((x+150+k*14,line_y-2,x+156+k*14,line_y+6),fill=mark_color if k <= i else (90,104,120))
        if i and local < .19:
            # Brief directional cut, synchronized with the sound accent.
            sweep = round(width*(1-local/.19))
            draw.polygon([(0,0),(sweep,0),(max(0,sweep-94),height),(0,height)],fill=accent)
        return frame.convert("RGB")

def sound(path):
    rate = 48000
    length = rate*DURATION
    mix = np.zeros((length,2),dtype=np.float32)
    rng = np.random.default_rng(802)
    def add(when, seconds, synth, gain, pan=0):
        start = round(when*rate)
        count = min(round(seconds*rate),length-start)
        t = np.arange(count)/rate
        signal = synth(t)*gain
        mix[start:start+count,0] += signal*(1-max(0,pan))
        mix[start:start+count,1] += signal*(1+min(0,pan))
    for beat in range(24):
        time = beat*.5
        add(time,.34,lambda t: np.sin(2*np.pi*(47*t+4.8*(1-np.exp(-23*t))))*np.exp(-13*t),.42)
        hz = (55,55,65.41,49)[beat//6]
        add(time+.055,.40,lambda t: (np.sin(2*np.pi*hz*t)+.32*np.sin(4*np.pi*hz*t))*np.exp(-7*t)*np.minimum(1,t*125),.23)
        if beat%2:
            add(time,.19,lambda t: (rng.uniform(-1,1,t.size)*.78+.22*np.sin(2*np.pi*188*t))*np.exp(-28*t),.22)
        for offset in (0,.25,.375):
            add(time+offset,.064,lambda t: rng.uniform(-1,1,t.size)*np.sin(2*np.pi*7200*t)*np.exp(-64*t),.11,(-1)**beat*.30)
    for cut in (.0,3.,6.,9.):
        add(cut,.39,lambda t: (np.sin(2*np.pi*(91*t+22*t*t))+.41*rng.uniform(-1,1,t.size))*np.exp(-13*t),.32)
    mix[-rate//5:] *= np.linspace(1,0,rate//5)[:,None]
    with wave.open(str(path),"wb") as handle:
        handle.setparams((2,2,rate,0,"NONE","not compressed"))
        handle.writeframes((np.tanh(mix*1.22)*32767).astype("<i2").tobytes())

def subtitle_files(voice, work, dimensions, model):
    if not shutil.which("whisper"):
        raise RuntimeError("Installez OpenAI Whisper et son modèle pour activer la transcription.")
    execute(["whisper", str(voice), "--model", model, "--word_timestamps","True",
             "--output_dir",str(work),"--output_format","json","--fp16","False"])
    data = json.loads((work / (voice.stem+".json")).read_text(encoding="utf-8"))
    words = [word for segment in data["segments"] for word in segment.get("words",[])
             if float(word["start"]) < DURATION]
    if not words:
        return None,None
    chunks = [words[i:i+4] for i in range(0,len(words),4)]
    def stamp(value, ass):
        units = 100 if ass else 1000
        seconds, fraction = divmod(round(float(value)*units),units)
        minute,second = divmod(seconds,60)
        return f"0:{minute:02}:{second:02}.{fraction:02}" if ass else f"00:{minute:02}:{second:02},{fraction:03}"
    width,height = dimensions
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Spot,Liberation Sans,42,&H004CFADC,&H00FFFFFF,&H00100C08,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,50,50,{height//7},1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass,srt = [],[]
    for index,chunk in enumerate(chunks,1):
        start = float(chunk[0]["start"])
        end = min(DURATION,float(chunk[-1]["end"]))
        clean = [re.sub(r"[{}\\\r\n]", "", w["word"]).strip() for w in chunk]
        highlights = []
        for i,w in enumerate(chunk):
            next_start = float(chunk[i+1]["start"]) if i+1<len(chunk) else end
            duration = max(1,round((next_start-float(w["start"]))*100))
            highlights.append(r"{\kf"+str(duration)+"}"+clean[i])
        ass.append(f"Dialogue: 0,{stamp(start,True)},{stamp(end,True)},Spot,,0,0,0,,"+" ".join(highlights))
        srt.append(f"{index}\n{stamp(start,False)} --> {stamp(end,False)}\n"+" ".join(clean))
    ass_path,srt_path = work/"captions.ass",work/"captions.srt"
    ass_path.write_text(header+"\n".join(ass),encoding="utf-8")
    srt_path.write_text("\n\n".join(srt)+"\n",encoding="utf-8")
    return ass_path,srt_path

def render(brief, output, voice=None, captions=None, model="base", draft=False, end_card=None):
    brief = checked_brief(brief)
    spot = Spot(brief)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    voice = Path(voice).resolve() if voice else None
    with tempfile.TemporaryDirectory(prefix=".nelvis-",dir=output.parent) as temporary:
        work = Path(temporary)
        beat = work/"beat.wav"
        sound(beat)
        filters = []
        args = ["ffmpeg","-v","error","-y","-filter_threads","2","-filter_complex_threads","2",
                "-f","rawvideo","-pix_fmt","rgb24","-s",f"{spot.width}x{spot.height}","-r",str(FPS),
                "-i","pipe:0","-i",str(beat)]
        if voice:
            args += ["-i",str(voice)]
            filters.append("[1:a]volume=0.29[bed];[2:a]volume=0.82,apad=whole_dur=12[voice];[bed][voice]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
        ass = srt = None
        if captions:
            ass = work/"captions.ass"
            if Path(captions).suffix.lower() == ".srt":
                execute(["ffmpeg","-v","error","-y","-i",str(Path(captions).resolve()),str(ass)])
            else:
                shutil.copyfile(captions,ass)
        elif voice and model:
            ass,srt = subtitle_files(voice,work,(spot.width,spot.height),model)
        video_filters = "setsar=1"
        if ass:
            video_filters = "ass=captions.ass,"+video_filters
        if not draft:
            video_filters += f",scale={spot.width*3//2}:{spot.height*3//2}:flags=lanczos"
        if end_card:
            card_index = 3 if voice else 2
            args += ["-i",str(Path(end_card).resolve())]
            filters += [
                "[0:v]trim=end=9,setpts=PTS-STARTPTS,format=yuv420p[main]",
                f"[{card_index}:v]fps=30,scale={spot.width}:{spot.height}:force_original_aspect_ratio=decrease,"
                f"pad={spot.width}:{spot.height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
                "tpad=stop_duration=3:stop_mode=clone,trim=end=3,setpts=PTS-STARTPTS[card]",
                f"[main][card]concat=n=2:v=1:a=0,{video_filters}[v]",
            ]
        elif voice:
            filters.append(f"[0:v]{video_filters}[v]")
        if filters:
            args += ["-filter_complex",";".join(filters),"-map","[v]","-map","[a]" if voice else "1:a:0"]
        else:
            args += ["-vf",video_filters,"-map","0:v:0","-map","1:a:0"]
        args += ["-c:v","libx264","-threads","4","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                 "-c:a","aac","-b:a","192k","-t",str(DURATION),"-movflags","+faststart","render.mp4"]
        with (work/"ffmpeg.log").open("w+") as log:
            with subprocess.Popen(args,stdin=subprocess.PIPE,stderr=log,cwd=work) as process:
                try:
                    frame_count = FPS * (CUTS[-2] if end_card else DURATION)
                    for index in range(frame_count):
                        process.stdin.write(spot.frame(index).tobytes())
                    process.stdin.close()
                    if process.wait():
                        raise BrokenPipeError
                except BrokenPipeError:
                    process.wait()
                    log.seek(0)
                    raise RuntimeError(log.read().strip() or "Échec de l’encodage FFmpeg.") from None
                except BaseException:
                    process.kill()
                    raise
        if srt:
            shutil.copyfile(srt,output.with_suffix(".srt"))
            shutil.copyfile(ass,output.with_suffix(".ass"))
        (work/"render.mp4").replace(output)
    return output

def load_brief(file):
    data = json.loads(file.read_text(encoding="utf-8"))
    data = checked_brief(data)
    data["images"] = [str((file.parent / name).resolve()) for name in data["images"]]
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief",type=Path)
    parser.add_argument("-o","--output",type=Path,default=Path("spot.mp4"))
    parser.add_argument("--format",choices=("9:16","16:9"))
    parser.add_argument("--voice",type=Path)
    parser.add_argument("--captions",type=Path,help="Sous-titres ASS ou SRT existants")
    parser.add_argument("--turn-frames",type=Path,help="Séquence PNG issue de Blender ou Natron")
    parser.add_argument("--end-card",type=Path,help="MP4 de fin, par exemple rendu Remotion")
    parser.add_argument("--vector-frames",type=Path,help="Séquence PNG RGBA issue de Glaxnimate ou d’un compositeur")
    parser.add_argument("--whisper-model",default="base")
    parser.add_argument("--no-whisper",action="store_true")
    parser.add_argument("--draft",action="store_true")
    options = parser.parse_args()
    data = load_brief(options.brief)
    if options.format:
        data["format"] = options.format
    if options.turn_frames:
        data["turn_frames"] = options.turn_frames
    if options.vector_frames:
        data["vector_frames"] = options.vector_frames
    print(render(data,options.output,options.voice,options.captions,
                 None if options.no_whisper else options.whisper_model,options.draft,options.end_card))

if __name__ == "__main__":
    main()
