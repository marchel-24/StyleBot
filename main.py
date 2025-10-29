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
        title=f"👋 Halo, {user_name}! Aku Style-E, Asisten Fashion Pribadimu!",
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
    gaya="Desired fashion style.", acara="Outfit context or occasion."
)
async def outfit(interaction: discord.Interaction, gaya: str, acara: str):
    await interaction.response.defer()
    # Logika untuk mengambil preferensi dan membuat prompt
    explicit_prefs = db.get_explicit_preferences(interaction.user.id)
    pref_text = ""
    if explicit_prefs:
        styles, colors, avoids = explicit_prefs
        pref_text += "\n\nUser preference Profile: "
        if styles:
            pref_text += f"Like this type of style {styles}. "
        if colors:
            pref_text += f"Like this color {colors}. "
        if avoids:
            pref_text += f"Avoids {avoids}."
    elif implicit_prefs := db.get_user_preferences(interaction.user.id):
        pref_text = f"\n\nThis user previously liked outfits like: {', '.join(implicit_prefs[:2])}"

    prompt = f"You are **Styl-E**, a warm, confident, and trend-savvy virtual fashion stylist.Your mission is to give friendly, clear, and stylish advice that makes people feel good and confident. Give outfit recommendation with '{gaya}' as the style, for '{acara}' as occasion. {pref_text} answer in Bahasa Indonesia."
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
        prompt = f"You are **Styl-E**, a warm, confident, and trend-savvy virtual fashion stylist.Your mission is to give friendly, clear, and stylish advice that makes people feel good and confident. Make an outfit combination for '{acara}' as the occasion. ONLY from the following clothing list:\n{wardrobe_list}\nExplain why it's suitable. Don't suggest items that aren't on the list. Answer in Bahasa Indonesia."
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
                context_text += "\n\nUser preference Profile: "
                if prefs[0]:
                    context_text += f"Like this type of style {prefs[0]}. "
                if prefs[1]:
                    context_text += f"Like this color {prefs[1]}. "
                if prefs[2]:
                    context_text += f"Avoids {prefs[2]}."

            if items := db.get_wardrobe_items(message.author.id):
                # ... (kode untuk mengambil item lemari tetap sama)
                wardrobe_list = ", ".join(f"{item[0]}" for item in items)
                context_text += f"\nDigital Wardrobe Contents: {wardrobe_list}"

            # Perbarui prompt untuk menyertakan nama pengguna dan instruksi untuk menyapa
            prompt = f"""
            You are **Styl-E**, a warm, confident, and trend-savvy virtual fashion stylist.
            Your mission is to give friendly, clear, and stylish advice that makes people feel good and confident.

            You excel at:
            1. **Outfit Crafting:** Combine user-provided clothing items into complete, fashionable looks and explain *why* they work.
            2. **Specific Advice:** Help users pick clothes for their body type, occasion, or vibe — always positive, inclusive, and practical.
            3. **Expertise:** You're fluent in streetwear, minimalist, smart casual, vintage, and techwear styles.
            4. **Tips & Tricks:** Offer clever insights on layering, colors, accessories, and balance.
            5. **OOTD:** If asked for an "Outfit of the Day", ask clarifying questions first like weather or occasion, then build a killer look.

            Your tone: Energetic, stylish, and encouraging — like a best friend with impeccable fashion sense.
            Answer in a clear and well-formatted style using emojis and markdown to make it fun to read.

            A user named "{user_name}" is asking: "{user_question}"
            
            {context_text}

            Your Task:
            1. Start your answer by greeting the user by name (e.g., "Hello {user_name}!" or "Sure, {user_name}!").
            2. Answer the question in detail and personally using the profile information and the contents of the provided closet.
            3. Answer in Bahasa Indonesia.
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
