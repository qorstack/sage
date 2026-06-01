"""
Render the two README demo GIFs (without-precept.gif, with-precept.gif)
directly with Pillow — no vhs/ffmpeg/ttyd required.

Run: uv run python assets/demo/render_gifs.py

The .sh + .tape variants in this folder remain valid for contributors who
prefer the VHS toolchain. This script is the zero-deps fallback that the
repo's own venv can run on any platform.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent

# Dracula-ish palette — matches the .tape files' theme.
BG     = "#282A36"
FG     = "#F8F8F2"
CYAN   = "#8BE9FD"
RED    = "#FF5555"
YELLOW = "#F1FA8C"
GREEN  = "#50FA7B"
GREY   = "#6272A4"

WIDTH, HEIGHT = 900, 600
PAD_X, PAD_Y  = 24, 24
FONT_SIZE     = 20
LINE_H        = 26


def _load_font(size: int) -> ImageFont.ImageFont:
    # Need wide Unicode coverage (⚙ ✓ ⏸ ── │ →). Cascadia Code is the
    # canonical Windows Terminal font and supports all of them; Consolas
    # does not. Order matters — first hit wins.
    candidates = [
        "C:/Windows/Fonts/CascadiaCode.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "CascadiaCode.ttf",
        "CascadiaMono.ttf",
        "DejaVuSansMono.ttf",
        "C:/Windows/Fonts/consola.ttf",  # last-resort fallback (missing ⚙ ✓ ⏸)
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = _load_font(FONT_SIZE)


# A "line" is a list of (text, color) segments rendered in sequence.
# An "event" is {"segments": [...], "delay": ms_after_drawing_this_line}.
Segment = tuple[str, str]
Event = dict


def _render_frame(lines: list[list[Segment]]) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    y = PAD_Y
    for line in lines:
        x = PAD_X
        for text, color in line:
            if not text:
                continue
            draw.text((x, y), text, font=FONT, fill=color)
            bbox = draw.textbbox((0, 0), text, font=FONT)
            x += bbox[2] - bbox[0]
        y += LINE_H
    return img


def _build_gif(events: list[Event], out_path: Path) -> None:
    lines: list[list[Segment]] = []
    frames: list[Image.Image] = []
    durations: list[int] = []
    for ev in events:
        lines.append(ev["segments"])
        frames.append(_render_frame(lines))
        durations.append(max(int(ev["delay"]), 40))

    # Linger on the last frame so viewers can read the punchline.
    durations[-1] = max(durations[-1], 3200)

    palette_frames = [
        f.quantize(method=Image.Quantize.MEDIANCUT, colors=64)
        for f in frames
    ]
    palette_frames[0].save(
        out_path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    size_kb = out_path.stat().st_size / 1024
    print(f"  wrote {out_path.name:30s}  {len(frames):3d} frames  {size_kb:6.1f} KB")


def _line(text: str, color: str = FG) -> list[Segment]:
    return [(text, color)]


def _multi(*segments: Segment) -> list[Segment]:
    return list(segments)


WITHOUT_PRECEPT: list[Event] = [
    {"segments": _line('$ claude "add Google SSO to /login"', CYAN),  "delay": 900},
    {"segments": _line("",   FG),    "delay": 50},
    {"segments": _multi(("▶ ", CYAN), ("Reading repo...", FG)),         "delay": 1100},
    {"segments": _line("✓  Created auth/sso/google.ts",          GREEN), "delay": 550},
    {"segments": _line("✓  Created OAuthClient.ts",              GREEN), "delay": 550},
    {"segments": _line("✓  Stored access_token in localStorage", GREEN), "delay": 550},
    {"segments": _line("✓  Committed: feat(auth): Google SSO",   GREEN), "delay": 1600},
    {"segments": _line("",   FG),    "delay": 50},
    {"segments": _line("── 2 days later, in PR review ──", GREY),       "delay": 950},
    {"segments": _line("reviewer: We already have AuthService —"),     "delay": 550},
    {"segments": _line("          why a new OAuthClient?"),            "delay": 950},
    {"segments": _line("reviewer: Tokens in localStorage??"),          "delay": 550},
    {"segments": _line("          that breaks our session policy."),   "delay": 1700},
    {"segments": _line("",   FG),    "delay": 50},
    {"segments": _line("→ Revert. Rewrite. Re-review.", RED),          "delay": 3200},
]


WITH_PRECEPT: list[Event] = [
    {"segments": _line('$ claude /precept "add Google SSO to /login"', CYAN), "delay": 900},
    {"segments": _line("",  FG),  "delay": 50},
    {"segments": _multi(("▶ ", CYAN), ("analyze_intent...", FG)),         "delay": 1400},
    {"segments": _line("",  FG),  "delay": 50},
    {"segments": _line("┌──────────────────────────────────┐"),         "delay": 60},
    {"segments": _multi(
        ("│ Domain:   ",            FG),
        ("auth (HIGH)",             RED),
        ("            │",            FG),
    ), "delay": 600},
    {"segments": _multi(
        ("│ Decision: ",            FG),
        ("ASK",                     YELLOW),
        ("                    │",   FG),
    ), "delay": 650},
    {"segments": _line("│ Reuse:    AuthService,           │"),         "delay": 400},
    {"segments": _line("│           SessionStore           │"),         "delay": 650},
    {"segments": _line('│ Rule:     "Sessions live         │'),         "delay": 400},
    {"segments": _line("│            server-side — never   │"),         "delay": 400},
    {"segments": _line('│            localStorage"         │'),         "delay": 400},
    {"segments": _line("│           (alice, approved)      │"),         "delay": 750},
    {"segments": _line("│ Risk:     auth → session →       │"),         "delay": 400},
    {"segments": _line("│           audit log              │"),         "delay": 650},
    {"segments": _line("└──────────────────────────────────┘"),         "delay": 60},
    {"segments": _line("",  FG),  "delay": 50},
    {"segments": _multi(
        ("■ ",                                YELLOW),
        ("Paused — awaiting human sign-off.", FG),
    ), "delay": 3500},
]


def main() -> None:
    print("Rendering demo GIFs to", OUT_DIR)
    _build_gif(WITHOUT_PRECEPT, OUT_DIR / "without-precept.gif")
    _build_gif(WITH_PRECEPT,    OUT_DIR / "with-precept.gif")


if __name__ == "__main__":
    main()
