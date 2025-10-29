# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from groq import Groq

import database as db
from view import RatingView, AddItemModal, PreferenceModal

# --- Konfigurasi Awal ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True  # Diperlukan untuk on_message
bot = commands.Bot(command_prefix="!", intents=intents)


# --- Event Utama Bot ---
@bot.event
async def on_ready():
    print(f"Bot telah login sebagai {bot.user}")
    db.init_db()  # Membuat file DB SQLite jika belum ada
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Gagal sinkronisasi command: {e}")


# --- Perintah Dasar & Perkenalan ---
@bot.tree.command(name="perkenalan", description="Perkenalkan diri dan fitur bot.")
async def perkenalan(interaction: discord.Interaction):
    user_name = interaction.user.display_name

    # Gunakan nama tersebut di dalam judul embed
    embed = discord.Embed(
        title=f"👋 Halo, {user_name}! Aku Gaya-san, Asisten Fashion Pribadimu!",
        description="Aku di sini untuk membantumu menemukan outfit terbaik setiap hari. Berikut beberapa hal yang bisa aku lakukan:",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="`/outfit`",
        value="Dapatkan rekomendasi outfit cepat berdasarkan gaya dan acara.",
        inline=False,
    )
    embed.add_field(
        name="`/lemari`",
        value="Simpan koleksi pakaianmu dan minta aku meracik outfit dari sana.",
        inline=False,
    )
    embed.add_field(
        name="✨ `/preferensi`",
        value="Atur gaya dan warna favoritmu agar rekomendasiku semakin pas!",
        inline=False,
    )
    embed.set_footer(text="Coba jalankan /preferensi atur untuk memulai personalisasi!")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- Fitur Rekomendasi Outfit Utama ---
@bot.tree.command(
    name="outfit", description="Dapatkan rekomendasi outfit harian dari AI Stylist."
)
@app_commands.describe(
    gaya="Gaya busana yang diinginkan.", acara="Konteks atau acara outfit."
)
async def outfit(interaction: discord.Interaction, gaya: str, acara: str):
    await interaction.response.defer()
    # Logika untuk mengambil preferensi dan membuat prompt
    explicit_prefs = db.get_explicit_preferences(interaction.user.id)
    pref_text = ""
    if explicit_prefs:
        styles, colors, avoids = explicit_prefs
        pref_text += "\n\nProfil Gaya Pengguna: "
        if styles:
            pref_text += f"Suka gaya {styles}. "
        if colors:
            pref_text += f"Suka warna {colors}. "
        if avoids:
            pref_text += f"Hindari {avoids}."
    elif implicit_prefs := db.get_user_preferences(interaction.user.id):
        pref_text = f"\n\nPengguna ini sebelumnya menyukai outfit seperti: {', '.join(implicit_prefs[:2])}"

    prompt = f"Anda adalah fashion stylist AI. Berikan rekomendasi outfit detail untuk gaya '{gaya}' di acara '{acara}'.{pref_text} Jawab dalam Bahasa Indonesia."
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant"
        )
        response = chat_completion.choices[0].message.content
        await interaction.followup.send(
            response, view=RatingView(outfit_description=response)
        )
    except Exception as e:
        await interaction.followup.send(
            "Maaf, terjadi kesalahan saat meracik outfit. Coba lagi nanti."
        )


