# src/downloader.py
# İndirme motoru - Gece modu hız sınırlama + progress callback

import os
import requests
import time
from typing import Optional, Callable
from header_rotator import HeaderRotator

class SimpleDownloader:
    def __init__(self, download_dir: str = "downloads", max_concurrent: int = 4):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.rotator = HeaderRotator()
        self.max_concurrent = max_concurrent

    def download_file(self, url: str, filename: Optional[str] = None, progress_callback: Optional[Callable[[float, str, float], None]] = None, config_manager=None) -> tuple[bool, str]:
        try:
            headers = self.rotator.get_headers(is_hls=True, referer=url)

            if not filename:
                filename = url.split("/")[-1] or "indirme.ts"
            file_path = os.path.join(self.download_dir, filename)

            start_time = time.time()
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))
                downloaded = 0

                # Gece modu hız sınırlama (config'den oku)
                speed_limit_kbps = 0
                if config_manager:
                    settings = config_manager.load_settings()
                    if config_manager.is_night_mode_active():
                        speed_limit_kbps = settings.get("night_speed_limit_kbps", 0)
                    else:
                        speed_limit_kbps = settings.get("global_speed_limit_kbps", 0)

                chunk_size = 8192
                last_time = time.time()
                last_downloaded = 0

                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Hız sınırlama (sleep ile throttle)
                            if speed_limit_kbps > 0:
                                current_time = time.time()
                                elapsed = current_time - last_time
                                if elapsed > 0:
                                    current_speed_kbps = (downloaded - last_downloaded) / elapsed / 1024 * 8
                                    if current_speed_kbps > speed_limit_kbps:
                                        sleep_time = ((current_speed_kbps - speed_limit_kbps) / speed_limit_kbps) * elapsed
                                        time.sleep(sleep_time)

                                last_time = current_time
                                last_downloaded = downloaded

                            if progress_callback and total_size > 0:
                                percent = downloaded / total_size
                                elapsed_total = time.time() - start_time
                                speed = downloaded / elapsed_total / 1024 / 1024 if elapsed_total > 0 else 0
                                eta = (total_size - downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                                progress_callback(percent, f"{speed:.2f} MB/s", eta)

                return True, file_path

        except Exception as e:
            return False, f"İndirme hatası: {str(e)}"
