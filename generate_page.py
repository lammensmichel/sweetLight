#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere pour le rig BSW (ChallengerBSW 20ch) + PAR ADJ + hazer + machines a etincelles :
   - les scenes .scex (couleurs, gobos, prisme, strobe, effets)
   - les pages 'COULEUR', 'GOBO', 'MANUEL', 'STROBE', 'FX' dans live.ini (mapping APC40 mkII)
Idempotent (remplace nos pages a chaque run). Usage : python3 generate_page.py [dossier_du_show]"""
import os, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/Users/mac-m3-michel/workspace/sweetLight/v1"
SCENES = os.path.join(BASE, "scenes")
LIVE = os.path.join(BASE, "Live", "live.ini")
OUT_GEN = os.path.join(BASE, "Editor", "Generator", "projects")
CURVES_PANTILT = os.path.join(BASE, "Editor", "Generator", "curves_pantilt")

# ---------- Fixtures (id, nom) --------- (show summer-joe-2026, verifie via fixtures.ini) ----------
BSW_ADDR = [65, 85, 105, 125, 145, 165, 185, 205]
BSW = [(1787608376, "ChallengerBSW(20ch)")] + [
    (1787608376 + k, "ChallengerBSW(20ch) #%d" % (k + 1)) for k in range(1, 8)
]
BSW_MODEL = "ChallengerBSW(20ch)"
BSW_IDS = [x[0] for x in BSW]
BSW_GEN = [(fid, addr - 1, nm) for (fid, nm), addr in zip(BSW, BSW_ADDR)]

PAR_ADDR = [1, 9, 17, 25, 33, 41, 49, 57]
PAR = [(1787608350, "par adj "), (1787608351, "par adj  #2"), (1787608352, "par adj  #3"),
       (1787608353, "par adj  #4"), (1787608354, "par adj  #5"), (1787608355, "par adj  #6"),
       (1787608356, "par adj  #7"), (1787608357, "par adj  #8")]
PAR_MODEL = "par adj "
PAR_IDS = [x[0] for x in PAR]

HAZER = [(1787608391, "hazer")]
HAZER_MODEL = "hazer"

SPARK = [(1787608407, "machine étincelles")]
SPARK_MODEL = "machine étincelles"

# Groupes (briques reutilisees dans les scenes FX) : paires dans chaque famille + union des 2 familles.
BSW_PAIRS = [(BSW[0:2]), (BSW[2:4]), (BSW[4:6]), (BSW[6:8])]
PAR_PAIRS = [(PAR[0:2]), (PAR[2:4]), (PAR[4:6]), (PAR[6:8])]
ALL_MACHINES = BSW + PAR

# ---------- Canaux (index positionnel, verifies via les profils .txt du show) ----------
# BSW ChallengerBSW(20ch) : 0 pan,1 upan,2 tilt,3 utilt,4 pantilt_speed,5 mode,6 pan_tilt_macro,
# 7 pan_tilt_macro_speed,8 color,9 gobo,10 gobo2,11 gobo_rotate2,12 iris,13 prism,14 prism_rotate,
# 15 focus,16 shutter,17 dimmer,18 udimmer,19 control.
# PAR par adj : 0 red,1 green,2 blue,3 amber,4 dimmer,5 strobe_effect,6/7 color_macro mode.
# hazer : 0 fog,1 fan. machine etincelles : 0 dimmer,1 Function,2 Heating.

BSW_CH = "pan,upan,tilt,utilt,pantilt_speed,mode,pan_tilt_macro,pan_tilt_macro_speed,color,gobo,gobo2,gobo_rotate2,iris,prism,prism_rotate,focus,shutter,dimmer,udimmer,control"
BSW_OTHER = ["pantilt_speed","mode","pan_tilt_macro","pan_tilt_macro_speed","color","gobo","gobo2",
             "gobo_rotate2","iris","prism","prism_rotate","focus","shutter","dimmer","udimmer","control"]

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

# ---------- Couleurs channel-mixees (reutilisees telles quelles, deja calibrees pour ce PAR) ----------
def par_c(rgba):
    r, g, b, a = rgba
    return [chan(4, "dimmer", 255), chan(0, "red", r), chan(1, "green", g), chan(2, "blue", b), chan(3, "amber", a)]

def bsw_c(slot):
    return [chan(16, "shutter", 12), chan(17, "dimmer", 255), chan(8, "color", slot)]

# 8 couleurs alignees PAR/LYRE (meme colonne = meme teinte). La roue LYRE n'a que 9 slots nommes
# (dont "open"=blanc) ; on en garde 8 pour tenir sur la grille APC40 (8 colonnes max/ligne), on laisse
# de cote "light_blue" (55) qui fait doublon visuel avec Bleu Fonce.
COLORS = [
    ("Blanc",  (255,255,255,0), 0),
    ("Rouge",  (255,0,0,0),     19),
    ("Orange", (255,45,0,0),    25),
    ("Jaune",  (255,255,0,0),   31),
    ("Vert",   (0,255,0,0),     37),
    ("Bleu",   (0,0,255,0),     43),
    ("Violet", (130,0,255,0),   49),
    ("Rose",   (255,0,120,0),   61),
]

# ===================== Pages (accumulateur commun) =====================
pages = {}         # nom_page -> [(col,line,fichier,titre,color_rgb_or_None)]
MIDI = {}          # titre -> (note, led_on, led_off)
FADER_BUTTONS = set()

def add(page, col, line, fname, title, rgb=None):
    pages.setdefault(page, []).append((col, line, fname, title, rgb))

# ===================== Codes LED APC40 mkII (relevees sur cette install) =====================
APC = {"blanc": (3,1), "rouge": (5,6), "orange": (8,61), "jaune": (11,18), "vert": (21,23),
       "bleu": (45,47), "violet": (49,50), "rose": (53,54)}
COLOR_WORDS = [("blanc","blanc"),("rouge","rouge"),("orange","orange"),("jaune","jaune"),
               ("vert","vert"),("bleu","bleu"),("violet","violet"),("rose","rose")]
def led_for(title):
    low = " " + title.lower() + " "
    for w, key in COLOR_WORDS:
        if w in low: return APC[key]
    return None

# ===================== PAGE COULEUR (PAR et LYRE alignes colonne par colonne, meme couleur) =====================
for c, (nm, rgba, slot) in enumerate(COLORS, start=1):
    tag = nm.upper().replace(" ", "_")
    title = "PAR_COULEUR_%s" % tag
    fn = write_scene(title + ".scex", PAR, PAR_MODEL, [(500, uniform(par_c(rgba)))])
    add("COULEUR", c, 1, fn, title, rgba[0]*65536 + rgba[1]*256 + rgba[2])
    title = "LYRE_COULEUR_%s" % tag
    fn = write_scene(title + ".scex", BSW, BSW_MODEL, [(500, uniform(bsw_c(slot)))])
    add("COULEUR", c, 2, fn, title)
title = "LYRE_COULEUR_RAPIDE"
fn = write_scene(title + ".scex", BSW, BSW_MODEL, [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(8,"color",185)]))])
add("COULEUR", 1, 3, fn, title)
title = "LYRE_COULEUR_LENTE"
fn = write_scene(title + ".scex", BSW, BSW_MODEL, [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(8,"color",140)]))])
add("COULEUR", 2, 3, fn, title)
# PAR : canal color_macro mode (6) en position "color fade mode" (154-204) + canal 7 = vitesse du fondu
# (non documente precisement sur ce profil -> pivots a calibrer en direct, meme logique que LYRE).
title = "PAR_COULEUR_RAPIDE"
fn = write_scene(title + ".scex", PAR, PAR_MODEL, [(500, uniform([chan(4,"dimmer",255),chan(6,"color_macro mode",180),chan(7,"color_macro mode",250)]))])
add("COULEUR", 3, 3, fn, title)
title = "PAR_COULEUR_LENTE"
fn = write_scene(title + ".scex", PAR, PAR_MODEL, [(500, uniform([chan(4,"dimmer",255),chan(6,"color_macro mode",180),chan(7,"color_macro mode",20)]))])
add("COULEUR", 4, 3, fn, title)

# ===================== PAGE GOBO (BSW/LYRE uniquement, seul a avoir une roue de gobo) =====================
GOBOS_1 = [("Ouvert",0), ("H1",8), ("H3",16), ("H4",23), ("H5",32), ("H6",40), ("Gobo6",48), ("Gobo7",56)]
for c, (nm, val) in enumerate(GOBOS_1, start=1):
    title = "LYRE_GOBO_%s" % nm.upper()
    fn = write_scene(title + ".scex", BSW, BSW_MODEL,
                      [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(9,"gobo",val)]))])
    add("GOBO", c, 1, fn, title)
GOBOS_2 = [("Ouvert",0), ("RR2B9",9), ("Circle1",18), ("GM015",27), ("Phones1",36), ("Sh10",45), ("GM010",54)]
for c, (nm, val) in enumerate(GOBOS_2, start=1):
    title = "LYRE_GOBO2_%s" % nm.upper()
    fn = write_scene(title + ".scex", BSW, BSW_MODEL,
                      [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(10,"gobo2",val)]))])
    add("GOBO", c, 2, fn, title)
GOBO_ROT = [("GOBO_ROTATION_LENTE", 9, 140), ("GOBO_ROTATION_RAPIDE", 9, 250),
            ("GOBO2_ROTATION_LENTE", 10, 140), ("GOBO2_ROTATION_RAPIDE", 10, 250)]
for c, (nm, idx, val) in enumerate(GOBO_ROT, start=1):
    title = "LYRE_%s" % nm
    ch_name = "gobo" if idx == 9 else "gobo2"
    fn = write_scene(title + ".scex", BSW, BSW_MODEL,
                      [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(idx,ch_name,val)]))])
    add("GOBO", c, 3, fn, title)

# ===================== PAGE MANUEL (BSW/LYRE : prisme, rotation, Beam/Spot/Wash) =====================
MANUEL_1 = [("PRISME_ON", 13, "prism", 120), ("PRISME_OFF", 13, "prism", 0),
            ("PRISME_ROTATION_LENTE", 14, "prism_rotate", 140), ("PRISME_ROTATION_RAPIDE", 14, "prism_rotate", 250)]
for c, (nm, idx, ch_name, val) in enumerate(MANUEL_1, start=1):
    title = "LYRE_%s" % nm
    fn = write_scene(title + ".scex", BSW, BSW_MODEL,
                      [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(idx,ch_name,val)]))])
    add("MANUEL", c, 1, fn, title)
# Beam/Spot/Wash : approxime via iris (12) + focus (15), aucun canal dedie sur ce profil -> a calibrer en direct.
BSW_MODES = [("BEAM", 0, 64), ("SPOT", 128, 128), ("WASH", 255, 200)]
for c, (nm, iris_v, focus_v) in enumerate(BSW_MODES, start=1):
    title = "LYRE_%s" % nm
    fn = write_scene(title + ".scex", BSW, BSW_MODEL,
                      [(500, uniform([chan(16,"shutter",12),chan(17,"dimmer",255),chan(12,"iris",iris_v),chan(15,"focus",focus_v)]))])
    add("MANUEL", c, 2, fn, title)

# ===================== PAGE STROBE =====================
# PAR : pas de canal strobe natif calibre -> flicker manuel (dimmer plein/coupe), pattern deja valide sur ce show.
def par_strobe(nm, length):
    title = "PAR_STROBE_%s" % nm
    fn = write_scene(title + ".scex", PAR, PAR_MODEL,
        [(length, uniform([chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",255),chan(2,"blue",255)])),
         (length, uniform([chan(4,"dimmer",0)]))])
    return fn, title
for c, (nm, length) in enumerate([("LENT",300), ("MOYEN",150), ("RAPIDE",70)], start=1):
    fn, title = par_strobe(nm, length)
    add("STROBE", c, 1, fn, title)
# BSW/LYRE : strobe natif (canal shutter, plage 16-131).
for c, (nm, val) in enumerate([("LENT",40), ("MOYEN",80), ("RAPIDE",125)], start=1):
    title = "LYRE_STROBE_%s" % nm
    fn = write_scene(title + ".scex", BSW, BSW_MODEL, [(500, uniform([chan(16,"shutter",val),chan(17,"dimmer",255)]))])
    add("STROBE", c, 2, fn, title)

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

fn, title = chase_scene("FX_CHASE_PAR", PAR, PAR_MODEL,
                         [chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",255),chan(2,"blue",255)],
                         [chan(4,"dimmer",0)])
add("FX", 1, 1, fn, title)
fn, title = chase_scene("FX_CHASE_LYRE", BSW, BSW_MODEL,
                         [chan(16,"shutter",12),chan(17,"dimmer",255),chan(8,"color",0)],
                         [chan(17,"dimmer",0)])
add("FX", 2, 1, fn, title)
title = "FX_BLACKOUT"
fn = write_multi(title + ".scex", [(BSW,BSW_MODEL,[chan(16,"shutter",0),chan(17,"dimmer",0)]),
                                    (PAR,PAR_MODEL,[chan(4,"dimmer",0)])])
add("FX", 3, 1, fn, title)
title = "FX_POWER"
fn = write_multi(title + ".scex", [(BSW,BSW_MODEL,[chan(16,"shutter",12),chan(17,"dimmer",255),chan(8,"color",0)]),
                                    (PAR,PAR_MODEL,[chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",255),chan(2,"blue",255)])])
add("FX", 4, 1, fn, title)

# Allumage/extinction progressifs par paliers (bouton fader : on scrube les paires 1->4, monte OU descend).
def machines_step(n_pairs_on):
    groups = []
    for k, pair in enumerate(BSW_PAIRS):
        on = k < n_pairs_on
        groups.append((pair, BSW_MODEL, [chan(16,"shutter",12 if on else 0), chan(17,"dimmer",255 if on else 0)]))
    for k, pair in enumerate(PAR_PAIRS):
        on = k < n_pairs_on
        groups.append((pair, PAR_MODEL, [chan(4,"dimmer",255 if on else 0),
                                          chan(0,"red",255 if on else 0), chan(1,"green",255 if on else 0), chan(2,"blue",255 if on else 0)]))
    return groups
title = "FX_ALLUMAGE_PROGRESSIF"
fn = write_seq(title + ".scex", [(300, machines_step(k)) for k in range(0, 5)])
add("FX", 1, 2, fn, title); FADER_BUTTONS.add(title)

# Hazer : 2 faders (fog/fan, en master_faders) + presets Min/Mid/Full/Stop.
HAZER_PRESETS = [("MIN", 60), ("MID", 125), ("FULL", 255), ("STOP", 0)]
for c, (nm, v) in enumerate(HAZER_PRESETS, start=1):
    title = "FX_HAZER_%s" % nm
    fn = write_scene(title + ".scex", HAZER, HAZER_MODEL, [(500, uniform([chan(0,"fog",v),chan(1,"fan",v)]))])
    add("FX", c, 3, fn, title)

# Groupes paires : chase alterne pair1/pair2/pair3/pair4 (demontre PAR_PAIRS/BSW_PAIRS).
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
fn, title = pair_chase("FX_PAIRES_PAR", PAR_PAIRS, PAR_MODEL,
                        [chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",255),chan(2,"blue",255)],
                        [chan(4,"dimmer",0)])
add("FX", 1, 4, fn, title)
fn, title = pair_chase("FX_PAIRES_LYRE", BSW_PAIRS, BSW_MODEL,
                        [chan(16,"shutter",12),chan(17,"dimmer",255),chan(8,"color",0)],
                        [chan(17,"dimmer",0)])
add("FX", 2, 4, fn, title)

# Machine a etincelles : impulsion manuelle (dimmer 11-255 = burst, Heating maintenu en auto).
title = "FX_ETINCELLES"
fn = write_scene(title + ".scex", SPARK, SPARK_MODEL,
                  [(500, uniform([chan(0,"dimmer",255),chan(1,"Function",0),chan(2,"Heating",50)]))])
add("FX", 3, 4, fn, title)

# ===================== PAGE MOUVEMENT (LYRE : generateurs .gpj a partir des courbes standard) =====================
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

def make_gpj_from_curve(curve_name, out_name, fixtures_gen, channels_str, other_channels):
    d, points = parse_gcv(os.path.join(CURVES_PANTILT, curve_name + ".gcv"))
    L = ["[Params]", "PanTiltShift = 0.0", "ExplodePanTilt = 0", "GroupRGB = 0",
         "FanPanOffset = 0", "FanTiltOffset = 0"]
    for i, (fid, dmx, name) in enumerate(fixtures_gen):
        L += ["[Fixture_%d]" % i, "ID = %d" % fid, "Name = %s" % name, "DMX = %d" % dmx,
              "Channels = %s" % channels_str, "ReversePan = 0", "ReverseTilt = 0",
              "OffsetPan = 0", "OffsetTilt = 0", "ZoomPan = 0", "ZoomTilt = 0", "ExplodeIndex = 0"]
    L += ["[Pan/Tilt/uPan/uTilt]", "Selected = 1", "CurveName = %s" % curve_name,
          "Transition = %s" % d["Transition"], "Duration = %s" % d["Duration"], "Shift = %s" % d["Shift"]]
    L += ["%s = %s" % (k, v) for k, v in points]
    for ch in other_channels:
        L += ["[%s]" % ch, "Selected = 0", "CurveName = Default Curve", "Transition = 0",
              "Duration = 50", "Shift = 0.0", "Point_0 = 0,65535", "Point_1 = 65535,65535"]
    if not os.path.isdir(OUT_GEN): os.makedirs(OUT_GEN)
    with open(os.path.join(OUT_GEN, out_name + ".gpj"), 'w', encoding='utf-8') as fh:
        fh.write("﻿\n" + "\n".join(L) + "\n")
    return out_name + ".gpj"

MOUVEMENTS = [
    ("circle_cw",  "CERCLE"),
    ("eight",      "HUIT"),
    ("wave",       "VAGUE"),
    ("star_cw",    "ETOILE"),
    ("crown",      "COURONNE"),
    ("square1_cw", "CARRE"),
]
for c, (curve, label) in enumerate(MOUVEMENTS, start=1):
    title = "LYRE_MOUVEMENT_%s" % label
    fn = make_gpj_from_curve(curve, title, BSW_GEN, BSW_CH, BSW_OTHER)
    add("MOUVEMENT", c, 1, fn, title)

# ===================== Construction des pages live.ini =====================
def midi_block(note, on, off):
    return ["trigger_midi_device = 0","trigger_midi_channel = 1","trigger_midi_type = 0",
            "trigger_midi_note = %d" % note,"trigger_midi_control = 0",
            "trigger_midiout_device = 0","trigger_midiout_channel = 1","trigger_midiout_type = 0",
            "trigger_midiout_note = %d" % note,"trigger_midiout_data = %d" % on,"trigger_midiout_data_off = %d" % off]

LINE_LED = {1: APC["blanc"], 2: APC["bleu"], 3: APC["violet"], 4: APC["rose"]}
for pname, btns in pages.items():
    for (col, ln, bname, title, rgb) in btns:
        if ln > 5: continue
        note = (5 - ln) * 8 + (col - 1)
        on, off = led_for(title) or LINE_LED.get(ln, APC["blanc"])
        MIDI[title] = (note, on, off)

def build_page_block(name, btns, PN):
    L = ["[page%d]" % PN, "name = %s" % name, "nb_buttons = %d" % len(btns)]
    for n, (col, lnn, bname, title, rgb) in enumerate(btns, start=1):
        L += ["[page%d_button%d]" % (PN, n), "line = %d" % lnn, "column = %d" % col, "name = %s" % bname, "title = %s" % title]
        if rgb is not None: L.append("color = %d" % rgb)
        if title in FADER_BUTTONS:
            L += ["fader = yes", "preset_step = 0"]
        else:
            L.append("masterspeedfader = %d" % (1 if bname.endswith(".gpj") else 0))
        if title in MIDI: L += midi_block(*MIDI[title])
    return "\n".join(L) + "\n"

content = open(LIVE, encoding='utf-8', errors='replace').read()

import re
board_i = content.index("[board]")
first_pg = re.search(r'(?m)^\[page\d+\]\s*$', content)
pstart = first_pg.start() if first_pg else board_i
head, tail = content[:pstart], content[board_i:]
# On remplace INTEGRALEMENT les pages existantes par nos pages (idempotent, cf CLAUDE.md).
PAGE_ORDER = ["COULEUR", "GOBO", "MANUEL", "STROBE", "FX", "MOUVEMENT"]
our_blocks = [build_page_block(nm, pages[nm], i + 1) for i, nm in enumerate(PAGE_ORDER) if nm in pages]
content = head + "".join(our_blocks) + tail
content = re.sub(r'(\[page\]\nnumber = )\d+', lambda mo: mo.group(1) + str(len(our_blocks)), content, count=1)

# ---------- Master faders : Vitesse (BSW pantilt_speed), Puissance faisceau (BSW+PAR dimmer), Hazer Fog/Fan ----------
def flist(ids, ch):
    return "".join("%d,%s|" % (i, ch) for i in ids)
vitesse = flist(BSW_IDS, "pantilt_speed")
puissance = flist(BSW_IDS, "dimmer") + flist(PAR_IDS, "dimmer")
hazer_fog = flist([HAZER[0][0]], "fog")
hazer_fan = flist([HAZER[0][0]], "fan")
mf = ("[master_faders]\n"
      "type_fader0 = 0\ncaption_fader0 = Vitesse\nv8_master_fader0 = %s\n"
      "type_fader1 = 0\ncaption_fader1 = Puissance faisceau\nv8_master_fader1 = %s\n"
      "type_fader2 = 0\ncaption_fader2 = Hazer Fog\nv8_master_fader2 = %s\n"
      "type_fader3 = 0\ncaption_fader3 = Hazer Fan\nv8_master_fader3 = %s\n"
     ) % (vitesse, puissance, hazer_fog, hazer_fan)
content = re.sub(r'master_faders = \d+\n', '', content)
content = content.replace("[live]\n", "[live]\nmaster_faders = 4\n", 1)
if not re.search(r'(?m)^fader\d+_midi_', content):
    fbind = "".join(
        "fader%d_midi_device = 0\nfader%d_midi_channel = %d\nfader%d_midi_type = 1\nfader%d_midi_note = 7\nfader%d_midi_control = 0\n"
        % (n, n, n, n, n, n) for n in range(1, 5))
    content = content.replace("master_faders = 4\n", "master_faders = 4\n" + fbind, 1)
if re.search(r'fade_time = \d+', content):
    content = re.sub(r'fade_time = \d+', 'fade_time = 0', content)
else:
    content = content.replace("[live]\n", "[live]\nfade_time = 0\n", 1)
mi = content.find("[master_faders]")
if mi != -1:
    nxt = content.find("\n[", mi + 1)
    content = content[:mi] + content[nxt + 1:]
content = content.replace("[page]\n", mf + "[page]\n", 1)

open(LIVE, 'w', encoding='utf-8').write(content)

print("OK : %d pages | %d boutons | MIDI sur %d boutons" % (len(our_blocks), sum(len(b) for b in pages.values()), len(MIDI)))
