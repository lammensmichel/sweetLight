# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Projet SweetLight — page DJ « KRYPTON + MINIBEAM »

Ce dépôt contient **`generate_page.py`** (~580 lignes, sans dépendances), le script qui génère pour
**Sweetlight / TheLightingController** :
- les **scènes** `.scex` (couleurs, gobos, strobes, effets, shows) — XML,
- les **générateurs de mouvement** `.gpj` (clonés des Lyre Ali express, pour Krypton + Minibeam) — INI,
- **deux pages** dans `live.ini` (boutons + raccourcis MIDI APC40) — INI :
  - page **« KRYPTON + MINIBEAM »** : contrôle détaillé machine par machine (couleurs/mouvements/effets/gobos KR & MB),
  - page **« LIVE »** : mapping busking multi-machines (KR + MB + Lyre + PAR + Blinder + Laser + Hazer) en grille APC40.

## Commandes
- `python3 generate_page.py` → génère dans la copie de travail `v1/` (cible par défaut). **Toujours tester ici d'abord.**
- `python3 generate_page.py ~/TheLightingController/LightShows/default` → applique au show réel.
- Pas de tests, lint, ni build : la validation se fait en ouvrant le show dans Sweetlight et en vérifiant boutons/MIDI.

## Cible
- Show actif : `~/TheLightingController/LightShows/default` (défini par `PROJECT = default` dans `~/TheLightingController/param.ini`).
- Matériel : 6 Martin MAC 250 Krypton (17 c., adresses 92/109/126/143/160/177), 8 Minibeam, 4 Lyre Ali express, 1 par ADJ (adr 1), 1 blinder/strobe JB Accu-Compact (adr 61), 1 laser RGB (adr 71), 1 hazer (adr 298). Contrôleur APC40 mkII.
- **Les IDs fixtures et adresses DMX sont codés en dur** (en haut du fichier pour KR/MB ; section LIVE pour Lyre/PAR/Blinder/Laser/Hazer). Ce sont **les IDs réels du show** lus dans `fixtures.ini` — ne jamais les inventer ; les vérifier dans le show si du matériel change.

