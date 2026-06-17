# Projet SweetLight — page DJ « KRYPTON + MINIBEAM »

Ce dépôt contient **`generate_page.py`**, le script qui génère pour le logiciel
**Sweetlight / TheLightingController** :
- les **scènes** `.scex` (couleurs, gobos, strobes, effets, shows),
- les **générateurs de mouvement** `.gpj` (clonés des Lyre Ali express, pour Krypton + Minibeam),
- la **page 3 « KRYPTON + MINIBEAM »** dans `live.ini` (boutons + raccourcis MIDI APC40).

## Cible
- Show actif : `~/TheLightingController/LightShows/default` (défini par `PROJECT = default` dans `~/TheLightingController/param.ini`).
- Exécution : `python3 generate_page.py <dossier_du_show>` (sans argument = copie de travail `v1/`).
- Matériel : 6 Martin MAC 250 Krypton (17 c., adresses 92/109/126/143/160/177), 8 Minibeam, 4 Lyre Ali express, 1 par ADJ. Contrôleur APC40 mkII.

## ⚠️ Règle technique
Sweetlight **réécrit `live.ini` en quittant** : il doit être **FERMÉ** avant d'appliquer le script au show `default`. Le script refuse de tourner si l'app est ouverte.

## Règles de travail
- **Commit à chaque demande** : après chaque demande de l'utilisateur entraînant une modification (script, scènes, config, doc), faire un `git commit` avec un message clair décrivant le changement.
- **`generate_page.py` est la source unique de vérité** : ne pas éditer les fichiers générés à la main ; modifier le script puis régénérer.
- Toujours **valider sur la copie `v1/`** avant d'appliquer au show `default`.
