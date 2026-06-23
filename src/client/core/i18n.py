"""VLK Launcher — Internationalization (i18n) support
Supports multiple languages with English as primary.
"""
import json
import os
from typing import Dict, Optional

# Language codes
LANG_EN = "en"
LANG_FR = "fr"

# Default language
DEFAULT_LANG = LANG_EN

# Translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    LANG_EN: {
        # Login Window
        "login_title": "VOLKZ CLAN",
        "login_subtitle": "RIVALS LAUNCHER  ·  v1.0.0",
        "tab_signin": "SIGN IN",
        "tab_register": "REGISTER",
        "field_username": "USERNAME",
        "field_password": "PASSWORD",
        "field_license": "LICENSE KEY",
        "field_roblox": "ROBLOX USERNAME",
        "btn_signin": "SIGN IN",
        "btn_register": "CREATE ACCOUNT",
        "btn_signing_in": "SIGNING IN...",
        "btn_registering": "REGISTERING...",
        "error_fill_fields": "Please fill in all fields.",
        "error_license_required": "License key, username, and password are required.",
        "error_invalid_credentials": "Invalid credentials or license key.",
        "error_wrong_password": "Wrong username or password.",
        "error_account_disabled": "Account disabled.",
        
        # Main Window
        "panel_home": "HOME",
        "panel_chat": "CHAT",
        "panel_members": "MEMBERS",
        "panel_voice": "VOICE",
        "panel_profile": "PROFILE",
        "panel_ranking": "RANKING",
        "panel_admin": "ADMIN",
        
        # Chat Panel
        "chat_title": "CLAN CHAT",
        "chat_note": "Messages are stored during session",
        "chat_placeholder": "Send a message to the clan...",
        "chat_send": "SEND",
        
        # Members Panel
        "members_title": "MEMBERS ONLINE",
        "members_none": "No members online",
        
        # Voice Panel
        "voice_title": "VOICE",
        "voice_join": "JOIN",
        "voice_leave": "LEAVE",
        "voice_mute": "Micro",
        "voice_deaf": "Sound",
        "voice_photo": "Photo",
        "voice_speaking": "Speaking...",
        "voice_connected": "Connected",
        "voice_muted": "Muted",
        "voice_waiting": "Waiting...",
        
        # Profile Panel
        "profile_title": "MY PROFILE",
        "profile_save": "SAVE CHANGES",
        "profile_saving": "SAVING...",
        "profile_saved": "Profile updated",
        "profile_username": "USERNAME",
        "profile_role": "ROLE",
        "profile_rank": "RANK",
        "profile_rank_points": "RANK POINTS",
        "profile_license": "LICENSE KEY",
        "profile_roblox": "ROBLOX USERNAME",
        "profile_avatar": "AVATAR",
        "profile_reassign": "REASSIGN LICENSE KEY",
        
        # Ranking Panel
        "ranking_title": "RANKINGS & USER MANAGEMENT",
        "ranking_refresh": "REFRESH",
        "ranking_promote": "PROMOTE",
        "ranking_disable": "DISABLE",
        "ranking_enable": "ENABLE",
        
        # Ranks
        "rank_recruit": "Recruit",
        "rank_member": "Member",
        "rank_veteran": "Veteran",
        "rank_elite": "Elite",
        "rank_officer": "Officer",
        "rank_commander": "Commander",
        "rank_legend": "Legend",
        
        # Roles
        "role_user": "user",
        "role_admin": "admin",
        "role_superadmin": "superadmin",
        
        # Admin Panel
        "admin_title": "VLK ADMIN PANEL",
        "admin_login_username": "Admin username",
        "admin_login_password": "Admin password",
        "admin_login_master": "Master password",
        "admin_login_btn": "LOGIN",
        "admin_login_error": "All fields are required.",
        "admin_connected": "CONNECTED",
        "admin_logout": "Logout",
        "admin_stats": "Stats",
        "admin_users": "Users",
        "admin_licenses": "Licenses",
        "admin_announcements": "Announcements",
        "admin_refresh": "Refresh",
    },
    LANG_FR: {
        # Login Window
        "login_title": "VOLKZ CLAN",
        "login_subtitle": "RIVALS LAUNCHER  ·  v1.0.0",
        "tab_signin": "CONNEXION",
        "tab_register": "INSCRIPTION",
        "field_username": "NOM D'UTILISATEUR",
        "field_password": "MOT DE PASSE",
        "field_license": "CLÉ DE LICENCE",
        "field_roblox": "NOM D'UTILISATEUR ROBLOX",
        "btn_signin": "SE CONNECTER",
        "btn_register": "CRÉER UN COMPTE",
        "btn_signing_in": "CONNEXION...",
        "btn_registering": "INSCRIPTION...",
        "error_fill_fields": "Veuillez remplir tous les champs.",
        "error_license_required": "La clé de licence, le nom d'utilisateur et le mot de passe sont requis.",
        "error_invalid_credentials": "Identifiants ou clé de licence invalides.",
        "error_wrong_password": "Mauvais nom d'utilisateur ou mot de passe.",
        "error_account_disabled": "Compte désactivé.",
        
        # Main Window
        "panel_home": "ACCUEIL",
        "panel_chat": "CHAT",
        "panel_members": "MEMBRES",
        "panel_voice": "VOCAL",
        "panel_profile": "PROFIL",
        "panel_ranking": "CLASSEMENT",
        "panel_admin": "ADMIN",
        
        # Chat Panel
        "chat_title": "CHAT DU CLAN",
        "chat_note": "Les messages sont stockés pendant la session",
        "chat_placeholder": "Envoyer un message au clan...",
        "chat_send": "ENVOYER",
        
        # Members Panel
        "members_title": "MEMBRES EN LIGNE",
        "members_none": "Aucun membre en ligne",
        
        # Voice Panel
        "voice_title": "VOCAL",
        "voice_join": "REJOINDRE",
        "voice_leave": "QUITTER",
        "voice_mute": "Micro",
        "voice_deaf": "Son",
        "voice_photo": "Photo",
        "voice_speaking": "Parle...",
        "voice_connected": "Connecté",
        "voice_muted": "Muet",
        "voice_waiting": "En attente...",
        
        # Profile Panel
        "profile_title": "MON PROFIL",
        "profile_save": "ENREGISTRER",
        "profile_saving": "ENREGISTREMENT...",
        "profile_saved": "Profil mis à jour",
        "profile_username": "NOM D'UTILISATEUR",
        "profile_role": "RÔLE",
        "profile_rank": "RANG",
        "profile_rank_points": "POINTS DE RANG",
        "profile_license": "CLÉ DE LICENCE",
        "profile_roblox": "NOM D'UTILISATEUR ROBLOX",
        "profile_avatar": "AVATAR",
        "profile_reassign": "RÉASSIGNER CLÉ DE LICENCE",
        
        # Ranking Panel
        "ranking_title": "CLASSEMENT & GESTION UTILISATEURS",
        "ranking_refresh": "ACTUALISER",
        "ranking_promote": "PROMOUVOIR",
        "ranking_disable": "DÉSACTIVER",
        "ranking_enable": "ACTIVER",
        
        # Ranks
        "rank_recruit": "Recrue",
        "rank_member": "Membre",
        "rank_veteran": "Vétéran",
        "rank_elite": "Élite",
        "rank_officer": "Officier",
        "rank_commander": "Commandant",
        "rank_legend": "Légende",
        
        # Roles
        "role_user": "utilisateur",
        "role_admin": "admin",
        "role_superadmin": "superadmin",
        
        # Admin Panel
        "admin_title": "PANNEAU ADMIN VLK",
        "admin_login_username": "Nom d'utilisateur admin",
        "admin_login_password": "Mot de passe admin",
        "admin_login_master": "Mot de passe master",
        "admin_login_btn": "SE CONNECTER",
        "admin_login_error": "Tous les champs sont requis.",
        "admin_connected": "CONNECTÉ",
        "admin_logout": "Déconnexion",
        "admin_stats": "Stats",
        "admin_users": "Utilisateurs",
        "admin_licenses": "Licences",
        "admin_announcements": "Annonces",
        "admin_refresh": "Actualiser",
    },
}


