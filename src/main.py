# src/main.py
# SpecterDLx2 - Portable Downloader
# Çoklu indirme kuyruğu + GUI progress entegrasyonu

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os

from xtream_parser import XtreamParser
from downloader import SimpleDownloader
from config_manager import ConfigManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SpecterDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpecterDLx2 - Portable Downloader")
        self.geometry("1200x900")
        self.resizable(True, True)

        self.config = ConfigManager()
        self.favorites = self.config.load_favorites()
        self.downloader = SimpleDownloader(max_concurrent=4)  # eşzamanlı limit

        self.progress_widgets = {}  # url -> {'frame': frame, 'bar': bar, 'label': label}

        # Üst kısım (favori + giriş) - önceki gibi kalıyor
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(self.top_frame, text="M3U / Xtream URL:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=(15, 10))

        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="http://...", height=40, font=("Consolas", 12), corner_radius=8)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10)

        ctk.CTkButton(self.top_frame, text="Yükle & Parse", width=160, height=40, command=self.parse_url).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.top_frame, text="Dosya Seç", width=120, height=40, command=self.select_file).pack(side="left")
        ctk.CTkButton(self.top_frame, text="Favori Ekle", width=140, height=40, fg_color="#3498db", command=self.add_favorite).pack(side="left", padx=(10, 0))

        self.fav_frame = ctk.CTkFrame(self.top_frame)
        self.fav_frame.pack(side="right", padx=10)
        ctk.CTkLabel(self.fav_frame, text="Favoriler:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.fav_combo = ctk.CTkComboBox(self.fav_frame, values=[f["name"] for f in self.favorites], width=200)
        self.fav_combo.pack(side="left", padx=5)
        ctk.CTkButton(self.fav_frame, text="Yükle", width=80, command=self.load_favorite).pack(side="left")

        # Sonuç alanı
        self.result_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.result_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.welcome_label = ctk.CTkLabel(self.result_frame, text="Henüz playlist yüklenmedi.", font=("Segoe UI", 16), text_color="gray")
        self.welcome_label.pack(pady=100)

        self.status_bar = ctk.CTkLabel(self, text="Hazır... | Maks 4 eşzamanlı indirme", height=30, anchor="w", padx=20, text_color="gray")
        self.status_bar.pack(fill="x", side="bottom")

    # add_favorite, load_favorite, parse_url, select_file fonksiyonları önceki gibi kalıyor
    # Sadece start_download'u güncelle (aşağıda)

    def start_download(self, url: str, name: str, channel_frame: ctk.CTkFrame):
        if url in self.progress_widgets:
            self.status_bar.configure(text="Bu indirme zaten çalışıyor.")
            return

        # Progress frame oluştur
        progress_frame = ctk.CTkFrame(channel_frame)
        progress_frame.pack(fill="x", pady=(5, 0))

        progress_bar = ctk.CTkProgressBar(progress_frame, width=400, height=20, mode="determinate")
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        progress_bar.set(0)

        status_label = ctk.CTkLabel(progress_frame, text="Başlatılıyor...", font=("Segoe UI", 10))
        status_label.pack(side="left")

        self.progress_widgets[url] = {'frame': progress_frame, 'bar': progress_bar, 'label': status_label}

        def update_progress(percent, speed, eta):
            progress_bar.set(percent)
            status_label.configure(text=f"{percent*100:.1f}% | {speed} MB/s | ETA: {eta:.0f}s")

        def thread_target():
            success, result = self.downloader.download_file(url, f"{name}.ts", update_progress)
            if success:
                status_label.configure(text="Tamamlandı → downloads klasöründe")
                progress_bar.set(1)
            else:
                status_label.configure(text=f"Hata: {result[:50]}...", text_color="red")
            time.sleep(3)  # 3 sn sonra progress frame'i sil
            progress_frame.pack_forget()
            del self.progress_widgets[url]
            self.status_bar.configure(text="İndirme tamamlandı: " + name)

        threading.Thread(target=thread_target, daemon=True).start()
        self.status_bar.configure(text=f"İndirme kuyruğa alındı: {name} (aktif: {len(self.progress_widgets)})")

    # parse_url, select_file vb. önceki halleriyle kalıyor (kodun geri kalanını buraya kopyala, değiştirmeden bırak)

if __name__ == "__main__":
    app = SpecterDLApp()
    app.mainloop()
