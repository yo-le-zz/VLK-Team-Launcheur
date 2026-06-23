# Scripts Utilitaires VLK Launcher

Scripts utilitaires pour le développement et la maintenance de VLK Launcher.

## Scripts Disponibles

### extract_version.py
Script d'extraction de version depuis le message de commit ou pyproject.toml.

**Utilisation:**
```bash
python3 scripts/extract_version.py
```

**Fonctionnement:**
1. Cherche un pattern de version (X.Y.Z) dans le message du dernier commit
2. Fallback sur pyproject.toml si pas de version trouvée
3. Fallback sur "1.0.0" si aucune version n'est trouvée

**Utilisé par:** GitHub Actions pour tagger les releases automatiquement.

### gen_licenses.py
Générateur de licences pour VLK Launcher.

**Utilisation:**
```bash
python3 scripts/gen_licenses.py
```

Permet de générer des clés de licence avec différents rôles (user, admin, superadmin).

### run_client.sh
Script de lancement du client VLK Launcher.

**Utilisation:**
```bash
./scripts/run_client.sh
```

Configure l'environnement et lance l'application client.

### run_server.sh
Script de lancement du serveur VLK Launcher.

**Utilisation:**
```bash
./scripts/run_server.sh
```

Configure l'environnement et lance le serveur FastAPI.

## Permissions

Les scripts shell doivent avoir les permissions d'exécution:
```bash
chmod +x scripts/*.sh
```

## Créé par

yolezz pour VOLKZ Clan
