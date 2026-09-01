# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Projet SweetLight — pages DJ pour le rig « BSW + PAR »

Ce dépôt contient **`generate_page.py`** (~510 lignes, sans dépendances), le script qui génère pour
**Sweetlight / TheLightingController** :
- les **scènes** `.scex` (couleurs, gobos, prisme, strobe, effets, impacts) — XML,
- les **générateurs de mouvement** `.gpj` (à partir des courbes `curves_pantilt/*.gcv`, pour les BSW) — INI,
- **7 pages** dans `live.ini` (boutons + MIDI APC40 mkII) — INI :
  `DJ LIVE` (busking BSW+PAR tout-en-un : L1 couleurs, L2 mouvements, L3 effets animés, L4 looks, L5 impacts),
  `COULEUR`, `GOBO`, `MANUEL`, `STROBE`, `FX`, `MOUVEMENT`.
  Le script **remplace INTÉGRALEMENT** les pages existantes par les siennes (idempotent) et **réécrit
  `[board]`/`[screenN]`** pour que les onglets collent 1:1 aux pages (un onglet par page, titre = nom
  de page ; DJ LIVE est le 1ᵉʳ onglet).
- Vignettes de boutons : `assets/gobos/` (vrai projeté du gobo), `assets/moves/` (tracé pan/tilt de la
  courbe), `assets/icons/` (Twemoji). Générées par **`tools/gen_thumbs.py`** (nécessite Pillow, hors
  script principal) ; format imposé = PNG palettisé + chunk tRNS ~72px sinon bouton blanc.

## Commandes
- `python3 generate_page.py` → génère dans la copie de travail `v1/` (cible par défaut). **Toujours tester ici d'abord.**
- `python3 generate_page.py ~/TheLightingController/LightShows/Summer_stromming` → applique au show réel.
- `python3 tools/gen_thumbs.py` → régénère les vignettes `assets/gobos` + `assets/moves` (si la planche
  gobo ou les `.gcv` changent).
- Pas de tests, lint, ni build : la validation se fait en ouvrant le show dans Sweetlight et en vérifiant boutons/MIDI.

## Cible
- Show actif : `~/TheLightingController/LightShows/Summer_stromming` (défini par `PROJECT` dans `~/TheLightingController/param.ini`).
- Matériel : **8 JB Systems ChallengerBSW (20 c., adr 1/21/41/61/81/101/121/141)**, **8 PAR ADJ (adr 267…323, pas de 8)**, 1 hazer (adr ~298), 1 machine à étincelles. Contrôleur APC40 mkII.
- **Les IDs fixtures et adresses DMX sont codés en dur** en haut de `generate_page.py` (`BSW`/`PAR`/`HAZER`/`SPARK`). Ce sont **les IDs réels du show** lus dans `fixtures.ini` — ne jamais les inventer ; les vérifier dans le show si du matériel change.

