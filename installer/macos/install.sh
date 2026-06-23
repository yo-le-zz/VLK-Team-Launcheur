#!/bin/bash
# VLK Launcher - Script d'installation simplifié macOS
# Créé par yolezz pour VOLKZ Clan

set -e

echo "========================================"
echo "VLK Launcher - Installation"
echo "========================================"
echo

# Vérifier si l'application existe
if [ ! -d "VLKLauncher.app" ]; then
    echo "[ERREUR] VLKLauncher.app non trouvé"
    echo "Assurez-vous d'avoir construit l'application avec PyInstaller d'abord"
    exit 1
fi

# Demander confirmation
read -p "Installer VLK Launcher dans /Applications? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Installation annulée"
    exit 0
fi

# Copier l'application
echo "[INFO] Copie de l'application vers /Applications..."
sudo cp -R VLKLauncher.app /Applications/

# Ajuster les permissions
echo "[INFO] Ajustement des permissions..."
sudo chmod -R 755 /Applications/VLKLauncher.app

echo
echo "========================================"
echo "[SUCCÈS] Installation terminée!"
echo "========================================"
echo "Vous pouvez lancer VLK Launcher depuis le dossier Applications"
echo
echo "Pour obtenir une licence, contactez yolezz:"
echo "- Discord: yolezz"
echo "- Email: yolezz.secret@gmail.com"
echo
