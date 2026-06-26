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
# Mapping pro profondeur-aware : les 8 faders sont des master faders (groupes), voir section master_faders.
# -> plus de curseur sur les faders physiques (Focus ira sur encodeur ; Strobe via pads/sous-faders).
FADER_MIDI = {}

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

# ===================== PAGE 'LIVE' (mapping pro APC40, scenes multi-machines) =====================
LYRE = [(1736278739,"Lyre Ali express"),(1736279250,"Lyre Ali express #2"),
        (1736279257,"Lyre Ali express #3"),(1736279265,"Lyre Ali express #4")]
LYRE_MODEL = "Lyre Ali express"
PAR_F = [(1748027678,"par adj ")]            # nom EXACT (espace final) tel que dans fixtures.ini
PAR_MODEL = "par adj"
BLINDER = [(1736353763,"JB systems Accu-Compact")]; BLINDER_MODEL = "JB systems Accu-Compact"  # strobe/blinder (adr 61)
LASER   = [(1736355282,"laser rgb")];               LASER_MODEL   = "laser rgb"                # laser (adr 71)
HAZER   = [(1782054663,"hazer")];                   HAZER_MODEL   = "hazer"                     # machine a brouillard (adr 298)

def _emit_step(out, length, groups):         # groups = [(fixtures,model,cf)] ; cf = liste OU func(i,fid)->liste
    out.append('    <Step length="%d">' % length)
    for fx,model,cf in groups:
        for i,(fid,nm) in enumerate(fx):
            chans = cf(i,fid) if callable(cf) else cf
            out.append('      <Fixture id="%d">' % fid); out.extend(chans); out.append('      </Fixture>')
    out.append('    </Step>')

def _scene_head(decl):
    out = ['<?xml version="1.0" encoding="UTF-8"?>','','<Scene>','  <Fixtures>']
    for fx,model,_ in decl:
        for fid,nm in fx: out.append('    <Fixture id="%d" name="%s" model="%s"/>' % (fid,nm,model))
    out += ['  </Fixtures>','  <Steps>']
    return out

def write_multi(filename, groups, length=500):   # scene 1 pas (couleurs/positions/looks/bumps)
    out = _scene_head(groups); _emit_step(out, length, groups); out += ['  </Steps>','</Scene>']
    open(os.path.join(SCENES, filename),'w',encoding='utf-8').write('\n'.join(out)+'\n')
    return filename

def write_seq(filename, steps):                  # anim multi-pas (effets) ; steps=[(length,groups),...]
    out = _scene_head(steps[0][1])
    for length, groups in steps: _emit_step(out, length, groups)
    out += ['  </Steps>','</Scene>']
    open(os.path.join(SCENES, filename),'w',encoding='utf-8').write('\n'.join(out)+'\n')
    return filename

