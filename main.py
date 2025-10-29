import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from groq import Groq

# 1. Muat environment variables dari file .env
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# 2. Inisialisasi Klien Groq
# Pastikan Anda telah mengatur GROQ_API_KEY di file .env Anda
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    # Jika tidak ada API Key, bot tidak bisa berjalan
    exit()


# 3. Tentukan intents untuk bot Discord.
# Intents.default() mencakup sebagian besar kebutuhan umum.
intents = discord.Intents.default()
intents.message_content = True # Diperlukan untuk beberapa interaksi pesan

# Inisialisasi bot dengan command prefix dan intents
# Kita akan menggunakan slash commands, jadi prefix tidak terlalu penting.
bot = commands.Bot(command_prefix="!", intents=intents)


# 4. Event handler saat bot siap dan online
@bot.event
async def on_ready():
    print(f'Bot telah login sebagai {bot.user}')
    # Sinkronisasi slash commands agar muncul di Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# 5. Membuat Slash Command untuk rekomendasi outfit
@bot.tree.command(name="outfit", description="Dapatkan rekomendasi outfit harian dari AI Stylist.")
async def outfit(
    interaction: discord.Interaction, 
    gaya: str = "kasual", 
    acara: str = "jalan-jalan santai"
):
    """
    Memberikan rekomendasi outfit berdasarkan gaya dan acara.
    
    Parameters
    ----------
    gaya: str
        Gaya busana yang diinginkan (e.g., kasual, formal, streetwear, vintage).
    acara: str
        Konteks atau acara outfit (e.g., ke kampus, kerja di kantor, kencan malam).
    """
    try:
        # Tampilkan pesan "sedang berpikir" agar pengguna tahu bot sedang bekerja
        await interaction.response.defer()

        # 6. Buat prompt yang detail untuk Groq LLM
        prompt = f"""
        Anda adalah seorang fashion stylist AI ahli bernama G-Style.
        Tugas Anda adalah memberikan rekomendasi outfit yang detail dan kreatif untuk pengguna di Indonesia.
        
        Konteks Pengguna:
        - Gaya yang diinginkan: "{gaya}"
        - Acara atau kegiatan: "{acara}"

        Berikan rekomendasi outfit lengkap dari atasan hingga bawahan, termasuk sepatu dan aksesori jika relevan.
        Gunakan format yang mudah dibaca, misalnya dengan poin-poin.
        Berikan juga sedikit tips atau alasan mengapa kombinasi tersebut cocok.
        Jawab dalam Bahasa Indonesia.
        """

        # 7. Kirim permintaan ke API Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah fashion stylist AI yang membantu memberikan rekomendasi outfit."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant", # Anda bisa ganti model lain yang tersedia di Groq
        )

        # 8. Ambil hasil dan kirim sebagai balasan
        response = chat_completion.choices[0].message.content
        
        # Menggunakan followup.send karena kita sudah menggunakan defer() sebelumnya
        await interaction.followup.send(response)

    except Exception as e:
        print(f"Terjadi error: {e}")
        await interaction.followup.send("Maaf, terjadi kesalahan saat saya mencoba meracik outfit untukmu. Coba lagi nanti.")


# 9. Jalankan bot dengan token Anda
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("DISCORD_TOKEN tidak ditemukan. Pastikan sudah diatur di file .env")