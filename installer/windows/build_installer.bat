@echo off
REM VLK Launcher - Script de construction installateur Windows
REM Créé par yolezz pour VOLKZ Clan

echo ========================================
echo VLK Launcher - Construction Installateur
echo ========================================
echo.

REM Récupérer la version depuis le premier argument ou utiliser celle par défaut
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

REM Définir le répertoire racine du projet
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo [INFO] Version: %VERSION%
echo [INFO] Répertoire racine: %PROJECT_ROOT%

REM Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier si PyInstaller est installé
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installation de PyInstaller...
    pip install pyinstaller
)

REM Vérifier si Inno Setup est installé
echo [INFO] Vérification de Inno Setup...
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    if not exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
        echo [ERREUR] Inno Setup 6 n'est pas installé
        echo Téléchargez-le depuis: https://jrsoftware.org/isdl.php
        pause
        exit /b 1
    )
)

REM Installer les dépendances
echo [INFO] Installation des dépendances...
pip install -r "%PROJECT_ROOT%\src\client\requirements.txt"

REM Nettoyer les builds précédents
echo [INFO] Nettoyage des builds précédents...
if exist "%PROJECT_ROOT%\dist" rmdir /s /q "%PROJECT_ROOT%\dist"
if exist "%PROJECT_ROOT%\build" rmdir /s /q "%PROJECT_ROOT%\build"
if exist output rmdir /s /q output

REM Construire l'exécutable avec PyInstaller
echo [INFO] Construction de l'exécutable avec PyInstaller...
pushd "%PROJECT_ROOT%"
pyinstaller vlk_launcher.spec --distpath dist/windows --workpath build/windows --clean --noconfirm
if %errorlevel% neq 0 (
    echo [ERREUR] Échec de la construction PyInstaller
    pause
    exit /b 1
)
popd

REM Vérifier que l'exécutable a été créé
if not exist "%PROJECT_ROOT%\dist\windows\VLKLauncher.exe" (
    echo [ERREUR] VLKLauncher.exe non trouvé après la construction
    pause
    exit /b 1
)

REM Mettre à jour la version dans le fichier .iss
echo [INFO] Mise à jour de la version dans le fichier .iss...
powershell -Command "(Get-Content vlk_launcher_setup.iss) -replace '#define AppVersion \".*\"', '#define AppVersion \"%VERSION%\"' | Set-Content vlk_launcher_setup.iss"

REM Créer le dossier de sortie
if not exist output mkdir output

REM Compiler l'installateur avec Inno Setup
echo [INFO] Compilation de l'installateur avec Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" vlk_launcher_setup.iss
) else (
    "C:\Program Files\Inno Setup 6\ISCC.exe" vlk_launcher_setup.iss
)

if %errorlevel% neq 0 (
    echo [ERREUR] Échec de la compilation Inno Setup
    pause
    exit /b 1
)

REM Renommer le fichier avec la version correcte
if exist "output\VLKLauncher-Setup-%VERSION%.exe" (
    echo [INFO] Installateur créé avec le bon nom de version
) else (
    echo [INFO] Renommage de l'installateur...
    if exist "output\*.exe" (
        rename "output\*.exe" "VLKLauncher-Setup-%VERSION%.exe"
    )
)

echo.
echo ========================================
echo [SUCCÈS] Installateur créé avec succès!
echo ========================================
echo Fichier: output\VLKLauncher-Setup-%VERSION%.exe
echo.
pause
