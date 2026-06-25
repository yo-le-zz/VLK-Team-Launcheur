@echo off
REM VLK Launcher - Script de réparation Windows
REM Créé par yolezz pour VOLKZ Clan

echo ========================================
echo VLK Launcher - Réparation
echo ========================================
echo.

REM Vérifier si l'application est installée
if not exist "%PROGRAMFILES%\VLKLauncher" (
    echo [ERREUR] VLK Launcher n'est pas installé
    echo Veuillez d'abord installer l'application
    pause
    exit /b 1
)

REM Arrêter l'application si elle est en cours d'exécution
echo [INFO] Arrêt de VLK Launcher...
taskkill /F /IM VLKLauncher.exe >nul 2>&1

REM Attendre que le processus se termine
timeout /t 2 /nobreak >nul

REM Sauvegarder la configuration
echo [INFO] Sauvegarde de la configuration existante...
if exist "%APPDATA%\VLKLauncher" (
    xcopy "%APPDATA%\VLKLauncher" "%TEMP%\VLKLauncher_backup\" /E /I /Y >nul 2>&1
)

REM Nettoyer les fichiers corrompus
echo [INFO] Nettoyage des fichiers corrompus...
del /Q "%PROGRAMFILES%\VLKLauncher\*.log" >nul 2>&1
del /Q "%PROGRAMFILES%\VLKLauncher\*.tmp" >nul 2>&1
del /Q "%PROGRAMFILES%\VLKLauncher\*.cache" >nul 2>&1

REM Restaurer la configuration si elle existe
if exist "%TEMP%\VLKLauncher_backup" (
    echo [INFO] Restauration de la configuration...
    xcopy "%TEMP%\VLKLauncher_backup\*" "%APPDATA%\VLKLauncher\" /E /I /Y >nul 2>&1
    rd /s /q "%TEMP%\VLKLauncher_backup" >nul 2>&1
)

REM Réenregistrer les entrées de registre
echo [INFO] Réenregistrement des entrées de registre...
reg add "HKLM\Software\VOLKZ Clan\VLKLauncher" /v "InstallPath" /t REG_SZ /d "%PROGRAMFILES%\VLKLauncher" /f >nul 2>&1
reg add "HKLM\Software\VOLKZ Clan\VLKLauncher" /v "Version" /t REG_SZ /d "1.0.1" /f >nul 2>&1

REM Recréer les raccourcis s'ils manquent
echo [INFO] Vérification des raccourcis...
if not exist "%PUBLIC%\Desktop\VLK Launcher.lnk" (
    if exist "%PROGRAMFILES%\VLKLauncher\VLKLauncher.exe" (
        echo [INFO] Recréation du raccourci Bureau...
        powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\VLK Launcher.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\VLKLauncher\VLKLauncher.exe'; $Shortcut.Save()"
    )
)

echo.
echo ========================================
echo [SUCCÈS] Réparation terminée!
echo ========================================
echo VLK Launcher a été réparé avec succès
echo.
echo Vous pouvez maintenant lancer l'application
echo.
pause
