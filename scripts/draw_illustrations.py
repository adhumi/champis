#!/usr/bin/env python3
"""Dessine les illustrations des espèces (shared/illustrations/<id>.svg), toutes du même gabarit.

Usage : python3 scripts/draw_illustrations.py          écrit les SVG et shared/illustrations/index.json
        python3 scripts/draw_illustrations.py --check  vérifie que les fichiers écrits sont à jour

Style « planche naturaliste » commun aux dix espèces (décision du 8 nov. 2026, spec › Produit) :
même cadre (viewBox 0 0 240 240, fond transparent), même encre, mêmes épaisseurs de trait, lumière
en haut à gauche, un sujet principal à droite, un sujet secondaire plus petit à gauche, ombre
portée et touffe au sol. Chaque espèce ne diffère que par ses formes et ses couleurs, décrites
dans SPECIES ci-dessous à partir des caractères de la littérature (chapeau, pied, hyménium, hôte).
Rien d'autre ne dessine : un nouveau fichier espèce reçoit son illustration ici, dans le même style.

Bibliothèque standard seulement, sortie déterministe (pas de hasard, pas d'horodatage).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "shared" / "illustrations"
SPECIES_DIR = ROOT / "species"

SIZE = 240
INK = "#3a2e22"  # encre des contours
INK_SOFT = "#3a2e22"  # détails (hyménium, réticule, zones), avec opacité
STROKE = 1.6
DETAIL = 0.9
GROUND_Y = 206.0
FRAME_SCALE = 1.15  # cadrage final (voir Canvas.svg)
LICENSE = "CC0-1.0"

# Sol et végétation, communs à toutes les planches
MOSS = "#7d8f5a"
MOSS_DARK = "#5e7044"
LEAF = "#a98d5a"
LEAF_DARK = "#8a6e40"
NEEDLE = "#6f7f4e"
SHADOW = "#3a2e22"


def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pts(*xy: float) -> str:
    return " ".join(fmt(v) for v in xy)


# ----------------------------------------------------------------------------- primitives de dessin
class Canvas:
    def __init__(self) -> None:
        self.defs: list[str] = []
        self.body: list[str] = []
        self._n = 0

    def uid(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def gradient(self, light: str, dark: str, *, angle: tuple[float, float, float, float] = (0, 0, 1, 1)) -> str:
        gid = self.uid("g")
        x1, y1, x2, y2 = angle
        self.defs.append(
            f'<linearGradient id="{gid}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}">'
            f'<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient>'
        )
        return f"url(#{gid})"

    def clip(self, d: str) -> str:
        cid = self.uid("c")
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        return cid

    def path(self, d: str, fill: str = "none", *, stroke: str | None = INK, width: float = STROKE, opacity: float | None = None, extra: str = "") -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"']
        if stroke:
            attrs.append(f'stroke="{stroke}" stroke-width="{fmt(width)}" stroke-linecap="round" stroke-linejoin="round"')
        if opacity is not None:
            attrs.append(f'opacity="{fmt(opacity)}"')
        if extra:
            attrs.append(extra)
        self.body.append(f"<path {' '.join(attrs)}/>")

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, fill: str, *, stroke: str | None = None, width: float = STROKE, opacity: float | None = None) -> None:
        attrs = [f'cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="{fill}"']
        if stroke:
            attrs.append(f'stroke="{stroke}" stroke-width="{fmt(width)}"')
        if opacity is not None:
            attrs.append(f'opacity="{fmt(opacity)}"')
        self.body.append(f"<ellipse {' '.join(attrs)}/>")

    def group(self, inner: list[str], *, transform: str = "", clip: str | None = None, opacity: float | None = None) -> None:
        attrs = []
        if transform:
            attrs.append(f'transform="{transform}"')
        if clip:
            attrs.append(f'clip-path="url(#{clip})"')
        if opacity is not None:
            attrs.append(f'opacity="{fmt(opacity)}"')
        self.body.append(f"<g {' '.join(attrs)}>" + "".join(inner) + "</g>")

    def capture(self):
        """Contexte : ce qui est dessiné dedans est retiré du corps et renvoyé (pour un groupe)."""
        return _Capture(self)

    def svg(self, title: str, desc: str) -> str:
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" role="img" aria-labelledby="t d">\n'
            f"<title id=\"t\">{title}</title>\n<desc id=\"d\">{desc}</desc>\n{defs}\n"
            # les sujets sont dessinés autour du sol GROUND_Y ; le cadrage les remonte et les agrandit pour
            # remplir le carré (même transformation pour toutes les planches)
            f'<g transform="translate(120 144) scale({fmt(FRAME_SCALE)}) translate(-120 -144)">\n' + "\n".join(self.body) + "\n</g>\n</svg>\n"
        )


class _Capture:
    def __init__(self, c: Canvas) -> None:
        self.c = c

    def __enter__(self) -> "_Capture":
        self.start = len(self.c.body)
        self.taken: list[str] = []
        return self

    def __exit__(self, *exc) -> None:
        self.taken = self.c.body[self.start :]
        del self.c.body[self.start :]


def wobble(cx: float, cy: float, rx: float, ry: float, bumps: int, amp: float, phase: float = 0.0, n: int = 72) -> str:
    """Ellipse à bord ondulé (marge d'une girolle, d'une trompette), chemin fermé lissé."""
    p = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + amp * math.sin(bumps * a + phase)
        p.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return smooth_closed(p)


def smooth_closed(p: list[tuple[float, float]]) -> str:
    """Catmull-Rom → courbes de Bézier, fermé."""
    n = len(p)
    out = [f"M{pts(*p[0])}"]
    for i in range(n):
        p0, p1, p2, p3 = p[(i - 1) % n], p[i], p[(i + 1) % n], p[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{pts(*c1)} {pts(*c2)} {pts(*p2)}")
    return " ".join(out) + " Z"


# ----------------------------------------------------------------------------- sol
def ground(c: Canvas, spots: list[tuple[float, float]], habitat: str) -> None:
    """Ombres portées sous chaque sujet, touffe de mousse et débris selon l'hôte."""
    for x, rx in spots:
        c.ellipse(x, GROUND_Y + 2, rx, rx * 0.22, SHADOW, opacity=0.13)
    # brins
    for x, h, lean in ((22, 18, -6), (29, 24, -2), (36, 16, 5), (206, 16, 4), (213, 22, 8), (221, 14, 10)):
        c.path(f"M{pts(x, GROUND_Y)} q{pts(lean * 0.4, -h * 0.6, lean, -h)}", stroke=MOSS_DARK, width=1.1)
    # mousse
    for x, rx in ((40, 14), (112, 18), (196, 12)):
        c.ellipse(x, GROUND_Y + 1, rx, 3.2, MOSS, opacity=0.9)
        c.ellipse(x - rx * 0.3, GROUND_Y - 0.6, rx * 0.5, 1.8, "#93a36c", opacity=0.9)
    if habitat == "conifer":
        for x, y, a in ((78, 211, -18), (96, 214, 12), (150, 213, -8), (170, 211, 24), (124, 212, -30)):
            r = math.radians(a)
            dx, dy = 13 * math.cos(r), 13 * math.sin(r) * 0.35
            c.path(f"M{pts(x - dx, y - dy)} L{pts(x + dx, y + dy)}", stroke=NEEDLE, width=1.4)
            c.path(f"M{pts(x - dx, y - dy)} L{pts(x + dx + 1.5, y + dy + 1.4)}", stroke=NEEDLE, width=1.2)
    else:
        for x, y, a, s in ((88, 211, -20, 1.0), (166, 213, 15, 0.9), (118, 214, 5, 0.8)):
            leaf(c, x, y, a, s)


