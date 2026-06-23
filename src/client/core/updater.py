"""VLK Launcher — GitHub Update Checker
Discord-style update verification system using GitHub releases.
"""
import os
import json
import requests
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path


class GitHubUpdater:
    """Check for updates from GitHub releases."""
    
    def __init__(self, repo_owner: str, repo_name: str, current_version: str = "1.0.0"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.last_check_file = Path.home() / ".vlk_launcher" / "last_update_check.json"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_last_check_time(self) -> Optional[datetime]:
        """Get the last update check time from cache."""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get('last_check'))
            except Exception:
                pass
        return None
    
    def _save_check_time(self):
        """Save the current check time to cache."""
        try:
            with open(self.last_check_file, 'w') as f:
                json.dump({'last_check': datetime.now().isoformat()}, f)
        except Exception:
            pass
    
    def should_check(self, interval_hours: int = 24) -> bool:
        """Check if enough time has passed since last check."""
        last_check = self._get_last_check_time()
        if not last_check:
            return True
        return datetime.now() - last_check > timedelta(hours=interval_hours)
    
    def get_latest_release(self) -> Optional[dict]:
        """Fetch the latest release from GitHub."""
        try:
            response = requests.get(f"{self.api_url}/releases/latest", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Failed to fetch release: {e}")
        return None
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings.
        Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        def normalize(v):
            return [int(x) for x in v.replace('v', '').split('.')]
        
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_val = v1_parts[i] if i < len(v1_parts) else 0
            v2_val = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1_val < v2_val:
                return -1
            elif v1_val > v2_val:
                return 1
        
        return 0
    
    def check_for_updates(self, force: bool = False) -> Tuple[bool, Optional[dict]]:
        """Check for updates.
        Returns: (has_update, release_info)
        """
        if not force and not self.should_check():
            return False, None
        
        release = self.get_latest_release()
        if not release:
            self._save_check_time()
            return False, None
        
        latest_version = release.get('tag_name', '').replace('v', '')
        has_update = self.compare_versions(latest_version, self.current_version) > 0
        
        self._save_check_time()
        
        if has_update:
            return True, {
                'version': latest_version,
                'name': release.get('name', ''),
                'body': release.get('body', ''),
                'html_url': release.get('html_url', ''),
                'published_at': release.get('published_at', ''),
                'assets': self._get_download_urls(release)
            }
        
        return False, None
    
    def _get_download_urls(self, release: dict) -> dict:
        """Extract download URLs for different platforms."""
        assets = {}
        for asset in release.get('assets', []):
            name = asset.get('name', '').lower()
            if 'windows' in name and '.zip' in name:
                assets['windows'] = {
                    'name': asset.get('name'),
                    'url': asset.get('browser_download_url'),
                    'size': asset.get('size', 0)
                }
            elif 'macos' in name or 'darwin' in name:
                if '.zip' in name or '.dmg' in name:
                    assets['macos'] = {
                        'name': asset.get('name'),
                        'url': asset.get('browser_download_url'),
                        'size': asset.get('size', 0)
                    }
        return assets
    
    def download_update(self, platform: str, release_info: dict, 
                        progress_callback=None) -> Optional[Path]:
        """Download update for specified platform.
        Returns: Path to downloaded file or None on failure.
        """
        assets = release_info.get('assets', {})
        if platform not in assets:
            return None
        
        asset = assets[platform]
        url = asset['url']
        filename = asset['name']
        
        # Create downloads directory
        download_dir = Path.home() / ".vlk_launcher" / "updates"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = download_dir / filename
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = asset.get('size', 0)
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            return output_path
        
        except Exception as e:
            print(f"Download failed: {e}")
            if output_path.exists():
                output_path.unlink()
            return None


def load_config_version() -> str:
    """Load current version from config.json if available."""
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('version', '1.0.0')
        except Exception:
            pass
    return '1.0.0'


def get_updater() -> GitHubUpdater:
    """Get configured updater instance."""
    # Load from environment or use defaults
    repo_owner = os.getenv('GITHUB_OWNER', 'yo-le-zz')
    repo_name = os.getenv('GITHUB_REPO', 'VLK-Team-Launcheur')
    current_version = load_config_version()
    
    return GitHubUpdater(repo_owner, repo_name, current_version)
