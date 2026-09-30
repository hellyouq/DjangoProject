"""Procedural sakura-flavoured vector art.

Every remote image on the site degrades to one of these generated SVGs, so the
UI never shows a broken picture. The output is deterministic: the same seed
always paints the same portrait.
"""

from __future__ import annotations

import math
import random

SKINS = ["#ffe0d0", "#fbd5c0", "#f7c9b1", "#f3bfa4", "#f0d3c4"]
HAIRS = [
    "#ffb7c8",  # sakura pink
    "#f7a8c4",  # candy pink
    "#7fd3e0",  # azure
    "#a5b4fc",  # periwinkle
    "#c4b5fd",  # lavender
    "#fcd34d",  # honey
    "#fff1b8",  # cream blonde
    "#ff9bb0",  # rose
    "#8be9c9",  # mint
    "#bae6fd",  # sky
]
EYES = ["#c94f7c", "#7c5cd6", "#2f8fd6", "#0f9c96", "#d97706", "#e0447f", "#5b6ee1"]
RIBBONS = ["#ff8fb8", "#ffffff", "#ffd166", "#c4b5fd", "#7dd3fc", "#fda4af", "#fbcfe8"]
COLLARS = ["#ffffff", "#fff5f8", "#fdeef4", "#f4f1ff", "#eef8ff"]


def _rng(seed: int) -> random.Random:
    return random.Random(seed * 7919 + 13)


