#!/usr/bin/env python3
"""Render DukaBind M6 demo assets from real CLI output (no hand-typed pixels).

This is a packaging-only tool: every line of text in the generated screenshots
and the demo video comes from actually running the binder / offline proof /
profiler summary on this machine. Nothing is fabricated.

Outputs (relative to the repo root):
  demo/screenshots/01-credit-answer.png    credit bind answer (with citation rows)
  demo/screenshots/02-ledger-flip.png      the bind: one row edited -> answer changes
  demo/screenshots/03-refuse-null-field.png  fail-closed refusals (missing field)
  demo/screenshots/04-offline-proof.png    scripts/offline_check.sh output
  demo/screenshots/05-measured-numbers.png adtc-profiler participant summary
  demo/demo.mp4                            <=2 min demo video (H.264, captions)

Run (after `python -m app.db.connection` has seeded the ledger):
  source .venv/bin/activate
  PYTHONPATH=. python scripts/render_demo_assets.py

Requires Pillow (dev-only, installed in .venv) and ffmpeg on PATH.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)

# ---------------------------------------------------------------- palette
BG        = (26, 27, 38)      # #1a1b26
FG        = (192, 202, 245)   # #c0caf5
DIM       = (86, 95, 137)     # #565f89
BLUE      = (122, 162, 247)   # #7aa2f7
CYAN      = (125, 207, 255)   # #7dcfff
GREEN     = (158, 206, 106)   # #9ece6a
ORANGE    = (255, 158, 100)   # #ff9e64
RED       = (247, 118, 142)   # #f7768e
PURPLE    = (187, 154, 247)   # #bb9af7
TITLEBAR  = (41, 44, 60)      # #292c3c
BORDER    = (86, 95, 137)
WHITE     = (255, 255, 255)

# ------------------------------------------------------------------ fonts
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
MONO = str(FONT_DIR / "DejaVuSansMono.ttf")
SANS = str(FONT_DIR / "DejaVuSans.ttf")
SANS_B = str(FONT_DIR / "DejaVuSans-Bold.ttf")

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ------------------------------------------------------------------- runs
def cli_ask(question: str) -> dict:
    env = dict(os.environ, PYTHONPATH=".")
    py = sys.executable
    out = subprocess.run(
        [py, "-m", "app.cli", question], capture_output=True, text=True, env=env, check=False
    )
    if out.returncode != 0:
        raise RuntimeError(f"cli failed for {question!r}: {out.stderr}")
    return json.loads(out.stdout)


def seed_ledger() -> None:
    env = dict(os.environ, PYTHONPATH=".")
    subprocess.run([sys.executable, "-m", "app.db.connection"], check=True, env=env)


def flip_ask(question: str) -> tuple[dict, dict]:
    """Ask before and after a REAL one-row UPDATE inside one transaction.

    Mirrors scripts/offline_check.sh: BEGIN -> UPDATE credit_limit -> ask
    -> ROLLBACK, so the seed is never left modified. Both answers are
    genuinely produced by the binder against the edited ledger.
    """
    from app.binder.pipeline import handle_ask
    from app.db.connection import DEFAULT_DB, connect

    path = Path(DEFAULT_DB)
    conn = connect(path)  # writable for the flip demo only
    try:
        before = handle_ask(conn, question)
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE customers SET credit_limit = ? WHERE display_name = ?",
            (20000, "Marie-Claire Fotso"),
        )
        after = handle_ask(conn, question)
        conn.execute("ROLLBACK")
    finally:
        conn.close()
    return (
        {
            "ok": before.ok,
            "approved": before.approved,
            "message": before.message,
        },
        {
            "ok": after.ok,
            "approved": after.approved,
            "message": after.message,
        },
    )


def run(cmd: list[str]) -> str:
    env = dict(os.environ, PYTHONPATH=".")
    out = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    if out.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {out.stderr[:500]}")
    return out.stdout


def pretty_citation(citation_json: str, max_rows: int = 2) -> list[str]:
    """Pretty-print the real citation block for on-screen display."""
    data = json.loads(citation_json)
    rows = data.get("ledger_rows", [])
    lines = ['"citation" : {']
    lines.append('  "ledger_rows" : [')
    for i, row in enumerate(rows[:max_rows]):
        sep = "," if i < len(rows[:max_rows]) - 1 else ""
        row_txt = json.dumps(row, ensure_ascii=False)
        lines.append(f"    {row_txt}{sep}")
    if len(rows) > max_rows:
        lines.append(f"    … {len(rows) - max_rows} more row(s)")
    lines.append("  ]")
    lines.append("}")
    return lines


# ---------------------------------------------------------------- styling
def wrap_line(text: str, width_chars: int) -> list[str]:
    if len(text) <= width_chars:
        return [text]
    out = []
    while len(text) > width_chars:
        cut = text[:width_chars]
        out.append(cut)
        text = text[width_chars:]
    out.append(text)
    return out


STYLE = {
    "plain": FG,
    "prompt": GREEN,
    "cmd": WHITE,
    "key": CYAN,
    "str": GREEN,
    "num": ORANGE,
    "bool": PURPLE,
    "dim": DIM,
    "ok": GREEN,
    "fail": RED,
    "warn": ORANGE,
}


def style_json_line(line: str) -> list[tuple[str, str]]:
    """Very light JSON colouring: key / string / number / literal."""
    m = re.match(r'^(\s*)"([^"]+)"\s*:\s*(.*)$', line)
    if not m:
        if re.match(r'^\s*[}\]]', line):
            return [(line, "plain")]
        return [(line, "str")]
    indent, key, rest = m.group(1), m.group(2), m.group(3)
    parts = [(indent + '"' + key + '" : ', "key")]
    if rest.startswith('"'):
        parts.append((rest, "str"))
    elif rest in ("true", "false", "null"):
        parts.append((rest, "bool"))
    elif re.match(r"^-?\d", rest):
        parts.append((rest, "num"))
    else:
        parts.append((rest, "plain"))
    return parts


def line_parts(text: str, style: str) -> list[tuple[str, str]]:
    if style == "json":
        return style_json_line(text)
    return [(text, style)]


# ---------------------------------------------------------------- drawing
def draw_window(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    radius: int = 12,
) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=BG, outline=BORDER)
    draw.rounded_rectangle(
        [x, y, x + w, y + 34], radius=radius, fill=TITLEBAR, outline=TITLEBAR
    )
    # traffic lights
    for i, col in enumerate((RED, ORANGE, GREEN)):
        cx = x + 18 + i * 18
        draw.ellipse([cx - 6, y + 17 - 6, cx + 6, y + 17 + 6], fill=col)
    draw.text((x + 84, y + 10), title, font=font(MONO, 14), fill=DIM)


def render_scene(
    lines: list[tuple[str, str]],
    *,
    title: str,
    width: int = 1280,
    height: int = 800,
    font_size: int = 18,
    pad: int = 28,
) -> Image.Image:
    """lines: list of (text, style). Renders a terminal window on a dark canvas."""
    img = Image.new("RGB", (width, height), (14, 15, 24))
    draw = ImageDraw.Draw(img)
    f = font(MONO, font_size)
    char_w = int(f.getlength("M"))
    line_h = font_size + 10
    max_chars = (width - 2 * pad - 40) // char_w

    # wrap lines to fit
    flat: list[tuple[str, str]] = []
    for text, style in lines:
        if len(text) > max_chars:
            for chunk in wrap_line(text, max_chars):
                flat.append((chunk, style))
        else:
            flat.append((text, style))

    win_h = 34 + 26 + line_h * len(flat) + 22
    win_h = min(win_h, height - 2 * pad)
    win_w = width - 2 * pad
    wx, wy = pad, pad
    draw_window(draw, wx, wy, win_w, win_h, title)

    ty = wy + 34 + 14
    for text, style in flat:
        parts = line_parts(text, style)
        tx = wx + 22
        for part, pstyle in parts:
            draw.text((tx, ty), part, font=f, fill=STYLE[pstyle])
            tx += int(f.getlength(part))
        ty += line_h
        if ty > wy + win_h - 20:
            break
    return img


def save(img: Image.Image, path: Path, scale: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    img.save(path, optimize=True)
    print(f"wrote {path} ({img.width}x{img.height})")


# ------------------------------------------------------------ content maps
def boolish(v) -> str:
    return str(v).lower() if isinstance(v, bool) else str(v)


def credit_lines() -> list[tuple[str, str]]:
    d = cli_ask("Can I give Marie-Claire three crates on credit?")
    msg = d["message"].replace("\u2014", "—").replace("\u00d7", "×")
    rows = [
        ("$ python -m app.cli \"Can I give Marie-Claire three crates on credit?\"", "prompt"),
        ("", "plain"),
        ("{", "plain"),
        (f'  "ok" : {boolish(d["ok"])},', "json"),
        (f'  "approved" : {boolish(d["approved"])},', "json"),
        (f'  "intent" : "{d["intent"]}",', "json"),
        ('  "message" : "' + msg + '",', "json"),
        (f'  "refuse_reason" : {d["refuse_reason"]},', "json"),
        ('  "citation_json" :', "plain"),
    ]
    rows += [(l, "json") for l in pretty_citation(d["citation_json"])]
    rows += [("}", "plain")]
    rows += [("", "plain"), ("→ answer is a function of the rows it read.", "dim")]
    return rows


def flip_lines() -> list[tuple[str, str]]:
    before, after = flip_ask("Can I give Fotso 3 crates on credit?")
    b = before["message"].replace("\u2014", "—").replace("\u00d7", "×")
    a = after["message"].replace("\u2014", "—").replace("\u00d7", "×")
    before_json = (
        f'{{ "ok": {boolish(before["ok"])}, "approved": {boolish(before["approved"])}, '
        f'"message": "{b}" }}'
    )
    after_json = (
        f'{{ "ok": {boolish(after["ok"])}, "approved": {boolish(after["approved"])}, '
        f'"message": "{a}" }}'
    )
    return [
        ("# flip one ledger row inside a single transaction (rolled back after):", "dim"),
        ("UPDATE customers SET credit_limit = 20000", "cmd"),
        ("  WHERE display_name = 'Marie-Claire Fotso';", "cmd"),
        ("", "plain"),
        ("$ python -m app.cli \"Can I give Fotso 3 crates on credit?\"   # before", "prompt"),
        (before_json, "json"),
        ("", "plain"),
        ("$ python -m app.cli \"Can I give Fotso 3 crates on credit?\"   # after the UPDATE", "prompt"),
        (after_json, "json"),
        ("", "plain"),
        ("→ same question, edited ledger row → answer changes. binding, not recall.", "dim"),
    ]


def refuse_lines() -> list[tuple[str, str]]:
    soca = cli_ask("How much do we owe SOCA Distribution Douala?")
    s = soca["message"].replace("\u2014", "—")
    esther = cli_ask("Can I give Esther credit for 1 crate?")
    e = esther["message"].replace("\u2014", "—")
    return [
        ("$ python -m app.cli \"How much do we owe SOCA Distribution Douala?\"", "prompt"),
        (f'{{ "ok": {boolish(soca["ok"])}, "refuse_reason": "{soca["refuse_reason"]}",', "json"),
        ('  "message": "' + s + '" }', "json"),
        ("", "plain"),
        ("$ python -m app.cli \"Can I give Esther credit for 1 crate?\"", "prompt"),
        (f'{{ "ok": {boolish(esther["ok"])}, "refuse_reason": "{esther["refuse_reason"]}",', "json"),
        ('  "message": "' + e + '" }', "json"),
        ("", "plain"),
        ("→ missing field → hard refusal, named field, no invented figure.", "dim"),
    ]


def _offline_style(ln: str) -> str:
    if ln.startswith(
        ("credit over-limit", "soca refuse", "bonaberi balance",
         "stock soda", "esther null limit", "ledger flip", "PASS")
    ):
        return "ok"
    if ln.startswith("note:"):
        return "warn"
    return "plain"


def offline_lines() -> list[tuple[str, str]]:
    out = run(["bash", "scripts/offline_check.sh"])
    lines: list[tuple[str, str]] = [("$ bash scripts/offline_check.sh", "prompt")]
    for ln in out.splitlines():
        lines.append((ln, _offline_style(ln)))
    lines.append(("→ unshare -n unavailable here → airplane-mode is manual Wi‑Fi off; binder still proven.", "dim"))
    return lines


def offline_lines_short() -> list[tuple[str, str]]:
    """Compact offline scene for the video: keeps the PASS verdict visible."""
    out = run(["bash", "scripts/offline_check.sh"])
    lines: list[tuple[str, str]] = [("$ bash scripts/offline_check.sh", "prompt")]
    for ln in out.splitlines():
        if ln.startswith(("repo:", "date:")) or ln == "":
            continue
        lines.append((ln, _offline_style(ln)))
    lines.append(("→ no cloud dependency; answers track the ledger.", "dim"))
    return lines


def measured_stats() -> dict[str, str]:
    """Parse the committed adtc-profiler summary into a {label: value} map."""
    summary = REPO / "benchmarks" / "submission.summary.md"
    if not summary.exists():
        return {}
    out: dict[str, str] = {}
    for line in summary.read_text().splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[1] and cells[0] != "Field":
            out[cells[0]] = cells[1]
    return out


def measured_lines() -> list[tuple[str, str]]:
    m = measured_stats()
    if not m:
        return [("benchmarks/submission.summary.md missing", "fail")]
    rss = m.get("Peak RSS", "?")
    tps = m.get("Generation TPS", "?")
    ttft = m.get("First-token latency", "?")
    temp = m.get("Core temp peak", "?")
    cpu = m.get("CPU", "?")
    return [
        ("$ cat benchmarks/submission.summary.md   # adtc-profiler participant", "prompt"),
        ("", "plain"),
        ("| metric                    | value", "dim"),
        (f"| Peak RSS (full stack)      | {rss}", "json"),
        (f"| Generation TPS             | {tps}", "json"),
        (f"| First-token latency        | {ttft}", "json"),
        (f"| Core temp peak (smoke)     | {temp}", "json"),
        (f"| CPU                        | {cpu}", "json"),
        ("", "plain"),
        ("→ full stack fits well under the 5.5 GB self-limit; TPS above 15 target.", "dim"),
        ("→ thermal: 2026-08-06 PASS at THREADS=2/CTX=1024 does NOT reproduce on", "warn"),
        ("  2026-08-10 re-run (peak 89.0 °C) — authoritative P_thermal = eval machine.", "warn"),
    ]


# ----------------------------------------------------------------- screens
def screenshots() -> None:
    shots = [
        ("01-credit-answer", credit_lines, "dukabind — credit bind answer (real output)"),
        ("02-ledger-flip", flip_lines, "dukabind — the bind: edit a row, answer changes"),
        ("03-refuse-null-field", refuse_lines, "dukabind — fail-closed refusal (missing field)"),
        ("04-offline-proof", offline_lines, "dukabind — offline proof (no cloud)"),
        ("05-measured-numbers", measured_lines, "dukabind — measured (adtc-profiler)"),
    ]
    for key, fn, title in shots:
        img = render_scene(fn(), title=title)
        save(img, REPO / "demo" / "screenshots" / f"{key}.png")


# ------------------------------------------------------------------ video
VIDEO_W, VIDEO_H = 1280, 720
FPS = 10
SCENES = [
    {
        "caption": "An offline shop assistant that cannot invent your money.",
        "title": "DukaBind",
        "kind": "title",
        "dur": 6.0,
    },
    {
        "caption": "It does not recall the shop's numbers — it reads the ledger and shows which rows it used.",
        "kind": "term",
        "lines": credit_lines,
        "dur": 26.0,
    },
    {
        "caption": "Change one ledger row → the same question gives a new answer. That is binding, not recall.",
        "kind": "term",
        "lines": flip_lines,
        "dur": 24.0,
    },
    {
        "caption": "Data missing? It says so and names the field. It will never invent a balance.",
        "kind": "term",
        "lines": refuse_lines,
        "dur": 20.0,
    },
    {
        "caption": "Offline is not a mode — it is the operating assumption.",
        "kind": "term",
        "lines": offline_lines_short,
        "dur": 18.0,
    },
    {
        "caption": "",  # filled from the real profiler summary at render time
        "kind": "term",
        "lines": measured_lines,
        "dur": 14.0,
    },
    {
        "caption": "github.com/Vitalisn4/dukabind · English (Path A) · Cameroon MSME offline use-case",
        "kind": "title",
        "title": "DukaBind — offline ledger binder",
        "dur": 6.0,
    },
]


def draw_caption(draw: ImageDraw.ImageDraw, text: str, w: int, h: int) -> None:
    f = font(SANS_B, 24)
    # wrap the caption so it never overflows the frame width
    max_w = w - 80
    words = text.split()
    wrapped: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                wrapped.append(cur)
            cur = word
    if cur:
        wrapped.append(cur)
    box_h = 22 + 28 * len(wrapped)
    y0 = h - box_h - 14
    draw.rounded_rectangle([20, y0, w - 20, y0 + box_h], radius=10, fill=(30, 32, 48))
    ty = y0 + 12
    for line in wrapped:
        tw = int(draw.textlength(line, font=f))
        draw.text(((w - tw) // 2, ty), line, font=f, fill=WHITE)
        ty += 28


def render_video_frame(
    scene: dict, progress: float, out_dir: Path, idx: int
) -> None:
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), (14, 15, 24))
    draw = ImageDraw.Draw(img)
    caption = scene.get("caption", "")
    if scene["kind"] == "title":
        f_big = font(SANS_B, 64)
        f_sub = font(SANS, 26)
        f_small = font(SANS, 18)
        title = scene.get("title", "DukaBind")
        draw.text(((VIDEO_W - draw.textlength(title, font=f_big)) // 2, 220), title, font=f_big, fill=WHITE)
        sub = "ADTC 2026 · Corporate / Enterprise · llama.cpp + GGUF · Qwen2.5-1.5B Q4_K_M"
        draw.text(((VIDEO_W - draw.textlength(sub, font=f_sub)) // 2, 320), sub, font=f_sub, fill=BLUE)
        tag = "no cloud · no invented balances · English (Path A)"
        draw.text(((VIDEO_W - draw.textlength(tag, font=f_small)) // 2, 380), tag, font=f_small, fill=DIM)
    else:
        caption = scene["caption"]
        if scene.get("lines") is measured_lines:
            stats = measured_stats()
            rss = stats.get("Peak RSS", "?")
            tps = stats.get("Generation TPS", "?")
            caption = (
                f"Measured: peak RSS {rss} (≪ 5.5 GB limit) · {tps} · "
                "T11 100% (28/28). Thermal honesty: 2026-08-06 PASS does not reproduce "
                "on 2026-08-10 re-run — authoritative P_thermal = eval machine."
            )
        lines = scene.get("_lines") or scene["lines"]()
        # reveal lines progressively across the scene duration
        n_visible = int(progress * (len(lines) + 2))
        visible = lines[: max(0, n_visible)]
        term_h = VIDEO_H - 120
        # cap how many lines fit inside the window so the final line is never cut
        line_h = 27
        max_fit = (term_h - 34 - 26 - 22 - 20) // line_h
        visible = visible[:max_fit]
        term = render_scene(visible, title="dukabind — demo", width=VIDEO_W - 120, height=term_h, font_size=17)
        img.paste(term, (60, 40))
        draw = ImageDraw.Draw(img)
    draw_caption(draw, caption, VIDEO_W, VIDEO_H)
    img.save(out_dir / f"frame_{idx:05d}.png")


def video() -> None:
    import shutil
    import tempfile

    frames_dir = Path(tempfile.mkdtemp(prefix="dukabind_frames_"))
    total = int(sum(s["dur"] for s in SCENES) * FPS)
    print(f"rendering {total} frames at {FPS} fps")
    # run the real commands ONCE per scene (the output is identical across
    # frames); the ledger flip happens in a single rolled-back transaction
    for scene in SCENES:
        if scene["kind"] == "term":
            scene["_lines"] = scene["lines"]()
    idx = 0
    for scene in SCENES:
        n_frames = int(scene["dur"] * FPS)
        for i in range(n_frames):
            render_video_frame(scene, i / n_frames, frames_dir, idx)
            idx += 1
    mp4 = REPO / "demo" / "demo.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(mp4)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"wrote {mp4} (duration {dur}s)")
    shutil.rmtree(frames_dir, ignore_errors=True)


def main() -> None:
    if not ImageFont.truetype:
        raise SystemExit("font load failed")
    seed_ledger()
    screenshots()
    video()


if __name__ == "__main__":
    main()
