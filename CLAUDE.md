# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Projet SweetLight — page DJ « KRYPTON + MINIBEAM »

Ce dépôt contient **`generate_page.py`** (~300 lignes, sans dépendances), le script qui génère pour
**Sweetlight / TheLightingController** :
- les **scènes** `.scex` (couleurs, gobos, strobes, effets, shows) — XML,
- les **générateurs de mouvement** `.gpj` (clonés des Lyre Ali express, pour Krypton + Minibeam) — INI,
- la **page 3 « KRYPTON + MINIBEAM »** dans `live.ini` (boutons + raccourcis MIDI APC40) — INI.

## Commandes
- `python3 generate_page.py` → génère dans la copie de travail `v1/` (cible par défaut). **Toujours tester ici d'abord.**
- `python3 generate_page.py ~/TheLightingController/LightShows/default` → applique au show réel.
- Pas de tests, lint, ni build : la validation se fait en ouvrant le show dans Sweetlight et en vérifiant boutons/MIDI.

## Cible
- Show actif : `~/TheLightingController/LightShows/default` (défini par `PROJECT = default` dans `~/TheLightingController/param.ini`).
- Matériel : 6 Martin MAC 250 Krypton (17 c., adresses 92/109/126/143/160/177), 8 Minibeam, 4 Lyre Ali express, 1 par ADJ. Contrôleur APC40 mkII.

## ⚠️ Règles techniques
- Sweetlight **réécrit `live.ini` en quittant** : l'app doit être **FERMÉE** avant d'appliquer le script au show `default`, sinon les modifs sont écrasées.
- Le script **lit `live.ini` existant et le réécrit** (il n'en crée pas un de zéro) : la cible doit déjà contenir un `live.ini` valide avec une section `[board]`.
- Le script **clone les `.gpj` depuis le show `default`** (`SRC_GEN`, codé en dur sur `~/TheLightingController/.../default`) quelle que soit la cible : les fichiers source des mouvements Lyre doivent exister dans `default`.

## Architecture de `generate_page.py`
Script linéaire et **idempotent** : il accumule des boutons puis réécrit les sections concernées de `live.ini`.

- **Constantes fixtures** (haut du fichier) : `KR`/`MB` = `(id, nom)` pour les scènes ; `KR_GEN`/`MB_GEN` = `(id, dmx=addr-1, nom)` + chaînes de canaux `KR_CH`/`MB_CH` pour les `.gpj`. Les **IDs sont ceux du show** (ne pas inventer).
- **Scènes `.scex`** : `write_scene(fichier, fixtures, model, steps)` où `steps = [(durée_ms, func)]` et `func(fid)` renvoie une liste de lignes `chan(index, nom, val, fade)`. **L'`index` de canal est positionnel et propre à chaque modèle** (ex. Krypton : 0=shutter, 1=dimmer, 3=color, 5=gobo, 8=focus, 11=pan, 13=tilt, 16=effect_speed ; Minibeam : 5=dimmer, 6=strobe_speed, 7=rainbow_color, 8=gobo, 10=fonction). `uniform(channels)` = même état pour toutes les fixtures.
- **Générateurs `.gpj`** : `make_gpj()` lit le `.gpj` Lyre source, reprend sa courbe `[Pan/Tilt/uPan/uTilt]`, et réécrit les blocs `[Fixture_N]` pour Krypton/Minibeam. Liste `MOVES` = `(fichier_source, label, note_MIDI, ...)`.
- **Modèle de page** : deux accumulateurs globaux — `buttons` = `(colonne, ligne, nom_fichier, titre, couleur|None)` et `MIDI` = `titre -> (note, led_on, led_off)`. Le code est organisé en blocs `COLONNE 1..9` (1-4 Krypton, 5 gobos KR, 6-8 Minibeam, 9 gobos MB). La page `[page3]` est ensuite construite bouton par bouton.
- **Réécriture idempotente de `live.ini`** : le script supprime toute section `[page3]` existante (jusqu'à `[board]`) puis réinsère ; idem pour `[master_faders]`. Relancer le script ne duplique jamais. Il manipule aussi `[page] number`, et insère les `[master_faders]` (fader1=Intensité→dimmers, fader2=Vitesse).

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