def leaf(c: Canvas, x: float, y: float, angle: float, s: float) -> None:
    """Feuille morte lobée (chêne, hêtre), à plat au sol."""
    d = (
        "M0,0 C-3,-2 -6,-4 -10,-3.4 C-12,-2.4 -11,-0.4 -12.6,0.4 C-15,1.6 -14,3.6 -11,3.6 "
        "C-8,3.6 -6,2.6 -3,2.4 C-1.5,2.3 -0.5,1.5 0,0 Z"
    )
    with c.capture() as cap:
        c.path(d, LEAF, stroke=LEAF_DARK, width=0.9)
        c.path("M-0.5,0.6 L-12,1.4", stroke=LEAF_DARK, width=0.6)
    c.group(cap.taken, transform=f"translate({fmt(x)} {fmt(y)}) rotate({fmt(angle)}) scale({fmt(s * 1.3)})")


# ----------------------------------------------------------------------------- bolets
def bolete(
    c: Canvas,
    *,
    cx: float,
    base_y: float,
    scale: float,
    cap: tuple[str, str],
    margin: str,
    pores: tuple[str, str],
    stipe: tuple[str, str],
    reticulum: tuple[str, float, float] | None,
    cap_h: float = 1.0,
    cracked: bool = False,
    young: bool = False,
) -> None:
    """Un bolet : pied clavé, tubes en croissant sous le chapeau, chapeau hémisphérique.
    `reticulum` = (couleur, étendue 0–1 du pied depuis le haut, opacité). `young` = bouchon trapu."""
    S = scale
    sh = (62 if not young else 46) * S  # hauteur du pied
    top = base_y - sh
    wt = (14 if not young else 15) * S  # demi-largeur du pied en haut
    wb = (20 if not young else 18) * S  # en bas (ventru)
    stipe_d = (
        f"M{pts(cx - wt, top)} C{pts(cx - wt - 4 * S, top + sh * 0.3, cx - wb - 2 * S, top + sh * 0.6, cx - wb, base_y - 6 * S)} "
        f"Q{pts(cx - wb + 2 * S, base_y, cx - wb * 0.6, base_y)} L{pts(cx + wb * 0.6, base_y)} Q{pts(cx + wb - 2 * S, base_y, cx + wb, base_y - 6 * S)} "
        f"C{pts(cx + wb + 2 * S, top + sh * 0.6, cx + wt + 4 * S, top + sh * 0.3, cx + wt, top)} Z"
    )
    c.path(stipe_d, c.gradient(stipe[0], stipe[1], angle=(0, 0, 1, 0.3)))
    if reticulum:
        colour, extent, op = reticulum
        clip = c.clip(stipe_d)
        with c.capture() as cap_:
            step = 5.2 * S
            y_end = top + sh * extent
            x0 = cx - wb - 6 * S
            k = 0
            while x0 + k * step < cx + wb + 6 * S + sh:
                xs = x0 + k * step
                c.path(f"M{pts(xs, top - 2)} L{pts(xs - sh * 0.75, y_end)}", stroke=colour, width=DETAIL, opacity=op)
                c.path(f"M{pts(xs - sh, top - 2)} L{pts(xs - sh * 0.25, y_end)}", stroke=colour, width=DETAIL, opacity=op)
                k += 1
            # le réticule s'estompe vers le bas
            c.path(
                f"M{pts(cx - wb - 10 * S, y_end - 8 * S)} L{pts(cx + wb + 10 * S, y_end - 8 * S)} L{pts(cx + wb + 10 * S, y_end + 2)} L{pts(cx - wb - 10 * S, y_end + 2)} Z",
                c.gradient("#ffffff", stipe[0], angle=(0, 0, 0, 1)),
                stroke=None,
                opacity=0.0,
            )
        c.group(cap_.taken, clip=clip)
    # chapeau
    cw = (40 if not young else 30) * S  # demi-largeur
    ch = (31 if not young else 29) * S * cap_h
    cy_margin = top + 4 * S  # la marge descend un peu sous le haut du pied
    # tubes (croissant sous la marge)
    pores_d = (
        f"M{pts(cx - cw, cy_margin)} C{pts(cx - cw * 0.6, cy_margin + 12 * S, cx + cw * 0.6, cy_margin + 12 * S, cx + cw, cy_margin)} "
        f"C{pts(cx + cw * 0.5, cy_margin + 1 * S, cx - cw * 0.5, cy_margin + 1 * S, cx - cw, cy_margin)} Z"
    )
    c.path(pores_d, c.gradient(pores[0], pores[1], angle=(0, 0, 0, 1)))
    # pores : pointillé fin
    with c.capture() as dots:
        for i in range(1, 12):
            t = i / 12
            x = cx - cw + 2 * cw * t
            depth = 12 * S * (1 - (2 * t - 1) ** 2) * 0.55
            c.path(f"M{pts(x, cy_margin + depth + 1.5 * S)} l0.01,0", stroke=INK, width=1.1, opacity=0.35)
            c.path(f"M{pts(x + 1.6 * S, cy_margin + depth * 0.55 + 1.5 * S)} l0.01,0", stroke=INK, width=1.0, opacity=0.3)
    c.group(dots.taken)
    cap_d = (
        f"M{pts(cx - cw, cy_margin)} C{pts(cx - cw * 1.02, cy_margin - ch * 0.9, cx - cw * 0.45, cy_margin - ch, cx, cy_margin - ch)} "
        f"C{pts(cx + cw * 0.45, cy_margin - ch, cx + cw * 1.02, cy_margin - ch * 0.9, cx + cw, cy_margin)} "
        f"C{pts(cx + cw * 0.5, cy_margin + 1 * S, cx - cw * 0.5, cy_margin + 1 * S, cx - cw, cy_margin)} Z"
    )
    c.path(cap_d, c.gradient(cap[0], cap[1], angle=(0.1, 0, 0.9, 1)))
    cclip = c.clip(cap_d)
    with c.capture() as over:
        # reflet en haut à gauche
        c.ellipse(cx - cw * 0.35, cy_margin - ch * 0.72, cw * 0.32, ch * 0.2, "#ffffff", opacity=0.22)
        # marge plus pâle
        c.path(
            f"M{pts(cx - cw, cy_margin)} C{pts(cx - cw * 0.5, cy_margin + 1 * S, cx + cw * 0.5, cy_margin + 1 * S, cx + cw, cy_margin)}",
            stroke=margin,
            width=3.5 * S,
            opacity=0.6,
        )
        if cracked:
            for x, y, l in ((-0.55, -0.55, 7), (-0.25, -0.8, 6), (0.1, -0.62, 8), (0.42, -0.74, 5), (0.62, -0.42, 6), (-0.05, -0.3, 5), (0.3, -0.35, 7), (-0.7, -0.25, 5)):
                px, py = cx + cw * x, cy_margin + ch * y
                c.path(f"M{pts(px, py)} l{pts(l * S * 0.7, l * S * 0.35)} l{pts(-l * S * 0.3, l * S * 0.5)}", stroke=INK, width=0.7, opacity=0.35)
    c.group(over.taken, clip=cclip)
    c.path(cap_d, "none")


