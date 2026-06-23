#!/usr/bin/env python3
"""
Script d'extraction de version depuis le message de commit
Créé par yolezz pour VOLKZ Clan
"""
import re
import sys
import subprocess

def extract_version_from_commit():
    """Extrait la version depuis le message du dernier commit"""
    try:
        # Récupérer le message du dernier commit
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_message = result.stdout.strip()
        
        # Chercher un pattern de version (ex: 1.0.0, 2.1.3, etc.)
        version_pattern = r'(\d+\.\d+\.\d+)'
        match = re.search(version_pattern, commit_message)
        
        if match:
            version = match.group(1)
            print(f"Version trouvée dans le commit: {version}", file=sys.stderr)
            return version
        else:
            print("Aucune version trouvée dans le message de commit", file=sys.stderr)
            print(f"Message: {commit_message}", file=sys.stderr)
            # Essayer de lire depuis pyproject.toml
            return extract_version_from_pyproject()
            
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la récupération du commit: {e}", file=sys.stderr)
        return extract_version_from_pyproject()
    except Exception as e:
        print(f"Erreur inattendue: {e}", file=sys.stderr)
        return extract_version_from_pyproject()

def extract_version_from_pyproject():
    """Extrait la version depuis pyproject.toml"""
    try:
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                version = match.group(1)
                print(f"Version trouvée dans pyproject.toml: {version}", file=sys.stderr)
                return version
    except Exception as e:
        print(f"Erreur lors de la lecture de pyproject.toml: {e}", file=sys.stderr)

    # Version par défaut
    print("Utilisation de la version par défaut: 1.0.0", file=sys.stderr)
    return "1.0.0"

if __name__ == "__main__":
    version = extract_version_from_commit()
    print(version)
    sys.exit(0)
