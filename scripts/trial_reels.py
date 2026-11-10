#!/usr/bin/env python3
"""Trial reels v2: one line, one clip, seven seconds.

Turns reel-edits/trial-reels-v2/BRIEF.md into 50 individual edit projects and
renders each one to a phone-ready MP4 as soon as its b-roll clip exists.

  python3 scripts/trial_reels.py parse            BRIEF.md -> reels.json
  python3 scripts/trial_reels.py build            one folder per reel: overlay.png, caption.txt, project.json, EDIT.md
  python3 scripts/trial_reels.py render [01 07]   clips/NN.* -> NN-slug/NN-slug.mp4 (all reels with a clip if none named)
  python3 scripts/trial_reels.py sheet            contact sheet of every overlay, for review
  python3 scripts/trial_reels.py desk             rebuild the desk page (desk/index.html) from reels.json

Clip naming: drop the b-roll for reel 7 in reel-edits/trial-reels-v2/clips/ as
07.mov (or .mp4/.m4v). Optional start offset: 07@3.5.mov starts 3.5 s in.

The render is muted with a silent track: the trending audio is added in
Edits or Instagram at posting, because licensed Reels audio can only be
attached inside Instagram's own apps.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent / "reel-edits" / "trial-reels-v2"
BRIEF = ROOT / "BRIEF.md"
DATA = ROOT / "reels.json"
CLIPS = ROOT / "clips"
FONT = ROOT / "fonts" / "PlayfairDisplay-Regular.woff"

W, H = 1080, 1920
SECONDS = 7
IVORY = (0xE9, 0xD7, 0xC4)
COCOA = (0x49, 0x2F, 0x16)
# Brand Bible safe area: top 220, sides 35, right 100 (we keep 100 on both for a calm margin).
SAFE_TOP, SAFE_LEFT, SAFE_RIGHT = 220, 80, 100
MAX_LINES = 4


def slugify(text):
    text = text.lower().replace("’", "").replace("'", "").replace("“", "").replace("”", "")
    text = re.sub(r"\[|\]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return "-".join(text.split("-")[:6])


def parse():
    lines = BRIEF.read_text(encoding="utf-8").splitlines()
    reels, section, cur = [], None, None
    for ln in lines:
        if ln.startswith("## "):
            section = ln[3:].split(" · ")[0].strip()
            cur = None
            continue
        m = re.match(r"^### (\d\d) · (.+)$", ln)
        if m:
            cur = {"n": m.group(1), "line": m.group(2).strip(), "section": section, "caption": []}
            reels.append(cur)
            continue
        if cur is None:
            continue
        if ln.startswith("B-roll:"):
            m = re.match(r"B-roll: (.+?)\s+Audio: (.+?) \(backup: (.+)\)\s*$", ln)
            cur["broll"], audio, cur["backup"] = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            track, _, artist = audio.rpartition(", ")
            cur["audio"] = {"track": track or audio, "artist": artist if track else ""}
        elif ln.startswith("Caption: "):
            cur["caption"].append(ln[len("Caption: "):])
        elif ln.strip():
            cur["caption"].append(ln.strip())
    for r in reels:
        r["caption"] = "\n\n".join(r["caption"])
        k = re.search(r"Comment ([A-Z]{3,})", r["caption"])
        r["keyword"] = k.group(1) if k else ""
        r["slug"] = f'{r["n"]}-{slugify(r["line"])}'
        r["placeholders"] = re.findall(r"\[[^\]]+\]", r["line"] + " " + r["caption"])
    assert len(reels) == 50, f"expected 50 reels, found {len(reels)}"
    DATA.write_text(json.dumps(reels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"parsed {len(reels)} reels -> {DATA.relative_to(ROOT.parent.parent)}")
    return reels


def load():
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else parse()


def wrap(draw, text, font, width):
    words, out, line = text.split(), [], ""
    for w in words:
        t = f"{line} {w}".strip()
        if draw.textlength(t, font=font) <= width or not line:
            line = t
        else:
            out.append(line)
            line = w
    out.append(line)
    return out


def overlay(text):
    """Transparent 1080x1920 PNG: Cocoa fade at the top, Ivory Playfair line with a soft Cocoa glow."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Cocoa fade from the top edge, ~70% at the edge, clear by ~38% of the frame.
    fade = Image.new("L", (1, H), 0)
    clear_at = int(H * 0.38)
    for y in range(clear_at):
        fade.putpixel((0, y), int(178 * (1 - y / clear_at) ** 1.6))
    img.paste(Image.new("RGBA", (W, H), COCOA + (255,)), (0, 0), fade.resize((W, H)))

    width = W - SAFE_LEFT - SAFE_RIGHT
    probe = ImageDraw.Draw(img)
    for size in range(92, 55, -2):
        font = ImageFont.truetype(str(FONT), size)
        rows = wrap(probe, text, font, width)
        if len(rows) <= MAX_LINES:
            break
    lead = int(size * 1.16)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, row in enumerate(rows):
        gd.text((SAFE_LEFT, SAFE_TOP + i * lead), row, font=font, fill=COCOA + (230,))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, glow)  # second pass deepens the glow without an outline

    d = ImageDraw.Draw(img)
    for i, row in enumerate(rows):
        d.text((SAFE_LEFT, SAFE_TOP + i * lead), row, font=font, fill=IVORY + (255,))
    return img