# --- Grup Perintah: /preferensi ---
class Preferensi(app_commands.Group):
    @app_commands.command(
        name="atur", description="Atur atau perbarui preferensi gayamu."
    )
    async def atur(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PreferenceModal())

    @app_commands.command(
        name="lihat", description="Lihat preferensi yang sudah kamu simpan."
    )
    async def lihat(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        prefs = db.get_explicit_preferences(interaction.user.id)
        if not prefs or all(not p for p in prefs):
            await interaction.followup.send(
                "Kamu belum mengatur preferensi. Coba `/preferensi atur`.",
                ephemeral=True,
            )
            return
        styles, colors, avoids = prefs
        embed = discord.Embed(
            title=f"Preferensi Gaya Milik {interaction.user.display_name}",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Gaya Favorit", value=styles or "_Belum diatur_", inline=False
        )
        embed.add_field(
            name="Warna Kesukaan", value=colors or "_Belum diatur_", inline=False
        )
        embed.add_field(
            name="Item Dihindari", value=avoids or "_Belum diatur_", inline=False
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


# --- Grup Perintah: /lemari ---
class Lemari(app_commands.Group):
    @app_commands.command(
        name="tambah", description="Tambahkan item pakaian baru ke lemari digitalmu."
    )
    async def tambah(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddItemModal())

    @app_commands.command(
        name="lihat", description="Lihat semua item di lemari digitalmu."
    )
    async def lihat(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        items = db.get_wardrobe_items(interaction.user.id)
        if not items:
            await interaction.followup.send(
                "Lemari digitalmu masih kosong! Tambahkan item dengan `/lemari tambah`.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title=f"Lemari Digital Milik {interaction.user.display_name}",
            color=discord.Color.blurple(),
        )
        for item_type, color, description in items:
            embed.add_field(
                name=f"{item_type.title()} ({color.title()})",
                value=f"_{description}_" if description else "Tanpa deskripsi",
                inline=False,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="outfit", description="Dapatkan rekomendasi outfit dari item di lemarimu."
    )
    @app_commands.describe(acara="Untuk acara apa outfit ini?")
    async def outfit(self, interaction: discord.Interaction, acara: str):
        await interaction.response.defer()
        items = db.get_wardrobe_items(interaction.user.id)
        if not items or len(items) < 2:
            await interaction.followup.send(
                "Kamu butuh setidaknya 2 item di lemari untuk diracik. Tambahkan item dengan `/lemari tambah`."
            )
            return
        wardrobe_list = "\n".join(f"- {item[0]} warna {item[1]}" for item in items)
        prompt = f"Anda adalah fashion stylist. Buat satu kombinasi outfit untuk acara '{acara}' HANYA dari daftar pakaian berikut:\n{wardrobe_list}\nJelaskan mengapa cocok. Jangan menyarankan item yang tidak ada di daftar. Jawab dalam Bahasa Indonesia."
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            response = chat_completion.choices[0].message.content
            await interaction.followup.send(response)
        except Exception as e:
            await interaction.followup.send(
                "Maaf, terjadi kesalahan saat meracik outfit dari lemarimu."
            )


bot.tree.add_command(
    Preferensi(name="preferensi", description="Kelola preferensi gayamu.")
)
bot.tree.add_command(
    Lemari(name="lemari", description="Kelola dan gunakan lemari digitalmu.")
)


# --- Event untuk Respon Percakapan ---
@bot.event
async def on_message(message):
    if message.author == bot.user or not bot.user.mentioned_in(message):
        return
    async with message.channel.typing():
        try:
            user_question = message.content.replace(
                f"<@!{bot.user.id}>", ""
            ).strip()  # Menghapus mention dengan lebih baik
            if not user_question:
                await message.reply(
                    "Hai! Ada yang bisa aku bantu seputar outfit? Mention aku dan ajukan pertanyaanmu, ya!"
                )
                return

            user_name = message.author.display_name

            # Kumpulkan konteks dari database (kode ini tetap sama)
            context_text = ""
            if prefs := db.get_explicit_preferences(message.author.id):
                # ... (kode untuk mengambil preferensi tetap sama)
                context_text += "\n\nProfil Gaya Pengguna: "
                if prefs[0]:
                    context_text += f"Suka gaya {prefs[0]}. "
                if prefs[1]:
                    context_text += f"Suka warna {prefs[1]}. "
                if prefs[2]:
                    context_text += f"Hindari {prefs[2]}."

            if items := db.get_wardrobe_items(message.author.id):
                # ... (kode untuk mengambil item lemari tetap sama)
                wardrobe_list = ", ".join(f"{item[0]}" for item in items)
                context_text += f"\nIsi Lemari Digital: {wardrobe_list}"

            # Perbarui prompt untuk menyertakan nama pengguna dan instruksi untuk menyapa
            prompt = f"""
            Anda adalah fashion stylist AI ramah bernama Gaya-san.
            Seorang pengguna bernama "{user_name}" bertanya: "{user_question}"
            
            {context_text}

            Tugas Anda:
            1.  Mulai jawaban Anda dengan menyapa pengguna dengan namanya (contoh: "Halo {user_name}!" atau "Tentu, {user_name}!").
            2.  Jawab pertanyaannya secara detail dan personal menggunakan informasi profil dan isi lemari yang diberikan.
            3.  Gunakan gaya percakapan yang santai dalam Bahasa Indonesia.
            """

            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            response = chat_completion.choices[0].message.content
            await message.reply(response)
        except Exception as e:
            print(f"Terjadi error pada on_message: {e}")
            await message.reply(
                "Waduh, sepertinya ada sedikit gangguan di koneksiku. Coba tanya lagi beberapa saat, ya."
            )


# --- Menjalankan Bot ---
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print(
            "ERROR: DISCORD_TOKEN tidak ditemukan. Pastikan sudah diatur di file .env"
        )
