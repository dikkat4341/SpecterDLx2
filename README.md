# SpecterDLx2 – Portable IPTV / Video Downloader

**Python tabanlı, tamamen portable (tek .exe hedefi), Xtream Codes / M3U / M3U8 destekli indirme aracı.**

### Özellikler (Planlanan)
- Xtream Codes API ve direkt M3U playlist desteği
- HLS (m3u8) indirme + segment birleştirme (ffmpeg entegrasyonu)
- Anti-detection: User-Agent rotasyonu + header randomization
- Tkinter / customtkinter ile modern GUI
- Favori URL kaydetme (JSON config)
- Hız sınırlama, gece modu
- yt-dlp entegrasyonu (YouTube vb. için)
- Tamamen portable: PyInstaller --onefile ile tek exe

### Hedef: Windows'ta kurulum gerektirmeden çalışsın (ffmpeg.exe ve yt-dlp gömülü)

### Kurulum (Geliştirme Aşaması)
1. Repo'yu clone et veya Codespaces ile aç.
2. `pip install -r requirements.txt`
3. `python src/main.py`

### Geliştirme Durumu
- [ ] Temel GUI
- [ ] Xtream Parser
- [ ] Header Rotator
- [ ] İndirme Motoru
- [ ] Config Sistemi
- [ ] PyInstaller spec

MIT License – Serbestçe kullan / fork / geliştir.

İstek / Issue açabilirsin.
