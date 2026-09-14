#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere pour le rig 'Generaliste' (Lyre Ali express + JB systems Accu-Compact +
   minibeamstpotled + hazer + machines a etincelles) :
   - les scenes .scex (couleurs, gobos, prisme, strobe, effets)
   - les pages 'COULEUR', 'GOBO', 'MANUEL', 'STROBE', 'FX', 'MOUVEMENT', 'DJ LIVE' dans live.ini
     (mapping APC40 mkII)
Idempotent (remplace nos pages a chaque run). Usage : python3 generate_page.py [dossier_du_show]
Le show Summer (BSW+PAR) est archive dans summer/ (generate_page.py fige separement)."""
import os, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/Users/mac-m3-michel/workspace/sweetLight/v2"
SCENES = os.path.join(BASE, "scenes")
LIVE = os.path.join(BASE, "Live", "live.ini")
OUT_GEN = os.path.join(BASE, "Editor", "Generator", "projects")
CURVES_PANTILT = os.path.join(BASE, "Editor", "Generator", "curves_pantilt")

# ---------- Fixtures (id, nom) --------- (show Generaliste, verifie via fixtures.ini) ----------
LYRE_ADDR = [1, 16, 31, 46]
LYRE = [(1789402923, "Lyre Ali express"), (1789402924, "Lyre Ali express #2"),
        (1789402925, "Lyre Ali express #3"), (1789402926, "Lyre Ali express #4")]
LYRE_MODEL = "Lyre Ali express"
LYRE_IDS = [x[0] for x in LYRE]
LYRE_GEN = [(fid, addr - 1, nm) for (fid, nm), addr in zip(LYRE, LYRE_ADDR)]
# La lyre est posee droite (pied au sol, pas suspendue) : le centre du curve pan/tilt (32768,32768)
# pointe donc au plafond au lieu de faire face au public. On decale son tilt via le champ OffsetTilt
# du generateur (prevu par Sweetlight pour ce cas : meme courbe partagee, orientation physique
# differente par fixture). Fixture avec debattement tilt total tres reduit (ViewAngleTilt=90 dans
# "Lyre Ali express.txt") : le centre pointait deja vers le haut, il faut donc pousser vers l'AUTRE
# extremite (horizontal/public) - offset positif, pas negatif (1er essai en negatif = pire, toujours
# plafond). HYPOTHESE de signe/echelle a reverifier en direct - si le mouvement part dans le mauvais
# sens ou pas assez/trop loin, changer cette seule valeur et relancer.
LYRE_TILT_OFFSET = -28000
# Meme logique pour le pan : une fois le tilt vers l'horizontale, le balayage pan devient tres visible
# (avant il tournait presque sur place, plafond = peu de pan visible). Retour terrain : le cote droit
# partait "derriere", le cote gauche etait correct -> on recentre le pan vers la gauche.
LYRE_PAN_OFFSET = -9000

COMPACT_ADDR = [61, 71, 81, 91, 101, 111, 121, 131, 141, 151, 161, 171]
COMPACT = [(1789402927 + k, "JB systems Accu-Compact" if k == 0 else "JB systems Accu-Compact #%d" % (k + 1))
           for k in range(12)]
COMPACT_MODEL = "JB systems Accu-Compact"
COMPACT_IDS = [x[0] for x in COMPACT]
COMPACT_GEN = [(fid, addr - 1, nm) for (fid, nm), addr in zip(COMPACT, COMPACT_ADDR)]

MINIBEAM_ADDR = [181, 193]
MINIBEAM = [(1789402939, "minibeamstpotled"), (1789402940, "minibeamstpotled #2")]
MINIBEAM_MODEL = "minibeamstpotled"
MINIBEAM_IDS = [x[0] for x in MINIBEAM]
MINIBEAM_GEN = [(fid, addr - 1, nm) for (fid, nm), addr in zip(MINIBEAM, MINIBEAM_ADDR)]

HAZER = [(1789402941, "hazer")]
HAZER_MODEL = "hazer"

SPARK_ADDR = [207, 210]
SPARK = [(1789402942, "machine étincelles"), (1789402943, "machine étincelles #2")]
SPARK_MODEL = "machine étincelles"

# Groupes (briques reutilisees dans les scenes FX) : paires/quarts dans chaque famille.
LYRE_PAIRS = [(LYRE[0:2]), (LYRE[2:4])]
COMPACT_PAIRS = [(COMPACT[0:3]), (COMPACT[3:6]), (COMPACT[6:9]), (COMPACT[9:12])]
ALL_MACHINES = LYRE + COMPACT + MINIBEAM

# ---------- Canaux (index positionnel, verifies via les profils .txt du show) ----------
# Lyre Ali express (15ch) : 0 pan,1 upan,2 tilt,3 utilt,4 motor_speed,5 rotation,6 dimmer,7 red,
#   8 green,9 blue,10 white,11 strobe_speed,12 color_jump,13 sped_adjust,14 reset.
#   rotation (ch5) : 128-191 "forward", 192-255 "rotation" (continue, bas=lent haut=rapide, HYPOTHESE
#   a confirmer/editer par l'utilisateur - cf commit qui introduit MANUEL/ROTATION).
# JB systems Accu-Compact (10ch) : 0 dimmer,1 red,2 green,3 blue,4 white,5 amber,6 strobe_dimmer,
#   7 animation,8 effect_speed,9 udimmer. strobe_dimmer : 0-14 open, 15-255 strobe (bas=lent haut=rapide).
# minibeamstpotled (12ch) : 0 pan,1 upan,2 tilt,3 utilt,4 pantilt_speed,5 dimmer,6 strobe_speed,
#   7 rainbow_color,8 gobo,9 prism3D,10 fonction,11 mode.
#   gobo : 0-9 open, puis 7 gobos statiques (10-79, pas de 10), 80-149 meme roue (bank 2), 150-255 auto.
#   prism3D : 0-127 pulse_close, 128-156 pulse_open, 157-255 rotate.
# hazer : 0 fog,1 fan. machine etincelles : 0 dimmer,1 Function,2 Heating (identique a Summer).

LYRE_CH = "pan,upan,tilt,utilt,motor speed,rotation,dimmer,red,green,blue,white,strobe_speed,color jump,sped adjust,reset"
LYRE_OTHER = ["motor speed", "rotation", "dimmer", "red", "green", "blue", "white", "strobe_speed",
              "color jump", "sped adjust", "reset"]
COMPACT_CH = "dimmer,red,green,blue,white,amber,strobe_dimmer,animation,effect_speed,udimmer"
COMPACT_OTHER = ["red", "green", "blue", "white", "amber", "strobe_dimmer", "animation", "effect_speed", "udimmer"]
MINIBEAM_CH = "pan,upan,tilt,utilt,pantilt_speed,dimmer,strobe_speed,rainbow_color,gobo,prism3D,fonction,mode"
MINIBEAM_OTHER = ["pantilt_speed", "dimmer", "strobe_speed", "rainbow_color", "gobo", "prism3D", "fonction", "mode"]

# ===================== Scenes .scex =====================
def chan(idx, name, val, fade=False):
    return '        <Channel index="%d" name="%s" value="%d"%s/>' % (idx, name, val, ' fade="1"' if fade else '')

def write_scene(filename, fixtures, model, steps):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '', '<Scene>', '  <Fixtures>']
    for fid, name in fixtures:
        out.append('    <Fixture id="%d" name="%s" model="%s"/>' % (fid, name, model))
    out += ['  </Fixtures>', '  <Steps>']
    for length, func in steps:
        out.append('    <Step length="%d">' % length)
        for fid, name in fixtures:
            out.append('      <Fixture id="%d">' % fid)
            out.extend(func(fid))
            out.append('      </Fixture>')
        out.append('    </Step>')
    out += ['  </Steps>', '</Scene>']
    with open(os.path.join(SCENES, filename), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out) + '\n')
    return filename

def uniform(channels):
    return lambda fid: list(channels)

def _emit_step(out, length, groups):     # groups = [(fixtures,model,cf)] ; cf = liste OU func(i,fid)->liste
    out.append('    <Step length="%d">' % length)
    for fx, model, cf in groups:
        for i, (fid, nm) in enumerate(fx):
            chans = cf(i, fid) if callable(cf) else cf
            out.append('      <Fixture id="%d">' % fid); out.extend(chans); out.append('      </Fixture>')
    out.append('    </Step>')

def _scene_head(decl):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '', '<Scene>', '  <Fixtures>']
    for fx, model, _ in decl:
        for fid, nm in fx:
            out.append('    <Fixture id="%d" name="%s" model="%s"/>' % (fid, nm, model))
    out += ['  </Fixtures>', '  <Steps>']
    return out

def write_multi(filename, groups, length=500):     # scene 1 pas, plusieurs familles
    out = _scene_head(groups); _emit_step(out, length, groups); out += ['  </Steps>', '</Scene>']
    open(os.path.join(SCENES, filename), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return filename

def write_seq(filename, steps):                    # anim multi-pas ; steps=[(length,groups),...]
    out = _scene_head(steps[0][1])
    for length, groups in steps: _emit_step(out, length, groups)
    out += ['  </Steps>', '</Scene>']
    open(os.path.join(SCENES, filename), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return filename

# ===================== Generateurs .gpj a partir d'une courbe (.gcv) =====================
def parse_gcv(path):
    d = {"Transition": "0", "Duration": "50", "Shift": "0.0"}
    points = []
    for line in open(path, encoding='utf-8', errors='replace').read().splitlines():
        s = line.strip()
        if '=' not in s: continue
        k, v = s.split('=', 1)
        k = k.strip(); v = v.strip()
        if k.startswith('Point_'): points.append((k, v))
        elif k in d: d[k] = v
    return d, points

def make_gpj_curve(curve_path, curve_label, out_name, groups, driven_section, duration=None, scale=1.0):
    """groups = [(fixtures_gen, channels_str, other_channels), ...] (plusieurs familles possibles,
    chacune avec son propre jeu de canaux). driven_section = section pilotee par la courbe.
    scale : resserre l'amplitude pan/tilt autour du centre (32768,32768) - 1.0 = amplitude pleine
    de la courbe d'origine (debattement mecanique complet), <1 = mouvement plus petit. scale peut
    etre un nombre (meme echelle pan/tilt) ou un tuple (scale_pan, scale_tilt) pour les regler
    separement."""
    d, points = parse_gcv(curve_path)
    if duration is not None: d["Duration"] = str(duration)
    scale_pan, scale_tilt = scale if isinstance(scale, tuple) else (scale, scale)
    if scale_pan != 1.0 or scale_tilt != 1.0:
        scaled = []
        for k, v in points:
            x, y = v.split(',')
            nx = min(max(int(round(32768 + (int(x) - 32768) * scale_pan)), 0), 65535)
            ny = min(max(int(round(32768 + (int(y) - 32768) * scale_tilt)), 0), 65535)
            scaled.append((k, "%d,%d" % (nx, ny)))
        points = scaled
    L = ["[Params]", "PanTiltShift = 0.0", "ExplodePanTilt = 0", "GroupRGB = 0",
         "FanPanOffset = 0", "FanTiltOffset = 0"]
    n, other_all = 0, []
    for fixtures_gen, channels_str, other_channels in groups:
        for fid, dmx, name in fixtures_gen:
            off_tilt = LYRE_TILT_OFFSET if fid in LYRE_IDS else 0
            off_pan = LYRE_PAN_OFFSET if fid in LYRE_IDS else 0
            L += ["[Fixture_%d]" % n, "ID = %d" % fid, "Name = %s" % name, "DMX = %d" % dmx,
                  "Channels = %s" % channels_str, "ReversePan = 0", "ReverseTilt = 0",
                  "OffsetPan = %d" % off_pan, "OffsetTilt = %d" % off_tilt, "ZoomPan = 0", "ZoomTilt = 0", "ExplodeIndex = 0"]
            n += 1
        for ch in other_channels:
            if ch not in other_all: other_all.append(ch)
    L += ["[%s]" % driven_section, "Selected = 1", "CurveName = %s" % curve_label,
          "Transition = %s" % d["Transition"], "Duration = %s" % d["Duration"], "Shift = %s" % d["Shift"]]
    L += ["%s = %s" % (k, v) for k, v in points]
    for ch in other_all:
        L += ["[%s]" % ch, "Selected = 0", "CurveName = Default Curve", "Transition = 0",
              "Duration = 50", "Shift = 0.0", "Point_0 = 0,65535", "Point_1 = 65535,65535"]
    if not os.path.isdir(OUT_GEN): os.makedirs(OUT_GEN)
    with open(os.path.join(OUT_GEN, out_name + ".gpj"), 'w', encoding='utf-8') as fh:
        fh.write("﻿\n" + "\n".join(L) + "\n")
    return out_name + ".gpj"

# Amplitude des mouvements pan/tilt (MOUVEMENT + DJ LIVE qui reutilise les memes .gpj) : 1.0 =
# debattement mecanique complet des courbes d'origine (trop large, sort du "devant soi"), <1 =
# mouvement resserre autour du centre. HYPOTHESE a caler en direct selon la position reelle des
# lyres/minibeams - remonter/redescendre ces valeurs et relancer le script suffit.
# Pan resserre plus que tilt : retour terrain "part trop a gauche et a droite" une fois le tilt
# correct (le pan devient tres visible/large une fois le tilt vers l'horizontale).
PAN_SCALE = 0.15
TILT_SCALE = 0.35

def make_gpj_from_curve(curve_name, out_name, groups, duration=None):
    """groups = [(fixtures_gen, channels_str, other_channels), ...] - plusieurs familles pan/tilt
    a la fois (ex Lyre + minibeam) sur la meme courbe."""
    path = os.path.join(CURVES_PANTILT, curve_name + ".gcv")
    return make_gpj_curve(path, curve_name, out_name, groups, "Pan/Tilt/uPan/uTilt", duration, scale=(PAN_SCALE, TILT_SCALE))

# Les 2 familles a pan/tilt ensemble (mouvement commun Lyre + minibeam).
MOVE_GROUPS = [(LYRE_GEN, LYRE_CH, [c for c in LYRE_OTHER if c not in ("dimmer",)]),
               (MINIBEAM_GEN, MINIBEAM_CH, [c for c in MINIBEAM_OTHER if c not in ("dimmer",)])]

# ---------- Couleurs channel-mixees ----------
def compact_c(rgba):
    r, g, b, a = rgba
    return [chan(0, "dimmer", 255), chan(1, "red", r), chan(2, "green", g), chan(3, "blue", b), chan(4, "white", 0), chan(5, "amber", a)]

def lyre_c(rgb_w):
    r, g, b, w = rgb_w
    return [chan(6, "dimmer", 255), chan(7, "red", r), chan(8, "green", g), chan(9, "blue", b), chan(10, "white", w)]

def minibeam_open(dim=255):
    # Pas de vrai mixage RGB (canal macro uniquement) : reste ouvert/blanc par defaut, pilote via
    # GOBO/MANUEL/STROBE plutot que COULEUR.
    return [chan(5, "dimmer", dim), chan(7, "rainbow_color", 10), chan(8, "gobo", 0)]

# 8 couleurs (RGBA pour COMPACT, RGB+White pour LYRE - meme teinte, colonne alignee).
COLORS = [
    ("Blanc",  (255,255,255,0), (255,255,255,255), "white.png"),
    ("Rouge",  (255,0,0,0),     (255,0,0,0),        "par_can_red.png"),
    ("Orange", (255,45,0,0),    (255,45,0,0),       "par_can_orange.png"),
    ("Jaune",  (255,255,0,0),   (255,255,0,0),      "par_can_yellow.png"),
    ("Vert",   (0,255,0,0),     (0,255,0,0),        "par_can_green.png"),
    ("Bleu",   (0,0,255,0),     (0,0,255,0),        "par_can_blue.png"),
    ("Violet", (130,0,255,0),   (130,0,255,0),      "magenta.png"),
    ("Rose",   (255,0,120,0),   (255,0,120,0),      "par_can_pink.png"),
]
ICON_DIR = "/Applications/SweetLight/TheLightingController/editor_fixtures_icons/channel"
def icon(name): return os.path.join(ICON_DIR, name)
ICONS_DIR = "/Users/mac-m3-michel/workspace/sweetLight/assets/icons"
def icon2(name): return os.path.join(ICONS_DIR, name)
ASSETS = "/Users/mac-m3-michel/workspace/sweetLight/assets"
def gobo_img(name): return os.path.join(ASSETS, "gobos", name + ".png")
def move_img(curve): return os.path.join(ASSETS, "moves", curve + ".png")

# ===================== Pages (accumulateur commun) =====================
pages = {}
MIDI = {}
FADER_BUTTONS = set()
FORCE_TITLE = {}
SPEED_TITLES = set()

def add(page, col, line, fname, title, rgb=None, img=None):
    pages.setdefault(page, []).append((col, line, fname, title, rgb, img))

# ===================== Codes LED APC40 mkII (relevees sur Summer, memes codes sur cette install) =====
# "bleu" corrige : le code 45 (releve sur Summer) n'est pas bleu sur cette install - retour terrain,
# le vrai bleu est le code 3 (utilise par defaut sur le 1er mouvement CERCLE, LINE_LED ligne 1).
# Consequence : "blanc" et "bleu" partagent maintenant le meme code (3,1) - a signaler si un jour un
# bouton "Blanc" doit vraiment etre distingue visuellement d'un bouton "Bleu" sur la moulinette APC.
APC = {"blanc": (3,1), "rouge": (5,6), "orange": (8,61), "jaune": (11,18), "vert": (21,23),
       "bleu": (3,1), "violet": (49,50), "rose": (53,54)}
COLOR_WORDS = [("blanc","blanc"),("rouge","rouge"),("orange","orange"),("jaune","jaune"),
               ("vert","vert"),("bleu","bleu"),("violet","violet"),("rose","rose")]
def led_for(title):
    low = " " + title.lower() + " "
    for w, key in COLOR_WORDS:
        if w in low: return APC[key]
    return None

# ===================== PAGE COULEUR (COMPACT + LYRE, memes teintes colonne par colonne) =====================
for c, (nm, rgba, rgbw, ic) in enumerate(COLORS, start=1):
    tag = nm.upper().replace(" ", "_")
    title = "COMPACT_COULEUR_%s" % tag
    fn = write_scene(title + ".scex", COMPACT, COMPACT_MODEL, [(500, uniform(compact_c(rgba)))])
    add("COULEUR", c, 1, fn, title, rgba[0]*65536 + rgba[1]*256 + rgba[2])
    title = "LYRE_COULEUR_%s" % tag
    fn = write_scene(title + ".scex", LYRE, LYRE_MODEL, [(500, uniform(lyre_c(rgbw)))])
    add("COULEUR", c, 2, fn, title, rgba[0]*65536 + rgba[1]*256 + rgba[2])
# Fondu couleur lent/rapide : COMPACT canal "animation" (7) zone "color fading" (128-159) + vitesse
# via "effect_speed" (8) ; LYRE canal "color jump" (12) zones degrade (161-255) - vitesse propre a
# la courbe, pas de canal vitesse dedie -> 2 valeurs figees (HYPOTHESE a caler en direct).
title = "COMPACT_COULEUR_RAPIDE"
fn = write_scene(title + ".scex", COMPACT, COMPACT_MODEL, [(500, uniform([chan(0,"dimmer",255),chan(7,"animation",140),chan(8,"effect_speed",250)]))])
add("COULEUR", 1, 3, fn, title)
title = "COMPACT_COULEUR_LENTE"
fn = write_scene(title + ".scex", COMPACT, COMPACT_MODEL, [(500, uniform([chan(0,"dimmer",255),chan(7,"animation",140),chan(8,"effect_speed",20)]))])
add("COULEUR", 2, 3, fn, title)
title = "LYRE_COULEUR_RAPIDE"
fn = write_scene(title + ".scex", LYRE, LYRE_MODEL, [(500, uniform([chan(6,"dimmer",255),chan(12,"color jump",255)]))])
add("COULEUR", 3, 3, fn, title)
title = "LYRE_COULEUR_LENTE"
fn = write_scene(title + ".scex", LYRE, LYRE_MODEL, [(500, uniform([chan(6,"dimmer",255),chan(12,"color jump",165)]))])
add("COULEUR", 4, 3, fn, title)

# ===================== PAGE GOBO (minibeamstpotled : seule fixture avec une vraie roue de gobo) =====
# Canal gobo (index 8) : 0-9 ouvert, puis 7 positions statiques sur 10-79 (pas de 10, centre de
# plage), 150-255 = roue auto. Image = vignette generique (pas de planche photo pour ce fixture -
# a produire plus tard avec tools/gen_thumbs.py si besoin).
GOBOS = [("Ouvert", 0)] + [("Gobo%d" % (i+1), 15 + i*10) for i in range(7)] + [("Auto", 200)]
for c, (nm, val) in enumerate(GOBOS, start=1):
    title = "MINIBEAM_GOBO_%s" % nm.upper()
    fn = write_scene(title + ".scex", MINIBEAM, MINIBEAM_MODEL,
                      [(500, uniform([chan(5,"dimmer",255), chan(8,"gobo",val)]))])
    add("GOBO", c, 1, fn, title, img=icon2("gobo.png") if c > 1 else icon2("open.png"))
    FORCE_TITLE[title] = nm.upper()

# ===================== PAGE MANUEL (LYRE rotation effet + minibeam prisme) =====================
# LYRE canal "rotation" (5) : plage 192-255 "rotation" continue - bas=lent haut=rapide (HYPOTHESE,
# l'utilisateur verifie/edite en direct). 128-191 = "forward" (fonction separee, non utilisee ici).
ROTATION_PRESETS = [("LENTE", 195), ("MOYENNE", 225), ("RAPIDE", 255)]
for c, (nm, val) in enumerate(ROTATION_PRESETS, start=1):
    title = "LYRE_ROTATION_%s" % nm
    fn = write_scene(title + ".scex", LYRE, LYRE_MODEL,
                      [(500, uniform([chan(6,"dimmer",255), chan(5,"rotation",val)]))])
    add("MANUEL", c, 1, fn, title, img=icon2("rotate.png")); FORCE_TITLE[title] = "ROT " + nm[:4]
# Minibeam prisme (canal prism3D, index 9) : pulse_close/pulse_open/rotate.
MANUEL_PRISM = [("PULSE_FERME", 60, "prism.png"), ("PULSE_OUVERT", 140, "prism.png"), ("ROTATION", 200, "rotate.png")]
for c, (nm, val, ic) in enumerate(MANUEL_PRISM, start=1):
    title = "MINIBEAM_PRISME_%s" % nm
    fn = write_scene(title + ".scex", MINIBEAM, MINIBEAM_MODEL,
                      [(500, uniform([chan(5,"dimmer",255), chan(9,"prism3D",val)]))])
    add("MANUEL", c, 2, fn, title, img=icon2(ic))

# ===================== PAGE STROBE (3 familles) =====================
for c, (nm, val) in enumerate([("LENT",60), ("MOYEN",140), ("RAPIDE",255)], start=1):
    title = "COMPACT_STROBE_%s" % nm
    fn = write_scene(title + ".scex", COMPACT, COMPACT_MODEL, [(500, uniform([chan(0,"dimmer",255),chan(6,"strobe_dimmer",val)]))])
    add("STROBE", c, 1, fn, title, img=icon2("strobe.png"))
for c, (nm, val) in enumerate([("LENT",40), ("MOYEN",120), ("RAPIDE",220)], start=1):
    title = "LYRE_STROBE_%s" % nm
    fn = write_scene(title + ".scex", LYRE, LYRE_MODEL, [(500, uniform([chan(6,"dimmer",255),chan(11,"strobe_speed",val)]))])
    add("STROBE", c, 2, fn, title, img=icon2("strobe.png"))
for c, (nm, val) in enumerate([("LENT",40), ("MOYEN",120), ("RAPIDE",220)], start=1):
    title = "MINIBEAM_STROBE_%s" % nm
    fn = write_scene(title + ".scex", MINIBEAM, MINIBEAM_MODEL, [(500, uniform([chan(5,"dimmer",255),chan(6,"strobe_speed",val)]))])
    add("STROBE", c, 3, fn, title, img=icon2("strobe.png"))

# ===================== PAGE FX =====================
def chase_scene(prefix_title, fixtures, model, on_chans, off_chans, step_len=150):
    ids = [x[0] for x in fixtures]
    def step(k):
        def f(fid):
            return on_chans if ids.index(fid) == k else off_chans
        return f
    title = prefix_title
    fn = write_scene(title + ".scex", fixtures, model, [(step_len, step(k)) for k in range(len(fixtures))])
    return fn, title

fn, title = chase_scene("FX_CHASE_COMPACT", COMPACT, COMPACT_MODEL,
                         [chan(0,"dimmer",255),chan(1,"red",255),chan(2,"green",255),chan(3,"blue",255)],
                         [chan(0,"dimmer",0)])
add("FX", 1, 1, fn, title); SPEED_TITLES.add(title)
fn, title = chase_scene("FX_CHASE_LYRE", LYRE, LYRE_MODEL,
                         [chan(6,"dimmer",255),chan(7,"red",255),chan(8,"green",255),chan(9,"blue",255)],
                         [chan(6,"dimmer",0)])
add("FX", 2, 1, fn, title); SPEED_TITLES.add(title)
title = "FX_BLACKOUT"
fn = write_multi(title + ".scex", [(LYRE,LYRE_MODEL,[chan(6,"dimmer",0)]),
                                    (COMPACT,COMPACT_MODEL,[chan(0,"dimmer",0)]),
                                    (MINIBEAM,MINIBEAM_MODEL,[chan(5,"dimmer",0)])])
add("FX", 3, 1, fn, title, img=icon2("lamp_off.png"))
title = "FX_POWER"
fn = write_multi(title + ".scex", [(LYRE,LYRE_MODEL,[chan(6,"dimmer",255),chan(7,"red",255),chan(8,"green",255),chan(9,"blue",255),chan(10,"white",255)]),
                                    (COMPACT,COMPACT_MODEL,[chan(0,"dimmer",255),chan(1,"red",255),chan(2,"green",255),chan(3,"blue",255),chan(4,"white",255)]),
                                    (MINIBEAM,MINIBEAM_MODEL,[chan(5,"dimmer",255),chan(7,"rainbow_color",10),chan(8,"gobo",0)])])
add("FX", 4, 1, fn, title, img=icon2("lamp_on.png"))

def machines_step(n_pairs_on):
    groups = []
    for k, pair in enumerate(LYRE_PAIRS):
        on = k < n_pairs_on
        groups.append((pair, LYRE_MODEL, [chan(6,"dimmer",255 if on else 0), chan(7,"red",255 if on else 0), chan(8,"green",255 if on else 0), chan(9,"blue",255 if on else 0)]))
    for k, pair in enumerate(COMPACT_PAIRS):
        on = k < n_pairs_on
        groups.append((pair, COMPACT_MODEL, [chan(0,"dimmer",255 if on else 0),
                                          chan(1,"red",255 if on else 0), chan(2,"green",255 if on else 0), chan(3,"blue",255 if on else 0)]))
    return groups
title = "FX_ALLUMAGE_PROGRESSIF"
fn = write_seq(title + ".scex", [(300, machines_step(k)) for k in range(0, 5)])
add("FX", 1, 2, fn, title); FADER_BUTTONS.add(title)

HAZER_PRESETS = [("MIN", 60), ("MID", 125), ("FULL", 255), ("STOP", 0)]
for c, (nm, v) in enumerate(HAZER_PRESETS, start=1):
    title = "FX_HAZER_%s" % nm
    fn = write_scene(title + ".scex", HAZER, HAZER_MODEL, [(500, uniform([chan(0,"fog",v),chan(1,"fan",v)]))])
    add("FX", c, 3, fn, title, img=icon2("hazer.png"))

def pair_chase(prefix_title, pairs, model, on_chans, off_chans):
    def step(k):
        active = pairs[k % len(pairs)]
        active_ids = [x[0] for x in active]
        def f(fid):
            return on_chans if fid in active_ids else off_chans
        return f
    all_fx = [x for pair in pairs for x in pair]
    fn = write_scene(prefix_title + ".scex", all_fx, model, [(300, step(k)) for k in range(len(pairs))])
    return fn, prefix_title
fn, title = pair_chase("FX_PAIRES_COMPACT", COMPACT_PAIRS, COMPACT_MODEL,
                        [chan(0,"dimmer",255),chan(1,"red",255),chan(2,"green",255),chan(3,"blue",255)],
                        [chan(0,"dimmer",0)])
add("FX", 1, 4, fn, title); SPEED_TITLES.add(title)
fn, title = pair_chase("FX_PAIRES_LYRE", LYRE_PAIRS, LYRE_MODEL,
                        [chan(6,"dimmer",255),chan(7,"red",255),chan(8,"green",255),chan(9,"blue",255)],
                        [chan(6,"dimmer",0)])
add("FX", 2, 4, fn, title); SPEED_TITLES.add(title)

title = "FX_ETINCELLES"
fn = write_multi(title + ".scex", [(SPARK, SPARK_MODEL, [chan(0,"dimmer",255),chan(1,"Function",0),chan(2,"Heating",50)])])
add("FX", 3, 4, fn, title)

title = "FX_PULSE"
fn = make_gpj_curve(os.path.join(BASE, "Editor", "Generator", "curves", "pulse.gcv"), "pulse", title,
                     [(LYRE_GEN, LYRE_CH, [c for c in LYRE_OTHER if c != "dimmer"]),
                      (COMPACT_GEN, COMPACT_CH, [c for c in COMPACT_OTHER if c != "dimmer"])],
                     "dimmer")
add("FX", 4, 4, fn, title)

# ===================== PAGE MOUVEMENT (LYRE + MINIBEAM : generateurs .gpj a partir des courbes) =====
MOVE_LAYOUT = [
    (1, [(1, "circle_cw",   "CERCLE")]),
    (2, [(1, "eight_small", "HUIT_PETIT"), (2, "eight", "HUIT")]),
    (3, [(1, "wave",        "VAGUE")]),
    (4, [(1, "square1_ccw", "CARRE1_INV"), (2, "square1_cw", "CARRE1")]),
    (5, [(1, "star_ccw",    "ETOILE_INV"), (2, "star_cw", "ETOILE"), (3, "star_small", "ETOILE_PETIT")]),
    (6, [(1, "square2_ccw", "CARRE2_INV"), (2, "square2_cw", "CARRE2")]),
    (7, [(1, "crown_vert",  "COURONNE_VERT"), (2, "crown", "COURONNE")]),
    (8, [(1, "star_rev",    "ETOILE_REV")]),
]
move_files = {}
for col, cells in MOVE_LAYOUT:
    for ln, curve, title in cells:
        fn = make_gpj_from_curve(curve, title, MOVE_GROUPS)
        move_files[curve] = fn
        add("MOUVEMENT", col, ln, fn, title, img=move_img(curve))

# ===================== PAGE DJ LIVE (busking : LYRE + COMPACT + MINIBEAM, tout sur un onglet) =====
DJ = "DJ LIVE"
COL_BY_NAME = {nm: (rgba, rgbw) for nm, rgba, rgbw, ic in COLORS}

def dj_col_lyre(rgbw):
    return [chan(6, "dimmer", 255), chan(7, "red", rgbw[0]), chan(8, "green", rgbw[1]), chan(9, "blue", rgbw[2]), chan(10, "white", rgbw[3])]

for c, (nm, rgba, rgbw, ic) in enumerate(COLORS, start=1):
    tag = nm.upper().replace(" ", "_")
    fn = write_multi("DJ_COL_%s.scex" % tag,
                     [(LYRE, LYRE_MODEL, dj_col_lyre(rgbw)), (COMPACT, COMPACT_MODEL, compact_c(rgba))])
    add(DJ, c, 1, fn, "DJ_COL_%s" % tag, rgba[0]*65536 + rgba[1]*256 + rgba[2])

DJ_MOVES = [("circle_cw","CERCLE"), ("eight","HUIT"), ("wave","VAGUE"), ("crown","COURONNE"),
            ("star_cw","ETOILE"), ("square1_cw","CARRE"), ("square2_cw","LOSANGE"), ("star_rev","ENTRELACE")]
for c, (curve, lbl) in enumerate(DJ_MOVES, start=1):
    add(DJ, c, 2, move_files[curve], "DJ_MOVE_%s" % lbl, img=move_img(curve))

def dj_dim(v):
    return [(LYRE, LYRE_MODEL, [chan(6,"dimmer",v)]),
            (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",v)])]
def dj_chase(k):
    lf = lambda i, fid: [chan(6,"dimmer",255 if i == k else 0), chan(7,"red",255), chan(8,"green",255), chan(9,"blue",255)]
    cf = lambda i, fid: [chan(0,"dimmer",255 if i % 4 == k % 4 else 0), chan(1,"red",255), chan(2,"green",255), chan(3,"blue",255)]
    return [(LYRE, LYRE_MODEL, lf), (COMPACT, COMPACT_MODEL, cf)]
def dj_police(k):
    red = (k % 2 == 0)
    return [(LYRE, LYRE_MODEL, [chan(6,"dimmer",255), chan(7,"red",255 if red else 0), chan(8,"green",0), chan(9,"blue",0 if red else 255)]),
            (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",255), chan(1,"red",255 if red else 0), chan(2,"green",0), chan(3,"blue",0 if red else 255)])]
def dj_strobe(v):
    return [(LYRE, LYRE_MODEL, [chan(6,"dimmer",v), chan(11,"strobe_speed",220)]),
            (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",v), chan(6,"strobe_dimmer",220)])]
def dj_wash(rgbw, rgba):
    return [(LYRE, LYRE_MODEL, dj_col_lyre(rgbw)), (COMPACT, COMPACT_MODEL, compact_c(rgba))]

dj_fx = [
    ("PULSE",   write_seq("DJ_FX_PULSE.scex",   [(260, dj_dim(255)), (260, dj_dim(45))])),
    ("CHASE",   write_seq("DJ_FX_CHASE.scex",   [(140, dj_chase(k)) for k in range(4)])),
    ("POLICE",  write_seq("DJ_FX_POLICE.scex",  [(170, dj_police(k)) for k in range(6)])),
    ("STROBE",  write_seq("DJ_FX_STROBE.scex",  [(70, dj_strobe(255)), (70, dj_strobe(0))])),
    ("ARCENCIEL", write_seq("DJ_FX_ARCENCIEL.scex", [(300, dj_wash(rgbw, rgba)) for nm, rgba, rgbw, ic in COLORS])),
    ("FLASH",   write_seq("DJ_FX_FLASH.scex",   [(90, dj_dim(255)), (240, dj_dim(0))])),
    ("BUILD",   write_seq("DJ_FX_BUILD.scex",   [(300, machines_step(k)) for k in range(5)])),
    ("BOUNCE",  write_seq("DJ_FX_BOUNCE.scex",  [(150, dj_chase(k)) for k in [0,1,2,3,2,1]])),
]
for c, (lbl, fn) in enumerate(dj_fx, start=1):
    title = "DJ_FX_%s" % lbl
    add(DJ, c, 3, fn, title)
    if lbl != "BUILD":
        SPEED_TITLES.add(title)
FADER_BUTTONS.add("DJ_FX_BUILD")

def dj_look(*names):
    vals = [COL_BY_NAME[n] for n in names]
    lf = lambda i, fid: dj_col_lyre(vals[i % len(vals)][1])
    cf = lambda i, fid: compact_c(vals[i % len(vals)][0])
    return [(LYRE, LYRE_MODEL, lf), (COMPACT, COMPACT_MODEL, cf)]
DJ_LOOKS = [
    ("DJ",       ("Rouge", "Bleu", "Vert", "Rose")),
    ("ROCK",     ("Rouge",)),
    ("WARM",     ("Orange",)),
    ("COLD",     ("Bleu",)),
    ("DISCO",    ("Rouge", "Vert", "Bleu", "Rose", "Jaune", "Violet")),
    ("UV",       ("Violet",)),
    ("NATURE",   ("Vert",)),
    ("FESTIVAL", ("Rose", "Orange", "Bleu", "Vert")),
]
for c, (lbl, names) in enumerate(DJ_LOOKS, start=1):
    fn = write_multi("DJ_LOOK_%s.scex" % lbl, dj_look(*names))
    add(DJ, c, 4, fn, "DJ_LOOK_%s" % lbl)

def dj_full(rgbw, rgba):
    return [(LYRE, LYRE_MODEL, dj_col_lyre(rgbw)),
            (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",255), chan(1,"red",rgba[0]), chan(2,"green",rgba[1]),
                              chan(3,"blue",rgba[2]), chan(5,"amber",rgba[3])])]
dj_impacts = [
    ("FLASH_BLANC", write_multi("DJ_HIT_BLANC.scex", dj_full((255,255,255,255), (255,255,255,0)))),
    ("FLASH_ROUGE", write_multi("DJ_HIT_ROUGE.scex", dj_full((255,0,0,0), (255,0,0,0)))),
    ("FLASH_BLEU",  write_multi("DJ_HIT_BLEU.scex",  dj_full((0,0,255,0), (0,0,255,0)))),
    ("BLINDERS",    write_multi("DJ_HIT_BLINDERS.scex",
                    [(LYRE, LYRE_MODEL, [chan(6,"dimmer",255), chan(7,"red",255), chan(8,"green",255), chan(9,"blue",255), chan(10,"white",255)]),
                     (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",255), chan(1,"red",255), chan(2,"green",180), chan(3,"blue",110), chan(5,"amber",255)])])),
    ("STROBE",      write_multi("DJ_HIT_STROBE.scex",
                    [(LYRE, LYRE_MODEL, [chan(6,"dimmer",255), chan(11,"strobe_speed",220)]),
                     (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",255), chan(6,"strobe_dimmer",220), chan(1,"red",255), chan(2,"green",255), chan(3,"blue",255)])])),
    ("PRISME",      write_multi("DJ_HIT_PRISME.scex",
                    [(MINIBEAM, MINIBEAM_MODEL, [chan(5,"dimmer",255), chan(7,"rainbow_color",10), chan(9,"prism3D",200)])])),
    ("ETINCELLES",  write_multi("DJ_HIT_ETINCELLES.scex",
                    [(SPARK, SPARK_MODEL, [chan(0,"dimmer",255), chan(1,"Function",0), chan(2,"Heating",50)])])),
    ("BLACKOUT",    write_multi("DJ_HIT_BLACKOUT.scex",
                    [(LYRE, LYRE_MODEL, [chan(6,"dimmer",0)]),
                     (COMPACT, COMPACT_MODEL, [chan(0,"dimmer",0)]),
                     (MINIBEAM, MINIBEAM_MODEL, [chan(5,"dimmer",0)])])),
]
for c, (lbl, fn) in enumerate(dj_impacts, start=1):
    img = icon2("strobe.png") if lbl == "STROBE" else icon2("lamp_off.png") if lbl == "BLACKOUT" else None
    add(DJ, c, 5, fn, "DJ_HIT_%s" % lbl, img=img)

# ===================== Construction des pages live.ini =====================
def midi_block(note, on, off):
    return ["trigger_midi_device = 0","trigger_midi_channel = 1","trigger_midi_type = 0",
            "trigger_midi_note = %d" % note,"trigger_midi_control = 0",
            "trigger_midiout_device = 0","trigger_midiout_channel = 1","trigger_midiout_type = 0",
            "trigger_midiout_note = %d" % note,"trigger_midiout_data = %d" % on,"trigger_midiout_data_off = %d" % off]

LINE_LED = {1: APC["blanc"], 2: APC["bleu"], 3: APC["violet"], 4: APC["rose"]}
for pname, btns in pages.items():
    for (col, ln, bname, title, rgb, img) in btns:
        if ln > 5: continue
        note = (5 - ln) * 8 + (col - 1)
        on, off = led_for(title) or LINE_LED.get(ln, APC["blanc"])
        MIDI[title] = (note, on, off)

def build_page_block(name, btns, PN):
    L = ["[page%d]" % PN, "name = %s" % name, "nb_buttons = %d" % len(btns)]
    for n, (col, lnn, bname, title, rgb, img) in enumerate(btns, start=1):
        if title in FORCE_TITLE:
            shown_title = FORCE_TITLE[title]
        else:
            shown_title = "" if (img is not None and name not in ("FX", "MANUEL", "STROBE", "GOBO")) else title
        L += ["[page%d_button%d]" % (PN, n), "line = %d" % lnn, "column = %d" % col, "name = %s" % bname, "title = %s" % shown_title]
        if rgb is not None: L.append("color = %d" % rgb)
        if img is not None: L.append("imgpath = %s" % img)
        if title in FADER_BUTTONS:
            L += ["fader = yes", "preset_step = 0"]
        else:
            speed = bname.endswith(".gpj") or title in SPEED_TITLES
            L.append("masterspeedfader = %d" % (1 if speed else 0))
            if speed: L += ["speed_slider = yes", "preset_step = 5"]
        if title in MIDI: L += midi_block(*MIDI[title])
    return "\n".join(L) + "\n"

content = open(LIVE, encoding='utf-8', errors='replace').read()

import re
board_i = content.index("[board]")
first_pg = re.search(r'(?m)^\[page\d+\]\s*$', content)
pstart = first_pg.start() if first_pg else board_i
head, tail = content[:pstart], content[board_i:]
PAGE_ORDER = ["DJ LIVE", "COULEUR", "GOBO", "MANUEL", "STROBE", "FX", "MOUVEMENT"]
used_names = [nm for nm in PAGE_ORDER if nm in pages]
our_blocks = [build_page_block(nm, pages[nm], i + 1) for i, nm in enumerate(used_names)]
content = head + "".join(our_blocks) + tail
content = re.sub(r'(\[page\]\nnumber = )\d+', r'\g<1>' + str(len(our_blocks)), content, count=1)

def flist(ids, ch):
    return "".join("%d,%s|" % (i, ch) for i in ids)
# Vitesse : type_fader0=1 (speed) scale deja la duree des courbes (.gpj masterspeedfader=1), mais ca
# ne pilote pas le limiteur de vitesse physique du moteur pan/tilt du fixture (canal "motor speed"
# Lyre / "pantilt_speed" minibeam) - sans ca le mouvement reel reste borne par la derniere valeur
# laissee sur ce canal. On ajoute donc aussi la liste de canaux (comme pour Puissance) pour que le
# meme fader pilote le logiciel ET le canal DMX de vitesse moteur.
vitesse = flist(LYRE_IDS, "motor speed") + flist(MINIBEAM_IDS, "pantilt_speed")
puissance = flist(LYRE_IDS, "dimmer") + flist(COMPACT_IDS, "dimmer") + flist(MINIBEAM_IDS, "dimmer")
hazer_fog = flist([HAZER[0][0]], "fog")
hazer_fan = flist([HAZER[0][0]], "fan")
rotation = flist(LYRE_IDS, "rotation")
# Vitesse de changement de couleur : seul le COMPACT a un canal dedie ("effect_speed", pilote deja
# via COMPACT_COULEUR_RAPIDE/LENTE) - la LYRE n'a pas de canal de vitesse separe pour "color jump"
# (la vitesse est encodee dans la zone du canal lui-meme), donc pas inclus ici.
coul_speed = flist(COMPACT_IDS, "effect_speed")
N_FADERS = 6
mf = ("[master_faders]\n"
      "type_fader0 = 1\ncaption_fader0 = Vitesse\nv8_master_fader0 = %s\n"
      "type_fader1 = 0\ncaption_fader1 = Puissance faisceau\nv8_master_fader1 = %s\n"
      "type_fader2 = 0\ncaption_fader2 = Hazer Fog\nv8_master_fader2 = %s\n"
      "type_fader3 = 0\ncaption_fader3 = Hazer Fan\nv8_master_fader3 = %s\n"
      "type_fader4 = 0\ncaption_fader4 = Rotation Lyre\nv8_master_fader4 = %s\n"
      "type_fader5 = 0\ncaption_fader5 = Vitesse Couleur\nv8_master_fader5 = %s\n"
     ) % (vitesse, puissance, hazer_fog, hazer_fan, rotation, coul_speed)
content = re.sub(r'master_faders = \d+\n', '', content)
content = content.replace("[live]\n", "[live]\nmaster_faders = %d\n" % N_FADERS, 1)
missing_binds = ""
for n in range(1, N_FADERS + 1):
    if not re.search(r'(?m)^fader%d_midi_' % n, content):
        missing_binds += (
            "fader%d_midi_device = 0\nfader%d_midi_channel = %d\nfader%d_midi_type = 1\nfader%d_midi_note = 7\nfader%d_midi_control = 0\n"
            % (n, n, n, n, n, n))
if missing_binds:
    content = content.replace("master_faders = %d\n" % N_FADERS, "master_faders = %d\n" % N_FADERS + missing_binds, 1)
if re.search(r'fade_time = \d+', content):
    content = re.sub(r'fade_time = \d+', 'fade_time = 0', content)
else:
    content = content.replace("[live]\n", "[live]\nfade_time = 0\n", 1)
mi = content.find("[master_faders]")
if mi != -1:
    nxt = content.find("\n[", mi + 1)
    content = content[:mi] + content[nxt + 1:]
content = content.replace("[page]\n", mf + "[page]\n", 1)

if not re.search(r'(?m)^buttonstab1_midi_', content):
    tabs = "".join(
        ("buttonstab{n}_midi_device = 0\nbuttonstab{n}_midi_channel = {n}\nbuttonstab{n}_midi_type = 0\n"
         "buttonstab{n}_midi_note = 52\nbuttonstab{n}_midi_control = 0\n"
         "buttonstab{n}_midiout_device = 0\nbuttonstab{n}_midiout_channel = {n}\nbuttonstab{n}_midiout_type = 0\n"
         "buttonstab{n}_midiout_note = 52\nbuttonstab{n}_midiout_data = -1\nbuttonstab{n}_midiout_data_off = -1\n"
         ).format(n=n) for n in range(1, 9))
    content = content.replace("[live]\n", "[live]\n" + tabs, 1)
for n in range(1, len(our_blocks) + 1):
    content = re.sub(r'(buttonstab%d_midiout_data = )-?\d+' % n, r'\g<1>1', content, count=1)
    content = re.sub(r'(buttonstab%d_midiout_data_off = )-?\d+' % n, r'\g<1>0', content, count=1)

nb = len(used_names)
board = "[board]\nnumber = %d\n" % nb
board += "".join("[board%d]\nscreen = %d\npage = %d\n" % (k, k - 1, k) for k in range(1, nb + 1))
board += "".join("[screen%d]\ntitle = %s\nwindow = no\n" % (k - 1, used_names[k - 1]) for k in range(1, nb + 1))
content = content[:content.index("[board]")] + board

open(LIVE, 'w', encoding='utf-8').write(content)

print("OK : %d pages | %d boutons | MIDI sur %d boutons" % (len(our_blocks), sum(len(b) for b in pages.values()), len(MIDI)))