def avatar_svg(seed: int, size: int = 320, accent: str = "#ff8fb8") -> str:
    """A kawaii stylised portrait, unique per seed."""
    r = _rng(seed)
    skin = r.choice(SKINS)
    hair = r.choice(HAIRS)
    hair_dark = _shade(hair, -0.22)
    hair_light = _lighten(hair, 0.25)
    eye = r.choice(EYES)
    ribbon = r.choice(RIBBONS)
    collar = r.choice(COLLARS)
    has_bows = r.random() < 0.55
    twin_tails = r.random() < 0.45
    long_hair = r.random() < 0.7
    bg_a = _lighten(accent, 0.55)
    bg_b = "#ffffff"
    eye_h = r.uniform(11, 16)
    eye_w = r.uniform(13, 18)
    head_w = r.uniform(74, 84)
    head_h = r.uniform(84, 94)
    cx = 160.0
    cy = 158.0

    petals = "".join(
        f'<path d="{_petal_path(r.uniform(14, 300), r.uniform(14, 300), r.uniform(7, 15), r.uniform(0, 360))}" '
        f'fill="#ffffff" opacity="{r.uniform(0.22, 0.5):.2f}"/>'
        for _ in range(11)
    )

    back_hair = ""
    if long_hair:
        back_hair = (
            f'<path d="M{cx - head_w - 16} {cy + 40} '
            f'C{cx - head_w - 30} {cy - 40}, {cx + head_w + 30} {cy - 40}, '
            f'{cx + head_w + 16} {cy + 40} '
            f'L{cx + head_w + 30} {cy + 200} L{cx - head_w - 30} {cy + 200} Z" '
            f'fill="{hair_dark}"/>'
        )
    tails = ""
    if twin_tails:
        for sgn in (-1, 1):
            x = cx + sgn * (head_w + 6)
            tails += (
                f'<ellipse cx="{x:.0f}" cy="{cy + 62:.0f}" rx="24" ry="56" fill="{hair}" '
                f'transform="rotate({sgn * 16:.0f} {x:.0f} {cy + 62:.0f})"/>'
                f'<ellipse cx="{x:.0f}" cy="{cy + 118:.0f}" rx="12" ry="20" fill="{hair_dark}"/>'
            )

    bangs = (
        f'<path d="M{cx - head_w} {cy - 16} '
        f'C{cx - head_w - 6} {cy - head_h}, {cx + head_w + 6} {cy - head_h}, {cx + head_w} {cy - 16} '
        f'C{cx + head_w * 0.6} {cy - 44}, {cx + head_w * 0.2} {cy - 30}, {cx + 4} {cy - 34} '
        f'C{cx - head_w * 0.3} {cy - 38}, {cx - head_w * 0.7} {cy - 30}, {cx - head_w} {cy - 16} Z" '
        f'fill="{hair}"/>'
        f'<path d="M{cx - head_w * 0.9} {cy - 18} C{cx - head_w * 0.5} {cy - 40}, '
        f'{cx - head_w * 0.1} {cy - 32}, {cx - head_w * 0.05} {cy - 8} '
        f'C{cx - head_w * 0.4} {cy - 16}, {cx - head_w * 0.7} {cy - 22}, {cx - head_w * 0.9} {cy - 18} Z" '
        f'fill="{hair_light}" opacity=".55"/>'
    )

    eyes = ""
    for sgn in (-1, 1):
        ex = cx + sgn * 30
        eyes += (
            f'<ellipse cx="{ex:.0f}" cy="{cy + 12:.0f}" rx="{eye_w:.1f}" ry="{eye_h:.1f}" fill="{eye}"/>'
            f'<ellipse cx="{ex:.0f}" cy="{cy + 15:.0f}" rx="{eye_w * 0.62:.1f}" ry="{eye_h * 0.68:.1f}" fill="#2b1c33"/>'
            f'<circle cx="{ex - eye_w * 0.3:.0f}" cy="{cy + 6:.0f}" r="{eye_w * 0.3:.1f}" fill="#ffffff"/>'
            f'<circle cx="{ex + eye_w * 0.34:.0f}" cy="{cy + 18:.0f}" r="{eye_w * 0.16:.1f}" fill="#ffffff" opacity=".9"/>'
            f'<path d="M{ex - eye_w - 3:.0f} {cy - eye_h - 4:.0f} Q{ex:.0f} {cy - eye_h - 13:.0f} '
            f'{ex + eye_w + 3:.0f} {cy - eye_h - 5:.0f}" stroke="#3b2a45" stroke-width="3.4" '
            f'fill="none" stroke-linecap="round"/>'
        )

    bow = ""
    if has_bows:
        bx = cx + head_w * r.uniform(0.5, 0.78)
        by = cy - head_h * r.uniform(0.42, 0.56)
        bow = (
            f'<g transform="translate({bx:.0f} {by:.0f})">'
            f'<path d="M0 0 L-24 -13 L-24 13 Z" fill="{ribbon}"/>'
            f'<path d="M0 0 L24 -13 L24 13 Z" fill="{ribbon}"/>'
            f'<circle r="6" fill="{_shade(ribbon, -0.18)}"/>'
            f'<path d="M0 6 L-9 24 L-2 20 L0 27 L4 20 L11 24 Z" fill="{ribbon}" opacity=".9"/>'
            f"</g>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 320" width="{size}" height="{size}" role="img" aria-label="Аниме-девочка">
<defs>
<radialGradient id="bg{seed}" cx="50%" cy="34%" r="78%">
<stop offset="0%" stop-color="{bg_a}"/><stop offset="100%" stop-color="{bg_b}"/>
</radialGradient>
<linearGradient id="hair{seed}" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="{hair_light}"/><stop offset="60%" stop-color="{hair}"/><stop offset="100%" stop-color="{hair_dark}"/>
</linearGradient>
<linearGradient id="cloth{seed}" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="{collar}"/>
</linearGradient>
</defs>
<rect width="320" height="320" fill="url(#bg{seed})"/>
{petals}
<circle cx="160" cy="152" r="126" fill="#ffffff" opacity=".45"/>
{back_hair}{tails}
<path d="M{cx - 104:.0f} 320 C{cx - 96:.0f} 244, {cx + 96:.0f} 244, {cx + 104:.0f} 320 Z" fill="url(#cloth{seed})"/>
<path d="M{cx - 26:.0f} {cy + head_h * 0.86:.0f} L{cx:.0f} {cy + head_h * 0.34:.0f} L{cx + 26:.0f} {cy + head_h * 0.86:.0f} Z" fill="{skin}"/>
<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{head_w:.0f}" ry="{head_h:.0f}" fill="{skin}"/>
<g>
<path d="M{cx - head_w * 0.9:.0f} {cy - 30:.0f} C{cx - head_w * 1.05:.0f} {cy - head_h * 0.7:.0f}, {cx + head_w * 1.05:.0f} {cy - head_h * 0.7:.0f}, {cx + head_w * 0.9:.0f} {cy - 30:.0f} L{cx + head_w:.0f} {cy - 14:.0f} L{cx - head_w:.0f} {cy - 14:.0f} Z" fill="url(#hair{seed})"/>
</g>
{bangs}
{eyes}
<ellipse cx="{cx - 44:.0f}" cy="{cy + 30:.0f}" rx="11" ry="6.5" fill="#ff9db4" opacity=".5"/>
<ellipse cx="{cx + 44:.0f}" cy="{cy + 30:.0f}" rx="11" ry="6.5" fill="#ff9db4" opacity=".5"/>
<path d="M{cx - 9:.0f} {cy + 36:.0f} Q{cx:.0f} {cy + 44:.0f} {cx + 9:.0f} {cy + 36:.0f}" stroke="#c76b7f" stroke-width="3" fill="none" stroke-linecap="round"/>
{bow}
<g opacity=".85">{''.join(f'<path d="{_petal_path(r.uniform(20, 300), r.uniform(200, 316), 9, r.uniform(0,360))}" fill="{accent}" opacity=".5"/>' for _ in range(6))}</g>
</svg>"""


def _petal_path(x: float, y: float, s: float, rot: float) -> str:
    return (
        f"M0 0 C{s * 0.55:.1f} {-s * 0.5:.1f} {s * 1.15:.1f} {-s * 0.1:.1f} {s * 0.9:.1f} {s * 0.35:.1f} "
        f"C{s * 0.65:.1f} {s * 0.8:.1f} {s * 0.15:.1f} {s * 0.6:.1f} 0 0 Z "
        f'transform="translate({x:.1f} {y:.1f}) rotate({rot:.0f})"'
    )


def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(h1: str, h2: str, t: float) -> str:
    a, b = _hex_to_rgb(h1), _hex_to_rgb(h2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _shade(h: str, t: float) -> str:
    return _mix(h, "#2a1a2e", abs(t))


def _lighten(h: str, t: float) -> str:
    return _mix(h, "#ffffff", t)


# --------------------------------------------------------------------------- #
#  Case artwork
# --------------------------------------------------------------------------- #

CASE_SCENES = {
    "sakura": ("Сакура", "cherry tree"),
    "torii": ("Тории", "torii"),
    "koi": ("Карп", "koi"),
    "moon": ("Луна", "moon"),
    "fan": ("Веер", "fan"),
    "lotus": ("Лотос", "lotus"),
    "kagura": ("Кагура", "lanterns"),
    "spirits": ("Духи", "orbs"),
    "frost": ("Иней", "frost"),
    "neon": ("Неон", "neon"),
    "origami": ("Оригами", "origami"),
    "abyss": ("Бездна", "abyss"),
    "kitsune": ("Кицуне", "kitsune"),
}


def case_svg(art_key: str, accent: str, accent2: str, seed: int = 7, width: int = 640, height: int = 400) -> str:
    """Illustrated case banner, always renders offline."""
    key = art_key if art_key in CASE_SCENES else "sakura"
    title, _ = CASE_SCENES[key]
    a = _lighten(accent, 0.28)
    b = accent2
    c = _lighten(accent2, 0.4)
    r = _rng(seed)
    uid = f"{art_key}{seed}"

    speckles = "".join(
        f'<circle cx="{r.uniform(0, width):.0f}" cy="{r.uniform(0, height):.0f}" r="{r.uniform(1, 2.8):.1f}" fill="#ffffff" opacity="{r.uniform(0.3, 0.9):.2f}"/>'
        for _ in range(46)
    )
    petals = "".join(
        f'<path d="{_petal_path(r.uniform(0, width), r.uniform(0, height), r.uniform(8, 17), r.uniform(0, 360))}" fill="#ffffff" opacity="{r.uniform(0.2, 0.55):.2f}"/>'
        for _ in range(13)
    )
    hills = (
        f'<path d="M0 {height} L0 {height * 0.72:.0f} Q{width * 0.25:.0f} {height * 0.58:.0f} {width * 0.5:.0f} {height * 0.74:.0f} '
        f'Q{width * 0.78:.0f} {height * 0.9:.0f} {width} {height * 0.7:.0f} L{width} {height} Z" fill="{a}" opacity=".5"/>'
        f'<path d="M0 {height} L0 {height * 0.84:.0f} Q{width * 0.35:.0f} {height * 0.74:.0f} {width * 0.68:.0f} {height * 0.88:.0f} '
        f'Q{width * 0.88:.0f} {height * 0.96:.0f} {width} {height * 0.84:.0f} L{width} {height} Z" fill="{c}" opacity=".55"/>'
    )

    def wrap(inner: str) -> str:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{title}">
<defs>
<linearGradient id="sky{uid}" x1="0" y1="0" x2="0.3" y2="1">
<stop offset="0%" stop-color="#ffffff"/><stop offset="52%" stop-color="{a}"/><stop offset="100%" stop-color="{b}"/>
</linearGradient>
<radialGradient id="sun{uid}" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#ffffff" stop-opacity=".95"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
</radialGradient>
<filter id="soft{uid}"><feGaussianBlur stdDeviation="12"/></filter>
</defs>
<rect width="{width}" height="{height}" fill="url(#sky{uid})"/>
<circle cx="{width * 0.78:.0f}" cy="{height * 0.24:.0f}" r="{height * 0.42:.0f}" fill="url(#sun{uid})"/>
{speckles}
{hills}
{inner}
{petals}
</svg>"""

    if key == "cherry tree":
        inner = _tree(width, height, a, b, uid)
    elif key == "torii":
        inner = _torii(width, height, b, c, uid)
    elif key == "koi":
        inner = _koi(width, height, b, c, uid)
    elif key == "moon":
        inner = (
            f'<circle cx="{width * 0.72:.0f}" cy="{height * 0.3:.0f}" r="{height * 0.2:.0f}" fill="#fffdf5" opacity=".95"/>'
            f'<circle cx="{width * 0.66:.0f}" cy="{height * 0.26:.0f}" r="{height * 0.2:.0f}" fill="{a}" opacity=".6"/>'
            + _floating(width, height, b)
        )
    elif key == "fan":
        inner = _fan(width, height, b, c, uid)
    elif key == "lotus":
        inner = _lotus(width, height, b, c, uid)
    elif key == "lanterns":
        inner = _lanterns(width, height, b, c, uid)
    elif key == "orbs":
        inner = _orbs(width, height, b, c, r)
    elif key == "frost":
        inner = _frost(width, height, b, c, uid)
    elif key == "neon":
        inner = _neon(width, height, b, c, uid)
    elif key == "origami":
        inner = _origami(width, height, b, c, r)
    elif key == "kitsune":
        inner = _kitsune(width, height, b, c, uid)
    else:
        inner = _abyss(width, height, b, c, r)

    return wrap(inner)


def _tree(w, h, a, b, uid) -> str:
    g = []
    for i, (x, y, s) in enumerate(((0.14, 0.5, 1.0), (0.84, 0.44, 0.8), (0.5, 0.62, 0.62))):
        g.append(
            f'<g transform="translate({w * x:.0f} {h * y:.0f}) scale({s})">'
            f'<path d="M-9 130 L-4 -60 L4 -60 L9 130 Z" fill="#8a6a72" opacity=".85"/>'
            + "".join(
                f'<circle cx="{math.cos(a2) * 66:.0f}" cy="{math.sin(a2) * 44 - 60:.0f}" r="{36 + (j % 3) * 9}" '
                f'fill="{a if j % 2 else b}" opacity=".62"/>'
                for j, a2 in enumerate([i2 * 0.9 for i2 in range(7)])
            )
            + "</g>"
        )
    return "".join(g)


def _torii(w, h, b, c, uid) -> str:
    return f"""<g opacity=".9">
<rect x="{w * 0.3:.0f}" y="{h * 0.28:.0f}" width="18" height="{h * 0.55:.0f}" rx="8" fill="{b}"/>
<rect x="{w * 0.58:.0f}" y="{h * 0.28:.0f}" width="18" height="{h * 0.55:.0f}" rx="8" fill="{b}"/>
<rect x="{w * 0.24:.0f}" y="{h * 0.22:.0f}" width="{w * 0.42:.0f}" height="20" rx="10" fill="{c}"/>
<rect x="{w * 0.2:.0f}" y="{h * 0.3:.0f}" width="{w * 0.5:.0f}" height="13" rx="7" fill="{b}" opacity=".8"/>
<rect x="{w * 0.33:.0f}" y="{h * 0.38:.0f}" width="{w * 0.26:.0f}" height="10" rx="5" fill="{c}" opacity=".7"/>
</g>"""


def _koi(w, h, b, c, uid) -> str:
    fish = []
    for x, y, s, col in ((0.3, 0.62, 1.0, b), (0.52, 0.44, 0.72, c), (0.7, 0.68, 0.55, b)):
        fish.append(
            f'<g transform="translate({w * x:.0f} {h * y:.0f}) scale({s}) rotate(-14)">'
            f'<ellipse rx="42" ry="17" fill="{col}" opacity=".8"/>'
            f'<path d="M40 0 L62 -16 L58 0 L62 16 Z" fill="{col}" opacity=".8"/>'
            f'<circle cx="-22" cy="-5" r="3.4" fill="#5b3a4a"/>'
            f'<path d="M-8 -16 Q4 -30 18 -18 Q2 -20 -6 -10 Z" fill="#ffffff" opacity=".55"/>'
            f"</g>"
        )
    return "".join(fish) + (
        f'<ellipse cx="{w * 0.5:.0f}" cy="{h * 0.78:.0f}" rx="{w * 0.44:.0f}" ry="{h * 0.2:.0f}" fill="#ffffff" opacity=".38"/>'
    )


def _floating(w, h, b) -> str:
    return "".join(
        f'<rect x="{w * 0.12 + i * 34:.0f}" y="{h * 0.6 + (i % 3) * 26:.0f}" width="24" height="34" rx="10" '
        f'fill="{b}" opacity=".4"/>'
        for i in range(6)
    )


def _fan(w, h, b, c, uid) -> str:
    cx, cy, rad = w * 0.7, h * 0.66, h * 0.42
    ribs = "".join(
        f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{cx + math.cos(math.radians(deg)) * rad:.0f}" '
        f'y2="{cy - math.sin(math.radians(deg)) * rad:.0f}" stroke="{c}" stroke-width="2.5" opacity=".7"/>'
        for deg in range(200, 341, 14)
    )
    return (
        f'<path d="M{cx - rad:.0f} {cy:.0f} A{rad:.0f} {rad:.0f} 0 0 1 {cx + rad:.0f} {cy:.0f} Z" '
        f'fill="#fffdfd" opacity=".8" stroke="{c}" stroke-width="2"/>'
        f"{ribs}"
        f'<path d="M{cx - rad * 0.6:.0f} {cy - rad * 0.55:.0f} Q{cx:.0f} {cy - rad * 0.95:.0f} {cx + rad * 0.6:.0f} {cy - rad * 0.55:.0f}" '
        f'fill="none" stroke="{b}" stroke-width="4" opacity=".55" stroke-linecap="round"/>'
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="10" fill="{b}"/>'
    )


def _lotus(w, h, b, c, uid) -> str:
    cx, cy = w * 0.5, h * 0.6
    petals = "".join(
        f'<ellipse cx="{cx + math.cos(math.radians(d)) * 46:.0f}" cy="{cy - math.sin(math.radians(d)) * 34:.0f}" '
        f'rx="30" ry="52" transform="rotate({d * 0.72:.0f} {cx:.0f} {cy:.0f})" fill="{b if i % 2 else c}" opacity=".7"/>'
        for i, d in enumerate(range(0, 360, 30))
    )
    return petals + f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="26" fill="#fff6fa" opacity=".95"/>'


def _lanterns(w, h, b, c, uid) -> str:
    out = []
    for i in range(7):
        x = w * 0.1 + i * (w * 0.13)
        y = h * 0.32 + (i % 3) * 40
        out.append(
            f'<g transform="translate({x:.0f} {y:.0f})">'
            f'<line x1="0" y1="-70" x2="0" y2="-26" stroke="{c}" stroke-width="2" opacity=".6"/>'
            f'<ellipse rx="26" ry="32" fill="{b if i % 2 else c}" opacity=".7"/>'
            f'<rect x="-26" y="-6" width="52" height="10" rx="4" fill="#7a4b58" opacity=".5"/>'
            f'<rect x="-26" y="-40" width="52" height="10" rx="4" fill="#7a4b58" opacity=".5"/>'
            f"</g>"
        )
    return "".join(out)


def _orbs(w, h, b, c, r) -> str:
    out = []
    for i in range(9):
        x = r.uniform(w * 0.12, w * 0.88)
        y = r.uniform(h * 0.2, h * 0.8)
        rr = r.uniform(14, 44)
        out.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.0f}" fill="url(#none)" opacity=".0"/>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.0f}" fill="{b if i % 2 else c}" opacity=".45"/>'
            f'<circle cx="{x - rr * 0.3:.0f}" cy="{y - rr * 0.3:.0f}" r="{rr * 0.28:.0f}" fill="#ffffff" opacity=".5"/>'
        )
    return "".join(out)


