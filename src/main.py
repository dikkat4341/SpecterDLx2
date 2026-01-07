# src/main.py
# SpecterDLx2 - Portable Downloader Başlangıç GUI
# Python 3.10+ , customtkinter ile modern dark tema

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Xtream parser'ı import et (önceki adımda eklediğimiz dosya)
from xtream_parser import XtreamParser

# Tema ayarları (dark/light/system)
ctk.set_appearance_mode("dark")          # "light" veya "system" de seçebilirsin
ctk.set_default_color_theme("dark-blue") # mavi tonlu güzel tema

class SpecterDLApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpecterDLx2 - Portable Downloader")
        self.geometry("1000x650")
        self.resizable(True, True)

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
        self.update()  # GUI'yi hemen güncelle

        try:
            parser = XtreamParser()
            channels, error = parser.parse(url)

            # Eski widget'ları temizle (welcome hariç)
            for widget in self.result_frame.winfo_children():
                if widget != self.welcome_label:
                    widget.destroy()

            if error:
                self.welcome_label.configure(
                    text=f"Hata oluştu:\n{error}",
                    text_color="red"
                )
                self.status_bar.configure(text=f"Hata: {error[:80]}...")
                return

            if not channels:
                self.welcome_label.configure(
                    text="Hiç kanal bulunamadı veya format desteklenmiyor.",
                    text_color="orange"
                )
                self.status_bar.configure(text="Parse tamamlandı ama boş liste döndü.")
                return

            # Başarılıysa welcome'ı gizle
            self.welcome_label.pack_forget()

            # Kanalları kategori başlıklarıyla göster
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
                    cat_label.pack(fill="x", pady=(15, 5), padx=10)
                    current_category = cat

                # Kanal bilgisi
                channel_text = f"{ch.get('name', 'İsimsiz')} → {ch['url'][:100]}..."
                channel_label = ctk.CTkLabel(
                    self.result_frame,
                    text=channel_text,
                    font=("Consolas", 11),
                    anchor="w",
                    justify="left",
                    text_color="white"
                )
                channel_label.pack(fill="x", pady=2, padx=20)

            self.status_bar.configure(text=f"Başarılı → {len(channels)} kanal yüklendi ({len(set(ch.get('category', '') for ch in channels))} kategori)")

        except Exception as e:
            self.welcome_label.configure(
                text=f"Beklenmedik hata:\n{str(e)}",
                text_color="red"
            )
            self.status_bar.configure(text="Genel hata – URL'yi kontrol edin")

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
