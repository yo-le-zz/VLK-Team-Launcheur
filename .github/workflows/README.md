# Workflow GitHub Actions - Build Automatisé

## Vue d'ensemble

Ce workflow construit automatiquement les installateurs VLK Launcher pour Windows et macOS à chaque push sur la branche `main`.

## Fonctionnement

### 1. Extraction de version
Le workflow extrait automatiquement la version depuis:
1. Le message du commit (pattern: `X.Y.Z`)
2. Fallback: pyproject.toml
3. Fallback: `1.0.0` (version par défaut)

**Exemple de commit:**
```bash
git commit -m "1.0.0 compile : project macos et windows + installateur macos et windows"
```

### 2. Build Windows
- Installation des dépendances Python
- Construction de l'exécutable avec PyInstaller
- Installation automatique de Inno Setup via Chocolatey
- Construction de l'installateur .exe
- Upload des artefacts

### 3. Build macOS
- Installation des dépendances Python et portaudio
- Construction de l'application .app avec PyInstaller
- Construction du package .pkg
- Upload des artefacts

### 4. Release GitHub
- Création automatique d'une release taggée
- Upload de 4 fichiers:
  - `VLKLauncher-Setup-X.Y.Z.exe` (Installateur Windows)
  - `VLKLauncher-X.Y.Z.pkg` (Package macOS)
  - `VLKLauncher-windows-standalone.zip` (Standalone Windows)
  - `VLKLauncher-macos-standalone.zip` (Standalone macOS)

## Installateurs (Hors Ligne)

Les installateurs embarquent tous les fichiers compilés et fonctionnent **sans connexion internet**:

### Windows
- L'exécutable et toutes les dépendances sont inclus dans le .exe
- Installation dans Program Files
- Raccourcis automatiques
- Désinstallation via Panneau de configuration

### macOS
- L'application .app complète est incluse dans le .pkg
- Installation standard dans /Applications
- Scripts de désinstallation intégrés

## Structure des artefacts

```
release-assets/
├── VLKLauncher-Setup-1.0.0.exe           # Installateur Windows (recommandé)
├── VLKLauncher-1.0.0.pkg                 # Package macOS (recommandé)
├── VLKLauncher-windows-standalone.zip    # Exécutable Windows seul
└── VLKLauncher-macos-standalone.zip      # Application macOS seule
```

## Déclenchement manuel

Le workflow peut aussi être déclenché manuellement via l'onglet "Actions" sur GitHub.

## Créé par

yolezz pour VOLKZ Clan