class I18nManager:
    """Manages internationalization and translations."""
    
    def __init__(self):
        self._current_lang = DEFAULT_LANG
        self._config_file = os.path.join(os.path.expanduser("~"), ".vlk_config.json")
        self._load_config()
    
    def _load_config(self):
        """Load language preference from config file."""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    config = json.load(f)
                    lang = config.get("language")
                    if lang in TRANSLATIONS:
                        self._current_lang = lang
        except Exception:
            pass
    
    def _save_config(self):
        """Save language preference to config file."""
        try:
            config = {"language": self._current_lang}
            with open(self._config_file, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass
    
    def set_language(self, lang: str) -> bool:
        """Set current language. Returns True if successful."""
        if lang in TRANSLATIONS:
            self._current_lang = lang
            self._save_config()
            return True
        return False
    
    def get_language(self) -> str:
        """Get current language code."""
        return self._current_lang
    
    def get_available_languages(self) -> list:
        """Get list of available language codes."""
        return list(TRANSLATIONS.keys())
    
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """Get translation for a key."""
        translations = TRANSLATIONS.get(self._current_lang, {})
        return translations.get(key, default or key)
    
    def t(self, key: str, default: Optional[str] = None) -> str:
        """Shorthand for translate()."""
        return self.translate(key, default)


# Global i18n manager instance
i18n = I18nManager()


def translate(key: str, default: Optional[str] = None) -> str:
    """Global translation function."""
    return i18n.translate(key, default)


def t(key: str, default: Optional[str] = None) -> str:
    """Global shorthand translation function."""
    return i18n.t(key, default)
