"""Composite every Kid Cue animation over a false-coloured background.

Colours are Apple's real colorways, decoded from CameraUI (colorways.json): the template is
false-coloured black -> dot colour, white -> bg colour.
usage: python3 background/compose_all.py   (needs ffmpeg + Pillow)
"""
import json, subprocess, tempfile
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
out = ROOT / "composited"; out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    for name, (dark, light) in COLORWAYS.items():
        bg = Path(tmp) / f"{name}.png"; make(512, 512, dark, light).save(bg)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(bg),
            "-i", str(ROOT / "raw_assets" / f"{name}.heics"), "-filter_complex",
            "[1:v:0][1:v:1]alphamerge,scale=512:512:flags=lanczos[fg];[0:v][fg]overlay=shortest=1,split[a][b];"
            "[a]palettegen[p];[b][p]paletteuse", "-loop", "0", str(out / f"{name}.gif")], check=True)
        print(name)

# swatches of all 13 real colorways
sw = ROOT / "background" / "swatches"; sw.mkdir(exist_ok=True)
for name, c in PALETTE.items():
    make(256, 256, c["dot"], c["bg"]).save(sw / f"{name}.png")
