#!/bin/bash
# VLK Launcher - Script de construction package macOS
# Créé par yolezz pour VOLKZ Clan

set -e

# Récupérer la version depuis le premier argument ou utiliser celle par défaut
VERSION=${1:-"1.0.0"}

echo "========================================"
echo "VLK Launcher - Construction Package macOS"
echo "========================================"
echo "Version: $VERSION"
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé"
    exit 1
fi

# Vérifier si PyInstaller est installé
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "[INFO] Installation de PyInstaller..."
    pip3 install pyinstaller
fi

# Installer les dépendances
echo "[INFO] Installation des dépendances..."
pip3 install -r ../src/client/requirements.txt

# Nettoyer les builds précédents
echo "[INFO] Nettoyage des builds précédents..."
cd ..
rm -rf dist build
cd installer/macos

# Construire l'application .app avec PyInstaller
echo "[INFO] Construction de l'application .app..."
cd ..
pyinstaller vlk_launcher.spec --distpath dist/macos --workpath build/macos --clean --noconfirm
cd installer/macos

if [ ! -d "../dist/macos/VLKLauncher.app" ]; then
    echo "[ERREUR] Échec de la construction .app"
    exit 1
fi

# Créer le dossier de travail pour le package
echo "[INFO] Préparation du package..."
WORK_DIR="pkg_work"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/Applications"

# Copier l'application dans le dossier de travail
cp -R ../dist/macos/VLKLauncher.app "$WORK_DIR/Applications/"

# Créer le script post-install
cat > "$WORK_DIR/postinstall" << 'EOF'
#!/bin/bash
# Script post-installation

# Créer un lien symbolique dans /Applications si l'utilisateur le souhaite
APP_PATH="/Applications/VLKLauncher.app"

if [ ! -e "$APP_PATH" ]; then
    ln -s "$2/Applications/VLKLauncher.app" "$APP_PATH"
fi

# Ajuster les permissions
chmod -R 755 "$2/Applications/VLKLauncher.app"

exit 0
EOF

chmod +x "$WORK_DIR/postinstall"

# Créer le script pre-remove (pour la désinstallation)
cat > "$WORK_DIR/preremove" << 'EOF'
#!/bin/bash
# Script de pré-désinstallation

# Supprimer l'application de /Applications
APP_PATH="/Applications/VLKLauncher.app"
if [ -L "$APP_PATH" ]; then
    rm "$APP_PATH"
fi

exit 0
EOF

chmod +x "$WORK_DIR/preremove"

# Créer le fichier de distribution
cat > "Distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>VLK Launcher</title>
    <package id="com.volkz.vlklauncher" version="$VERSION" auth="root">
        <payload-install/>
    </package>
    <choices-outline>
        <line choice="default">
            <line choice="vlklauncher"/>
        </line>
    </choices-outline>
    <choice id="default" visible="false"/>
    <choice id="vlklauncher" visible="true" title="VLK Launcher" description="Lanceur SaaS esports pour VOLKZ Clan">
        <pkg-ref id="com.volkz.vlklauncher"/>
    </choice>
    <pkg-ref id="com.volkz.vlklauncher" version="$VERSION" onConclusion="none">VLKLauncher.pkg</pkg-ref>
    <welcome file="welcome.html"/>
    <license file="license.txt"/>
    <conclusion file="conclusion.html"/>
</installer-gui-script>
EOF

# Créer le fichier de licence
cat > "license.txt" << 'EOF'
VLK LAUNCHER - CONTRAT DE LICENCE D'UTILISATION

VOLKZ Clan - Créé par yolezz
Version 1.0.0

IMPORTANT: VEUILLEZ LIRE ATTENTIVEMENT CE CONTRAT AVANT D'UTILISER CE LOGICIEL.

1. PROPRIÉTÉ DU LOGICIEL
Ce logiciel ("VLK Launcher") est la propriété exclusive de yolezz et du clan VOLKZ.
Tous les droits, titres et intérêts dans et sur le logiciel sont réservés.

2. LICENCE D'UTILISATION
L'utilisation de ce logiciel est soumise à l'obtention préalable d'une licence valide.
Pour obtenir une licence, vous devez contacter yolezz directement:
- Discord: yolezz
- Email: yolezz.secret@gmail.com

3. RESTRICTIONS
- Vous n'avez pas le droit de distribuer, copier, modifier ou reverse-engineer ce logiciel
- L'utilisation sans licence valide est strictement interdite
- Toute tentative de contourner le système de licence entraînera une désactivation immédiate

4. DÉCLARATION DE CONFIDENTIALITÉ
Ce logiciel ne collecte aucune donnée personnelle sans votre consentement explicite.

5. LIMITATION DE RESPONSABILITÉ
Ce logiciel est fourni "tel quel", sans garantie d'aucune sorte, expresse ou implicite.

6. SUPPORT
Pour toute question relative aux licences ou au support technique, contactez yolezz.

En installant ce logiciel, vous acceptez les termes de ce contrat de licence.

© 2024 VOLKZ Clan - Tous droits réservés
EOF

# Créer la page de bienvenue
cat > "welcome.html" << EOF
<html>
<head>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; }
        h1 { color: #00d4ff; }
        .info { background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🎮 VLK Launcher</h1>
    <p>Bienvenue dans l'installateur du VLK Launcher pour VOLKZ Clan.</p>
    
    <div class="info">
        <strong>Informations importantes:</strong>
        <ul>
            <li>Version: $VERSION</li>
            <li>Créé par: yolezz</li>
            <li>Pour: VOLKZ Clan</li>
        </ul>
    </div>
    
    <p><strong>Obtenir une licence:</strong></p>
    <p>Pour utiliser ce logiciel, vous devez obtenir une licence valide auprès de yolezz:</p>
    <ul>
        <li>Discord: yolezz</li>
        <li>Email: yolezz.secret@gmail.com</li>
    </ul>
    
    <p>Cliquez sur "Continuer" pour procéder à l'installation.</p>
</body>
</html>
EOF

# Créer la page de conclusion
cat > "conclusion.html" << 'EOF'
<html>
<head>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 20px; }
        h1 { color: #00d4ff; }
        .success { background: #d4edda; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>✅ Installation terminée</h1>
    
    <div class="success">
        <p>VLK Launcher a été installé avec succès!</p>
    </div>
    
    <p>Vous pouvez lancer l'application depuis le dossier Applications.</p>
    
    <p><strong>Pour obtenir une licence:</strong></p>
    <ul>
        <li>Discord: yolezz</li>
        <li>Email: yolezz.secret@gmail.com</li>
    </ul>
    
    <p>Merci d'utiliser VLK Launcher!</p>
</body>
</html>
EOF

# Créer le package avec pkgbuild
echo "[INFO] Création du package .pkg..."
pkgbuild \
    --root "$WORK_DIR" \
    --component-plist "Component.plist" \
    --install-location / \
    --scripts "$WORK_DIR" \
    --identifier com.volkz.vlklauncher \
    --version "$VERSION" \
    VLKLauncher.pkg

# Créer le package de distribution
echo "[INFO] Création du package de distribution..."
productbuild \
    --distribution Distribution.xml \
    --package-path . \
    --resources . \
    "output/VLKLauncher-$VERSION.pkg"

# Nettoyer
echo "[INFO] Nettoyage..."
rm -rf "$WORK_DIR"
rm -f VLKLauncher.pkg Component.plist

echo
echo "========================================"
echo "[SUCCÈS] Package créé avec succès!"
echo "========================================"
echo "Fichier: output/VLKLauncher-1.0.0.pkg"
echo
