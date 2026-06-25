#!/usr/bin/env python3
"""
Script de génération du fichier Inno Setup avec version dynamique
Créé par yolezz pour VOLKZ Clan
"""
import sys
import os
import re

def extract_version():
    """Extrait la version depuis pyproject.toml ou le commit"""
    # Essayer de lire depuis pyproject.toml
    try:
        with open('../../pyproject.toml', 'r') as f:
            content = f.read()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
    except:
        pass
    
    # Fallback: version par défaut
    return "1.0.1"

def generate_iss():
    """Génère le fichier .iss avec la version extraite"""
    version = extract_version()
    
    # Lire le template
    template_file = 'vlk_launcher_setup.template.iss'
    output_file = 'vlk_launcher_setup.iss'
    
    if os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # Si pas de template, utiliser le fichier existant
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # Remplacer les placeholders de version
    content = re.sub(r'#define AppVersion ".*"', f'#define AppVersion "{version}"', content)
    content = re.sub(r'VLKLauncher-Setup-.*\.exe', f'VLKLauncher-Setup-{version}.exe', content)
    
    # Écrire le fichier généré
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier .iss généré avec version {version}")
    return version

if __name__ == "__main__":
    generate_iss()