def bolete_plate(c: Canvas, p: dict) -> None:
    ground(c, [(152, 48), (64, 30)], p["habitat"])
    bolete(c, cx=64, base_y=GROUND_Y - 2, scale=1.0, young=True, **p["body"])
    bolete(c, cx=152, base_y=GROUND_Y, scale=1.45, **p["body"])


# ----------------------------------------------------------------------------- chanterelles et trompette
def funnel(
    c: Canvas,
    *,
    cx: float,
    base_y: float,
    scale: float,
    height: float,
    rim_rx: float,
    rim_ry: float,
    stipe_w: float,
    outside: tuple[str, str],
    top: tuple[str, str],
    inside: str | None,
    ridges: tuple[str, int, float] | None,
    bumps: int = 5,
    amp: float = 0.06,
    tilt: float = 0.0,
    pruina: bool = False,
    bruise: str | None = None,
) -> None:
    """Un entonnoir (girolle, trompette) : corps évasé, marge ondulée, plis décurrents sur l'extérieur.
    `ridges` = (couleur, nombre, opacité). `inside` = couleur du creux visible (trompette)."""
    S = scale
    H = height * S
    rx, ry = rim_rx * S, rim_ry * S
    rim_cy = base_y - H
    sw = stipe_w * S
    with c.capture() as cap:
        # corps extérieur : de la marge gauche au pied, puis à la marge droite
        body_d = (
            f"M{pts(cx - rx, rim_cy)} C{pts(cx - rx * 0.8, rim_cy + H * 0.5, cx - sw * 1.6, base_y - H * 0.45, cx - sw, base_y - 4 * S)} "
            f"Q{pts(cx - sw * 0.9, base_y, cx - sw * 0.5, base_y)} L{pts(cx + sw * 0.5, base_y)} Q{pts(cx + sw * 0.9, base_y, cx + sw, base_y - 4 * S)} "
            f"C{pts(cx + sw * 1.6, base_y - H * 0.45, cx + rx * 0.8, rim_cy + H * 0.5, cx + rx, rim_cy)} Z"
        )
        c.path(body_d, c.gradient(outside[0], outside[1], angle=(0, 0, 1, 0.6)))
        if ridges:
            colour, n, op = ridges
            clip = c.clip(body_d)
            with c.capture() as rg:
                for i in range(n):
                    t = (i + 0.5) / n
                    x_top = cx - rx + 2 * rx * t
                    x_bot = cx - sw * 0.8 + 1.6 * sw * t
                    y_bot = base_y - H * 0.22
                    bend = (t - 0.5) * rx * 0.4
                    c.path(
                        f"M{pts(x_top, rim_cy + 1)} C{pts(x_top + bend * 0.2, rim_cy + H * 0.35, x_bot + bend, y_bot - H * 0.25, x_bot, y_bot)}",
                        stroke=colour,
                        width=DETAIL,
                        opacity=op,
                    )
                    if i % 2 == 0 and i < n - 1:  # plis fourchus
                        x2 = cx - rx + 2 * rx * (t + 0.5 / n)
                        c.path(
                            f"M{pts(x2, rim_cy + 1)} C{pts(x2, rim_cy + H * 0.2, x_top + bend * 0.3, rim_cy + H * 0.3, x_top + bend * 0.25, rim_cy + H * 0.4)}",
                            stroke=colour,
                            width=DETAIL * 0.8,
                            opacity=op * 0.8,
                        )
            c.group(rg.taken, clip=clip)
        if bruise:
            clipb = c.clip(body_d)
            with c.capture() as br:
                c.ellipse(cx + rx * 0.55, rim_cy + H * 0.3, rx * 0.3, H * 0.22, bruise, opacity=0.35)
                c.ellipse(cx - rx * 0.6, rim_cy + H * 0.5, rx * 0.22, H * 0.16, bruise, opacity=0.3)
            c.group(br.taken, clip=clipb)
        c.path(body_d, "none")
        # dessus : disque ondulé
        rim_d = wobble(cx, rim_cy, rx, ry, bumps, amp, phase=0.6)
        c.path(rim_d, c.gradient(top[0], top[1], angle=(0, 0, 0.6, 1)))
        if inside:
            # creux de la trompette : ombre interne décentrée
            cclip = c.clip(rim_d)
            with c.capture() as hole:
                c.ellipse(cx + rx * 0.08, rim_cy + ry * 0.15, rx * 0.7, ry * 0.62, inside)
                c.ellipse(cx + rx * 0.12, rim_cy + ry * 0.25, rx * 0.45, ry * 0.4, "#000000", opacity=0.45)
            c.group(hole.taken, clip=cclip)
        else:
            # centre déprimé, un peu plus foncé
            c.ellipse(cx + rx * 0.05, rim_cy + ry * 0.1, rx * 0.5, ry * 0.45, top[1], opacity=0.55)
            c.ellipse(cx + rx * 0.08, rim_cy + ry * 0.15, rx * 0.25, ry * 0.22, top[1], opacity=0.5)
        if pruina:
            c.ellipse(cx - rx * 0.3, rim_cy - ry * 0.2, rx * 0.5, ry * 0.45, "#ffffff", opacity=0.45)
        c.path(rim_d, "none")
    c.group(cap.taken, transform=f"rotate({fmt(tilt)} {fmt(cx)} {fmt(base_y)})" if tilt else "")