def _frost(w, h, b, c, uid) -> str:
    flakes = []
    for i in range(14):
        x = (w / 14) * i + 20
        y = h * (0.18 + (i % 5) * 0.16)
        rr = 10 + (i % 3) * 7
        arms = "".join(
            f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + math.cos(math.radians(d)) * rr:.0f}" '
            f'y2="{y + math.sin(math.radians(d)) * rr:.0f}" stroke="{c}" stroke-width="2.6" stroke-linecap="round" opacity=".8"/>'
            for d in range(0, 360, 60)
        )
        flakes.append(arms)
    return "".join(flakes)


def _neon(w, h, b, c, uid) -> str:
    bars = "".join(
        f'<rect x="{rnd:.0f}" y="0" width="10" height="{h}" fill="{b if i % 2 else c}" opacity=".3"/>'
        for i, rnd in enumerate(range(0, int(w), 54))
    )
    return (
        bars
        + f'<path d="M0 {h * 0.66:.0f} L{w * 0.3:.0f} {h * 0.4:.0f} L{w * 0.55:.0f} {h * 0.72:.0f} L{w * 0.8:.0f} {h * 0.34:.0f} L{w} {h * 0.6:.0f}" '
        f'fill="none" stroke="{b}" stroke-width="4" opacity=".8" stroke-linejoin="round"/>'
    )


