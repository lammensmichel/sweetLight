#!/usr/bin/env bash
# Installe les dependances necessaires pour generer les light shows (generate_page.py) et faire
# tourner le pont MIDI APC40<->Sweetlight (tools/apc40_bridge.py) sur un Mac.
#
# Ce que ce script fait :
#   - verifie python3 (deja present sur macOS / via Xcode Command Line Tools)
#   - installe python-rtmidi (pip3) pour le pont MIDI
#   - installe Pillow (pip3) pour tools/gen_thumbs.py (regenerer les vignettes) - optionnel
#
#   - copie le show reel "Generaliste" (inclus dans ce repo) dans
#     ~/TheLightingController/LightShows/Generaliste - il apparait alors tel quel dans Sweetlight
#     ("Ouvrir un lightshow"), sans copie manuelle. Ne touche pas a un dossier deja present.
#   - installe VirtualHere USB Client (partage du D512S Sweetlight depuis le Pi) dans /Applications,
#     depuis le site officiel virtualhere.com
#
# Ce que ce script NE fait PAS (et ne peut pas automatiser) :
#   - installer Sweetlight lui-meme (deja installe manuellement, /Applications/SweetLight)
#   - configurer les peripheriques MIDI virtuels dans Sweetlight (Preferences > Midi > Ajouter) :
#     ca doit etre fait une fois a la main dans l'appli apres avoir lance le pont au moins une
#     fois (pour que les ports virtuels existent et soient visibles dans la liste), voir README.
#
# Lancement : ./install.sh

set -e

echo "=== Mise a jour du repo (git pull) ==="
git -C "$(cd "$(dirname "$0")" && pwd)" pull || echo "pull impossible (pas un depot git ? pas de reseau ?) - on continue avec la version locale."

echo
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
echo "=== Show reel Generaliste (~/TheLightingController/LightShows/Generaliste) ==="
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SHOW_SRC="$REPO_DIR/Generaliste"
SHOW_DIR="$HOME/TheLightingController/LightShows/Generaliste"
if [ -e "$SHOW_DIR" ]; then
  echo "deja present ($SHOW_DIR)."
  if pgrep -f "TheLightingController" >/dev/null 2>&1; then
    echo "Sweetlight est ouvert - on ne touche pas au show pendant que l'appli tourne (risque"
    echo "d'ecraser un travail en cours). Ferme Sweetlight puis relance ./install.sh."
  else
    echo "Sweetlight ferme : reapplication du script (met a jour boutons/mouvements/chemins,"
    echo "preserve le MIDI-learn deja fait a la main)..."
    python3 "$REPO_DIR/generate_page.py" "$SHOW_DIR"
  fi
else
  mkdir -p "$HOME/TheLightingController/LightShows"
  cp -R "$SHOW_SRC" "$SHOW_DIR"
  echo "copie dans $SHOW_DIR."
  # Premiere installation seulement (rien d'existant a ecraser) : applique tout de suite le script
  # dessus, pour que les chemins d'images/icones etc. soient corrects des le depart.
  python3 "$REPO_DIR/generate_page.py" "$SHOW_DIR"
fi

echo
echo "=== VirtualHere USB Client (partage du D512S Sweetlight depuis le Pi) ==="
if [ -d "/Applications/VirtualHereUniversal.app" ]; then
  echo "deja installe."
else
  TMP_DMG="$(mktemp -t virtualhere).dmg"
  if curl -fL -o "$TMP_DMG" "https://www.virtualhere.com/sites/default/files/usbclient/VirtualHereUniversal.dmg"; then
    MOUNT_DIR=$(hdiutil attach "$TMP_DMG" -nobrowse | awk '/\/Volumes\// {print $NF; exit}')
    if [ -n "$MOUNT_DIR" ] && [ -d "$MOUNT_DIR/VirtualHereUniversal.app" ]; then
      cp -R "$MOUNT_DIR/VirtualHereUniversal.app" /Applications/
      echo "installe dans /Applications."
    else
      echo "echec : app introuvable dans l'image montee."
    fi
    [ -n "$MOUNT_DIR" ] && hdiutil detach "$MOUNT_DIR" -quiet
  else
    echo "echec du telechargement - installe-le manuellement : https://www.virtualhere.com/usb_client_software"
  fi
  rm -f "$TMP_DMG"
fi

echo
echo "=== OK ==="
echo "Generaliste devrait maintenant apparaitre dans Sweetlight (Ouvrir un lightshow)."
echo
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
