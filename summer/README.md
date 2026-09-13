# Archive — Summer festival (rig « BSW + PAR »)

Snapshot figé de tout ce qui a servi pour le festival d'été. Ce dossier est un
instantané : le dépôt principal (`../generate_page.py`, `../CLAUDE.md`, `../v1/`)
continue d'évoluer pour d'autres projets (ex. la soirée généraliste) sans toucher
à cette archive.

## Contenu

- **`LightShow_Summer_stromming/`** — copie complète du show réel Sweetlight tel
  qu'appliqué (`~/TheLightingController/LightShows/Summer_stromming`) : `live.ini`,
  `fixtures.ini`, `scenes/`, `Editor/Generator/curves_pantilt/*.gcv`, etc.
  Pour la restaurer : copier ce dossier dans `~/TheLightingController/LightShows/`
  (Sweetlight fermé), et sélectionner ce projet dans `param.ini` / au lancement.
- **`generate_page.py`** — le script exact (constantes fixtures + pages) qui a
  généré ce show. Fige les IDs/adresses DMX du rig Summer.
- **`CLAUDE_at_archive_time.md`** — copie des instructions du dépôt au moment de
  l'archivage (documente les conventions utilisées pour ce show).
- **`assets/`**, **`tools/`** — vignettes (gobos/mouvements/icônes) et le
  générateur `gen_thumbs.py` utilisés pour ce rig.

## Rig Summer (rappel)
8 JB Systems ChallengerBSW (20 ch., adr 1/21/41/61/81/101/121/141),
8 PAR ADJ (adr 267…323, pas de 8), 1 hazer (~adr 298), 1 machine à étincelles.
Contrôleur APC40 mkII. 7 pages : DJ LIVE, COULEUR, GOBO, MANUEL, STROBE, FX, MOUVEMENT.

Archivé le 2026-09-13.