def _origami(w, h, b, c, r) -> str:
    out = []
    for i in range(7):
        x = r.uniform(w * 0.1, w * 0.9)
        y = r.uniform(h * 0.25, h * 0.78)
        s = r.uniform(26, 58)
        col = b if i % 2 else c
        out.append(
            f'<path d="M{x:.0f} {y - s:.0f} L{x + s:.0f} {y:.0f} L{x:.0f} {y + s * 0.3:.0f} L{x - s:.0f} {y:.0f} Z" '
            f'fill="{col}" opacity=".55"/>'
            f'<path d="M{x:.0f} {y - s:.0f} L{x:.0f} {y + s * 0.3:.0f} L{x - s:.0f} {y:.0f} Z" fill="#ffffff" opacity=".45"/>'
        )
    return "".join(out)


def _kitsune(w, h, b, c, uid) -> str:
    def fox(x, y, s, col, op):
        return f"""<g transform="translate({x:.0f} {y:.0f}) scale({s})" opacity="{op}">
<path d="M-30 40 Q-34 -18 0 -30 Q34 -18 30 40 Z" fill="{col}"/>
<path d="M-20 -14 L-30 -50 L-4 -26 Z" fill="{col}"/>
<path d="M20 -14 L30 -50 L4 -26 Z" fill="{col}"/>
<path d="M-18 -22 L-24 -42 L-8 -28 Z" fill="#ffffff" opacity=".5"/>
<path d="M18 -22 L24 -42 L8 -28 Z" fill="#ffffff" opacity=".5"/>
<circle cx="-11" cy="-8" r="3.2" fill="#4a2c3a"/><circle cx="11" cy="-8" r="3.2" fill="#4a2c3a"/>
<path d="M-5 6 Q0 12 5 6 Z" fill="#4a2c3a"/>
<path d="M22 22 Q48 30 56 62 Q40 44 24 40 Z" fill="{col}" opacity=".9"/>
</g>"""

    return (
        fox(w * 0.32, h * 0.5, 1.0, b, 0.9)
        + fox(w * 0.66, h * 0.36, 0.62, c, 0.8)
        + fox(w * 0.82, h * 0.62, 0.44, b, 0.6)
        + "".join(
            f'<circle cx="{w * 0.1 + i * 46:.0f}" cy="{h * 0.8:.0f}" r="{5 + (i % 3) * 3}" fill="#ffffff" opacity=".45"/>'
            for i in range(9)
        )
    )


