"""Recreate the Kid Cue (ShutterBuddy) background.

The app false-colors shutterbuddy_bg_template.png (CIFalseColor): black -> dark
colour, white -> light colour. The template is a vertical halftone gradient
(tiny dots at the top, solid black at the bottom), 82px wide, tiled across the
width and stretched to the screen height.

usage: make_background.py OUT.png WIDTH HEIGHT DARK_HEX LIGHT_HEX [SCALE]   (default: height/2160, gradient spans the screen)
"""
import sys
from pathlib import Path
from PIL import Image

TEMPLATE = Path(__file__).parent.parent / "raw_assets" / "shutterbuddy_bg_template.png"

def hexrgb(s):
    s = s.lstrip("#"); return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def make(width, height, dark, light, tile_scale=0):
    t = Image.open(TEMPLATE).convert("L")
    s = tile_scale or height / t.height                 # uniform scale; default: gradient spans the height
    tw, th = max(1, round(t.width * s)), max(1, round(t.height * s))
    t = t.resize((tw, th), Image.LANCZOS)
    if th < height:                                      # pad with the last (solid) row
        pad = Image.new("L", (tw, height), t.getpixel((0, th - 1))); pad.paste(t, (0, 0)); t = pad
    t = t.crop((0, 0, tw, height))
    strip = Image.new("L", (width, height))
    for x in range(0, width, tw):
        strip.paste(t, (x, 0))
    d, l = hexrgb(dark) if isinstance(dark, str) else dark, hexrgb(light) if isinstance(light, str) else light
    lut = [tuple(round(d[c] + (l[c] - d[c]) * v / 255) for c in range(3)) for v in range(256)]
    out = Image.new("RGB", (width, height))
    out.putdata([lut[v] for v in strip.get_flattened_data()]) if hasattr(strip,"get_flattened_data") else out.putdata([lut[v] for v in strip.getdata()])
    return out

if __name__ == "__main__":
    out, w, h, dark, light = sys.argv[1:6]
    make(int(w), int(h), dark, light, float(sys.argv[6]) if len(sys.argv) > 6 else 0).save(out)
