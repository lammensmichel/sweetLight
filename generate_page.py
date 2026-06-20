#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere pour les Krypton + Minibeam :
   - les scenes .scex (couleurs, effets, shows)
   - les generateurs de mouvement .gpj clones des Lyre Ali express (memes courbes)
   - la page 3 'KRYPTON + MINIBEAM' (avec reprise des raccourcis MIDI des lyres)
Idempotent. Usage : python3 generate_page.py [dossier_du_show]"""
import math, os, sys, re

BASE = sys.argv[1] if len(sys.argv) > 1 else "/Users/mac-m3-michel/workspace/sweetLight/v1"
SCENES = os.path.join(BASE, "scenes")
LIVE = os.path.join(BASE, "Live", "live.ini")
OUT_GEN = os.path.join(BASE, "Editor", "Generator", "projects")
# Source de reference des generateurs lyres (show default)
SRC_GEN = os.path.expanduser("~/TheLightingController/LightShows/default/Editor/Generator/projects")

# ---------- Fixtures (id, nom) ----------
KR = [(1740304174, "MAC250_KRYPTON"), (1740304175, "MAC250_KRYPTON #2"),
      (1740304176, "MAC250_KRYPTON #3"), (1740304177, "MAC250_KRYPTON #4"),
      (1740304178, "MAC250_KRYPTON #5"), (1740304179, "MAC250_KRYPTON #6")]
KR_MODEL = "MAC250_KRYPTON"
KR_IDS = [x[0] for x in KR]
MB = [(1756657696, "minibeamstpotled"), (1756657758, "minibeamstpotled #2"),
      (1756683768, "minibeamstpotled #3"), (1756683769, "minibeamstpotled #4"),
      (1756683770, "minibeamstpotled #5"), (1756683771, "minibeamstpotled #6"),
      (1756683772, "minibeamstpotled #7"), (1756683773, "minibeamstpotled #8")]
MB_MODEL = "minibeamstpotled"

# ---------- Pour les .gpj : (id, dmx=addr-1, nom) + liste de canaux du profil ----------
KR_GEN = [(1740304174, 91, "MAC250_KRYPTON"), (1740304175, 108, "MAC250_KRYPTON #2"),
          (1740304176, 125, "MAC250_KRYPTON #3"), (1740304177, 142, "MAC250_KRYPTON #4"),
          (1740304178, 159, "MAC250_KRYPTON #5"), (1740304179, 176, "MAC250_KRYPTON #6")]
KR_CH = "shutter,dimmer,dimmer_fine,color,color_fine,gobo,gobo_rotate,gobo_urotate,focus,focus_fine,prism,pan,upan,tilt,utilt,pantilt_speed,effect_speed"
KR_OTHER = ["shutter","dimmer","dimmer_fine","color","color_fine","gobo","gobo_rotate",
            "gobo_urotate","focus","focus_fine","prism","pantilt_speed","effect_speed"]
MB_GEN = [(1756657696, 201, "minibeamstpotled"), (1756657758, 213, "minibeamstpotled #2"),
          (1756683768, 225, "minibeamstpotled #3"), (1756683769, 237, "minibeamstpotled #4"),
          (1756683770, 249, "minibeamstpotled #5"), (1756683771, 261, "minibeamstpotled #6"),
          (1756683772, 273, "minibeamstpotled #7"), (1756683773, 285, "minibeamstpotled #8")]
MB_CH = "pan,upan,tilt,utilt,pantilt_speed,dimmer,strobe_speed,rainbow_color,gobo,prism3D,fonction,mode"
MB_OTHER = ["pantilt_speed","dimmer","strobe_speed","rainbow_color","gobo","prism3D","fonction","mode"]

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

# Decalage pan des Krypton (~ -90 deg : pan 540deg sur 16 bits -> 65535/6 ~= 10923).
# Les Krypton pointaient ~90 deg trop a droite ; on ramene le centre face public.
KR_PAN_OFF16 = -10923
def kr_pos(p_coarse, tilt, fade=True):
    v = max(0, min(65535, p_coarse * 256 + KR_PAN_OFF16))
    return [chan(11,"pan",v//256,fade), chan(12,"upan",v%256,fade),
            chan(13,"tilt",tilt,fade), chan(14,"utilt",0), chan(15,"pantilt_speed",0)]

# ===================== Generateurs .gpj =====================
def parse_sections(text):
    secs, cur = {}, None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            cur = s; secs[cur] = []
        elif cur is not None:
            secs[cur].append(line)
    return secs

def make_gpj(src_label, out_name, fixtures, channels_str, other_channels, pan_off=0):
    src = open(os.path.join(SRC_GEN, src_label + ".gpj"), encoding='utf-8', errors='replace').read()
    secs = parse_sections(src)
    params = secs.get("[Params]", ["PanTiltShift = 0.0","ExplodePanTilt = 0","GroupRGB = 0","FanPanOffset = 0","FanTiltOffset = 0"])
    pantilt = secs["[Pan/Tilt/uPan/uTilt]"]            # courbe de mouvement
    if pan_off:                                        # decale le pan (X) de chaque point
        nb = []
        for line in pantilt:
            m = re.match(r'\s*(Point_\d+)\s*=\s*(\d+),(\d+)\s*$', line)
            if m:
                x = max(0, min(65535, int(m.group(2)) + pan_off))
                nb.append("%s = %d,%s" % (m.group(1), x, m.group(3)))
            else:
                nb.append(line)
        pantilt = nb
    L = ["[Params]"] + params
    for i, (fid, dmx, name) in enumerate(fixtures):
        L += ["[Fixture_%d]" % i, "ID = %d" % fid, "Name = %s" % name, "DMX = %d" % dmx,
              "Channels = %s" % channels_str, "ReversePan = 0", "ReverseTilt = 0",
              "OffsetPan = 0", "OffsetTilt = 0", "ZoomPan = 0", "ZoomTilt = 0", "ExplodeIndex = 0"]
    L += ["[Pan/Tilt/uPan/uTilt]"] + pantilt
    for ch in other_channels:
        L += ["[%s]" % ch, "Selected = 0", "CurveName = Default Curve", "Transition = 0",
              "Duration = 50", "Shift = 0.0", "Point_0 = 0,65535", "Point_1 = 65535,65535"]
    if not os.path.isdir(OUT_GEN):
        os.makedirs(OUT_GEN)
    with open(os.path.join(OUT_GEN, out_name + ".gpj"), 'w', encoding='utf-8') as fh:
        fh.write("﻿\n" + "\n".join(L) + "\n")
    return out_name + ".gpj"

# Mouvements lyres a cloner : (fichier source, label, note MIDI, out_data, out_off)
MOVES = [
    ("Lyre Move 1", "Move 1", 32, 49, 50),
    ("Lyre Move 2", "Move 2", 33, 49, 50),
    ("lyre move 3", "Move 3", 34, 49, 50),
    ("lyre move haut bas", "Haut-Bas", 37, 49, 50),
    ("lyre move haut bas delais", "Haut-Bas delais", 38, 49, 50),
    ("lyre move fix bas max", "Bas max", 39, 49, 50),
    ("lyres mouvement en 8", "En 8", 24, 49, 50),
    ("lyre move chenillard", "Chenillard mvt", 19, 41, 40),
    ("lyre droite gauche", "Droite-Gauche", 35, 49, 50),
    ("lyre mouvement gauche droite delais", "GD delais", 36, 49, 50),
]

buttons = []      # (col, line, name_fichier, titre, color_or_None)
MIDI = {}         # titre -> (note, on, off)

# ============ COLONNE 1 : KRYPTON COULEURS ============
# (titre, valeur_color, rgb_tuile, note_APC40, LED_on, LED_off) - LED = code couleur APC40 mkII
KR_COLORS = [("KR Blanc",0,16777215,8,3,1),("KR Rouge",77,16711680,10,5,6),
             ("KR Bleu",33,255,9,45,43),("KR Vert",55,65280,11,21,23),
             ("KR Jaune",22,16776960,13,12,18),("KR Rose",44,16738740,14,57,58),
             ("KR Orange",110,16753920,20,9,8),("KR Magenta",88,16711935,25,53,54),
             ("KR Violet",132,8388736,22,49,50)]
ln = 1
# effect_speed=0 (tracking) = la roue se positionne a vitesse MAX ; pas de fade sur color = saut direct.
for title, cval, rgb, note, on, off in KR_COLORS:
    write_scene(title + ".scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",cval),chan(16,"effect_speed",0)]))])
    buttons.append((1, ln, title + ".scex", title, rgb))
    if note is not None: MIDI[title] = (note, on, off)
    ln += 1
write_scene("KR Couleur Auto.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",215),chan(16,"effect_speed",0)]))])
buttons.append((1, 10, "KR Couleur Auto.scex", "KR Couleur Auto", None)); MIDI["KR Couleur Auto"] = (12,37,36)

# ============ COLONNE 2 : KRYPTON MOUVEMENTS (.gpj clones) ============
for i, (src, label, note, on, off) in enumerate(MOVES, start=1):
    fn = make_gpj(src, "KR " + label, KR_GEN, KR_CH, KR_OTHER, pan_off=KR_PAN_OFF16)
    title = "KR " + label
    buttons.append((2, i, fn, title, None)); MIDI[title] = (note, on, off)

# ============ COLONNE 3 : KRYPTON EFFETS ============
write_scene("KR Dimmer.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255)]))])
buttons.append((3,1,"KR Dimmer.scex","KR Dimmer (ON)",None)); MIDI["KR Dimmer (ON)"] = (15,3,1)
# Strobe Krypton : sur cette machine, shutter haut = LENT, bas = RAPIDE. Note 83 = pad lyre Strobe sur le Normal.
for li,(stitle,sval,smidi) in enumerate([("KR Strobe Lent",71,(82,3,1)),("KR Strobe Normal",62,(83,3,1)),("KR Strobe Rapide",54,(84,3,1))], start=2):
    write_scene(stitle + ".scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",sval),chan(1,"dimmer",255)]))])
    buttons.append((3,li,stitle + ".scex",stitle,None))
    if smidi: MIDI[stitle] = smidi
write_scene("KR Gobo Rotation.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255),chan(5,"gobo",54),chan(6,"gobo_rotate",60)]))])
buttons.append((3,5,"KR Gobo Rotation.scex","KR Gobo Rotation",None)); MIDI["KR Gobo Rotation"] = (16,41,40)
write_scene("KR Prisme.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255),chan(10,"prism",120)]))])
buttons.append((3,6,"KR Prisme.scex","KR Prisme",None))
write_scene("KR Blackout.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",0),chan(1,"dimmer",0)]))])
buttons.append((3,7,"KR Blackout.scex","KR Blackout",None))

# ============ COLONNE 4 : KRYPTON DIVERS / SHOWS ============
write_scene("KR Centre.scex", KR, KR_MODEL, [(500, uniform(kr_pos(128,128,False)))])
buttons.append((4,1,"KR Centre.scex","KR Centre",None))
write_scene("KR Reset.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",212)]))])
buttons.append((4,2,"KR Reset.scex","KR Reset",None))
write_scene("KR Lampe ON.scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",232)]))])
buttons.append((4,6,"KR Lampe ON.scex","KR Lampe ON",None))
CHASE = [77,33,55,22,44,88]
def chase_step(k):
    def f(fid):
        i = KR_IDS.index(fid)
        return [chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",CHASE[(i+k)%len(CHASE)]),chan(16,"effect_speed",0)]
    return f
write_scene("KR Chenillard Couleurs.scex", KR, KR_MODEL, [(300, chase_step(k)) for k in range(len(CHASE))])
buttons.append((4,3,"KR Chenillard Couleurs.scex","KR Chenillard Couleurs",None))
circle = [(128+round(60*math.cos(a*math.pi/4)),128+round(45*math.sin(a*math.pi/4))) for a in range(8)]
write_scene("KR Show Cercle.scex", KR, KR_MODEL, [(350, uniform(kr_pos(p,t)+[chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",0)])) for p,t in circle])
buttons.append((4,4,"KR Show Cercle.scex","KR Show Cercle",None))
def kr_wave(phase):
    def f(fid):
        i = KR_IDS.index(fid); fp = i*(2*math.pi/len(KR))
        return kr_pos(int(128+70*math.sin(phase+fp)), int(115+45*math.sin(phase+fp+math.pi/2)))+[chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",215)]
    return f
write_scene("KR Show Vague.scex", KR, KR_MODEL, [(400, kr_wave(k*2*math.pi/8)) for k in range(8)])
buttons.append((4,5,"KR Show Vague.scex","KR Show Vague",None))
# Focus en FADER BUTTON (curseur) : scene 2 pas focus 0 -> 255 ; le curseur balaie la nettete.
# Les fader buttons marchent sur tout canal (la demo en a un sur gobo_rotate). focus = canal index 8.
write_scene("KR Focus.scex", KR, KR_MODEL, [(500, uniform([chan(8,"focus",0)])), (500, uniform([chan(8,"focus",255)]))])
buttons.append((4,7,"KR Focus.scex","Focus KR",None))
FADER_BUTTONS = {"Focus KR"}

# ---- Curseurs STROBE pilotes par le fader 4 (APC ch4, CC7) ----
# Bornes SURES : le curseur interpole pas1->pas2, il ne balaie jamais 0-255 -> jamais 212(reset)/232(lampe).
# KR : shutter 72(lent) -> 50(rapide), reste dans la zone strobe 50-72.
# MB : strobe_speed 0(eteint) -> 255(rapide) ; dimmer=255 aux deux pas pour que le flash soit VISIBLE.
write_scene("KR Strobe Fader.scex", KR, KR_MODEL,
    [(500, uniform([chan(0,"shutter",72),chan(1,"dimmer",255)])),
     (500, uniform([chan(0,"shutter",50),chan(1,"dimmer",255)]))])
buttons.append((3,8,"KR Strobe Fader.scex","KR Strobe Fader",None))
write_scene("MB Strobe Fader.scex", MB, MB_MODEL,
    [(500, uniform([chan(5,"dimmer",255),chan(6,"strobe_speed",0),chan(10,"fonction",0)])),
     (500, uniform([chan(5,"dimmer",255),chan(6,"strobe_speed",255),chan(10,"fonction",0)]))])
buttons.append((8,9,"MB Strobe Fader.scex","MB Strobe Fader",None))
FADER_BUTTONS |= {"KR Strobe Fader", "MB Strobe Fader"}
FADER_MIDI = {"KR Strobe Fader": (4,7), "MB Strobe Fader": (4,7)}  # meme fader 4 -> les deux strobent ensemble

# ============ COLONNE 5 : MINIBEAM COULEURS (toutes les couleurs de la roue) ============
# rainbow_color : white 0-19, color1..6 (20-139), auto 160-255. On expose les 6 couleurs.
# gobo=0 (ouvert) + fonction=0 (mode manuel) pour une couleur propre, non masquee.
# Couleurs reelles de la roue identifiees par l'utilisateur. note MIDI = pad lyre correspondant.
# Memes notes que les couleurs Krypton -> un pad colore KR + MB ensemble
MB_COLORS = [("MB Blanc",0,16777215,8,3,1), ("MB Rouge",80,16711680,10,5,6), ("MB Rose",61,16738740,14,57,58),
             ("MB Jaune",30,16776960,13,12,18),
             ("MB Vert",45,65280,11,21,23), ("MB Bleu",70,255,9,45,43),
             ("MB Orange",90,16753920,20,9,8), ("MB Jaune-Vert",110,10079232,None,0,0),
             ("MB Bleu-Rose",130,9055202,None,0,0), ("MB Multicolore",200,None,12,37,36)]
for j,(title,rval,rgb,note,on,off) in enumerate(MB_COLORS, start=1):
    write_scene(title + ".scex", MB, MB_MODEL, [(500, uniform([chan(5,"dimmer",255),chan(7,"rainbow_color",rval),chan(8,"gobo",0),chan(10,"fonction",0)]))])
    buttons.append((6, j, title + ".scex", title, rgb))
    if note is not None: MIDI[title] = (note, on, off)

# ============ COLONNE 6 : MINIBEAM MOUVEMENTS (.gpj clones) ============
for i,(src,label,note,on,off) in enumerate(MOVES, start=1):
    fn = make_gpj(src, "MB " + label, MB_GEN, MB_CH, MB_OTHER)
    title = "MB " + label
    buttons.append((7, i, fn, title, None)); MIDI[title] = (note, on, off)

# ============ COLONNE 7 : MINIBEAM EFFETS / SHOWS ============
mbfx = [("MB Gobo Auto",[chan(5,"dimmer",255),chan(8,"gobo",200)]),
        ("MB Sound",[chan(5,"dimmer",255),chan(10,"fonction",200)]),
        ("MB Strobe Lent",[chan(5,"dimmer",255),chan(6,"strobe_speed",40),chan(8,"gobo",0),chan(10,"fonction",0)]),
        ("MB Strobe Normal",[chan(5,"dimmer",255),chan(6,"strobe_speed",130),chan(8,"gobo",0),chan(10,"fonction",0)]),
        ("MB Strobe Rapide",[chan(5,"dimmer",255),chan(6,"strobe_speed",240),chan(8,"gobo",0),chan(10,"fonction",0)]),
        ("MB Prisme",[chan(5,"dimmer",255),chan(9,"prism3D",200)]),
        ("MB Blackout",[chan(5,"dimmer",0)]),
        ("MB Full Auto",[chan(5,"dimmer",255),chan(7,"rainbow_color",200),chan(8,"gobo",200),chan(10,"fonction",200)])]
for j,(title,chans) in enumerate(mbfx, start=1):
    write_scene(title + ".scex", MB, MB_MODEL, [(500, uniform(chans))])
    buttons.append((8, j, title + ".scex", title, None))
# Strobes MB sur les memes pads que KR (Lent 85, Normal 83, Rapide 86)
for st,nt in [("MB Strobe Lent",82),("MB Strobe Normal",83),("MB Strobe Rapide",84)]:
    MIDI[st] = (nt,3,1)

# ============ COLONNE 5 : KRYPTON GOBOS (selection slot par slot) ============
GOBO_NOTES = [21,23,26,27,28,29,30,31]  # meme note KR/MB : un pad = gobo N des deux familles
KR_GOBOS = [("KR Gobo Ouvert",0),("KR Gobo 1",8),("KR Gobo 2",13),("KR Gobo 3",18),
            ("KR Gobo 4",23),("KR Gobo 5",28),("KR Gobo 6",33),("KR Gobo 7",38)]
for k,(title,gval) in enumerate(KR_GOBOS, start=1):
    write_scene(title + ".scex", KR, KR_MODEL, [(500, uniform([chan(0,"shutter",35),chan(1,"dimmer",255),chan(5,"gobo",gval)]))])
    buttons.append((5, k, title + ".scex", title, None)); MIDI[title] = (GOBO_NOTES[k-1], 3, 1)

# ============ COLONNE 9 : MINIBEAM GOBOS ============
MB_GOBOS = [("MB Gobo Ouvert",0),("MB Gobo 1",85),("MB Gobo 2",15),("MB Gobo 3",35),
            ("MB Gobo 4",45),("MB Gobo 5",55),("MB Gobo 6",65),("MB Gobo 7",75)]
for k,(title,gval) in enumerate(MB_GOBOS, start=1):
    write_scene(title + ".scex", MB, MB_MODEL, [(500, uniform([chan(5,"dimmer",255),chan(8,"gobo",gval),chan(10,"fonction",0)]))])
    buttons.append((9, k, title + ".scex", title, None)); MIDI[title] = (GOBO_NOTES[k-1], 3, 1)

# ===================== Construction page 3 =====================
def midi_block(note, on, off):
    return ["trigger_midi_device = 0","trigger_midi_channel = 1","trigger_midi_type = 0",
            "trigger_midi_note = %d" % note,"trigger_midi_control = 0",
            "trigger_midiout_device = 0","trigger_midiout_channel = 1","trigger_midiout_type = 0",
            "trigger_midiout_note = %d" % note,"trigger_midiout_data = %d" % on,"trigger_midiout_data_off = %d" % off]

def fader_midi_block(channel, cc):                   # curseur pilote par un fader physique (CC continu, type 1)
    return ["trigger_midi_device = 0","trigger_midi_channel = %d" % channel,"trigger_midi_type = 1",
            "trigger_midi_note = %d" % cc,"trigger_midi_control = 0"]

# Boutons dont la vitesse suit le fader Master Speed du panneau Live (mouvements + shows animes)
SPEED_TITLES = {"KR Show Cercle", "KR Show Vague", "KR Chenillard Couleurs"}
lines = ["[page3]", "name = KRYPTON + MINIBEAM", "nb_buttons = %d" % len(buttons)]
for n,(col,lnn,name,title,color) in enumerate(buttons, start=1):
    lines += ["[page3_button%d]" % n, "line = %d" % lnn, "column = %d" % col, "name = %s" % name, "title = %s" % title]
    if color is not None: lines.append("color = %d" % color)
    if title in FADER_BUTTONS:                       # bouton-curseur (fade pas1 -> pas2)
        lines += ["fader = yes", "preset_step = 0"]
        if title in FADER_MIDI: lines += fader_midi_block(*FADER_MIDI[title])
    else:
        msf = 1 if (name.endswith(".gpj") or title in SPEED_TITLES) else 0
        lines.append("masterspeedfader = %d" % msf)
    if title in MIDI: lines += midi_block(*MIDI[title])
page_block = "\n".join(lines) + "\n"

content = open(LIVE, encoding='utf-8', errors='replace').read()
content = content.replace("[page]\nnumber = 2", "[page]\nnumber = 3", 1)
i = content.find("[page3]")
if i != -1:
    content = content[:i] + content[content.index("[board]", i):]
idx = content.index("[board]")
content = content[:idx] + page_block + content[idx:]

# --- Master faders APC40 : F1 Intensite | F2 Focus | F3 Vitesse | F4 Strobe ---
# NB : un master fader pilote AUSSI un canal non-dimming (focus Krypton confirme OK en test).
# Bindings fader materiel -> master fader (faderN_midi_* dans [live]) regles dans SweetLight (UI)
# et conserves tels quels : APC fader N (canal MIDI N) pilote master_fader(N-1).
LYRE_IDS = [1736278739, 1736279250, 1736279257, 1736279265]
PAR_ID = 1748027678
def flist(ids, ch):
    return "".join("%d,%s|" % (i, ch) for i in ids)
dimmers = flist(KR_IDS, "dimmer") + flist([x[0] for x in MB], "dimmer") + flist(LYRE_IDS, "dimmer") + flist([PAR_ID], "dimmer")
focus = flist(KR_IDS, "focus")                       # F2 = nettete des Krypton (canal 'focus')
# F4 (Strobe) n'est PLUS un master fader : le strobe passe par 2 curseurs bornes (KR + MB) pilotes
# par le fader 4 (voir FADER_MIDI plus haut) -> course sure, jamais de reset Krypton.
mf = ("[master_faders]\n"
      "type_fader0 = 0\ncaption_fader0 = Intensite\nv8_master_fader0 = %s\n"
      "type_fader1 = 0\ncaption_fader1 = Focus\nv8_master_fader1 = %s\n"
      "type_fader2 = 1\ncaption_fader2 = Vitesse\nv8_master_fader2 = \n") % (dimmers, focus)
content = re.sub(r'master_faders = \d+\n', '', content)                   # retire toute ancienne ligne (mauvaise section)
content = content.replace("[live]\n", "[live]\nmaster_faders = 3\n", 1)  # 3 master faders, dans [live]
# Focus reactif : on annule le lissage global (fade_time 300 -> 0). NB : un master fader pilote
# en temps reel ; si le focus reste lent c'est la vitesse mecanique du Krypton (effect_speed).
# Effet de bord assume : les fondus de scene/couleur deviennent des coupures seches.
if re.search(r'fade_time = \d+', content):
    content = re.sub(r'fade_time = \d+', 'fade_time = 0', content)
else:
    content = content.replace("[live]\n", "[live]\nfade_time = 0\n", 1)
mi = content.find("[master_faders]")
if mi != -1:                                   # remplace une section existante
    nxt = content.find("\n[", mi + 1)
    content = content[:mi] + content[nxt + 1:]
content = content.replace("[page]\n", mf + "[page]\n", 1)

open(LIVE, 'w', encoding='utf-8').write(content)

print("OK : %d boutons | %d mouvements .gpj x2 (KR+MB) | MIDI sur %d boutons" % (len(buttons), len(MOVES), len(MIDI)))
