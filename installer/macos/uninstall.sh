#!/bin/bash
# VLK Launcher - Script de désinstallation macOS
# Créé par yolezz pour VOLKZ Clan

set -e

echo "========================================"
echo "VLK Launcher - Désinstallation"
echo "========================================"
echo

# Vérifier si l'application est installée
if [ ! -d "/Applications/VLKLauncher.app" ]; then
    echo "[INFO] VLK Launcher n'est pas installé"
    exit 0
fi

# Demander confirmation
read -p "Voulez-vous vraiment désinstaller VLK Launcher? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Désinstallation annulée"
    exit 0
fi

# Supprimer l'application
echo "[INFO] Suppression de l'application..."
sudo rm -rf /Applications/VLKLauncher.app

# Nettoyer les fichiers de configuration (optionnel)
read -p "Supprimer également les fichiers de configuration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Suppression des fichiers de configuration..."
    rm -rf ~/Library/Application\ Support/VLKLauncher
    rm -rf ~/Library/Caches/VLKLauncher
    rm -rf ~/Library/Preferences/com.volkz.vlklauncher.plist
fi

echo
echo "========================================"
echo "[SUCCÈS] Désinstallation terminée!"
echo "========================================"
echo "VLK Launcher a été désinstallé de votre système"
echo