def funnel_plate(c: Canvas, p: dict) -> None:
    ground(c, [(152, 44), (64, 30)], p["habitat"])
    funnel(c, cx=64, base_y=GROUND_Y - 2, scale=0.95, tilt=-14, **p["body"])
    funnel(c, cx=152, base_y=GROUND_Y, scale=1.4, **p["body"])


# ----------------------------------------------------------------------------- pied de mouton
def hydnum(c: Canvas, *, cx: float, base_y: float, scale: float, cap: tuple[str, str], spines: str, stipe: tuple[str, str], tilt: float = 0.0) -> None:
    S = scale
    sh = 36 * S
    top = base_y - sh
    sw = 15 * S
    with c.capture() as capd:
        stipe_d = (
            f"M{pts(cx - sw, top)} C{pts(cx - sw - 2 * S, top + sh * 0.5, cx - sw - 1 * S, base_y - 6 * S, cx - sw * 0.9, base_y - 4 * S)} "
            f"Q{pts(cx - sw * 0.8, base_y, cx - sw * 0.4, base_y)} L{pts(cx + sw * 0.5, base_y)} Q{pts(cx + sw, base_y, cx + sw * 1.05, base_y - 4 * S)} "
            f"C{pts(cx + sw * 1.1, base_y - 8 * S, cx + sw * 1.4, top + sh * 0.5, cx + sw * 1.3, top)} Z"
        )
        c.path(stipe_d, c.gradient(stipe[0], stipe[1], angle=(0, 0, 1, 0.3)))
        # chapeau bosselé, excentré, marge enroulée ; les aiguillons pendent sous la marge
        cw = 44 * S
        ch = 20 * S
        cy = top + 3 * S
        under_d = (
            f"M{pts(cx - cw, cy)} C{pts(cx - cw * 0.6, cy + 11 * S, cx + cw * 0.5, cy + 12 * S, cx + cw * 0.9, cy + 1 * S)} "
            f"C{pts(cx + cw * 0.5, cy + 3 * S, cx - cw * 0.4, cy + 3 * S, cx - cw, cy)} Z"
        )
        c.path(under_d, spines)
        clip = c.clip(under_d)
        with c.capture() as sp:
            n = 26
            for i in range(n):
                t = (i + 0.5) / n
                x = cx - cw + (cw + cw * 0.9) * t
                depth = 12 * S * math.sin(math.pi * t) ** 0.7
                c.path(f"M{pts(x, cy)} L{pts(x + 0.6 * S, cy + depth)}", stroke=INK, width=0.8, opacity=0.5)
        c.group(sp.taken, clip=clip)
        # bord inférieur crénelé des aiguillons
        c.path(
            f"M{pts(cx - cw, cy)} C{pts(cx - cw * 0.6, cy + 11 * S, cx + cw * 0.5, cy + 12 * S, cx + cw * 0.9, cy + 1 * S)}",
            stroke=INK,
            width=STROKE,
            extra='stroke-dasharray="1.2 1.6"',
        )
        cap_d = (
            f"M{pts(cx - cw, cy)} C{pts(cx - cw * 1.05, cy - ch * 0.7, cx - cw * 0.7, cy - ch * 1.05, cx - cw * 0.3, cy - ch * 0.9)} "
            f"C{pts(cx - cw * 0.05, cy - ch * 1.15, cx + cw * 0.35, cy - ch * 1.1, cx + cw * 0.55, cy - ch * 0.75)} "
            f"C{pts(cx + cw * 0.8, cy - ch * 0.6, cx + cw * 1.0, cy - ch * 0.25, cx + cw * 0.9, cy + 1 * S)} "
            f"C{pts(cx + cw * 0.5, cy + 3 * S, cx - cw * 0.4, cy + 3 * S, cx - cw, cy)} Z"
        )
        c.path(cap_d, c.gradient(cap[0], cap[1], angle=(0.1, 0, 0.9, 1)))
        cclip = c.clip(cap_d)
        with c.capture() as over:
            c.ellipse(cx - cw * 0.35, cy - ch * 0.65, cw * 0.3, ch * 0.22, "#ffffff", opacity=0.3)
            c.ellipse(cx + cw * 0.3, cy - ch * 0.55, cw * 0.18, ch * 0.16, "#ffffff", opacity=0.18)
        c.group(over.taken, clip=cclip)
        c.path(cap_d, "none")
    c.group(capd.taken, transform=f"rotate({fmt(tilt)} {fmt(cx)} {fmt(base_y)})" if tilt else "")


