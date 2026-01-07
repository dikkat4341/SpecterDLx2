# src/xtream_parser.py
# Xtream Codes API + Standart M3U/M3U8 Parser
# Xtream UI / XUI.ONE mantığına tam uyumlu (player_api.php + get.php m3u)
# HeaderRotator entegrasyonu eklendi (anti-detection)

import requests
import re
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Tuple, Optional

# Header rotator'ı import et (önceki adımda eklediğimiz dosya)
from header_rotator import HeaderRotator

class XtreamParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15  # saniye
        self.rotator = HeaderRotator()  # Anti-detection kalbi burada başlatılıyor

    def parse(self, url_or_path: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Ana parse fonksiyonu.
        Dönüş: (kanallar listesi, hata mesajı)
        Her kanal dict: {'category': str, 'name': str, 'url': str, 'type': 'live'|'vod'|'series'}
        """
        error = None
        channels = []

        # Header'ları rotator'dan al (her istek için yeni ve rastgele)
        headers = self.rotator.get_headers(is_hls=False)  # Genel istekler için

        if url_or_path.startswith(("http://", "https://")):
            # URL ise Xtream Codes mu yoksa direkt m3u mu kontrol et
            parsed_url = urlparse(url_or_path)
            if "player_api.php" in url_or_path or "get.php" in url_or_path:
                return self._parse_xtream_api(url_or_path, headers)
            else:
                # Direkt m3u8 veya m3u linki
                try:
                    resp = self.session.get(url_or_path, headers=headers)
                    resp.raise_for_status()
                    content = resp.text
                except Exception as e:
                    return [], f"URL erişim hatası: {str(e)}"
        else:
            # Yerel dosya yolu (header gerekmez)
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

    def _parse_xtream_api(self, base_url: str, base_headers: Dict) -> Tuple[List[Dict], Optional[str]]:
        """Xtream Codes player_api.php mantığı - HeaderRotator ile"""
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

        try:
            # Live kategorileri al
            live_cat_url = f"{server}/player_api.php?action=get_live_categories&username={username}&password={password}"
            # Her API çağrısı için yeni header al (rotasyon)
            cat_headers = self.rotator.get_headers(is_hls=False)
            resp = self.session.get(live_cat_url, headers=cat_headers)
            if resp.status_code == 200:
                cats = resp.json()
                for cat in cats:
                    cat_name = cat.get("category_name", "Uncategorized")

                    # M3U endpoint için HLS header kullan (video akışı)
                    m3u_url = f"{server}/get.php?username={username}&password={password}&type=m3u_plus&output=ts"
                    m3u_headers = self.rotator.get_headers(is_hls=True)  # HLS için optimize header
                    m3u_resp = self.session.get(m3u_url, headers=m3u_headers)
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
