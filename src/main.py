# src/main.py
# SpecterDLx2 - Portable Downloader Başlangıç GUI
# Python 3.10+ , customtkinter ile modern dark tema

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading  # İndirme arka planda çalışsın diye

# Xtream parser ve downloader import
from xtream_parser import XtreamParser
from downloader import SimpleDownloader

# Tema ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SpecterDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpecterDLx2 - Portable Downloader")
        self.geometry("1200x750")  # Biraz genişlettik (butonlar için)
        self.resizable(True, True)

        # Downloader instance (downloads klasörüne kaydeder)
        self.downloader = SimpleDownloader(download_dir="downloads")

        # Üst çerçeve: URL girişi
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

        # Orta kısım: Sonuç alanı
        self.result_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.result_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.welcome_label = ctk.CTkLabel(
            self.result_frame,
            text="Henüz playlist yüklenmedi.\nURL girip 'Yükle & Parse' butonuna basın.",
            font=("Segoe UI", 16),
            text_color="gray"
        )
        self.welcome_label.pack(pady=100)

        # Alt durum çubuğu
        self.status_bar = ctk.CTkLabel(
            self,
            text="Hazır... | SpecterDLx2 v0.1 - Xtream & M3U Downloader",
            height=30,
            anchor="w",
            padx=20,
            text_color="gray"
        )
        self.status_bar.pack(fill="x", side="bottom")

    def parse_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Giriş eksik", "Lütfen bir URL veya dosya yolu girin.")
            return

        self.status_bar.configure(text="Playlist yükleniyor... Lütfen bekleyin.")
        self.update()

        try:
            parser = XtreamParser()
            channels, error = parser.parse(url)

            # Eski widget'ları temizle
            for widget in self.result_frame.winfo_children():
                if widget != self.welcome_label:
                    widget.destroy()

            if error:
                self.welcome_label.configure(text=f"Hata oluştu:\n{error}", text_color="red")
                self.status_bar.configure(text=f"Hata: {error[:80]}...")
                return

            if not channels:
                self.welcome_label.configure(text="Hiç kanal bulunamadı.", text_color="orange")
                self.status_bar.configure(text="Parse tamamlandı ama boş liste.")
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

                # Kanal frame (yatay düzen)
                channel_frame = ctk.CTkFrame(self.result_frame)
                channel_frame.pack(fill="x", pady=4, padx=20)

                name_label = ctk.CTkLabel(
                    channel_frame,
                    text=ch.get('name', 'İsimsiz'),
                    font=("Consolas", 11),
                    anchor="w",
                    width=400
                )
                name_label.pack(side="left", padx=(0, 10))

                url_label = ctk.CTkLabel(
                    channel_frame,
                    text=ch['url'][:100] + ("..." if len(ch['url']) > 100 else ""),
                    font=("Consolas", 10),
                    text_color="gray",
                    anchor="w"
                )
                url_label.pack(side="left", fill="x", expand=True)

                # İndir butonu
                download_btn = ctk.CTkButton(
                    channel_frame,
                    text="İndir",
                    width=100,
                    height=30,
                    fg_color="green",
                    hover_color="darkgreen",
                    command=lambda u=ch['url'], n=ch.get('name', 'indirme'): self.start_download(u, n)
                )
                download_btn.pack(side="right", padx=(10, 0))

            self.status_bar.configure(text=f"Başarılı → {len(channels)} kanal yüklendi")

        except Exception as e:
            self.welcome_label.configure(text=f"Beklenmedik hata:\n{str(e)}", text_color="red")
            self.status_bar.configure(text="Genel hata – URL kontrol edin")

    def start_download(self, url: str, name: str):
        """İndirmeyi arka planda başlat (GUI donmasın)"""
        def thread_target():
            success, result = self.downloader.download_file(url, filename=f"{name}.ts")
            if success:
                self.status_bar.configure(text=f"İndirme tamamlandı: {os.path.basename(result)} → downloads klasöründe")
            else:
                self.status_bar.configure(text=f"İndirme hatası: {result[:80]}")

        threading.Thread(target=thread_target, daemon=True).start()
        self.status_bar.configure(text=f"İndirme başladı: {name}")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="M3U/M3U8 Dosyası Seç",
            filetypes=[("Playlist Dosyaları", "*.m3u *.m3u8 *.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, file_path)
            self.parse_url()


if __name__ == "__main__":
    app = SpecterDLApp()
    app.mainloop()