def edit_sheet(r):
    a = r["audio"]
    ph = ", ".join(r["placeholders"]) if r["placeholders"] else "none"
    return f"""# {r['n']} · {r['line']}

**Section:** {r['section']} · **Keyword:** {r['keyword'] or 'none'} · **Placeholders to confirm:** {ph}

## Clip
{r['broll']}
One locked-off shot, muted, no cuts. Save it as `clips/{r['n']}.mov` (or `.mp4`), then run
`python3 scripts/trial_reels.py render {r['n']}`. To start later in the clip: `clips/{r['n']}@3.5.mov`.

## Text overlay
`overlay.png` (1080 x 1920, transparent). Playfair Display, Ivory with a Cocoa glow, top safe area,
on screen from frame one for all 7 seconds. Already burned into `{r['slug']}.mp4` once rendered.

## Audio (added in Edits or Instagram, not in the file)
- **Use:** {a['track']}{', ' + a['artist'] if a['artist'] else ''}, the recognisable section
- **Backup:** {r['backup']}
- Check the audio page first: if its reel count has stopped rising, use the backup.

## In Edits
1. New project, import `{r['slug']}.mp4` (or the raw clip plus `overlay.png` as an overlay, full frame, 0 to 7 s).
2. Audio: search the track above, set the start to the recognisable section, clip volume 0.
3. Export, or share to Instagram.

## Posting settings (Instagram share screen)
- Trial reel: **on**
- Share to Facebook: **off**
- Share to Threads: **off**
- Caption: paste `caption.txt`

## Caption
{r['caption']}
"""


def build():
    reels = load()
    CLIPS.mkdir(exist_ok=True)
    for r in reels:
        d = ROOT / r["slug"]
        d.mkdir(exist_ok=True)
        overlay(r["line"]).save(d / "overlay.png", optimize=True)
        (d / "caption.txt").write_text(r["caption"] + "\n", encoding="utf-8")
        (d / "EDIT.md").write_text(edit_sheet(r), encoding="utf-8")
        proj = {k: r[k] for k in ("n", "line", "section", "broll", "audio", "backup", "keyword", "placeholders")}
        proj.update({
            "duration_s": SECONDS, "size": [W, H], "clip": f"clips/{r['n']}.*",
            "overlay": "overlay.png", "caption": "caption.txt", "export": f"{r['slug']}.mp4",
            "post": {"account": "@taraphilipofficial", "trial_reel": True,
                     "share_to_facebook": False, "share_to_threads": False},
        })
        (d / "project.json").write_text(json.dumps(proj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built {len(reels)} projects in {ROOT.relative_to(ROOT.parent.parent)}/")


def find_clip(n):
    for p in sorted(CLIPS.glob(f"{n}*")):
        m = re.match(rf"^{n}(?:@([\d.]+))?\.(mov|mp4|m4v|MOV|MP4)$", p.name)
        if m:
            return p, float(m.group(1) or 0)
    return None, 0


def render(only):
    reels = [r for r in load() if not only or r["n"] in only]
    done = 0
    for r in reels:
        clip, start = find_clip(r["n"])
        if not clip:
            if only:
                print(f"{r['n']}: no clip in clips/ yet")
            continue
        d = ROOT / r["slug"]
        if not (d / "overlay.png").exists():
            build()
        out = d / f"{r['slug']}.mp4"
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
              f"format=yuv420p[v];[v][1:v]overlay=0:0:format=auto,format=yuv420p[o]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(SECONDS), "-i", str(clip),
               "-loop", "1", "-t", str(SECONDS), "-i", str(d / "overlay.png"),
               "-f", "lavfi", "-t", str(SECONDS), "-i", "anullsrc=r=48000:cl=stereo",
               "-filter_complex", vf, "-map", "[o]", "-map", "2:a",
               "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-t", str(SECONDS), "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
        print(f"{r['n']}: {out.relative_to(ROOT.parent.parent)}")
        done += 1
    print(f"rendered {done} reel(s)")


def sheet():
    reels = load()
    tw, th, cols = 216, 384, 10
    rows = (len(reels) + cols - 1) // cols
    out = Image.new("RGB", (tw * cols, th * rows), (0xD3, 0xB8, 0x9E))
    for i, r in enumerate(reels):
        bg = Image.new("RGBA", (W, H), (0x0F, 0x5F, 0x61, 255))
        bg = Image.alpha_composite(bg, Image.open(ROOT / r["slug"] / "overlay.png"))
        out.paste(bg.convert("RGB").resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    p = ROOT / "overlays-sheet.jpg"
    out.save(p, quality=85)
    print(p)


def desk():
    """Inject reels.json into the desk template -> desk/index.html (the page published as the Trial Reels Desk)."""
    keys = ("n", "line", "section", "broll", "audio", "backup", "caption", "keyword", "slug", "placeholders")
    data = json.dumps([{k: r[k] for k in keys} for r in load()], ensure_ascii=False, separators=(",", ":"))
    tpl = (ROOT / "desk" / "desk.template.html").read_text(encoding="utf-8")
    out = ROOT / "desk" / "index.html"
    out.write_text(tpl.replace("__REELS__", data.replace("</", "<\\/")), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"parse": lambda: parse(), "build": build, "sheet": sheet, "desk": desk,
     "render": lambda: render(sys.argv[2:])}.get(cmd, lambda: sys.exit(__doc__))()
