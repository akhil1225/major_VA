import subprocess
import re
import os
from typing import Dict, List, Optional

from skills.application_discovery import ApplicationDiscovery


_discovery = ApplicationDiscovery()
_last_choice: Dict[str, str] = {}  

_SYSTEM_KEYWORDS = (
    "runtime", "framework", "vclibs", "sdk",
    "host", "bridge", "update", "redistributable"
)

def _is_system_app(name: str) -> bool:
    lname = name.lower()
    return any(k in lname for k in _SYSTEM_KEYWORDS)


def _clean_name(name: str) -> str:
    name = name.lower()

    name = re.sub(r"^[0-9a-f]{4,}\s*", "", name)
    name = name.replace(".", " ").replace("_", " ")
    name = " ".join(name.split())

    return name.title()


def find_app_candidates(query: str) -> List[Dict]:
    query = query.lower().strip()
    apps = _discovery.get_installed_apps()

    if not query:
        return []

   
    if query in _last_choice:
        chosen = _last_choice[query]
        for app in apps.values():
            if app["name"].lower() == chosen:
                return [app]

   
    contains = [
        app for app in apps.values()
        if query in app["name"].lower()
        and not _is_system_app(app["name"])
    ]

    if contains:
        return contains

 
    fuzzy = [
        app for app in _discovery.fuzzy_match(query)
        if not _is_system_app(app["name"])
    ]

    return fuzzy




def open_application(query: str) -> str:
    matches = find_app_candidates(query)

    if not matches:
        return f"I couldn't find any installed application matching '{query}'."

    app = matches[0]

    _last_choice[query] = app["name"].lower()

    try:
        if app["type"] == "uwp":
            subprocess.Popen(
                app["command"].split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False
            )
        else:
            subprocess.Popen(
                [app["command"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False
            )

        return f"Opening {_clean_name(app['name'])}."
    except Exception:
        return f"Failed to open {_clean_name(app['name'])}."

def close_application(query: str) -> str:
    matches = find_app_candidates(query)

    if not matches:
        return f"I couldn't find any running application matching '{query}'."

    app = matches[0]

    if app["type"] == "uwp":
        return f"I cannot safely close {_clean_name(app['name'])}."

    exe = os.path.basename(app["command"])

    if not exe.lower().endswith(".exe"):
        return f"I cannot determine how to close {_clean_name(app['name'])}."

    try:
        subprocess.call(
            ["taskkill", "/f", "/im", exe],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"Closed {_clean_name(app['name'])}."
    except Exception:
        return f"Failed to close {_clean_name(app['name'])}."


def list_installed_applications():
    apps = _discovery.get_installed_apps()

    cleaned = sorted(
        {
            _clean_name(app["name"])
            for app in apps.values()
            if not _is_system_app(app["name"])
        }
    )

    return {
        "summary": f"There are {len(cleaned)} installed applications.",
        "items": cleaned
    }


def refresh_applications() -> str:
    _discovery.refresh()
    _last_choice.clear()
    return "Application list refreshed."
