# src/config_manager.py
# Favoriler + ayarlar JSON yönetimi (gece modu + hız sınırlama eklendi)

import json
import os
from typing import List, Dict, Any
from datetime import datetime

class ConfigManager:
    def __init__(self, base_dir: str = "."):
        self.config_dir = os.path.join(base_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.favorites_file = os.path.join(self.config_dir, "favorites.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.useragents_file = os.path.join(self.config_dir, "useragents.json")

    def load_favorites(self) -> List[Dict[str, str]]:
        if not os.path.exists(self.favorites_file):
            return []
        try:
            with open(self.favorites_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_favorites(self, favorites: List[Dict[str, str]]):
        with open(self.favorites_file, "w", encoding="utf-8") as f:
            json.dump(favorites, f, ensure_ascii=False, indent=4)

    def add_favorite(self, name: str, url: str):
        favorites = self.load_favorites()
        if any(f["url"] == url for f in favorites):
            return False
        favorites.append({"name": name or "İsimsiz", "url": url})
        self.save_favorites(favorites)
        return True

    def remove_favorite(self, url: str):
        favorites = self.load_favorites()
        favorites = [f for f in favorites if f["url"] != url]
        self.save_favorites(favorites)

    def load_settings(self) -> Dict[str, Any]:
        defaults = {
            "max_concurrent": 4,
            "night_mode": False,
            "night_start": "22:00",
            "night_end": "08:00",
            "night_speed_limit_kbps": 512,  # gece modu hız sınırı
            "global_speed_limit_kbps": 0,   # 0 = sınırsız
            "user_agent_mode": "random"     # random / cycle
        }
        if not os.path.exists(self.settings_file):
            self.save_settings(defaults)
            return defaults
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return defaults

    def save_settings(self, settings: Dict[str, Any]):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def is_night_mode_active(self) -> bool:
        settings = self.load_settings()
        if not settings.get("night_mode", False):
            return False
        now = datetime.now().time()
        start = datetime.strptime(settings["night_start"], "%H:%M").time()
        end = datetime.strptime(settings["night_end"], "%H:%M").time()
        if start < end:
            return start <= now <= end
        else:
            # Gece yarısını geçen aralık (ör: 22:00 - 08:00)
            return now >= start or now <= end