## ⚠️ Règles techniques
- Sweetlight **réécrit `live.ini` en quittant** : l'app doit être **FERMÉE** avant d'appliquer le script au show réel, sinon les modifs sont écrasées.
- Le script **lit `live.ini` existant et le réécrit** (il n'en crée pas un de zéro) : la cible doit déjà contenir un `live.ini` valide avec `[live]` et `[board]`.
- Les `.gpj` de mouvement sont générés à partir des courbes `<cible>/Editor/Generator/curves_pantilt/*.gcv` : ces fichiers doivent exister dans le show cible (et dans `v1/`).

## Architecture de `generate_page.py`
Script linéaire et **idempotent** : il accumule des boutons dans `pages` puis réécrit les sections concernées de `live.ini`.

- **Constantes fixtures** (haut du fichier) : `BSW`/`PAR` = `[(id, nom), …]` pour les scènes ; `BSW_GEN`/`PAR_GEN` = `(id, dmx=addr-1, nom)` + chaînes de canaux `BSW_CH`/`PAR_CH` (+ `*_OTHER`) pour les `.gpj`. `HAZER`, `SPARK` idem. Les **IDs sont ceux du show** lus dans `fixtures.ini` (ne pas inventer).
- **Canaux BSW ChallengerBSW(20ch)** (index positionnel) : 0 pan, 2 tilt, 4 pantilt_speed, 8 color (roue), 9 gobo, 10 gobo2, 11 gobo_rotate2, 12 iris (= Angle/Frost : 0-63 Beam, 64-127 Spot, 128-255 Frost), 13 prism, 14 prism_rotate, 15 focus, 16 shutter (0-7 fermé, 8-15 ouvert, 16-131 strobe), 17 dimmer. **PAR par adj** : 0 red, 1 green, 2 blue, 3 amber, 4 dimmer, 5 strobe_effect, 6/7 color_macro mode.
- **Scènes `.scex`** : `write_scene(fichier, fixtures, model, steps)` (une famille) où `steps = [(durée_ms, func)]`, `func(fid)` → liste de `chan(index, nom, val, fade)`. `uniform(channels)` = même état pour toutes.
- **Scènes multi-machines** : `write_multi(fichier, groups, length=500)` = 1 pas ; `write_seq(fichier, steps)` = anim (`steps = [(length, groups), …]`, le 1ᵉʳ pas doit lister toutes les fixtures). `groups = [(fixtures, model, cf)]` où `cf` = liste de `chan(...)` **ou** `func(i, fid)` (varier par fixture : chenillards, vagues, looks alternés).
- **Générateurs `.gpj`** : `make_gpj_from_curve(courbe, out, fixtures_gen, channels_str, other_channels, duration=None)` lit `<courbe>.gcv`, garde sa courbe pan/tilt et réécrit les `[Fixture_N]` pour les BSW. `make_gpj_curve(...)` est la version générique (peut piloter une autre section, ex. `dimmer` pour FX_PULSE via `curves/pulse.gcv`). `duration` remplace le `Duration` de la courbe.
- **Pages** (dans `PAGE_ORDER`, réécrites intégralement) :
  - `DJ LIVE` : busking BSW+PAR, 5 lignes × 8 colonnes. L1 couleurs (BSW roue + PAR RGBA, `dj_col`/`par_c`), L2 mouvements (réutilise les `.gpj` de MOUVEMENT via `move_files`, suivent le fader Vitesse), L3 effets animés (`dj_dim`/`dj_chase`/`dj_police`/`dj_strobe` + `DJ_FX_BUILD` = bouton-curseur via `machines_step`), L4 looks (`dj_look` = teinte alternée fixture par fixture), L5 impacts 1 pas (`dj_full`, blinders, strobe, prisme, étincelles, blackout).
  - `COULEUR`, `GOBO` (2 roues + rotations, `FORCE_TITLE` sur les 4 boutons rotation), `MANUEL` (prisme, Beam/Spot/Wash), `STROBE`, `FX`, `MOUVEMENT` (`MOVE_LAYOUT` = 1 famille/colonne, 1 ligne/variante de forme).
- **MIDI auto** (boucle commune) : `MIDI[titre] = (note, led_on, led_off)` avec `note = (5-ligne)*8 + (colonne-1)` — grille clip APC40 mkII numérotée **de bas en haut** : ligne 1 affichée en haut → rangée du haut (32-39), ligne 5 → rangée du bas (0-7). LED : couleur nommée dans le titre (`led_for`) sinon `LINE_LED` par ligne. **Les titres doivent être uniques toutes pages confondues** (`MIDI` est indexé par titre → tous les boutons DJ sont préfixés `DJ_`).
- **`build_page_block`** : `title` affiché caché quand il y a une image, SAUF pages `FX`/`MANUEL`/`STROBE` (icône pas assez parlante) et `FORCE_TITLE` (texte court imposé). `fader = yes` si titre dans `FADER_BUTTONS` ; sinon `masterspeedfader = 1` si le fichier est un `.gpj`.
- **Réécriture de `live.ini`** : remplace tout de `[page1]` à `[board]` par nos blocs ; **`[page] number` = NOMBRE de pages** (⚠️ pas l'onglet actif — mettre moins que le nombre réel de blocs `[pageN]` fait **supprimer** les pages en trop par SweetLight au chargement suivant). Puis :
  - **`[master_faders]`** entièrement réécrit : F0 **Vitesse** (`type_fader0 = 1` = *speed*, liste vide → scale la vitesse des `.gpj` qui ont `masterspeedfader = 1`), F1 Puissance faisceau (BSW+PAR dimmer), F2 Hazer Fog, F3 Hazer Fan.
  - **Bindings `faderN_midi` = préservation** : injectés (défaut `canal N, CC7, type 1`) **seulement** si `live.ini` n'en contient aucun. ⚠️ Ne jamais re-forcer : ça écraserait le MIDI-learn de l'utilisateur.
  - **`fade_time = 0`** forcé (focus réactif ; effet de bord assumé : les fondus deviennent des coupures).
  - **`buttonstabN`** (bascule de page depuis l'APC40) : les blocs sont créés si absents ; le script active **seulement** le retour LED (`_midiout_data = 1` / `_data_off = 0`) des N pages, **sans toucher l'entrée** `buttonstabN_midi_*` (préservation MIDI-learn). Défaut note 52 / canal N = les 8 boutons **CLIP STOP** de l'APC40 mkII → Clip Stop k affiche la page k.
  - **`[board]`/`[screenN]`** entièrement réécrits : un onglet par page, `screenN title` = nom de page, board k → page k.

## Conventions métier (régressions faciles)
- **Gobos** : roue 1 (canal 9) plages 8-15 G1 … 56-62 G7 (G1-G5 = réducteurs de faisceau, G6/G7 motifs) ; roue 2 (canal 10) 9-17 G1 … 54-63 G6. Valeurs = centre de plage du manuel AYRA ERO 150BSW MKII (= Challenger BSW rebrandé). Vignettes = vrai projeté découpé de `assets/gobos/_source_montage.png`.
- **Strobe BSW** : canal shutter, plage 16-131 (bas = lent, haut = rapide).
- **Rotation gobo/prisme** : 128-190 CCW rapide→lent, 194-255 CW lent→rapide.
- **MIDI APC40 mkII** : `note` = pad (0-39 grille) ; `led_on`/`led_off` = codes LED APC (`APC` dict, relevés sur l'install). Protocole : `note 0x34 canaux 1-8` = boutons CLIP STOP (bascule d'onglet).
- **Format image de bouton** : PNG **palettisé + chunk tRNS**, ~72×72, sinon le bouton s'affiche **blanc** (même un RGB 128×128 identique à la biblio SweetLight ne marche pas). `tools/gen_thumbs.py` (`save_icon`) produit ce format.
- **Vitesse des mouvements** : plus de boutons Lent/Rapide — chaque `.gpj` a `masterspeedfader = 1` et suit le master fader **Vitesse** (type *speed*). Sa vitesse propre = le « 100 % ».

## Règles de travail
- **Commit à chaque demande** : après chaque demande entraînant une modification (script, scènes, config, doc), faire un `git commit` avec un message clair décrivant le changement.
- **`generate_page.py` est la source unique de vérité** : ne **jamais** éditer les fichiers générés (`.scex`, `.gpj`, `live.ini`) à la main ; modifier le script puis régénérer.
- Toujours **valider sur la copie `v1/`** avant d'appliquer au show réel (`Summer_stromming`).
- Les valeurs DMX (couleurs, strobes, gobos) se règlent **par essais** ; les messages de commit historiques documentent ces calages — les consulter avant de retoucher une valeur.