## ⚠️ Règles techniques
- Sweetlight **réécrit `live.ini` en quittant** : l'app doit être **FERMÉE** avant d'appliquer le script au show `default`, sinon les modifs sont écrasées.
- Le script **lit `live.ini` existant et le réécrit** (il n'en crée pas un de zéro) : la cible doit déjà contenir un `live.ini` valide avec une section `[board]`.
- Le script **clone les `.gpj` depuis le show `default`** (`SRC_GEN`, codé en dur sur `~/TheLightingController/.../default`) quelle que soit la cible : les fichiers source des mouvements Lyre doivent exister dans `default`.

## Architecture de `generate_page.py`
Script linéaire et **idempotent** : il accumule des boutons puis réécrit les sections concernées de `live.ini`.

- **Constantes fixtures** (haut du fichier) : `KR`/`MB` = `(id, nom)` pour les scènes ; `KR_GEN`/`MB_GEN` = `(id, dmx=addr-1, nom)` + chaînes de canaux `KR_CH`/`MB_CH` pour les `.gpj`. Les **IDs sont ceux du show** (ne pas inventer).
- **Scènes `.scex`** : `write_scene(fichier, fixtures, model, steps)` où `steps = [(durée_ms, func)]` et `func(fid)` renvoie une liste de lignes `chan(index, nom, val, fade)`. **L'`index` de canal est positionnel et propre à chaque modèle** (ex. Krypton : 0=shutter, 1=dimmer, 3=color, 5=gobo, 8=focus, 11=pan, 13=tilt, 16=effect_speed ; Minibeam : 5=dimmer, 6=strobe_speed, 7=rainbow_color, 8=gobo, 10=fonction). `uniform(channels)` = même état pour toutes les fixtures.
- **Générateurs `.gpj`** : `make_gpj()` lit le `.gpj` Lyre source, reprend sa courbe `[Pan/Tilt/uPan/uTilt]`, et réécrit les blocs `[Fixture_N]` pour Krypton/Minibeam. Liste `MOVES` = `(fichier_source, label, note_MIDI, ...)`.
- **Page « KRYPTON + MINIBEAM »** : accumulateur global `buttons` = `(colonne, ligne, nom_fichier, titre, couleur|None)` + dict `MIDI` = `titre -> (note, led_on, led_off)`. Organisée en blocs `COLONNE 1..9` (1-4 Krypton, 5 gobos KR, 6-8 Minibeam, 9 gobos MB). Une seule famille de fixtures par scène.
- **Page « LIVE »** (mapping busking) : accumulateur `live_buttons`, scènes **multi-machines** via helpers dédiés. `write_multi(fichier, groups)` = scène 1 pas ; `write_seq(fichier, steps)` = anim multi-pas. `groups = [(fixtures, model, cf)]` où `cf` est une liste de `chan(...)` **ou** une `func(i, fid)` (pour varier par fixture : chenillards, vagues). Helpers couleur par famille (`_krc`/`_mbc`/`_lyc`/`_prc`) et position (`_mbpt`/`_lypt`/`kr_pos`), agrégés par `color_groups*`/`pos_groups`/`dim_groups`. Grille 6 lignes : 1 couleurs, 2 positions, 3 effets animés, 4 looks, 5 impacts, 6 sous-faders. **MIDI auto** : pour les lignes 1-5, `note = (ligne-1)*8 + (colonne-1)` (grille clip APC40, 0-39) ; ligne 6 (sous-faders) hors grille, pas de note.
- **Réécriture idempotente de `live.ini`** : le script lit le fichier, **retire nos pages par nom** (`OUR_NAMES`), **renumérote les pages utilisateur 1..k sans trou** (un trou force SweetLight à renumeroter), puis ajoute nos pages à la suite et règle `[page] number` pour afficher LIVE. Il réécrit aussi entièrement `[master_faders]` et les bindings faders physiques. Relancer le script ne duplique jamais.
- **8 master faders profondeur-aware** (section `[master_faders]`) : F1 KR Avant / F2 KR Arrière / F3 Minibeam / F4 Lyre / F5 PAR Ambiance / F6 Vitesse / F7 Laser / F8 Master. Chaque fader liste `id,canal|...`. Les **bindings physiques APC40** (`faderN_midi_*`, canal N, CC7, type 1) sont figés dans le script pour survivre aux redémarrages. `fade_time = 0` est forcé pour un focus réactif (effet de bord assumé : les fondus deviennent des coupures sèches).

## Conventions métier (régressions faciles)
- **Décalage pan Krypton** : `KR_PAN_OFF16 = -10923` (≈ -90°) recentre les Krypton face public ; appliqué dans `kr_pos()` et au pan des `.gpj`. Ne pas retirer sans raison.
- **MIDI APC40 mkII** : `note` = pad, `led_on`/`led_off` = codes couleur LED de l'APC40. KR et MB partagent souvent la même note (un pad allume les deux familles). Les couleurs sont parfois calées sur les pads des Lyre existantes.
- **Strobe Krypton** : shutter **haut = lent, bas = rapide** (contre-intuitif). Valeurs réglées finement par essais (voir messages de commit).
- **Boutons spéciaux** : `FADER_BUTTONS` (curseur, ex. Focus, scène 2-pas), `SPEED_TITLES` + `.gpj` → `masterspeedfader = 1` (suivent le fader Vitesse).
- **`color` sans `fade` + `effect_speed = 0`** : saut direct de la roue de couleur à vitesse max (pas de transition).

## Règles de travail
- **Commit à chaque demande** : après chaque demande entraînant une modification (script, scènes, config, doc), faire un `git commit` avec un message clair décrivant le changement.
- **`generate_page.py` est la source unique de vérité** : ne **jamais** éditer les fichiers générés (`.scex`, `.gpj`, `live.ini`) à la main ; modifier le script puis régénérer.
- Toujours **valider sur la copie `v1/`** avant d'appliquer au show `default`.
- Les valeurs DMX (couleurs, strobes, gobos) se règlent **par essais** ; les messages de commit historiques documentent ces calages — les consulter avant de retoucher une valeur.
