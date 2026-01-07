# src/main.py
# SpecterDLx2 - Portable Downloader Başlangıç GUI
# Python 3.10+ , customtkinter ile modern dark tema

import customtkinter as ctk
from tkinter import filedialog, messagebox

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

        # Orta kısım: Sonuç alanı (şimdilik basit label'lar, sonra treeview olacak)
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

        self.status_bar.configure(text="Yükleniyor... Lütfen bekleyin.")
        self.update()

        # Şimdilik test mesajı (parse mantığı sonraki adımda gelecek)
        self.welcome_label.configure(text="Yükleme testi başarılı!\nURL: " + url[:100] + "...")
        self.status_bar.configure(text=f"Parse tamamlandı → Test modu (gerçek parse sonraki adım)")

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