def hydnum_plate(c: Canvas, p: dict) -> None:
    ground(c, [(154, 50), (58, 34)], p["habitat"])
    hydnum(c, cx=58, base_y=GROUND_Y - 2, scale=0.9, tilt=-18, **p["body"])
    hydnum(c, cx=154, base_y=GROUND_Y, scale=1.35, **p["body"])


# ----------------------------------------------------------------------------- lactaire
def lactarius(c: Canvas, *, cx: float, base_y: float, scale: float, cap: tuple[str, str], zones: str, gills: tuple[str, str], stipe: tuple[str, str], pits: str, stain: str, tilt: float = 0.0, show_gills: bool = False) -> None:
    S = scale
    sh = 36 * S
    top = base_y - sh
    sw = 13 * S
    with c.capture() as capd:
        stipe_d = (
            f"M{pts(cx - sw, top)} L{pts(cx - sw * 0.95, base_y - 4 * S)} Q{pts(cx - sw * 0.9, base_y, cx - sw * 0.5, base_y)} L{pts(cx + sw * 0.5, base_y)} "
            f"Q{pts(cx + sw * 0.9, base_y, cx + sw * 0.95, base_y - 4 * S)} L{pts(cx + sw, top)} Z"
        )
        c.path(stipe_d, c.gradient(stipe[0], stipe[1], angle=(0, 0, 1, 0.2)))
        sclip = c.clip(stipe_d)
        with c.capture() as pt:
            for x, y, r in ((-0.5, 0.3, 1.6), (0.3, 0.45, 1.4), (-0.1, 0.65, 1.5), (0.55, 0.78, 1.2), (-0.6, 0.85, 1.3)):
                c.ellipse(cx + sw * x, top + sh * y, r * S * 1.3, r * S, pits, opacity=0.8)
            c.ellipse(cx - sw * 0.5, base_y - 6 * S, 3.5 * S, 2.5 * S, stain, opacity=0.45)
        c.group(pt.taken, clip=sclip)
        cw = 38 * S
        ch = 15 * S
        cy = top + 2 * S
        if show_gills:
            # vu de dessous : lames rayonnantes
            g_d = f"M{pts(cx - cw, cy)} A{pts(cw, ch * 1.2)} 0 0 0 {pts(cx + cw, cy)} A{pts(cw, ch * 0.5)} 0 0 1 {pts(cx - cw, cy)} Z"
        else:
            g_d = (
                f"M{pts(cx - cw, cy)} C{pts(cx - cw * 0.6, cy + 10 * S, cx + cw * 0.6, cy + 10 * S, cx + cw, cy)} "
                f"C{pts(cx + cw * 0.5, cy + 1.5 * S, cx - cw * 0.5, cy + 1.5 * S, cx - cw, cy)} Z"
            )
        c.path(g_d, c.gradient(gills[0], gills[1], angle=(0, 0, 0, 1)))
        gclip = c.clip(g_d)
        with c.capture() as gl:
            n = 30
            for i in range(n + 1):
                t = i / n
                x = cx - cw + 2 * cw * t
                depth = (10 if not show_gills else 16) * S * math.sin(math.pi * t) ** 0.6
                c.path(f"M{pts(x, cy - 2)} L{pts(cx + (x - cx) * 0.75, cy + depth)}", stroke=INK, width=0.7, opacity=0.4)
        c.group(gl.taken, clip=gclip)
        c.path(g_d, "none")
        # chapeau : déprimé au centre, marge enroulée
        cap_d = (
            f"M{pts(cx - cw, cy)} C{pts(cx - cw * 1.0, cy - ch * 0.9, cx - cw * 0.6, cy - ch * 1.05, cx - cw * 0.3, cy - ch * 0.9)} "
            f"Q{pts(cx, cy - ch * 0.7, cx + cw * 0.3, cy - ch * 0.9)} C{pts(cx + cw * 0.6, cy - ch * 1.05, cx + cw * 1.0, cy - ch * 0.9, cx + cw, cy)} "
            f"C{pts(cx + cw * 0.5, cy + 1.5 * S, cx - cw * 0.5, cy + 1.5 * S, cx - cw, cy)} Z"
        )
        c.path(cap_d, c.gradient(cap[0], cap[1], angle=(0.1, 0, 0.9, 1)))
        cclip = c.clip(cap_d)
        with c.capture() as over:
            # zones concentriques
            for k, r in enumerate((0.92, 0.78, 0.62, 0.45, 0.28)):
                c.path(
                    f"M{pts(cx - cw * r, cy - ch * (1 - r) * 0.9)} Q{pts(cx, cy - ch * 0.25 - ch * r * 0.55, cx + cw * r, cy - ch * (1 - r) * 0.9)}",
                    stroke=zones,
                    width=2.2 * S if k % 2 == 0 else 1.4 * S,
                    opacity=0.5,
                )
            c.ellipse(cx + cw * 0.35, cy - ch * 0.55, 3 * S, 1.6 * S, stain, opacity=0.5)
            c.ellipse(cx - cw * 0.55, cy - ch * 0.35, 2.4 * S, 1.3 * S, stain, opacity=0.45)
            c.ellipse(cx - cw * 0.4, cy - ch * 0.7, cw * 0.25, ch * 0.18, "#ffffff", opacity=0.25)
        c.group(over.taken, clip=cclip)
        c.path(cap_d, "none")
    c.group(capd.taken, transform=f"rotate({fmt(tilt)} {fmt(cx)} {fmt(base_y)})" if tilt else "")


