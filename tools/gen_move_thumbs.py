#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere une vignette PNG par courbe de mouvement (assets/moves/<courbe>.png).

Chaque .gcv de v1/Editor/Generator/curves_pantilt/ decrit un chemin pan/tilt : une
liste de points (pan,tilt) sur 0..65535 parcourus en boucle. On les trace tels quels
(polyligne fermee pour Transition=1, spline Catmull-Rom fermee pour Transition=2) avec
les points de controle marques -> on voit d'un coup d'oeil la forme du mouvement.

Sortie = images statiques versionnees (comme assets/icons/). generate_page.py ne fait
que les referencer par chemin, il ne les recree pas (il reste sans dependance).
Relancer ce script si les .gcv changent :  python3 tools/gen_move_thumbs.py
Necessite Pillow (pip3 install pillow) -- uniquement pour cet outil, pas pour le script principal.
"""
import os, glob
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "v1", "Editor", "Generator", "curves_pantilt")
OUT = os.path.join(ROOT, "assets", "moves")
SIZE = 160          # cote de la vignette (px)
PAD = 18            # marge interieure
FG = (255, 255, 255)
DOT = (120, 200, 255)
BG = (14, 16, 22)

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
    """0..65535 -> coords image (Y inverse : tilt haut = haut de l'image)."""
    span = SIZE - 2 * PAD
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

def render(trans, pts, dst):
    im = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(im)
    p = norm(pts)
    if len(p) == 1:
        path = p
    elif len(p) == 2:
        path = [p[0], p[1], p[0]]                     # aller-retour (ex: VAGUE)
    elif trans == 2:
        path = catmull_closed(p)
    else:
        path = p + [p[0]]                             # polyligne fermee
    if len(path) >= 2:
        d.line(path, fill=FG, width=3, joint="curve")
    r = 3.5
    for x, y in p:
        d.ellipse((x - r, y - r, x + r, y + r), fill=DOT)
    im.save(dst)

def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for f in sorted(glob.glob(os.path.join(SRC, "*.gcv"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if name == "default":
            continue
        trans, pts = parse(f)
        if not pts:
            continue
        render(trans, pts, os.path.join(OUT, name + ".png"))
        n += 1
    print("OK : %d vignettes -> %s" % (n, OUT))

if __name__ == "__main__":
    main()
