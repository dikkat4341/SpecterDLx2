# src/tray_manager.py
# Tray icon + bildirim yönetimi (indirme tamamlanınca balon göster + ses çal)

import pystray
from PIL import Image
import threading
import winsound  # Windows ses çalma
import os
from datetime import datetime

class TrayManager:
    def __init__(self, on_quit_callback=None):
        self.icon = None
        self.menu = pystray.Menu(
            pystray.MenuItem("Göster", lambda: None),  # placeholder
            pystray.MenuItem("Çıkış", on_quit_callback or self.default_quit)
        )
        self.thread = None

    def default_quit(self):
        if self.icon:
            self.icon.stop()

    def show_notification(self, title: str, message: str):
        """Windows balon bildirimi göster (pystray destekliyorsa)"""
        if self.icon:
            self.icon.notify(message, title)

    def play_completion_sound(self):
        """Basit başarı sesi çal (Windows beep)"""
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)  # Varsayılan Windows sesi

    def run_tray(self):
        # Basit icon (program dizininde icon.ico olmalı, yoksa default)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.ico")
        if not os.path.exists(icon_path):
            # Default icon oluştur (pillow ile)
            image = Image.new('RGB', (64, 64), color=(0, 128, 255))
            self.icon = pystray.Icon("SpecterDLx2", image, "SpecterDLx2 - Arka Planda", self.menu)
        else:
            image = Image.open(icon_path)
            self.icon = pystray.Icon("SpecterDLx2", image, "SpecterDLx2 - Arka Planda", self.menu)

        self.icon.run()

    def start(self):
        self.thread = threading.Thread(target=self.run_tray, daemon=True)
        self.thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def notify_download_complete(self, name: str):
        self.show_notification("İndirme Tamamlandı", f"{name} başarıyla indirildi.")
        self.play_completion_sound()
