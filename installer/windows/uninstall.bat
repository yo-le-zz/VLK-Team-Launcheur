@echo off
REM VLK Launcher - Script de désinstallation Windows
REM Créé par yolezz pour VOLKZ Clan

echo ========================================
echo VLK Launcher - Désinstallation
echo ========================================
echo.

REM Vérifier si l'application est installée
if not exist "%PROGRAMFILES%\VLKLauncher" (
    echo [INFO] VLK Launcher n'est pas installé
    pause
    exit /b 0
)

REM Demander confirmation
echo Vous allez désinstaller VLK Launcher.
echo.
set /p confirm="Continuer? (y/n): "
if /i not "%confirm%"=="y" (
    echo [INFO] Désinstallation annulée
    pause
    exit /b 0
)

REM Arrêter l'application si elle est en cours d'exécution
echo [INFO] Vérification si VLK Launcher est en cours d'exécution...
taskkill /F /IM VLKLauncher.exe >nul 2>&1

REM Supprimer les fichiers
echo [INFO] Suppression des fichiers...
rd /s /q "%PROGRAMFILES%\VLKLauncher"

REM Supprimer les raccourcis
echo [INFO] Suppression des raccourcis...
del "%PUBLIC%\Desktop\VLK Launcher.lnk" >nul 2>&1
del "%APPDATA%\Microsoft\Internet Explorer\Quick Launch\VLK Launcher.lnk" >nul 2>&1

REM Nettoyer le registre
echo [INFO] Nettoyage du registre...
reg delete "HKLM\Software\VOLKZ Clan\VLKLauncher" /f >nul 2>&1

REM Demander si on veut supprimer les fichiers de configuration
echo.
set /p clean_config="Supprimer également les fichiers de configuration? (y/n): "
if /i "%clean_config%"=="y" (
    echo [INFO] Suppression des fichiers de configuration...
    rd /s /q "%APPDATA%\VLKLauncher" >nul 2>&1
    rd /s /q "%LOCALAPPDATA%\VLKLauncher" >nul 2>&1
)

echo.
echo ========================================
echo [SUCCÈS] Désinstallation terminée!
echo ========================================
echo VLK Launcher a été désinstallé de votre système
echo.
pause
