# src/xtream_parser.py
# Xtream Codes API + Standart M3U/M3U8 Parser
# Xtream UI / XUI.ONE mantığına tam uyumlu (player_api.php + get.php m3u)
# Güvenlik: Her istekte header rotasyonu eklenecek (sonraki adımda)

import requests
import re
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Tuple, Optional

class XtreamParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15  # saniye

    def _get_headers(self) -> Dict[str, str]:
        """Geçici basit header (anti-detection için sonraki adımda HeaderRotator ile değiştirilecek)"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Connection": "keep-alive"
        }

    def parse(self, url_or_path: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Ana parse fonksiyonu.
        Dönüş: (kanallar listesi, hata mesajı)
        Her kanal dict: {'category': str, 'name': str, 'url': str, 'type': 'live'|'vod'|'series'}
        """
        error = None
        channels = []

        if url_or_path.startswith(("http://", "https://")):
            # URL ise Xtream Codes mu yoksa direkt m3u mu kontrol et
            parsed_url = urlparse(url_or_path)
            if "player_api.php" in url_or_path or "get.php" in url_or_path:
                return self._parse_xtream_api(url_or_path)
            else:
                # Direkt m3u8 veya m3u linki
                try:
                    resp = self.session.get(url_or_path, headers=self._get_headers())
                    resp.raise_for_status()
                    content = resp.text
                except Exception as e:
                    return [], f"URL erişim hatası: {str(e)}"
        else:
            # Yerel dosya yolu
            try:
                with open(url_or_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return [], f"Dosya okuma hatası: {str(e)}"

        # İçerik m3u formatındaysa parse et
        channels = self._parse_m3u_content(content)
        if channels:
            return channels, None

        return [], "Desteklenmeyen format veya boş içerik"

    def _parse_xtream_api(self, base_url: str) -> Tuple[List[Dict], Optional[str]]:
        """Xtream Codes player_api.php mantığı"""
        # base_url örnek: http://sunucu:port/player_api.php?username=xxx&password=yyy
        # veya http://sunucu:port/get.php?username=xxx&password=yyy&type=m3u_plus&output=ts

        params = {}
        if "?" in base_url:
            query = base_url.split("?", 1)[1]
            for p in query.split("&"):
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = v

        username = params.get("username", "")
        password = params.get("password", "")

        if not username or not password:
            return [], "Xtream URL'de username/password eksik"

        server = base_url.split("/player_api.php")[0] if "/player_api.php" in base_url else base_url.split("/get.php")[0]

        channels = []

        # Live kategorileri al (örnek endpoint)
        try:
            live_cat_url = f"{server}/player_api.php?action=get_live_categories&username={username}&password={password}"
            resp = self.session.get(live_cat_url, headers=self._get_headers())
            if resp.status_code == 200:
                cats = resp.json()
                for cat in cats:
                    cat_name = cat.get("category_name", "Uncategorized")
                    # Kanalları ayrı endpoint ile al (veya direkt m3u8 ile)
                    # Şimdilik basit: direkt m3u_plus endpoint varsayalım
                    m3u_url = f"{server}/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                    m3u_resp = self.session.get(m3u_url, headers=self._get_headers())
                    if m3u_resp.status_code == 200:
                        m3u_channels = self._parse_m3u_content(m3u_resp.text)
                        for ch in m3u_channels:
                            ch["category"] = cat_name
                            channels.append(ch)
        except Exception as e:
            return [], f"Xtream API hatası: {str(e)}"

        return channels, None

    def _parse_m3u_content(self, content: str) -> List[Dict]:
        """Standart #EXTINF format parse"""
        channels = []
        current = None
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                current = {"name": "", "url": "", "category": "Uncategorized", "type": "live"}
                # group-title parse
                if 'group-title="' in line:
                    gt = line.split('group-title="')[1].split('"')[0]
                    current["category"] = gt
                # isim
                if "," in line:
                    current["name"] = line.split(",", 1)[-1].strip()
            elif line.startswith("http") and current:
                current["url"] = line
                channels.append(current)
                current = None

        return channels
