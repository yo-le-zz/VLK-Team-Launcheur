# Installateurs VLK Launcher

Ce dossier contient les scripts de construction d'installateurs pour VLK Launcher.

## Structure

```
installer/
├── windows/          # Installateur Windows (Inno Setup)
│   ├── vlk_launcher_setup.iss    # Script Inno Setup
│   ├── build_installer.bat       # Script de construction
│   ├── license.txt               # Contrat de licence
│   └── output/                   # Sortie de l'installateur
└── macos/            # Package macOS
    ├── build_pkg.sh              # Script de construction .pkg
    ├── install.sh                # Script d'installation manuel
    ├── uninstall.sh              # Script de désinstallation
    └── output/                   # Sortie du package
```

## Instructions

### Windows

1. Télécharger et installer Inno Setup 6 depuis https://jrsoftware.org/isdl.php
2. Ouvrir une invite de commande dans `installer/windows/`
3. Exécuter `build_installer.bat`
4. L'installateur sera créé dans `output/VLKLauncher-Setup-1.0.0.exe`

### macOS

1. S'assurer que Xcode Command Line Tools sont installés (`xcode-select --install`)
2. Ouvrir un terminal dans `installer/macos/`
3. Exécuter `./build_pkg.sh`
4. Le package sera créé dans `output/VLKLauncher-1.0.0.pkg`

## Contact

Pour toute question sur les installateurs ou les licences, contactez yolezz:
- Discord: yolezz
- Email: yolezz.secret@gmail.com
