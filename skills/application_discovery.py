import subprocess
import winreg
import time
from difflib import SequenceMatcher
from typing import Dict, List

CACHE_TTL_SECONDS = 300  # 5 minutes


class ApplicationDiscovery:
    """
    Discovers installed applications (Win32 + UWP),
    caches results, and supports fuzzy matching.
    """

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._last_scan = 0


    def get_installed_apps(self) -> Dict[str, Dict]:
        now = time.time()
        if now - self._last_scan < CACHE_TTL_SECONDS and self._cache:
            return self._cache

        apps: Dict[str, Dict] = {}
        try:
            self._discover_win32(apps)
            self._discover_uwp(apps)
        except Exception:
            # log or ignore, but don't crash the app
            pass

        self._cache = apps
        self._last_scan = now
        return apps


    def refresh(self) -> Dict[str, Dict]:
        self._cache = {}
        self._last_scan = 0
        return self.get_installed_apps()

    def _discover_win32(self, apps: Dict):
        uninstall_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]

        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for path in uninstall_paths:
                try:
                    with winreg.OpenKey(root, path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                sub = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, sub) as appkey:
                                    name, _ = winreg.QueryValueEx(appkey, "DisplayName")
                                    cmd = self._get_command(appkey)

                                    if name and cmd:
                                        apps[name.lower()] = {
                                            "name": name,
                                            "command": cmd,
                                            "type": "win32"
                                        }
                            except Exception:
                                continue
                except Exception:
                    continue

    def _get_command(self, key):
        for field in ("DisplayIcon", "InstallLocation", "UninstallString"):
            try:
                value, _ = winreg.QueryValueEx(key, field)
                if isinstance(value, str) and value.strip():
                    return value.split(",")[0].strip('"')
            except Exception:
                continue
        return None


    def _discover_uwp(self, apps: Dict):
        try:
            output = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-StartApps | Select Name, AppID | ConvertTo-Json"
                ],
                text=True,
                errors="ignore"
            )

            import json
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            for app in data:
                name = app.get("Name")
                appid = app.get("AppID")
                if name and appid:
                    apps[name.lower()] = {
                        "name": name,
                        "command": f"explorer shell:AppsFolder\\{appid}",
                        "type": "uwp"
                    }

        except Exception:
            pass


    def fuzzy_match(self, query: str, threshold: float = 0.6) -> List[Dict]:
        query = query.lower().strip()
        apps = self.get_installed_apps()

        scored = []
        for key, app in apps.items():
            score = SequenceMatcher(None, query, key).ratio()
            if score >= threshold:
                scored.append((score, app))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [app for _, app in scored]
