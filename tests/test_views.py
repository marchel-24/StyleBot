# tests/test_views.py
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Atur env vars untuk database tes (meskipun kita mock, ini praktik yang baik)
import os
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_NAME"] = "test_gaya_san.db"

# Impor kelas View kita
from view import PreferenceModal, AddItemModal

class TestViews(unittest.IsolatedAsyncioTestCase):

    # --- Kasus Uji 4 ---
    @patch("view.db.update_preferences") # Mock fungsi 'update_preferences' di modul 'view'
    async def test_preference_modal_submit(self, mock_update_preferences):
        """Kasus 4: Tes submit PreferenceModal memanggil db.update_preferences."""
        
        # Siapkan Modal
        modal = PreferenceModal()
        
        # --- DIUBAH ---
        # Kita tidak bisa mengatur .value dari TextInput asli.
        # Kita ganti seluruh komponen dengan MagicMock dan atur .value di sana.
        modal.favorite_styles = MagicMock()
        modal.favorite_styles.value = "Test Style"
        
        modal.favorite_colors = MagicMock()
        modal.favorite_colors.value = "Test Color"
        
        modal.avoided_items = MagicMock()
        modal.avoided_items.value = "Test Avoid"
        
        modal.gender = MagicMock()
        modal.gender.value = "Test Gender"
        # --- Akhir Perubahan ---
        
        # Siapkan Mock Interaction
        mock_interaction = MagicMock()
        mock_interaction.user.id = 123
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        # Jalankan fungsi on_submit
        await modal.on_submit(mock_interaction)
        
        # Verifikasi bahwa response.defer dan followup.send dipanggil
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True, thinking=True)
        mock_interaction.followup.send.assert_called_once()
        
        # Verifikasi KUNCI: db.update_preferences dipanggil dengan data yang benar
        mock_update_preferences.assert_called_once_with(
            123,                # user_id
            "Test Style",       # styles
            "Test Color",       # colors
            "Test Avoid",       # avoids
            "Test Gender"       # gender
        )

    # --- Kasus Uji 5 ---
    @patch("view.db.update_preferences")
    async def test_preference_modal_submit_empty_fields(self, mock_update_preferences):
        """Kasus 5: Tes submit PreferenceModal dengan field kosong (mengirim None)."""
        
        modal = PreferenceModal()
        
        # --- DIUBAH ---
        # Sama seperti di atas, gunakan MagicMock
        modal.favorite_styles = MagicMock()
        modal.favorite_styles.value = "" # Field kosong
        
        modal.favorite_colors = MagicMock()
        modal.favorite_colors.value = "" # Field kosong
        
        modal.avoided_items = MagicMock()
        modal.avoided_items.value = "" # Field kosong
        
        modal.gender = MagicMock()
        modal.gender.value = "" # Field kosong
        # --- Akhir Perubahan ---
        
        mock_interaction = MagicMock()
        mock_interaction.user.id = 456
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        await modal.on_submit(mock_interaction)

        # Verifikasi bahwa data 'None' yang dikirim ke DB (karena 'value or None')
        mock_update_preferences.assert_called_once_with(
            456,    # user_id
            None,   # styles
            None,   # colors
            None,   # avoids
            None    # gender
        )

    # --- Kasus Uji 6 ---
    @patch("view.db.add_item_to_wardrobe") # Mock fungsi 'add_item_to_wardrobe'
    async def test_add_item_modal_submit(self, mock_add_item):
        """Kasus 6: Tes submit AddItemModal memanggil db.add_item_to_wardrobe."""
        
        modal = AddItemModal()
        
        # --- DIUBAH ---
        # Sama seperti di atas, gunakan MagicMock
        modal.item_type = MagicMock()
        modal.item_type.value = "Sepatu"
        
        modal.color = MagicMock()
        modal.color.value = "Hitam"
        
        modal.description = MagicMock()
        modal.description.value = "Sepatu lari"
        # --- Akhir Perubahan ---
        
        mock_interaction = MagicMock()
        mock_interaction.user.id = 789
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        
        await modal.on_submit(mock_interaction)
        
        # Verifikasi
        mock_interaction.response.defer.assert_called_once_with(ephemeral=True, thinking=True)
        
        # Verifikasi KUNCI: db.add_item_to_wardrobe dipanggil dengan data yang benar
        mock_add_item.assert_called_once_with(
            789,             # user_id
            "Sepatu",        # item_type
            "Hitam",         # color
            "Sepatu lari"    # description
        )