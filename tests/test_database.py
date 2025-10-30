# tests/test_database.py
import os
import unittest

# Atur env vars untuk database tes SEBELUM mengimpor 'database.py'
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_NAME"] = "test_gaya_san.db"

# Impor modul database kita SEKARANG
import database as db

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Dipanggil sebelum setiap metode tes. Membuat DB baru."""
        # Hapus DB lama jika ada, untuk kebersihan
        if os.path.exists("test_gaya_san.db"):
            os.remove("test_gaya_san.db")
        # Buat tabel baru
        db.init_db()

    def tearDown(self):
        """Dipanggil setelah setiap metode tes. Menghapus DB."""
        try:
            os.remove("test_gaya_san.db")
        except OSError as e:
            print(f"Error removing test DB: {e}")

    # --- Kasus Uji 1 ---
    def test_add_and_get_wardrobe_items(self):
        """Kasus 1: Tes menambah dan mengambil item lemari."""
        user_id = 123
        
        # Awalnya harus kosong
        self.assertEqual(db.get_wardrobe_items(user_id), [])
        
        # Tambah 1 item
        db.add_item_to_wardrobe(user_id, "Kemeja", "Putih", "Kemeja katun")
        items = db.get_wardrobe_items(user_id)
        
        # Verifikasi
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0], ("Kemeja", "Putih", "Kemeja katun"))

    # --- Kasus Uji 2 ---
    def test_update_and_get_preferences(self):
        """Kasus 2: Tes menyimpan, memperbarui, dan mengambil preferensi."""
        user_id = 456
        
        # Awalnya harus None
        self.assertIsNone(db.get_explicit_preferences(user_id))
        
        # Data awal
        styles, colors, avoids, gender = "Casual", "Biru", "Pink", "Pria"
        db.update_preferences(user_id, styles, colors, avoids, gender)
        
        # Verifikasi data awal
        prefs = db.get_explicit_preferences(user_id)
        self.assertEqual(prefs, (styles, colors, avoids, gender))
        
        # Data baru untuk pembaruan
        new_styles = "Streetwear"
        new_gender = "Androgini"
        db.update_preferences(user_id, new_styles, colors, avoids, new_gender)
        
        # Verifikasi data yang diperbarui
        updated_prefs = db.get_explicit_preferences(user_id)
        self.assertEqual(updated_prefs, (new_styles, colors, avoids, new_gender))

    # --- Kasus Uji 3 ---
    def test_ratings_and_implicit_preferences(self):
        """Kasus 3: Tes menyimpan rating dan mengambil preferensi implisit (hanya 'Suka')."""
        user_id = 789
        
        # Awalnya harus kosong
        self.assertEqual(db.get_user_preferences(user_id), [])
        
        # Simpan 1 'Suka' (rating 1)
        outfit_suka = "Kemeja putih dan jeans biru"
        db.save_rating(user_id, outfit_suka, 1)
        
        # Simpan 1 'Tidak Suka' (rating -1)
        outfit_tidak_suka = "Kaos hijau dan celana kuning"
        db.save_rating(user_id, outfit_tidak_suka, -1)
        
        # Ambil preferensi implisit
        implicit_prefs = db.get_user_preferences(user_id)
        
        # Verifikasi bahwa HANYA outfit yang disukai yang kembali
        self.assertEqual(len(implicit_prefs), 1)
        self.assertEqual(implicit_prefs[0], outfit_suka)
        self.assertNotIn(outfit_tidak_suka, implicit_prefs)

# Untuk menjalankan tes ini: python -m unittest tests.test_database