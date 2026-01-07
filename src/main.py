# src/main.py
# SpecterDLx2 - Portable Downloader
# GUI progress bar + ETA/hız gösterme eklendi

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os

from xtream_parser import XtreamParser
from downloader import SimpleDownloader

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SpecterDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpecterDLx2 - Portable Downloader")
        self.geometry("1200x800")
        self.resizable(True, True)

        self.downloader = SimpleDownloader(download_dir="downloads")
        self.active_downloads = {}  # {url: {'progress': CTkProgressBar, 'label': CTkLabel, ...}}

        # Üst çerçeve
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(
            self.top_frame,
            text="M3U / Xtream URL veya yerel .m3u8 dosyası:",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=(15, 10))

        self.url_entry = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="http://sunucu:port/get.php?... veya C:/playlist.m3u",
            height=40,
            font=("Consolas", 12),
            corner_radius=8
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10)

        ctk.CTkButton(
            self.top_frame,
            text="Yükle & Parse",
            width=160,
            height=40,
            command=self.parse_url
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.top_frame,
            text="Dosya Seç",
            width=120,
            height=40,
            command=self.select_file
        ).pack(side="left")

        # Sonuç alanı
        self.result_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.result_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.welcome_label = ctk.CTkLabel(
            self.result_frame,
            text="Henüz playlist yüklenmedi.\nURL girip 'Yükle & Parse' butonuna basın.",
            font=("Segoe UI", 16),
            text_color="gray"
        )
        self.welcome_label.pack(pady=100)

        # Durum çubuğu
        self.status_bar = ctk.CTkLabel(
            self,
            text="Hazır... | SpecterDLx2 v0.2 - İndirme aktif",
            height=30,
            anchor="w",
            padx=20,
            text_color="gray"
        )
        self.status_bar.pack(fill="x", side="bottom")

    def parse_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Giriş eksik", "Lütfen URL veya dosya yolu girin.")
            return

        self.status_bar.configure(text="Yükleniyor...")
        self.update()

        try:
            parser = XtreamParser()
            channels, error = parser.parse(url)

            for widget in self.result_frame.winfo_children():
                if widget != self.welcome_label:
                    widget.destroy()

            if error:
                self.welcome_label.configure(text=f"Hata:\n{error}", text_color="red")
                self.status_bar.configure(text=f"Hata: {error[:80]}...")
                return

            if not channels:
                self.welcome_label.configure(text="Kanal bulunamadı.", text_color="orange")
                self.status_bar.configure(text="Boş liste.")
                return

            self.welcome_label.pack_forget()

            current_category = None
            for ch in channels:
                cat = ch.get("category", "Genel")
                if cat != current_category:
                    cat_label = ctk.CTkLabel(
                        self.result_frame,
                        text=f"──── {cat} ────",
                        font=("Segoe UI", 14, "bold"),
                        text_color="#00bfff"
                    )
                    cat_label.pack(fill="x", pady=(20, 5), padx=10)
                    current_category = cat

                channel_frame = ctk.CTkFrame(self.result_frame)
                channel_frame.pack(fill="x", pady=6, padx=20)

                name_label = ctk.CTkLabel(
                    channel_frame,
                    text=ch.get('name', 'İsimsiz'),
                    font=("Consolas", 12),
                    anchor="w",
                    width=350
                )
                name_label.pack(side="left", padx=(0, 10))

                url_label = ctk.CTkLabel(
                    channel_frame,
                    text=ch['url'][:80] + "..." if len(ch['url']) > 80 else ch['url'],
                    font=("Consolas", 10),
                    text_color="gray",
                    anchor="w"
                )
                url_label.pack(side="left", fill="x", expand=True)

                # İndirme butonu + progress alanı
                download_btn = ctk.CTkButton(
                    channel_frame,
                    text="İndir",
                    width=100,
                    height=32,
                    fg_color="#2ecc71",
                    hover_color="#27ae60",
                    command=lambda u=ch['url'], n=ch.get('name', 'indirme'): self.start_download(u, n, channel_frame)
                )
                download_btn.pack(side="right", padx=(10, 0))

        except Exception as e:
            self.welcome_label.configure(text=f"Hata:\n{str(e)}", text_color="red")
            self.status_bar.configure(text="Genel hata oluştu.")

    def start_download(self, url: str, name: str, channel_frame: ctk.CTkFrame):
        """İndirmeyi arka planda başlat + GUI progress bar ekle"""
        # Progress frame oluştur (butonun altına)
        progress_frame = ctk.CTkFrame(channel_frame)
        progress_frame.pack(fill="x", pady=(5, 0))

        progress_bar = ctk.CTkProgressBar(progress_frame, width=400, height=20, mode="determinate")
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        progress_bar.set(0)

        status_label = ctk.CTkLabel(progress_frame, text="Başlatılıyor...", font=("Segoe UI", 10))
        status_label.pack(side="left")

        # İndirme thread'i
        def download_thread():
            try:
                # Basit indirme simülasyonu yerine gerçek indirme
                # Gerçek progress için requests stream + manuel güncelleme
                headers = self.downloader.rotator.get_headers(is_hls=True)
                r = requests.get(url, headers=headers, stream=True, timeout=30)
                r.raise_for_status()

                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                filename = f"{name}.ts"
                file_path = os.path.join("downloads", filename)

                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = (downloaded / total_size) if total_size > 0 else 0
                            progress_bar.set(percent)
                            speed = downloaded / (time.time() - start_time) / 1024 / 1024  # MB/s
                            eta = (total_size - downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                            status_label.configure(text=f"{percent*100:.1f}% | {speed:.2f} MB/s | ETA: {eta:.0f}s")

                status_label.configure(text="Tamamlandı → downloads klasöründe")
                progress_bar.set(1)

            except Exception as e:
                status_label.configure(text=f"Hata: {str(e)[:50]}...", text_color="red")

        start_time = time.time()
        threading.Thread(target=download_thread, daemon=True).start()
        self.status_bar.configure(text=f"İndirme başladı: {name}")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="M3U/M3U8 Seç",
            filetypes=[("Playlist", "*.m3u *.m3u8 *.txt"), ("Tüm", "*.*")]
        )
        if file_path:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, file_path)
            self.parse_url()


if __name__ == "__main__":
    app = SpecterDLApp()
    app.mainloop()
