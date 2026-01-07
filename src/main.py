# src/main.py
# SpecterDLx2 - Portable Downloader
# Ayarlar ekranı eklendi (gece modu, hız limitleri, concurrent sayısı)

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os
import re

from xtream_parser import XtreamParser
from downloader import SimpleDownloader
from config_manager import ConfigManager
from ytdlp_wrapper import YtdlpWrapper

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config: ConfigManager):
        super().__init__(parent)
        self.title("Ayarlar")
        self.geometry("600x500")
        self.resizable(False, False)
        self.config = config
        self.settings = self.config.load_settings()

        # Gece modu toggle
        ctk.CTkLabel(self, text="Gece Modu:", font=("Segoe UI", 14)).pack(pady=10)
        self.night_toggle = ctk.CTkSwitch(self, text="Aktif", variable=ctk.BooleanVar(value=self.settings.get("night_mode", False)))
        self.night_toggle.pack()

        # Gece başlama saati
        ctk.CTkLabel(self, text="Gece Başlama (HH:MM):", font=("Segoe UI", 12)).pack(pady=5)
        self.night_start = ctk.CTkEntry(self, placeholder_text="22:00", width=100)
        self.night_start.insert(0, self.settings.get("night_start", "22:00"))
        self.night_start.pack()

        # Gece bitiş saati
        ctk.CTkLabel(self, text="Gece Bitiş (HH:MM):", font=("Segoe UI", 12)).pack(pady=5)
        self.night_end = ctk.CTkEntry(self, placeholder_text="08:00", width=100)
        self.night_end.insert(0, self.settings.get("night_end", "08:00"))
        self.night_end.pack()

        # Gece hız sınırı
        ctk.CTkLabel(self, text="Gece Hız Sınırı (KB/s):", font=("Segoe UI", 12)).pack(pady=5)
        self.night_speed = ctk.CTkEntry(self, placeholder_text="512", width=100)
        self.night_speed.insert(0, str(self.settings.get("night_speed_limit_kbps", 512)))
        self.night_speed.pack()

        # Global hız sınırı
        ctk.CTkLabel(self, text="Genel Hız Sınırı (KB/s - 0=sınırsız):", font=("Segoe UI", 12)).pack(pady=5)
        self.global_speed = ctk.CTkEntry(self, placeholder_text="0", width=100)
        self.global_speed.insert(0, str(self.settings.get("global_speed_limit_kbps", 0)))
        self.global_speed.pack()

        # Maks concurrent
        ctk.CTkLabel(self, text="Maks Eşzamanlı İndirme:", font=("Segoe UI", 12)).pack(pady=5)
        self.max_conc = ctk.CTkEntry(self, placeholder_text="4", width=100)
        self.max_conc.insert(0, str(self.settings.get("max_concurrent", 4)))
        self.max_conc.pack()

        # Kaydet butonu
        ctk.CTkButton(self, text="Ayarları Kaydet", width=200, height=40, fg_color="green", command=self.save_settings).pack(pady=30)

    def save_settings(self):
        try:
            new_settings = {
                "night_mode": self.night_toggle.get(),
                "night_start": self.night_start.get(),
                "night_end": self.night_end.get(),
                "night_speed_limit_kbps": int(self.night_speed.get()),
                "global_speed_limit_kbps": int(self.global_speed.get()),
                "max_concurrent": int(self.max_conc.get()),
                "user_agent_mode": self.config.load_settings().get("user_agent_mode", "random")
            }
            self.config.save_settings(new_settings)
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi! Yeni indirmelerde uygulanacak.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen sayısal değerler girin (hız, concurrent vb.)")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")

class SpecterDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpecterDLx2 - Portable Downloader")
        self.geometry("1200x900")
        self.resizable(True, True)

        self.config = ConfigManager()
        self.favorites = self.config.load_favorites()
        self.downloader = SimpleDownloader(max_concurrent=self.config.load_settings().get("max_concurrent", 4))
        self.ytdlp_wrapper = YtdlpWrapper()

        self.progress_widgets = {}

        # Üst kısım
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(self.top_frame, text="M3U / Xtream / YouTube URL:", font=("Segoe UI", 14, "bold")).pack(side="left", padx=(15, 10))

        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="http://... veya https://youtube.com/...", height=40, font=("Consolas", 12), corner_radius=8)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10)

        ctk.CTkButton(self.top_frame, text="Yükle & Parse", width=160, height=40, command=self.parse_url).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.top_frame, text="Dosya Seç", width=120, height=40, command=self.select_file).pack(side="left")
        ctk.CTkButton(self.top_frame, text="Favori Ekle", width=140, height=40, fg_color="#3498db", command=self.add_favorite).pack(side="left", padx=(10, 0))
        ctk.CTkButton(self.top_frame, text="Ayarlar", width=120, height=40, fg_color="#8e44ad", command=self.open_settings).pack(side="left", padx=(10, 0))

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

        self.status_bar = ctk.CTkLabel(self, text="Hazır... | Ayarlar için üstteki butona bas", height=30, anchor="w", padx=20, text_color="gray")
        self.status_bar.pack(fill="x", side="bottom")

    def open_settings(self):
        SettingsWindow(self, self.config)

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

    def parse_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Giriş eksik", "Lütfen URL girin.")
            return

        self.status_bar.configure(text="Yükleniyor...")
        self.update()

        if re.search(r'(youtube\.com|youtu\.be)', url, re.IGNORECASE):
            self.status_bar.configure(text="YouTube tespit edildi - yt-dlp ile indiriliyor...")
            self.start_ytdlp_download(url, "youtube_video")
            return

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
                    cat_label = ctk.CTkLabel(self.result_frame, text=f"──── {cat} ────", font=("Segoe UI", 14, "bold"), text_color="#00bfff")
                    cat_label.pack(fill="x", pady=(20, 5), padx=10)
                    current_category = cat

                channel_frame = ctk.CTkFrame(self.result_frame)
                channel_frame.pack(fill="x", pady=6, padx=20)

                name_label = ctk.CTkLabel(channel_frame, text=ch.get('name', 'İsimsiz'), font=("Consolas", 12), anchor="w", width=350)
                name_label.pack(side="left", padx=(0, 10))

                url_label = ctk.CTkLabel(channel_frame, text=ch['url'][:80] + "..." if len(ch['url']) > 80 else ch['url'], font=("Consolas", 10), text_color="gray", anchor="w")
                url_label.pack(side="left", fill="x", expand=True)

                download_btn = ctk.CTkButton(channel_frame, text="İndir", width=100, height=32, fg_color="#2ecc71", hover_color="#27ae60", command=lambda u=ch['url'], n=ch.get('name', 'indirme'), cf=channel_frame: self.start_download(u, n, cf))
                download_btn.pack(side="right", padx=(10, 0))

            self.status_bar.configure(text=f"Başarılı → {len(channels)} kanal yüklendi")

        except Exception as e:
            self.welcome_label.configure(text=f"Hata:\n{str(e)}", text_color="red")
            self.status_bar.configure(text="Genel hata oluştu.")

    def start_download(self, url: str, name: str, channel_frame: ctk.CTkFrame):
        if url in self.progress_widgets:
            self.status_bar.configure(text="Bu indirme zaten çalışıyor.")
            return

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
            success, result = self.downloader.download_file(
                url, f"{name}.ts", update_progress, config_manager=self.config
            )
            if success:
                status_label.configure(text="Tamamlandı → downloads klasöründe")
                progress_bar.set(1)
            else:
                status_label.configure(text=f"Hata: {result[:50]}...", text_color="red")
            time.sleep(3)
            progress_frame.pack_forget()
            del self.progress_widgets[url]
            self.status_bar.configure(text="İndirme tamamlandı: " + name)

        threading.Thread(target=thread_target, daemon=True).start()
        self.status_bar.configure(text=f"İndirme kuyruğa alındı: {name} (aktif: {len(self.progress_widgets)})")

    def start_ytdlp_download(self, url: str, name: str):
        progress_frame = ctk.CTkFrame(self.result_frame)
        progress_frame.pack(fill="x", pady=10, padx=20)

        progress_bar = ctk.CTkProgressBar(progress_frame, width=600, height=25, mode="determinate")
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(0)

        status_label = ctk.CTkLabel(progress_frame, text="YouTube indirme başlatılıyor...", font=("Segoe UI", 12))
        status_label.pack(pady=5)

        def update_progress(percent, speed, eta):
            progress_bar.set(percent)
            status_label.configure(text=f"{percent*100:.1f}% | Hız: {speed} | ETA: {eta:.0f}s")

        def thread_target():
            success, result = self.ytdlp_wrapper.download(url, output_dir="downloads", progress_callback=update_progress)
            if success:
                status_label.configure(text=f"Tamamlandı: {os.path.basename(result)}")
                progress_bar.set(1)
            else:
                status_label.configure(text=f"Hata: {result}", text_color="red")
            time.sleep(5)
            progress_frame.pack_forget()
            self.status_bar.configure(text="YouTube indirme tamamlandı.")

        threading.Thread(target=thread_target, daemon=True).start()
        self.status_bar.configure(text="YouTube indirme kuyruğa alındı...")

    def select_file(self):
        file_path = filedialog.askopenfilename(title="M3U/M3U8 Seç", filetypes=[("Playlist", "*.m3u *.m3u8 *.txt"), ("Tüm", "*.*")])
        if file_path:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, file_path)
            self.parse_url()


if __name__ == "__main__":
    app = SpecterDLApp()
    app.mainloop()