def _abyss(w, h, b, c, r) -> str:
    rings = "".join(
        f'<ellipse cx="{w * 0.5:.0f}" cy="{h * 0.55:.0f}" rx="{60 + i * 42}" ry="{20 + i * 14}" '
        f'fill="none" stroke="{b if i % 2 else c}" stroke-width="{3 - i * 0.2:.1f}" opacity="{0.5 - i * 0.05:.2f}"/>'
        for i in range(6)
    )
    return rings + f'<circle cx="{w * 0.5:.0f}" cy="{h * 0.55:.0f}" r="30" fill="#ffffff" opacity=".8"/>'


def logo_svg(size: int = 56) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" aria-hidden="true">
<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#ffd6e7"/><stop offset="100%" stop-color="#ff7fb0"/></linearGradient></defs>
<circle cx="32" cy="32" r="30" fill="url(#lg)"/>
<g fill="#ffffff">
<circle cx="32" cy="19" r="6.2"/><circle cx="44" cy="27" r="6.2"/><circle cx="40" cy="41" r="6.2"/>
<circle cx="24" cy="41" r="6.2"/><circle cx="20" cy="27" r="6.2"/><circle cx="32" cy="30" r="3.4"/>
</g>
<circle cx="32" cy="30" r="1.9" fill="#ff5fa2"/>
</svg>"""


PETAL_CSS = [
    ("#ffd6e7", 9, 14), ("#ffc2da", 7, 11), ("#ffffff", 6, 9), ("#ffe3ee", 11, 18), ("#ffcfe3", 5, 8),
]
