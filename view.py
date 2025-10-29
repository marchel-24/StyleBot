# views.py
import discord
import database as db


# --- View untuk Rating ---
class RatingView(discord.ui.View):
    def __init__(self, outfit_description: str):
        super().__init__(timeout=300)
        self.outfit_description = outfit_description

    async def disable_buttons(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Suka 👍", style=discord.ButtonStyle.green)
    async def like_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        db.save_rating(interaction.user.id, self.outfit_description, 1)
        await interaction.response.send_message(
            "Terima kasih! Feedback-mu sudah disimpan.", ephemeral=True
        )
        await self.disable_buttons(interaction)

    @discord.ui.button(label="Tidak Suka 👎", style=discord.ButtonStyle.red)
    async def dislike_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        db.save_rating(interaction.user.id, self.outfit_description, -1)
        await interaction.response.send_message(
            "Oke, dicatat. Aku akan belajar dari ini.", ephemeral=True
        )
        await self.disable_buttons(interaction)


# --- Modal (Formulir) untuk Menambah Item ke Lemari ---
class AddItemModal(discord.ui.Modal, title="Tambah Item ke Lemari Digital"):
    item_type = discord.ui.TextInput(
        label="Jenis Pakaian", placeholder="Contoh: Kemeja Flanel, Celana Jeans..."
    )
    color = discord.ui.TextInput(
        label="Warna Dominan", placeholder="Contoh: Biru Dongker, Putih..."
    )
    description = discord.ui.TextInput(
        label="Deskripsi Singkat (Opsional)",
        placeholder="Contoh: Kemeja oversized...",
        required=False,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db.add_item_to_wardrobe(
            interaction.user.id,
            self.item_type.value,
            self.color.value,
            self.description.value,
        )
        await interaction.followup.send(
            f"✅ **{self.item_type.value}** berhasil ditambahkan ke lemari digitalmu!",
            ephemeral=True,
        )


# --- Modal (Formulir) untuk Mengatur Preferensi ---
class PreferenceModal(discord.ui.Modal, title="Atur Preferensi Gayamu"):
    favorite_styles = discord.ui.TextInput(
        label="Gaya Favoritmu",
        placeholder="Contoh: Kasual, Streetwear, Vintage...",
        required=False,
    )
    favorite_colors = discord.ui.TextInput(
        label="Warna Kesukaanmu",
        placeholder="Contoh: Earth tone, Monokrom, Pastel...",
        required=False,
    )
    avoided_items = discord.ui.TextInput(
        label="Item yang Kamu Hindari",
        placeholder="Contoh: Topi, Rok, Warna pink...",
        required=False,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        db.update_preferences(
            interaction.user.id,
            self.favorite_styles.value,
            self.favorite_colors.value,
            self.avoided_items.value,
        )
        await interaction.followup.send(
            "✅ Preferensimu sudah disimpan! Aku akan mengingat ini.", ephemeral=True
        )