# LIGNE 1 - couleurs globales : (titre, rgb_LED, KR color, MB rainbow, Lyre(r,g,b,w), PAR(r,g,b,amber))
GLOBAL_COLORS = [
 ("Rouge",  16711680, 77, 80, (255,0,0,0),      (255,0,0,0)),
 ("Bleu",   255,      33, 70, (0,0,255,0),      (0,0,255,0)),
 ("Vert",   65280,    55, 45, (0,255,0,0),      (0,255,0,0)),
 ("Blanc",  16777215, 0,  0,  (255,255,255,255),(255,255,255,0)),
 ("Ambre",  16760576, 22, 30, (255,90,0,0),     (0,0,0,255)),
 ("UV",     8388736,  132,130,(110,0,255,0),    (130,0,255,0)),
 ("Rose",   16738740, 44, 61, (255,0,120,0),    (255,0,120,0)),
 ("Orange", 16753920, 110,90, (255,45,0,0),     (255,45,0,0)),
]
def color_groups(krv, mbv, lyr, par):
    r,g,b,w = lyr; pr,pg,pb,pa = par
    return [
      (KR,    KR_MODEL,   [chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",krv),chan(16,"effect_speed",0)]),
      (MB,    MB_MODEL,   [chan(5,"dimmer",255),chan(7,"rainbow_color",mbv),chan(8,"gobo",0),chan(10,"fonction",0)]),
      (LYRE,  LYRE_MODEL, [chan(6,"dimmer",255),chan(7,"red",r),chan(8,"green",g),chan(9,"blue",b),chan(10,"white",w)]),
      (PAR_F, PAR_MODEL,  [chan(4,"dimmer",255),chan(0,"red",pr),chan(1,"green",pg),chan(2,"blue",pb),chan(3,"amber",pa)]),
    ]
live_buttons = []                            # (col, ligne, fichier, titre, couleur_LED)
for c,(title,rgb,krv,mbv,lyr,par) in enumerate(GLOBAL_COLORS, start=1):
    fn = write_multi("LIVE %s.scex" % title, color_groups(krv,mbv,lyr,par))
    live_buttons.append((c, 1, fn, "LIVE %s" % title, rgb))    # ligne 1 = couleurs

# ---- helpers couleur par famille (avec dimmer pour visibilite ; separation pure = phase busking) ----
COLVAL = {t:(krv,mbv,lyr,par) for (t,rgb,krv,mbv,lyr,par) in GLOBAL_COLORS}
def _krc(v):    return [chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",v),chan(16,"effect_speed",0)]
def _mbc(v):    return [chan(5,"dimmer",255),chan(7,"rainbow_color",v),chan(8,"gobo",0),chan(10,"fonction",0)]
def _lyc(rgbw): r,g,b,w=rgbw; return [chan(6,"dimmer",255),chan(7,"red",r),chan(8,"green",g),chan(9,"blue",b),chan(10,"white",w)]
def _prc(rgba): pr,pg,pb,pa=rgba; return [chan(4,"dimmer",255),chan(0,"red",pr),chan(1,"green",pg),chan(2,"blue",pb),chan(3,"amber",pa)]
def color_groups_named(name):
    krv,mbv,lyr,par = COLVAL[name]
    return [(KR,KR_MODEL,_krc(krv)),(MB,MB_MODEL,_mbc(mbv)),(LYRE,LYRE_MODEL,_lyc(lyr)),(PAR_F,PAR_MODEL,_prc(par))]

# ---- helpers pan/tilt par famille (positions/mouvements ; pan/tilt SEULS = combinables) ----
def _mbpt(p,t): return [chan(0,"pan",p),chan(1,"upan",0),chan(2,"tilt",t),chan(3,"utilt",0),chan(4,"pantilt_speed",0)]
def _lypt(p,t): return [chan(0,"pan",p),chan(1,"upan",0),chan(2,"tilt",t),chan(3,"utilt",0)]
def pos_groups(fn):                          # fn(i,n)->(pan,tilt) ; KR+MB+Lyre (PAR ne bouge pas)
    return [(KR,  KR_MODEL,  lambda i,fid: kr_pos(*fn(i,len(KR)))),
            (MB,  MB_MODEL,  lambda i,fid: _mbpt(*fn(i,len(MB)))),
            (LYRE,LYRE_MODEL,lambda i,fid: _lypt(*fn(i,len(LYRE))))]

# ===== LIGNE 2 : POSITIONS (pan/tilt seuls -> combinables avec couleurs) =====
POSITIONS = [
 ("Center",  lambda i,n:(128,128)),
 ("Wide",    lambda i,n:(40+int(175*i/max(1,n-1)),128)),
 ("X",       lambda i,n:((85,85) if i%2==0 else (170,170))),
 ("Fan",     lambda i,n:(40+int(175*i/max(1,n-1)),70)),
 ("Circle",  lambda i,n:(128+int(70*math.cos(2*math.pi*i/n)),128+int(55*math.sin(2*math.pi*i/n)))),
 ("Audience",lambda i,n:(128,205)),
 ("Sky",     lambda i,n:(128,15)),
 ("Mirror",  lambda i,n:((95,128) if i<n//2 else (160,128))),
]
for c,(t,fn) in enumerate(POSITIONS, start=1):
    f = write_multi("LIVE Pos %s.scex" % t, pos_groups(fn))
    live_buttons.append((c, 2, f, "POS %s" % t, None))

# ===== LIGNE 3 : EFFETS (animes ; suivent le Master Speed/BPM) =====
def dim_groups(v):
    return [(KR,KR_MODEL,[chan(1,"dimmer",v)]),(MB,MB_MODEL,[chan(5,"dimmer",v)]),
            (LYRE,LYRE_MODEL,[chan(6,"dimmer",v)]),(PAR_F,PAR_MODEL,[chan(4,"dimmer",v)]),
            (BLINDER,BLINDER_MODEL,[chan(0,"dimmer",v)]),(LASER,LASER_MODEL,[chan(0,"dimmer",v)])]
PAL6 = ["Rouge","Ambre","Vert","Bleu","UV","Rose"]
def chase_groups(k, rnd=False):
    pal=[COLVAL[n] for n in PAL6]; idx=(lambda i:(i*7+k*5)%len(pal)) if rnd else (lambda i:(i+k)%len(pal))
    return [(KR,KR_MODEL,   lambda i,fid:_krc(pal[idx(i)][0])),
            (MB,MB_MODEL,   lambda i,fid:_mbc(pal[idx(i)][1])),
            (LYRE,LYRE_MODEL,lambda i,fid:_lyc(pal[idx(i)][2])),
            (PAR_F,PAR_MODEL,lambda i,fid:_prc(pal[idx(i)][3]))]
def snake_groups(k):
    mk=lambda di,n:(lambda i,fid:[chan(di,"dimmer",255 if i==(k%n) else 30)])
    return [(KR,KR_MODEL,mk(1,len(KR))),(MB,MB_MODEL,mk(5,len(MB))),(LYRE,LYRE_MODEL,mk(6,len(LYRE))),(PAR_F,PAR_MODEL,[chan(4,"dimmer",90)])]
def wave_g(ph): return pos_groups(lambda i,n:(128,int(128+90*math.sin(ph+i*2*math.pi/n))))
def circ_g(a):  return pos_groups(lambda i,n:(128+int(70*math.cos(a+i*2*math.pi/n)),128+int(55*math.sin(a+i*2*math.pi/n))))
def saw_g(p):   return pos_groups(lambda i,n:(p,128))
write_seq("LIVE Eff Wave.scex",    [(200,wave_g(k*math.pi/4)) for k in range(8)])
write_seq("LIVE Eff Circle.scex",  [(200,circ_g(k*math.pi/4)) for k in range(8)])
write_seq("LIVE Eff Pulse.scex",   [(250,dim_groups(255)),(250,dim_groups(45))])
write_seq("LIVE Eff Random.scex",  [(260,chase_groups(k,rnd=True)) for k in range(6)])
write_seq("LIVE Eff Saw.scex",     [(200,saw_g(v)) for v in (40,100,160,220)])
write_seq("LIVE Eff Snake.scex",   [(160,snake_groups(k)) for k in range(8)])
write_seq("LIVE Eff Chase.scex",   [(260,chase_groups(k)) for k in range(6)])
write_seq("LIVE Eff Rainbow.scex", [(300,color_groups_named(n)) for n in PAL6])
EFFETS = ["Wave","Circle","Pulse","Random","Saw","Snake","Chase","Rainbow"]
live_speed_titles = set()
for c,t in enumerate(EFFETS, start=1):
    live_buttons.append((c, 3, "LIVE Eff %s.scex" % t, "EFF %s" % t, None)); live_speed_titles.add("EFF %s" % t)

# ===== LIGNE 4 : LOOKS (ambiances = couleur d'ensemble) =====
def multi_groups(names):
    vals=[COLVAL[n] for n in names]
    return [(KR,KR_MODEL,   lambda i,fid:_krc(vals[i%len(vals)][0])),
            (MB,MB_MODEL,   lambda i,fid:_mbc(vals[i%len(vals)][1])),
            (LYRE,LYRE_MODEL,lambda i,fid:_lyc(vals[i%len(vals)][2])),
            (PAR_F,PAR_MODEL,lambda i,fid:_prc(vals[i%len(vals)][3]))]
LOOKS = [
 ("DJ",       lambda: multi_groups(["Rouge","Bleu","Vert","Rose"])),
 ("Rock",     lambda: color_groups_named("Rouge")),
 ("Warm",     lambda: color_groups_named("Ambre")),
 ("Cold",     lambda: color_groups_named("Bleu")),
 ("Disco",    lambda: multi_groups(["Rouge","Vert","Bleu","Rose","Ambre","UV"])),
 ("House",    lambda: color_groups_named("UV")),
 ("Techno",   lambda: color_groups_named("Vert")),
 ("Festival", lambda: multi_groups(["Rose","Ambre","Bleu","Vert"])),
]
for c,(t,g) in enumerate(LOOKS, start=1):
    f = write_multi("LIVE Look %s.scex" % t, g())
    live_buttons.append((c, 4, f, "LOOK %s" % t, None))

# ===== LIGNE 5 : IMPACTS / FLASHS (couleur + intensite plein) =====
def strobe_groups():                         # strobe rapide sur tout + le vrai blinder Accu-Compact
    return [(KR,KR_MODEL,[chan(0,"shutter",54),chan(1,"dimmer",255)]),
            (MB,MB_MODEL,[chan(5,"dimmer",255),chan(6,"strobe_speed",255),chan(8,"gobo",0),chan(10,"fonction",0)]),
            (LYRE,LYRE_MODEL,[chan(6,"dimmer",255),chan(11,"strobe_speed",200)]),
            (BLINDER,BLINDER_MODEL,[chan(0,"dimmer",255),chan(4,"white",255),chan(6,"strobe_dimmer",210)])]
def blinder_groups():                        # blinders = les PAR plein feu vers le public (blanc chaud)
    return [(PAR_F,PAR_MODEL,[chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",185),chan(2,"blue",110),chan(3,"amber",255)])]
def laser_groups():                          # vrai laser : dimmer + motif + couleur
    return [(LASER,LASER_MODEL,[chan(0,"dimmer",255),chan(1,"red",0),chan(2,"green",255),chan(3,"blue",30),chan(7,"pattern selection",40)])]
BUMPS = [
 ("Flash Blanc", lambda: color_groups_named("Blanc")),
 ("Flash Rouge", lambda: color_groups_named("Rouge")),
 ("Flash Bleu",  lambda: color_groups_named("Bleu")),
 ("Blinders",    blinder_groups),
 ("Strobe",      strobe_groups),
 ("Hit",         lambda: color_groups_named("Blanc")),
 ("Boom",        lambda: color_groups_named("Orange")),
 ("Laser",       laser_groups),
]
for c,(t,g) in enumerate(BUMPS, start=1):
    f = write_multi("LIVE Bump %s.scex" % t, g())
    live_buttons.append((c, 5, f, "IMPACT %s" % t, None))

# ===== BOUTONS SOUS FADERS (impacts globaux ; ligne 6, a mapper sur les boutons sous les faders) =====
def all_white_full():
    return [(KR,KR_MODEL,[chan(0,"shutter",35),chan(1,"dimmer",255),chan(3,"color",0)]),
            (MB,MB_MODEL,[chan(5,"dimmer",255),chan(7,"rainbow_color",0),chan(8,"gobo",0),chan(10,"fonction",0)]),
            (LYRE,LYRE_MODEL,[chan(6,"dimmer",255),chan(7,"red",255),chan(8,"green",255),chan(9,"blue",255),chan(10,"white",255)]),
            (PAR_F,PAR_MODEL,[chan(4,"dimmer",255),chan(0,"red",255),chan(1,"green",255),chan(2,"blue",255),chan(3,"amber",255)])]
def hazer_groups(v=255):                     # hazer 2 canaux : CH0=fog (fumee) + CH1=fan (ventilo), les deux a fond
    return [(HAZER,HAZER_MODEL,[chan(0,"fog",v),chan(1,"fan",255)])]   # noms = profil fixtures/hazer.txt (sinon canal ignore)
SOUS = [
 ("Blackout", lambda: dim_groups(0)),
 ("Full On",  all_white_full),
 ("Flash",    all_white_full),
 ("Strobe",   strobe_groups),
 ("UV",       lambda: color_groups_named("UV")),
 ("White",    all_white_full),
 ("Public",   lambda: color_groups_named("Ambre")),
 ("Smoke",    lambda: hazer_groups()),       # hazer (machine ajoutee, adr 298)
]
for c,(t,g) in enumerate(SOUS, start=1):
    f = write_multi("LIVE SF %s.scex" % t, g())
    live_buttons.append((c, 6, f, "SF %s" % t, None))

# ---- MIDI auto sur la grille APC40 (deduit de la page 'lyres' apprise sur hardware) ----
# La grille clip de l'APC40 envoie notes 0-39, par bancs de 8 : note = (ligne-1)*8 + (colonne-1),
# canal 1, type 0 (note on/off). On allume aussi la LED (codes couleur APC40 mkII valides par l'install).
# Les lignes 1-5 = grille physique ; la ligne 6 (sous-faders) n'est PAS dans la grille -> pas de note auto.
LED = {"Blanc":(3,1),"Rouge":(5,6),"Bleu":(45,43),"Vert":(21,23),"Jaune":(12,18),
       "Rose":(57,58),"Orange":(9,8),"Magenta":(53,54),"Violet":(49,50),"Ambre":(9,8),"UV":(49,50)}
LINE_LED = {2:(45,43), 3:(21,23), 4:(49,50), 5:(5,6)}   # Positions=bleu, Effets=vert, Looks=violet, Impacts=rouge
for (col,ln,bname,title,color) in live_buttons:
    if ln > 5: continue                                # sous-faders : hors grille
    note = (ln-1)*8 + (col-1)                          # 0..39
    word = title.split()[-1] if ln==1 else None        # couleur -> LED assortie
    on,off = LED.get(word, LINE_LED.get(ln,(3,1)))
    MIDI[title] = (note, on, off)

# ===================== Construction des pages (KRYPTON + LIVE) =====================
# Boutons dont la vitesse suit le fader Master Speed du panneau Live (mouvements + shows animes)
SPEED_TITLES = {"KR Show Cercle", "KR Show Vague", "KR Chenillard Couleurs"} | live_speed_titles
PAGE_NAME = "KRYPTON + MINIBEAM"
LIVE_NAME = "LIVE"
OUR_PAGES = [(PAGE_NAME, buttons), (LIVE_NAME, live_buttons)]
OUR_NAMES = {nm for nm, _ in OUR_PAGES}

def build_page_block(name, btns, PN):
    L = ["[page%d]" % PN, "name = %s" % name, "nb_buttons = %d" % len(btns)]
    for n,(col,lnn,bname,title,color) in enumerate(btns, start=1):
        L += ["[page%d_button%d]" % (PN, n), "line = %d" % lnn, "column = %d" % col, "name = %s" % bname, "title = %s" % title]
        if color is not None: L.append("color = %d" % color)
        if title in FADER_BUTTONS:                       # bouton-curseur (fade pas1 -> pas2)
            L += ["fader = yes", "preset_step = 0"]
            if title in FADER_MIDI: L += fader_midi_block(*FADER_MIDI[title])
        else:
            msf = 1 if (bname.endswith(".gpj") or title in SPEED_TITLES) else 0
            L.append("masterspeedfader = %d" % msf)
        if title in MIDI: L += midi_block(*MIDI[title])
    return "\n".join(L) + "\n"

content = open(LIVE, encoding='utf-8', errors='replace').read()

# --- Pages robustes : SweetLight RENUMEROTE/reordonne les pages en quittant. On retire toutes les
#     occurrences de NOS pages (par nom), on renumerote les pages utilisateur 1..k SANS TROU (un trou
#     fait renumeroter SweetLight), et on ajoute NOS pages a la suite. ---
board_i = content.index("[board]")
first_pg = re.search(r'(?m)^\[page\d+\]\s*$', content)
pstart = first_pg.start()
head, region, tail = content[:pstart], content[pstart:board_i], content[board_i:]
blocks = [b for b in re.split(r'(?m)(?=^\[page\d+\]\s*$)', region) if b.strip()]
kept = []
for b in blocks:
    m = re.search(r'(?m)^name = (.*)$', b)            # 1er 'name =' = nom de la page
    if m and m.group(1).strip() in OUR_NAMES:
        continue                                     # retire nos pages (anciennes/doublons)
    kept.append(b)
def _renum(block, n):                                # renumerote [pageX] et [pageX_buttonY]
    block = re.sub(r'(?m)^\[page\d+\]', '[page%d]' % n, block, count=1)
    block = re.sub(r'(?m)^\[page\d+_button', '[page%d_button' % n, block)
    return block
kept = [_renum(b, i) for i, b in enumerate(kept, start=1)]
our_blocks = [build_page_block(nm, btns, len(kept)+1+i) for i,(nm,btns) in enumerate(OUR_PAGES)]
content = head + "".join(kept) + "".join(our_blocks) + tail
display_n = len(kept) + len(OUR_PAGES)               # afficher la page LIVE (la derniere)
content = re.sub(r'(\[page\]\nnumber = )\d+', lambda mo: mo.group(1) + str(display_n), content, count=1)

# --- 8 master faders APC40 (PROFONDEUR-AWARE, d'apres le plan de scene) ---
#  F1 KR Avant | F2 KR Arriere | F3 Minibeam | F4 Lyre | F5 PAR+Blinder | F6 Vitesse(BPM/UI) | F7 Laser | F8 Master
#  Adressage Krypton = ordre physique DJ->fond (confirme) : Avant=92/109/126, Arriere=143/160/177.
LYRE_IDS = [1736278739, 1736279250, 1736279257, 1736279265]
PAR_ID = 1748027678
def flist(ids, ch):
    return "".join("%d,%s|" % (i, ch) for i in ids)
kr_front = flist(KR_IDS[:3], "dimmer")                                  # 3 Krypton avant (pres DJ)
kr_back  = flist(KR_IDS[3:], "dimmer")                                  # 3 Krypton arriere (fond)
mb_dim   = flist([x[0] for x in MB], "dimmer")
lyre_dim = flist(LYRE_IDS, "dimmer")
par_amb  = flist([PAR_ID], "dimmer")                                    # PAR = ambiance cotes chapiteau (1 canal, homogene)
laser_d  = flist([LASER[0][0]], "dimmer")
all_dim  = kr_front + kr_back + mb_dim + lyre_dim + par_amb + flist([BLINDER[0][0]], "dimmer") + laser_d  # grand master
mf = ("[master_faders]\n"
      "type_fader0 = 0\ncaption_fader0 = KR Avant\nv8_master_fader0 = %s\n"
      "type_fader1 = 0\ncaption_fader1 = KR Arriere\nv8_master_fader1 = %s\n"
      "type_fader2 = 0\ncaption_fader2 = Minibeam\nv8_master_fader2 = %s\n"
      "type_fader3 = 0\ncaption_fader3 = Lyre\nv8_master_fader3 = %s\n"
      "type_fader4 = 0\ncaption_fader4 = PAR Ambiance\nv8_master_fader4 = %s\n"
      "type_fader5 = 0\ncaption_fader5 = Vitesse\nv8_master_fader5 = \n"
      "type_fader6 = 0\ncaption_fader6 = Laser\nv8_master_fader6 = %s\n"
      "type_fader7 = 0\ncaption_fader7 = Master\nv8_master_fader7 = %s\n"
     ) % (kr_front, kr_back, mb_dim, lyre_dim, par_amb, laser_d, all_dim)
content = re.sub(r'master_faders = \d+\n', '', content)                   # retire toute ancienne ligne (mauvaise section)
content = content.replace("[live]\n", "[live]\nmaster_faders = 8\n", 1)  # 8 master faders (mapping pro)
# Bindings faders physiques APC40 -> master faders : fader N (canal MIDI N, CC7) pilote master_fader(N-1).
# Appris dans l'UI a l'origine ; on les FIGE ici pour qu'ils survivent (idempotent : on retire puis reinjecte).
content = re.sub(r'(?m)^fader\d+_midi_\w+ = .*\n', '', content)
fbind = "".join(
    "fader%d_midi_device = 0\nfader%d_midi_channel = %d\nfader%d_midi_type = 1\nfader%d_midi_note = 7\nfader%d_midi_control = 0\n"
    % (n,n,n,n,n,n) for n in range(1,9))
content = content.replace("master_faders = 8\n", "master_faders = 8\n" + fbind, 1)
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
