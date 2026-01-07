# src/header_rotator.py
# Anti-detection header rotasyonu - Xtream / M3U8 istekleri için gerçek tarayıcı trafiğine yakın
# 15 yıllık tecrübe: Header sırası, random UA, Sec-Fetch, Accept varyasyonları kritik
# 2026 Chrome/Firefox/Android TV gerçek UA'ları kullanıyoruz

import random
from typing import Dict, Optional

class HeaderRotator:
    def __init__(self):
        # Gerçekçi User-Agent havuzu (IPTV server'ları için Android TV, Smart TV, Windows Chrome vb.)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.107 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; AOSP on TV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
            "Dalvik/2.1.0 (Linux; U; Android 14; Generic TELEVISION Build/UPB1.240105.002)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
        ]

        # Rastgele Accept-Language varyasyonları
        self.accept_languages = [
            "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-US,en;q=0.9,tr;q=0.8",
            "en-GB,en;q=0.9",
        ]

        self._ua_index = 0  # Döngüsel mod için

    def get_headers(self, is_hls: bool = False, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Her istek için yeni header seti üretir.
        is_hls=True ise video akışı için optimize (Sec-Fetch-Empty vb.)
        """
        # UA seçimi: random veya döngüsel (config'den seçilebilir)
        ua = random.choice(self.user_agents)

        headers = {
            "User-Agent": ua,
            "Accept": "*/*" if is_hls else "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(self.accept_languages),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # Modern Chrome-like Sec-Fetch headers (anti-bot bypass için çok kritik)
        if is_hls:
            headers.update({
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
            })
        else:
            headers.update({
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })

        # Sec-Ch-Ua (Chrome 90+ fingerprint)
        headers["Sec-Ch-Ua"] = '"Not_A Brand";v="8", "Chromium";v="131", "Google Chrome";v="131"'
        headers["Sec-Ch-Ua-Mobile"] = "?0" if "Mobile" not in ua else "?1"
        headers["Sec-Ch-Ua-Platform"] = '"Windows"' if "Windows" in ua else '"Android"'

        # Rastgele referer ekleme (%60 ihtimal - bazı Xtream server'ları referer kontrol eder)
        if referer and random.random() > 0.4:
            headers["Referer"] = referer
        elif random.random() > 0.6:
            fake_referers = [
                "https://www.google.com/search?q=iptv+playlist",
                "https://youtube.com/watch?v=example",
                "https://www.google.com/",
            ]
            headers["Referer"] = random.choice(fake_referers)

        # Cache kontrolü varyasyonu
        cache_options = ["no-cache", "max-age=0", "no-store"]
        headers["Cache-Control"] = random.choice(cache_options)

        # IPTV canlı akış için ekstra (bazı server'lar Icy-MetaData ister)
        if is_hls:
            headers["Icy-MetaData"] = "1"

        return headers
