#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les vignettes des boutons GOBO et MOUVEMENT.

Sortie = PNG 72x72 palettise AVEC chunk tRNS (transparence), profil de chunks
identique aux icones assets/icons/*.png (Twemoji) qui s'affichent sur les boutons
live.ini : IHDR + PLTE + tRNS + IDAT + IEND. Un PNG opaque (sans tRNS), ou du RGB
128x128, ne s'affiche PAS sur un bouton (bouton blanc). D'ou le cadre transparent
de 2 px + la quantification Fast-Octree qui conserve l'index transparent.

  assets/gobos/w{1,2}_{open,g1..g7}.png
      Le vrai projete de chaque gobo, decoupe de la planche constructeur
      assets/gobos/_source_montage.png (roue 1 : ouvert+7, puis roue 2 : ouvert+6),
      chaque case remise sur fond noir carre.

  assets/moves/<courbe>.png
      Le trace pan/tilt de chaque courbe v1/Editor/Generator/curves_pantilt/*.gcv
      (figure + points de controle) : polyligne fermee (Transition=1) ou spline
      Catmull-Rom fermee (Transition=2).

generate_page.py ne fait que referencer ces fichiers ; il ne les recree pas et reste
sans dependance. Relancer cet outil si la planche ou les .gcv changent :
    python3 tools/gen_thumbs.py
Necessite Pillow (pip3 install pillow), pour cet outil uniquement.
"""
import os, glob
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 72                                     # comme assets/icons/*.png (Twemoji) qui s'affichent

def save_icon(im, path):
    """PNG palettise 72x72 avec tRNS : contenu dans un cadre transparent de 2 px,
    puis quantification Fast-Octree (seule methode qui garde l'alpha en mode P).
    Reproduit le profil de chunks des icones qui s'affichent (IHDR/PLTE/tRNS/IDAT)."""
    content = im.convert("RGB").resize((S - 4, S - 4), Image.LANCZOS)
    rgba = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rgba.paste(content.convert("RGBA"), (2, 2))
    rgba.quantize(colors=255, method=2).save(path, optimize=True)

# ------------------------------------------------------------------ GOBOS
MONTAGE = os.path.join(ROOT, "assets", "gobos", "_source_montage.png")
GOUT = os.path.join(ROOT, "assets", "gobos")
# planche : 5 colonnes x 3 lignes, ~6 px de marge a droite, lignes a 150 px
GRID_W, GRID_H, COLS, ROWS = 444, 450, 5, 3
GOBO_NAMES = [
    ["w1_open", "w1_g1", "w1_g2", "w1_g3", "w1_g4"],
    ["w1_g5",   "w1_g6", "w1_g7", "w2_open", "w2_g1"],
    ["w2_g2",   "w2_g3", "w2_g4", "w2_g5",  "w2_g6"],
]

def gen_gobos():
    src = Image.open(MONTAGE).convert("RGB")
    cw, ch = GRID_W / COLS, GRID_H / ROWS
    for r in range(ROWS):
        for c in range(COLS):
            cell = src.crop((round(c * cw), round(r * ch),
                             round((c + 1) * cw), round((r + 1) * ch)))
            canvas = Image.new("RGB", (S, S), (0, 0, 0))
            cc = cell.copy()
            cc.thumbnail((S, S), Image.LANCZOS)
            canvas.paste(cc, ((S - cc.width) // 2, (S - cc.height) // 2))
            save_icon(canvas, os.path.join(GOUT, GOBO_NAMES[r][c] + ".png"))
    print("OK : 15 gobos -> %s" % GOUT)

# ------------------------------------------------------------------ MOUVEMENTS
SRC = os.path.join(ROOT, "v1", "Editor", "Generator", "curves_pantilt")
MOUT = os.path.join(ROOT, "assets", "moves")
R = 216                                    # taille de rendu, redescendue en 72 par save_icon
PAD = 26
BG, FG, DOT = (12, 14, 20), (255, 255, 255), (120, 200, 255)

def parse(path):
    trans, pts = 2, []
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        s = line.strip()
        if s.startswith("Transition"):
            trans = int(s.split("=", 1)[1])
        elif s.startswith("Point_"):
            x, y = s.split("=", 1)[1].split(",")
            pts.append((float(x), float(y)))
    return trans, pts

def norm(pts):
    span = R - 2 * PAD
    return [(PAD + x / 65535 * span, PAD + (1 - y / 65535) * span) for x, y in pts]

def catmull_closed(pts, steps=24):
    n = len(pts)
    if n < 3:
        return pts
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for t in range(steps):
            u = t / steps
            u2, u3 = u * u, u * u * u
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
            out.append((x, y))
    out.append(out[0])
    return out

def gen_moves():
    os.makedirs(MOUT, exist_ok=True)
    n = 0
    for f in sorted(glob.glob(os.path.join(SRC, "*.gcv"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if name == "default":
            continue
        trans, pts = parse(f)
        if not pts:
            continue
        im = Image.new("RGB", (R, R), BG)
        d = ImageDraw.Draw(im)
        p = norm(pts)
        if len(p) == 1:
            path = p
        elif len(p) == 2:
            path = [p[0], p[1], p[0]]
        elif trans == 2:
            path = catmull_closed(p)
        else:
            path = p + [p[0]]
        if len(path) >= 2:
            d.line(path, fill=FG, width=7, joint="curve")
        r = 8
        for x, y in p:
            d.ellipse((x - r, y - r, x + r, y + r), fill=DOT)
        save_icon(im, os.path.join(MOUT, name + ".png"))
        n += 1
    print("OK : %d mouvements -> %s" % (n, MOUT))

if __name__ == "__main__":
    gen_gobos()
    gen_moves()
