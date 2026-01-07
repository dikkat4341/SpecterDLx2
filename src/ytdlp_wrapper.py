# src/ytdlp_wrapper.py
# yt-dlp entegrasyonu - GUI progress ile uyumlu wrapper
# yt-dlp'yi subprocess yerine python modülü olarak kullanıyoruz

import yt_dlp
from typing import Callable, Optional
import time

class YtdlpWrapper:
    def download(self, url: str, output_dir: str = "downloads", progress_callback: Optional[Callable[[float, str, float], None]] = None) -> tuple[bool, str]:
        """
        YouTube / playlist / video indirme
        Dönüş: (başarılı mı, dosya yolu veya hata)
        """
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0%')
                    percent_float = float(percent.strip('%')) / 100 if '%' in percent else 0
                    speed = d.get('_speed_str', '0 MB/s')
                    eta = d.get('_eta_str', '--s')
                    if progress_callback:
                        # speed ve eta string olarak geliyor, float'a çevirmeye gerek yok
                        progress_callback(percent_float, speed, float(eta.split('s')[0]) if 's' in eta else 0)
                elif d['status'] == 'finished':
                    if progress_callback:
                        progress_callback(1.0, "İşleniyor...", 0)

            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
                'continuedl': True,
                'retries': 10,
                'fragment_retries': 10,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return True, filename

        except Exception as e:
            return False, f"yt-dlp hatası: {str(e)}"