def lactarius_underside(c: Canvas, *, cx: float, cy: float, scale: float, gills: tuple[str, str], stipe: tuple[str, str], pits: str, stain: str, latex: str) -> None:
    """Un lactaire renversé au sol, lames vers le ciel : disque de lames rayonnantes, pied creux au centre."""
    S = scale
    rx, ry = 36 * S, 15 * S
    disc = f"M{pts(cx - rx, cy)} A{pts(rx, ry)} 0 1 0 {pts(cx + rx, cy)} A{pts(rx, ry)} 0 1 0 {pts(cx - rx, cy)} Z"
    c.path(disc, c.gradient(gills[0], gills[1], angle=(0, 0, 1, 1)))
    clip = c.clip(disc)
    with c.capture() as gl:
        n = 36
        for i in range(n):
            a = 2 * math.pi * i / n
            c.path(f"M{pts(cx + 7 * S * math.cos(a), cy + 3 * S * math.sin(a))} L{pts(cx + rx * math.cos(a), cy + ry * math.sin(a))}", stroke=INK, width=0.7, opacity=0.45)
        c.ellipse(cx - rx * 0.45, cy - ry * 0.3, 3 * S, 1.6 * S, stain, opacity=0.5)
    c.group(gl.taken, clip=clip)
    c.path(disc, "none")
    # pied creux, vu en bout
    c.ellipse(cx, cy, 8 * S, 4.5 * S, stipe[0], stroke=INK, width=STROKE)
    c.ellipse(cx, cy, 4.5 * S, 2.4 * S, pits, opacity=0.7)
    # gouttes de lait
    c.ellipse(cx + rx * 0.7, cy + ry * 0.55, 2.4 * S, 1.8 * S, latex, stroke=INK, width=0.8)
    c.ellipse(cx + rx * 0.9, cy + ry * 0.95, 1.6 * S, 1.2 * S, latex, stroke=INK, width=0.8)


