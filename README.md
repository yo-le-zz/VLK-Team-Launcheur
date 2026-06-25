# VLK Launcher — VOLKZ Clan

> Private esports SaaS launcher for the VOLKZ clan — Roblox Rivals.

**Author:** yolezz  
**Version:** 1.0.1
**Platforms:** Windows + macOS

---

## 📋 Table of contents

- [Architecture](#architecture)
- [Features](#features)
- [Quick installation](#quick-installation)
- [Configuration](#configuration)
- [Authentication system](#authentication-system)
- [Voice integration](#voice-integration)
- [Admin panel](#admin-panel)
- [CI/CD](#cicd)
- [Installers](#installers)
- [License](#license)


---

## 🏗️ Architecture

For a detailed view of the project structure, see [STRUCTURE.md](STRUCTURE.md).

```
vlk-launcher/
├── src/
│   ├── client/               # Application desktop PySide6
│   │   ├── assets/           # Icônes (icon.ico, icon.png, icon.svg)
│   │   ├── core/             # API client + WebSocket
│   │   ├── ui/               # Fenêtres et panneaux UI
│   │   │   ├── panels/       # Home, Chat, Members, Profile, Ranking, Admin
│   │   │   ├── login_window.py
│   │   │   ├── main_window.py
│   │   │   ├── theme.py      # Design tokens + QSS
│   │   │   └── widgets.py    # Composants partagés
│   │   └── voice/            # Abstraction service vocal (LiveKit/Mumble/WebRTC)
│   └── server/               # Backend FastAPI
│       ├── core/             # DB, config, JWT auth, WS manager
│       ├── routers/          # auth, licenses, admin, announcements
│       └── static/           # Admin panel HTML
├── scripts/                  # Scripts utilitaires (lancement, licences, etc.)
├── installer/                # Scripts de construction d'installateurs
├── .github/workflows/        # CI/CD (build + auto-release)
├── .env.example              # Template des variables d'environnement
├── pyproject.toml            # Configuration du projet
└── README.md                 # Ce fichier
```

---

## Features


### Client
- **Modern UI**: Dark design with a custom theme
- **Panels**: Home, Chat, Members, Profile, Ranking, Admin
- **Real-time chat**: WebSocket for instant communication
- **Ranks system**: Recruit → Member → Veteran → Elite → Officer → Commander → Legend
- **Rank points**: Progression system based on points
- **User profile**: Profile management and license re-assignment
- **Voice integration**: Support for LiveKit, Mumble, and WebRTC


### Server

- **API REST**: FastAPI avec documentation automatique
- **Base de données**: SQLAlchemy avec support async
- **JWT authentication**: Secure tokens with configurable expiration
- **License management**: License key system with roles
- **Panneau admin**: Interface web pour la gestion complète
- **Annonces**: Système de diffusion d'annonces aux utilisateurs
- **WebSocket**: Communication temps réel pour le chat et les mises à jour

### Administration
- **Tableau de bord**: Statistiques en temps réel
- **Gestion utilisateurs**: Modifier rôles, rangs, activer/désactiver comptes
- **Gestion licences**: Générer, révoquer, assigner des licences
- **Annonces**: Créer et diffuser des annonces
- **Broadcast**: Messages système diffusés en temps réel

---

## Quick installation

### Prerequisites

- Python 3.11 ou supérieur
- pip (gestionnaire de paquets Python)

### Server

1. **Clone the repository**
```bash
cd vlk-launcher
```

2. **Installer les dépendances**
```bash
uv pip install -r src/server/requirements.txt
```

3. **Configure the environment**
```bash
cp .env.example .env
# Éditez .env avec vos configurations (clés secrètes, DB, etc.)
```

4. **Lancer le serveur**
```bash
./scripts/run_server.sh
```

Ou directement:
```bash
uvicorn src.server.main:app --host 0.0.0.0 --port 8000 --reload
```

**Clé de licence admin par défaut**: `VLK-ADMIN-0000`

### Client

1. **Installer les dépendances**
```bash
uv pip install -r src/client/requirements.txt
```

2. **Configurer l'URL du serveur**
```bash
export VLK_SERVER_URL=http://your-server:8000
```

3. **Lancer le client**
```bash
./scripts/run_client.sh
```

Ou directement:
```bash
python -m src.client.main
```

### Build (manuel)

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller vlk_launcher.spec
```

---

## ⚙️ Configuration

### Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./vlk.db` | Connexion base de données |
| `JWT_SECRET` | — | **À modifier** - Secret pour les tokens JWT |
| `JWT_EXPIRE_HOURS` | `24` | Durée de validité des tokens (heures) |
| `MASTER_PASSWORD` | — | Admin master password |
| `VOICE_SERVICE` | `livekit` | Service vocal: `livekit` / `mumble` / `webrtc` |
| `LIVEKIT_URL` | — | URL du serveur LiveKit |
| `LIVEKIT_API_KEY` | — | Clé API LiveKit |
| `LIVEKIT_API_SECRET` | — | Secret API LiveKit |
| `MUMBLE_HOST` | — | Hôte du serveur Mumble |
| `VLK_SERVER_URL` | `http://localhost:8000` | URL du serveur (client) |

### Exemple de fichier .env

```env
DATABASE_URL=sqlite+aiosqlite:///./vlk.db
JWT_SECRET=votre_secret_jwt_ici
JWT_EXPIRE_HOURS=24
MASTER_PASSWORD=votre_mot_de_passe_admin_ici
VOICE_SERVICE=livekit
LIVEKIT_URL=wss://votre-livekit-server.com
LIVEKIT_API_KEY=votre_api_key
LIVEKIT_API_SECRET=votre_api_secret
```

---

## Authentication system

### Registration flow
1. **Clé de licence** → Entrer une clé valide
2. **Nom d'utilisateur** → Choisir un pseudo unique
3. **Password** → Set a strong password

### Rôles utilisateurs
- **user**: Utilisateur standard avec accès aux fonctionnalités de base
- **admin**: Gestion des utilisateurs et des licences
- **superadmin**: Accès complet, y compris désactivation de comptes

### Sécurité
- Tokens JWT avec expiration configurable (24h par défaut)
- Hachage des mots de passe avec bcrypt
- Panneau admin protégé par mot de passe master
Support for license re-assignment in the Profile panel

---

## Voice integration

Voice chat is handled by external services. Configure via `.env`:

### LiveKit (par défaut)
Génère un lien LiveKit Meet pour la salle VLK.

```env
VOICE_SERVICE=livekit
LIVEKIT_URL=wss://votre-livekit-server.com
LIVEKIT_API_KEY=votre_api_key
LIVEKIT_API_SECRET=votre_api_secret
```

### Mumble
Lance le client Mumble local avec URI `mumble://`.

```env
VOICE_SERVICE=mumble
MUMBLE_HOST=votre-serveur-mumble.com
```

### WebRTC
Ouvre une URL WebRTC configurée (Jitsi ou custom).

```env
VOICE_SERVICE=webrtc
WEBRTC_URL=https://votre-service-webrtc.com
```

> **Note**: Aucun audio brut n'est traité dans le launcher.

---

## Admin panel

### Accès
The admin panel can be accessed via:
- **Web interface**: `http://your-server:8000/admin`
- **Authentication**: Master password (MASTER_PASSWORD)

### Key features


#### Tableau de bord
- Statistiques en temps réel
- Utilisateurs en ligne
- Utilisateurs en vocal
- État des licences

#### Gestion utilisateurs
- Liste des utilisateurs avec recherche et filtres
- Modification des rôles (user/admin/superadmin)
- Changement de rang et points
- **Activation/Désactivation de comptes** (superadmin uniquement)
- Suppression d'utilisateurs

#### Gestion licences
- Génération de nouvelles licences
- Attribution de rôles aux licences
- Révocation de licences
- Visualisation de l'état d'utilisation

#### Annonces
- Création d'annonces avec priorité (normal/important/urgent)
- Diffusion en temps réel
- Historique des annonces

#### Broadcast
- Messages système diffusés à tous les utilisateurs connectés
- Communication instantanée

---

## CI/CD

Les pushs sur la branche `main` déclenchent automatiquement GitHub Actions:

1. **Build Windows**: Création d'un `.exe` via PyInstaller
2. **Build macOS**: Création d'un bundle `.app`
3. **Release**: Création d'une release versionnée avec les deux archives

### Workflow
```yaml
# .github/workflows/release.yml
- Checkout du code
- Setup Python
- Installation des dépendances
- Build pour Windows et macOS
- Upload des artefacts
- Création de la GitHub Release
```

---

## License

Private — Utilisation interne exclusive au clan VOLKZ.

### Obtention d'une licence

Pour obtenir une licence valide pour VLK Launcher, vous devez contacter directement **yolezz**:

- **Discord**: yolezz
- **Email**: yolezz.secret@gmail.com

Sans licence valide, l'utilisation de ce logiciel n'est pas autorisée.

---

## Installers

Automatic installers are available to simplify installation and uninstallation on Windows and macOS.

### Windows

L'installateur Windows inclut:
- Installation automatique dans Program Files
- Création de raccourcis (Bureau, Menu Démarrer)
- Option de lancement au démarrage
Full uninstall support via Control Panel
- Réparation automatique en cas de réinstallation

**Construction de l'installateur Windows:**
```bash
cd installer/windows
build_installer.bat
```

**Prérequis:**
- Python 3.11+
- Inno Setup 6 (téléchargeable depuis https://jrsoftware.org/isdl.php)

L'installateur sera généré dans `installer/windows/output/` sous le nom `VLKLauncher-Setup-1.0.1.exe`.

### macOS

Le package macOS inclut:
- Installation standard dans le dossier Applications
Uninstall support via dedicated script
- Pages de bienvenue et de conclusion personnalisées
- Informations de licence intégrées

**Construction du package macOS:**
```bash
cd installer/macos
./build_pkg.sh
```

**Installation manuelle (alternative):**
```bash
cd installer/macos
./install.sh
```

**Désinstallation:**
```bash
cd installer/macos
./uninstall.sh
```

**Prérequis:**
- Python 3.11+
- Xcode Command Line Tools (pour pkgbuild)

Le package sera généré dans `installer/macos/output/` sous le nom `VLKLauncher-1.0.1.pkg`.

---

## 🤝 Support

For any questions or issues, contact **yolezz**:

- **Discord**: yolezz
- **Email**: yolezz.secret@gmail.com

---

**Version 1.0.1** — VOLKZ Clan © 2026
**Créé par yolezz**
