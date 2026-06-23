# VLK Launcher — VOLKZ Clan

> Lanceur SaaS esports privé pour le clan VOLKZ — Roblox Rivals.

**Créé par:** yolezz  
**Version:** 1.0.0  
**Plateforme:** Windows + macOS

---

## 📋 Table des matières

- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
- [Installation rapide](#installation-rapide)
- [Configuration](#configuration)
- [Système d'authentification](#système-dauthentification)
- [Intégration vocale](#intégration-vocale)
- [Panneau d'administration](#panneau-dadministration)
- [CI/CD](#cicd)
- [Installateurs](#installateurs)
- [Licence](#licence)

---

## 🏗️ Architecture

Pour une vue détaillée de la structure du projet, voir [STRUCTURE.md](STRUCTURE.md).

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

## ✨ Fonctionnalités

### Client
- **Interface moderne**: Design sombre avec thème personnalisé
- **Panneaux**: Home, Chat, Members, Profile, Ranking, Admin
- **Chat en temps réel**: WebSocket pour la communication instantanée
- **Système de rangs**: Recruit → Member → Veteran → Elite → Officer → Commander → Legend
- **Points de rang**: Système de progression basé sur les points
- **Profil utilisateur**: Gestion du profil et réassignation de licence
- **Intégration vocale**: Support de LiveKit, Mumble et WebRTC

### Serveur
- **API REST**: FastAPI avec documentation automatique
- **Base de données**: SQLAlchemy avec support async
- **Authentification JWT**: Tokens sécurisés avec expiration
- **Gestion des licences**: Système de clés de licence avec rôles
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

## 🚀 Installation rapide

### Prérequis

- Python 3.11 ou supérieur
- pip (gestionnaire de paquets Python)

### Serveur

1. **Cloner le repository**
```bash
cd vlk-launcher
```

2. **Installer les dépendances**
```bash
pip install -r src/server/requirements.txt
```

3. **Configurer l'environnement**
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
pip install -r src/client/requirements.txt
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

Pour créer un exécutable standalone:

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
| `MASTER_PASSWORD` | — | Mot de passe master pour le panneau admin |
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

## 🔐 Système d'authentification

### Flux d'inscription
1. **Clé de licence** → Entrer une clé valide
2. **Nom d'utilisateur** → Choisir un pseudo unique
3. **Mot de passe** → Définir un mot de passe sécurisé

### Rôles utilisateurs
- **user**: Utilisateur standard avec accès aux fonctionnalités de base
- **admin**: Gestion des utilisateurs et des licences
- **superadmin**: Accès complet, y compris désactivation de comptes

### Sécurité
- Tokens JWT avec expiration configurable (24h par défaut)
- Hachage des mots de passe avec bcrypt
- Panneau admin protégé par mot de passe master
- Support de la réassignation de licence dans le panneau Profil

---

## 🎙️ Intégration vocale

Le vocal est géré par des services externes. Configurez via `.env`:

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

## 👨‍💼 Panneau d'administration

### Accès
Le panneau admin est accessible via:
- **Interface web**: `http://votre-serveur:8000/admin`
- **Authentification**: Mot de passe master (MASTER_PASSWORD)

### Fonctionnalités

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

## 🔄 CI/CD

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

## 📄 Licence

Private — Utilisation interne exclusive au clan VOLKZ.

### Obtention d'une licence

Pour obtenir une licence valide pour VLK Launcher, vous devez contacter directement **yolezz**:

- **Discord**: yolezz
- **Email**: yolezz.secret@gmail.com

Sans licence valide, l'utilisation de ce logiciel n'est pas autorisée.

---

## 📦 Installateurs

Des installateurs automatiques sont disponibles pour faciliter l'installation et la désinstallation sur Windows et macOS.

### Windows

L'installateur Windows inclut:
- Installation automatique dans Program Files
- Création de raccourcis (Bureau, Menu Démarrer)
- Option de lancement au démarrage
- Support de désinstallation complète via Panneau de configuration
- Réparation automatique en cas de réinstallation

**Construction de l'installateur Windows:**
```bash
cd installer/windows
build_installer.bat
```

**Prérequis:**
- Python 3.11+
- Inno Setup 6 (téléchargeable depuis https://jrsoftware.org/isdl.php)

L'installateur sera généré dans `installer/windows/output/` sous le nom `VLKLauncher-Setup-1.0.0.exe`.

### macOS

Le package macOS inclut:
- Installation standard dans le dossier Applications
- Support de désinstallation via script dédié
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

Le package sera généré dans `installer/macos/output/` sous le nom `VLKLauncher-1.0.0.pkg`.

---

## 🤝 Support

Pour toute question ou problème, contactez **yolezz**:

- **Discord**: yolezz
- **Email**: yolezz.secret@gmail.com

---

**Version 1.0.0** — VOLKZ Clan © 2024
**Créé par yolezz**