def lactarius_plate(c: Canvas, p: dict) -> None:
    ground(c, [(154, 50), (64, 34)], p["habitat"])
    body = p["body"]
    lactarius_underside(c, cx=64, cy=GROUND_Y - 14, scale=0.95, gills=body["gills"], stipe=body["stipe"], pits=body["pits"], stain=body["stain"], latex=p["latex"])
    lactarius(c, cx=154, base_y=GROUND_Y, scale=1.4, **body)


# ----------------------------------------------------------------------------- les espèces
SPECIES: dict[str, dict] = {
    "boletus_edulis": {
        "plate": bolete_plate,
        "habitat": "broadleaf",
        "desc": "Chapeau brun noisette à marge blanchâtre, pied ventru clair à fin réticule blanc, tubes blancs puis jaune-vert.",
        "body": dict(
            cap=("#b9865a", "#6f4a2c"),
            margin="#e9dcc6",
            pores=("#f3eedd", "#d6d19a"),
            stipe=("#efe4cd", "#c9b48d"),
            reticulum=("#ffffff", 0.45, 0.7),
        ),
    },
    "boletus_aereus": {
        "plate": bolete_plate,
        "habitat": "broadleaf",
        "desc": "Chapeau brun très sombre, presque noir, velouté ; pied brun ocre à réticule brun ; tubes blancs puis jaunâtres.",
        "body": dict(
            cap=("#5a4232", "#241a14"),
            margin="#6b5440",
            pores=("#f1ead6", "#d8cf9a"),
            stipe=("#d8bd8e", "#9c7a4e"),
            reticulum=("#6b4a2a", 0.7, 0.55),
        ),
    },
    "boletus_pinophilus": {
        "plate": bolete_plate,
        "habitat": "conifer",
        "desc": "Chapeau brun rouge vineux, pied trapu rougeâtre à réticule roux ; sous les pins et les épicéas.",
        "body": dict(
            cap=("#a85a3c", "#5e2a1c"),
            margin="#c98a6a",
            pores=("#f2eddc", "#d9d29e"),
            stipe=("#e4c9a4", "#b4845a"),
            reticulum=("#9a5a3a", 0.75, 0.55),
            cap_h=1.1,
        ),
    },
    "boletus_reticulatus": {
        "plate": bolete_plate,
        "habitat": "broadleaf",
        "desc": "Chapeau brun ocre clair, sec et craquelé par temps chaud ; pied réticulé sur toute sa hauteur ; sous les chênes.",
        "body": dict(
            cap=("#c9a473", "#8a6a44"),
            margin="#d9c39d",
            pores=("#f3eedd", "#d9d39e"),
            stipe=("#e8d6b4", "#b8976a"),
            reticulum=("#8d6a44", 1.0, 0.6),
            cracked=True,
        ),
    },
    "cantharellus_cibarius": {
        "plate": funnel_plate,
        "habitat": "broadleaf",
        "desc": "Girolle jaune d'œuf, chapeau en entonnoir à marge ondulée, plis épais décurrents sur le pied.",
        "body": dict(
            height=52,
            rim_rx=34,
            rim_ry=12,
            stipe_w=9,
            outside=("#f4c74a", "#d99a1e"),
            top=("#f6cf62", "#e2a92a"),
            inside=None,
            ridges=("#9c6a12", 11, 0.6),
            bumps=5,
            amp=0.07,
        ),
    },
    "cantharellus_pallens": {
        "plate": funnel_plate,
        "habitat": "broadleaf",
        "desc": "Girolle pâle : chapeau crème pruineux, presque blanc, plis et pied jaunes, chair qui roussit au toucher.",
        "body": dict(
            height=48,
            rim_rx=38,
            rim_ry=13,
            stipe_w=11,
            outside=("#f1d98a", "#d9ac3a"),
            top=("#f4ead0", "#e3cf9a"),
            inside=None,
            ridges=("#a37a1e", 11, 0.55),
            bumps=4,
            amp=0.06,
            pruina=True,
            bruise="#c96a2a",
        ),
    },
    "cantharellus_alborufescens": {
        "plate": funnel_plate,
        "habitat": "broadleaf",
        "desc": "Girolle blanchissante : petite, chapeau crème à blanchâtre, pied blanc, rougissant par endroits ; sous les chênes verts.",
        "body": dict(
            height=46,
            rim_rx=30,
            rim_ry=11,
            stipe_w=8,
            outside=("#f3e3c4", "#dcb57a"),
            top=("#f6ead2", "#e2c99a"),
            inside=None,
            ridges=("#b08a3a", 10, 0.5),
            bumps=6,
            amp=0.08,
            bruise="#c0583a",
        ),
    },
    "craterellus_cornucopioides": {
        "plate": funnel_plate,
        "habitat": "broadleaf",
        "desc": "Trompette de la mort : entonnoir creux gris noir, extérieur gris cendré presque lisse, marge largement évasée et ondulée.",
        "body": dict(
            height=62,
            rim_rx=28,
            rim_ry=13,
            stipe_w=6,
            outside=("#8a8378", "#4a443e"),
            top=("#4a423c", "#241f1c"),
            inside="#17110f",
            ridges=("#2a2522", 7, 0.35),
            bumps=5,
            amp=0.1,
        ),
    },
    "hydnum_repandum": {
        "plate": hydnum_plate,
        "habitat": "broadleaf",
        "desc": "Pied de mouton : chapeau bosselé crème à chamois, aiguillons pâles sous le chapeau, pied court et blanc.",
        "body": dict(
            cap=("#f0d9b0", "#d2a56a"),
            spines="#f6ecd8",
            stipe=("#f7f1e4", "#d9c8a8"),
        ),
    },
    "lactarius_deliciosus": {
        "plate": lactarius_plate,
        "habitat": "conifer",
        "desc": "Lactaire délicieux : chapeau orange zoné, déprimé au centre, lames et lait orange, pied creux à fossettes, taches vertes ; sous les pins.",
        "latex": "#e8762a",
        "body": dict(
            cap=("#e99a52", "#c2622a"),
            zones="#b85a22",
            gills=("#f0a862", "#d97a32"),
            stipe=("#f0b374", "#d6873f"),
            pits="#c25f26",
            stain="#5f8a5a",
        ),
    },
}


