# src/main.py
# SpecterDLx2 - Portable Downloader
# Favori sistemi eklendi (config_manager ile)

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
        self.geometry("1200x800")
        self.resizable(True, True)

        self.downloader = SimpleDownloader(download_dir="downloads")
        self.config = ConfigManager()  # config/ klasörü yönetimi
        self.favorites = self.config.load_favorites()

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

        ctk.CTkButton(
            self.top_frame,
            text="Favori Ekle",
            width=140,
            height=40,
            fg_color="#3498db",
            command=self.add_favorite
        ).pack(side="left", padx=(10, 0))

        # Favori listesi alanı
        self.fav_frame = ctk.CTkFrame(self.top_frame)
        self.fav_frame.pack(side="right", padx=10)
        ctk.CTkLabel(self.fav_frame, text="Favoriler:", font=("Segoe UI", 12)).pack(side="left", padx=5)
        self.fav_combo = ctk.CTkComboBox(self.fav_frame, values=[f["name"] for f in self.favorites], width=200)
        self.fav_combo.pack(side="left", padx=5)
        ctk.CTkButton(self.fav_frame, text="Yükle", width=80, command=self.load_favorite).pack(side="left")

        # Sonuç alanı
        self.result_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.result_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.welcome_label = ctk.CTkLabel(
            self.result_frame,
            text="Henüz playlist yüklenmedi.",
            font=("Segoe UI", 16),
            text_color="gray"
        )
        self.welcome_label.pack(pady=100)

        self.status_bar = ctk.CTkLabel(
            self,
            text="Hazır... | SpecterDLx2 v0.3",
            height=30,
            anchor="w",
            padx=20,
            text_color="gray"
        )
        self.status_bar.pack(fill="x", side="bottom")

    def add_favorite(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Giriş eksik", "Favori eklemek için URL girin.")
            return
        name = ctk.CTkInputDialog(text="Favori ismi girin:", title="Favori Ekle").get_input()
        if name:
            if self.config.add_favorite(name, url):
                self.favorites = self.config.load_favorites()
                self.fav_combo.configure(values=[f["name"] for f in self.favorites])
                messagebox.showinfo("Başarılı", f"{name} favorilere eklendi.")
            else:
                messagebox.showwarning("Uyarı", "Bu URL zaten favorilerde.")

    def load_favorite(self):
        selected_name = self.fav_combo.get()
        for f in self.favorites:
            if f["name"] == selected_name:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, f["url"])
                self.parse_url()
                break

    # parse_url, start_download, select_file fonksiyonları önceki gibi kalıyor
    # Sadece parse_url içinde status_bar güncellemesi için ufak iyileştirme yapabilirsin, ama zorunlu değil

    # ... (önceki parse_url, start_download, select_file fonksiyonlarını buraya kopyala, değiştirmeden bırak)

if __name__ == "__main__":
    app = SpecterDLApp()
    app.mainloop()
