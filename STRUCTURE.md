# Structure du Projet VLK Launcher

Arborescence organisée et documentée du projet VLK Launcher créé par yolezz pour VOLKZ Clan.

```
vlk-launcher/
├── .github/
│   └── workflows/
│       ├── release.yml              # Workflow automatisé de build et release
│       ├── start_server.sh          # Script de démarrage serveur (GitHub Actions)
│       └── README.md                # Documentation du workflow
│
├── installer/                       # Scripts et configuration des installateurs
│   ├── README.md                    # Documentation des installateurs
│   ├── windows/                     # Installateur Windows (Inno Setup)
│   │   ├── build_installer.bat      # Script de construction installateur
│   │   ├── generate_iss.py          # Générateur de script Inno Setup
│   │   ├── license.txt              # Contrat de licence
│   │   ├── repair.bat               # Script de réparation
│   │   ├── uninstall.bat            # Script de désinstallation
│   │   └── vlk_launcher_setup.iss    # Configuration Inno Setup
│   └── macos/                       # Installateur macOS (pkgbuild)
│       ├── build_pkg.sh             # Script de construction package
│       ├── install.sh               # Script d'installation manuel
│       └── uninstall.sh             # Script de désinstallation
│
├── scripts/                         # Scripts utilitaires
│   ├── extract_version.py          # Extraction de version depuis commit
│   ├── gen_licenses.py             # Générateur de licences
│   ├── run_client.sh               # Lancement du client
│   └── run_server.sh               # Lancement du serveur
│
├── src/                            # Code source principal
│   ├── client/                     # Application desktop (PySide6)
│   │   ├── assets/                 # Icônes et ressources
│   │   │   ├── icon.ico            # Icône Windows
│   │   │   ├── icon.png            # Icône PNG
│   │   │   └── icon.svg            # Icône SVG
│   │   ├── core/                   # Logique métier client
│   │   │   ├── api.py              # Client API
│   │   │   ├── config_loader.py    # Chargement configuration
│   │   │   └── updater.py          # Gestionnaire de mises à jour
│   │   ├── ui/                     # Interface utilisateur
│   │   │   ├── dialogs/            # Boîtes de dialogue
│   │   │   │   └── update_dialog.py
│   │   │   ├── panels/             # Panneaux de l'interface
│   │   │   │   ├── admin_panel.py
│   │   │   │   ├── chat_panel.py
│   │   │   │   ├── home_panel.py
│   │   │   │   ├── members_panel.py
│   │   │   │   ├── profile_panel.py
│   │   │   │   ├── ranking_panel.py
│   │   │   │   └── voice_panel.py
│   │   │   ├── login_window.py     # Fenêtre de connexion
│   │   │   ├── main_window.py      # Fenêtre principale
│   │   │   ├── theme.py            # Thème et styles
│   │   │   └── widgets.py          # Composants UI personnalisés
│   │   ├── voice/                  # Intégration vocale
│   │   │   ├── voice_client.py     # Client vocal
│   │   │   └── voice_engine.py     # Moteur vocal
│   │   ├── __init__.py
│   │   ├── main.py                 # Point d'entrée client
│   │   └── requirements.txt        # Dépendances Python client
│   │
│   └── server/                     # Backend FastAPI
│       ├── core/                   # Cœur du serveur
│       │   ├── auth_utils.py       # Utilitaires d'authentification
│       │   ├── config.py           # Configuration serveur
│       │   ├── database.py         # Gestion base de données
│       │   └── ws_manager.py       # Gestionnaire WebSocket
│       ├── models/                 # Modèles de données
│       ├── routers/                # Routes API
│       │   ├── admin.py            # Routeur administration
│       │   ├── announcements.py    # Routeur annonces
│       │   ├── auth.py             # Routeur authentification
│       │   └── licenses.py         # Routeur licences
│       ├── static/                 # Fichiers statiques
│       │   └── admin.html          # Interface admin web
│       ├── __init__.py
│       ├── main.py                 # Point d'entrée serveur
│       └── requirements.txt        # Dépendances Python serveur
│
├── .env.client.example             # Exemple configuration client
├── .env.example                    # Exemple configuration serveur
├── .gitignore                      # Fichiers ignorés par Git
├── config.json.example             # Exemple configuration application
├── pyproject.toml                  # Configuration projet Python
├── README.md                       # Documentation principale
├── uv.lock                         # Lock des dépendances (uv)
└── vlk_launcher.spec               # Spécification PyInstaller
```

## Description des Dossiers Principaux

### `/src` - Code Source
- **client/**: Application desktop avec interface PySide6
- **server/**: Backend API FastAPI avec WebSocket

### `/installer` - Installateurs
- **windows/**: Scripts pour créer l'installateur Windows (.exe)
- **macos/**: Scripts pour créer le package macOS (.pkg)

### `/scripts` - Scripts Utilitaires
- Scripts de lancement, génération de licences, extraction de version

### `/.github/workflows` - CI/CD
- Workflow automatisé pour le build et la release sur GitHub

## Fichiers de Configuration

- **pyproject.toml**: Configuration du projet et dépendances
- **vlk_launcher.spec**: Configuration PyInstaller pour créer les exécutables
- **.gitignore**: Fichiers à exclure du versioning
- **README.md**: Documentation principale du projet

## Workflow de Build

1. **Push sur main** → Déclenche GitHub Actions
2. **Extraction version** → Depuis le message de commit
3. **Build Windows** → Exécutable + Installateur
4. **Build macOS** → Application + Package
5. **Release** → Création automatique sur GitHub

## Notes

- Tous les fichiers créés par yolezz pour VOLKZ Clan
- Les installateurs embarquent les fichiers pour fonctionner hors ligne
- Pour obtenir une licence: contacter yolezz (Discord: yolezz, Email: yolezz.secret@gmail.com)
