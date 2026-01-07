# src/downloader.py
# Basit HTTP/HLS indirme motoru - Progress bar ile (tqdm)
# İleride FFmpeg entegrasyonu + concurrent indirme eklenecek
# Güvenlik: HeaderRotator ile her indirme farklı header alır

import os
import requests
from tqdm import tqdm
from typing import Optional
from header_rotator import HeaderRotator

class SimpleDownloader:
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.rotator = HeaderRotator()

    def download_file(self, url: str, filename: Optional[str] = None) -> tuple[bool, str]:
        """
        Basit HTTP indirme + progress bar
        Dönüş: (başarılı mı, dosya yolu veya hata mesajı)
        """
        try:
            # Her indirme için yeni header seti al
            headers = self.rotator.get_headers(is_hls=True, referer=url)

            # Dosya adını URL'den çıkar veya otomatik ver
            if not filename:
                filename = url.split("/")[-1] or "indirme.ts"
            file_path = os.path.join(self.download_dir, filename)

            # İstek at
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))
                block_size = 1024 * 8  # 8KB blok

                with open(file_path, "wb") as f, tqdm(
                    desc=filename,
                    total=total_size,
                    unit="iB",
                    unit_scale=True,
                    unit_divisor=1024,
                    leave=True
                ) as bar:
                    for chunk in r.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))

            return True, file_path

        except Exception as e:
            return False, f"İndirme hatası: {str(e)}"