def draw(species_id: str, names: dict) -> str:
    spec = SPECIES[species_id]
    c = Canvas()
    spec["plate"](c, spec)
    title = f"{names['fr']} ({names['la']})"
    return c.svg(title, spec["desc"])


def manifest(ids: list[str]) -> dict:
    return {
        "version": 1,
        "license": LICENSE,
        "author": "Champis (dessins générés par scripts/draw_illustrations.py)",
        "style": "Planche naturaliste : encre et aplats, cadre 240 × 240, fond transparent, sujet principal à droite, secondaire à gauche, sol commun.",
        "viewBox": f"0 0 {SIZE} {SIZE}",
        "illustrations": [{"species": sid, "file": f"{sid}.svg"} for sid in ids],
    }


def render_all() -> dict[Path, str]:
    files: dict[Path, str] = {}
    ids = []
    for path in sorted(SPECIES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        sid = data["id"]
        if sid not in SPECIES:
            raise SystemExit(f"ECHEC  pas de dessin pour l'espèce {sid} : l'ajouter dans scripts/draw_illustrations.py")
        files[OUT / f"{sid}.svg"] = draw(sid, data["names"])
        ids.append(sid)
    for sid in SPECIES:
        if sid not in ids:
            raise SystemExit(f"ECHEC  dessin {sid} sans fichier espèce")
    files[OUT / "index.json"] = json.dumps(manifest(ids), ensure_ascii=False, indent=2) + "\n"
    return files


def main(argv: list[str]) -> int:
    files = render_all()
    if "--check" in argv:
        stale = [p for p, s in files.items() if not p.is_file() or p.read_text(encoding="utf-8") != s]
        # le README (style, licence) est écrit à la main ; tout autre SVG ou JSON doit venir d'ici
        extra = [p for p in list(OUT.glob("*.svg")) + list(OUT.glob("*.json")) if p not in files]
        for p in stale:
            print(f"ECHEC  {p.relative_to(ROOT)} : à régénérer (python3 scripts/draw_illustrations.py)")
        for p in extra:
            print(f"ECHEC  {p.relative_to(ROOT)} : fichier inattendu dans shared/illustrations/")
        if stale or extra:
            return 1
        print(f"ok  {len(files) - 1} illustrations à jour")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p, s in files.items():
        p.write_text(s, encoding="utf-8")
    print(f"ok  {len(files) - 1} illustrations écrites dans {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
