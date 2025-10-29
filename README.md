# Styl-e

Styl-e adalah bot Discord cerdas yang berfungsi sebagai asisten fashion pribadi Anda. Ditenagai oleh Groq API yang super cepat, bot ini memberikan rekomendasi outfit yang kreatif dan relevan langsung di server Anda, baik melalui perintah khusus maupun percakapan natural.

![Contoh Penggunaan Bot](https://i.pinimg.com/originals/6d/0e/2c/6d0e2cc4225dba6bb60f0e284a87734b.gif)

---

## ## Fitur Utama

* **⚡ Respons Super Cepat:** Menggunakan Groq API untuk memberikan rekomendasi outfit dalam sekejap.
* **🗣️ Interaksi Ganda:**
    * Gunakan slash command `/outfit` untuk permintaan terstruktur.
    * Mention `@Styl-e` untuk percakapan yang lebih alami dan fleksibel.
* **🎨 Kustomisasi Mudah:** Tentukan gaya (`kasual`, `formal`, `streetwear`) dan acara (`kantor`, `kencan`, `konser`) untuk mendapatkan saran yang paling sesuai.
* **🧠 Kontekstual:** Dirancang untuk memahami permintaan dalam Bahasa Indonesia secara natural.

---

## ## Teknologi yang Digunakan

* **Bahasa:** Python 3.8+
* **Library Utama:**
    * `discord.py`: Untuk berinteraksi dengan API Discord.
    * `groq`: Klien resmi untuk terhubung dengan Groq API.
    * `python-dotenv`: Untuk mengelola environment variables (API keys) dengan aman.

---

## ## Instalasi dan Konfigurasi

Ikuti langkah-langkah ini untuk menjalankan bot di server Anda sendiri.

### ### 1. Prasyarat
* Python 3.8 atau yang lebih baru.
* Akun [Discord](https://discord.com/) dan hak akses untuk mengundang bot ke server.
* API Key dari [Groq Cloud](https://console.groq.com/).

### ### 2. Clone Repositori
Clone repositori ini ke mesin lokal Anda:
```bash
git clone https://github.com/marchel-24/StyleBot.git
cd StyleBot
