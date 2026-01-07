# src/downloader.py
# İndirme motoru - Eşzamanlılık sınırı + progress desteği

import os
import requests
from tqdm import tqdm
from typing import Optional, Callable
from header_rotator import HeaderRotator
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class SimpleDownloader:
    def __init__(self, download_dir: str = "downloads", max_concurrent: int = 4):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.rotator = HeaderRotator()
        self.max_concurrent = max_concurrent
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)

    def download_file(self, url: str, filename: Optional[str] = None, progress_callback: Optional[Callable[[float, str, float], None]] = None) -> tuple[bool, str]:
        """Tek dosya indirme - progress callback ile GUI güncelleme"""
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

                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                percent = downloaded / total_size
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed / 1024 / 1024 if elapsed > 0 else 0  # MB/s
                                eta = (total_size - downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                                progress_callback(percent, f"{speed:.2f} MB/s", eta)

                return True, file_path

        except Exception as e:
            return False, f"İndirme hatası: {str(e)}"

    def download_multiple(self, urls_with_names: list[tuple[str, str]], progress_callbacks: dict[str, Callable]):
        """Çoklu indirme - max_concurrent sınırlı"""
        futures = []
        for url, name in urls_with_names:
            def callback(percent, speed, eta):
                if url in progress_callbacks:
                    progress_callbacks[url](percent, speed, eta)

            future = self.executor.submit(self.download_file, url, f"{name}.ts", callback)
            futures.append((url, future))

        results = {}
        for url, future in futures:
            success, result = future.result()
            results[url] = (success, result)

        return results
