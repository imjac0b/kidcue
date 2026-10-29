"""Composite every Kid Cue animation over a false-coloured background.

Colours are Apple's real colorways, decoded from CameraUI (colorways.json): the template is
false-coloured black -> dot colour, white -> bg colour.
usage: python3 background/render_all.py   (needs ffmpeg + Pillow)
"""
import json, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from make_background import make

ROOT = Path(__file__).resolve().parent.parent
PALETTE = json.loads((Path(__file__).parent / "colorways.json").read_text())
# The app picks a colorway per session (log: "Picked session colorway"), not per animation.
# This animation -> colorway pairing is only for the demo GIFs. balloons/blanket matches the
# asset-catalog menu image.
ASSIGN = {
    "balloons": "blanket", "bonk": "pumpkin", "brushingteeth": "peppermint", "bubbles": "lucyblue",
    "fingerpaint": "woodstock", "flyingace": "doghouse", "happydance": "campfire", "magnifier": "newspaper",
    "maskedmarvel": "violet", "rocket": "lunar", "rollerskates": "sunset", "snoopyinspace": "lunar",
    "spraybottle": "beach", "surfingsnoopy": "beach", "tennis": "scout",
}
COLORWAYS = {a: (PALETTE[c]["dot"], PALETTE[c]["bg"]) for a, c in ASSIGN.items()}  # (dark=dot, light=bg)
SIZE = 1024
FG = lambda i: "[%d:v:0][%d:v:1]alphamerge,scale=%d:%d:flags=lanczos" % (i, i, SIZE, SIZE)   # colour track + alpha track
OUT = {k: ROOT / k for k in ("transparent", "composited")}
for k, fm in (("transparent", ("gif", "webp", "webm")), ("composited", ("gif", "webp", "mp4"))):
    for f in fm: (OUT[k] / f).mkdir(parents=True, exist_ok=True)

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)

def render(name):
    src = str(ROOT / "raw_assets" / f"{name}.heics")
    dark, light = COLORWAYS[name]
    with tempfile.TemporaryDirectory() as tmp:
        bg = Path(tmp) / "bg.png"; make(SIZE, SIZE, dark, light).save(bg)
        t, c = OUT["transparent"], OUT["composited"]
        # transparent
        ff("-i", src, "-filter_complex", FG(0) + ",split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse=alpha_threshold=128", "-loop", "0", str(t / "gif" / f"{name}.gif"))
        ff("-i", src, "-filter_complex", FG(0), "-c:v", "libwebp_anim", "-quality", "80", "-loop", "0", str(t / "webp" / f"{name}.webp"))
        ff("-i", src, "-filter_complex", FG(0) + ",format=yuva420p", "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-auto-alt-ref", "0", str(t / "webm" / f"{name}.webm"))
        # composited over the colorway background
        comp = f"{FG(1)}[fg];[0:v][fg]overlay=shortest=1"
        ff("-loop", "1", "-i", str(bg), "-i", src, "-filter_complex", comp + ",split[a][b];[a]palettegen[p];[b][p]paletteuse", "-loop", "0", str(c / "gif" / f"{name}.gif"))
        ff("-loop", "1", "-i", str(bg), "-i", src, "-filter_complex", comp, "-c:v", "libwebp_anim", "-quality", "80", "-loop", "0", str(c / "webp" / f"{name}.webp"))
        ff("-loop", "1", "-i", str(bg), "-i", src, "-filter_complex", comp + ",format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(c / "mp4" / f"{name}.mp4"))
    return name

with ThreadPoolExecutor(4) as ex:
    for n in ex.map(render, COLORWAYS): print(n, flush=True)

# swatches of all 13 real colorways
sw = ROOT / "background" / "swatches"; sw.mkdir(exist_ok=True)
for name, c in PALETTE.items():
    make(256, 256, c["dot"], c["bg"]).save(sw / f"{name}.png")
