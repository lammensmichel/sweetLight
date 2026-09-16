#!/usr/bin/env bash
# Installe les dependances necessaires pour generer les light shows (generate_page.py) et faire
# tourner le pont MIDI APC40<->Sweetlight (tools/apc40_bridge.py) sur un Mac.
#
# Ce que ce script fait :
#   - verifie python3 (deja present sur macOS / via Xcode Command Line Tools)
#   - installe python-rtmidi (pip3) pour le pont MIDI
#   - installe Pillow (pip3) pour tools/gen_thumbs.py (regenerer les vignettes) - optionnel
#
# Ce que ce script NE fait PAS (et ne peut pas automatiser) :
#   - installer Sweetlight lui-meme (deja installe manuellement, /Applications/SweetLight)
#   - configurer les peripheriques MIDI virtuels dans Sweetlight (Preferences > Midi > Ajouter) :
#     ca doit etre fait une fois a la main dans l'appli apres avoir lance le pont au moins une
#     fois (pour que les ports virtuels existent et soient visibles dans la liste), voir README.
#   - creer/deployer un light show reel dans ~/TheLightingController/LightShows/ : ce depot ne
#     contient qu'un sandbox de travail (v2/) ; appliquer au show reel avec :
#       python3 generate_page.py ~/TheLightingController/LightShows/<NomDuShow>
#
# Lancement : ./install.sh

set -e

echo "=== Verification de python3 ==="
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 introuvable. Installe les Xcode Command Line Tools :"
  echo "  xcode-select --install"
  exit 1
fi
python3 --version

echo
echo "=== Installation de python-rtmidi (pont MIDI, tools/apc40_bridge.py) ==="
python3 -c "import rtmidi" 2>/dev/null && echo "deja installe, rien a faire." || python3 -m pip install python-rtmidi

echo
echo "=== Installation de Pillow (optionnel, tools/gen_thumbs.py) ==="
# Pas de --upgrade : ce Python est partage avec d'autres outils qui epinglent leur propre version
# de Pillow/cffi - une mise a jour forcee ici peut casser leurs dependances.
python3 -c "import PIL" 2>/dev/null && echo "deja installe, rien a faire." || python3 -m pip install Pillow || echo "Pillow non installe (optionnel, ignore si erreur)."

echo
echo "=== OK ==="
echo "Pour tester le generateur de show (sandbox v2/, ne touche rien de reel) :"
echo "  python3 generate_page.py"
echo
echo "Pour lancer le pont MIDI APC40 (branche l'APC40 avant) :"
echo "  python3 tools/apc40_bridge.py"
echo "  puis ouvre http://localhost:8090"
echo
echo "1ere fois seulement : dans Sweetlight > Preferences > Midi, clique Ajouter et selectionne"
echo "les peripheriques 'SweetLight-P1-...' a 'SweetLight-P7-...' crees par le pont (entree ET"
echo "sortie), en plus de l'APC40 mkII physique deja present."
