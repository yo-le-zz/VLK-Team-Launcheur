# Changelog VLK Launcher

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet adhère à [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-23

### Ajouté
- Application desktop client avec interface PySide6 moderne
- Backend FastAPI avec WebSocket pour communication temps réel
- Système d'authentification JWT sécurisé
- Gestion des licences avec rôles (user, admin, superadmin)
- Panneaux: Home, Chat, Members, Profile, Ranking, Admin
- Intégration vocale (LiveKit, Mumble, WebRTC)
- Chat en temps réel
- Système de rangs et points
- Panneau d'administration web
- Système d'annonces et broadcast
- Installateurs automatiques pour Windows (Inno Setup) et macOS (pkgbuild)
- Workflow GitHub Actions pour build automatisé
- Extraction automatique de version depuis les commits
- Scripts utilitaires (lancement, génération de licences)
- Documentation complète (README, STRUCTURE, scripts, installateurs)
- Système de mise à jour intégré

### Installateurs
- Windows: Installateur .exe avec désinstallation et réparation
- macOS: Package .pkg avec installation standard
- Les deux embarquent les fichiers pour fonctionner hors ligne

### Sécurité
- Tokens JWT avec expiration configurable
- Hachage des mots de passe avec bcrypt
- Panneau admin protégé par mot de passe master
- Support de la réassignation de licence

### Documentation
- README.md avec guide d'installation et configuration
- STRUCTURE.md avec arborescence détaillée
- Documentation des scripts et installateurs
- Contrat de licence inclus dans les installateurs

---

## Contact

Pour obtenir une licence ou pour le support:
- **Discord**: yolezz
- **Email**: yolezz.secret@gmail.com

**Créé par yolezz pour VOLKZ Clan**
