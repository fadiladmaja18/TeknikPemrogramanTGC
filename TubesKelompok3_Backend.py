import pandas as pd
from datetime import datetime
import numpy as np

class Nasabah:
    """Kelas merepresentasikan entitas Nasabah. ARGUMEN DISESUAIKAN DENGAN NAMA KOLOM DATAFRAME."""
    
    # PERBAIKAN: Mengubah nama parameter agar match dengan key dari data.to_dict()
    def __init__(self, Rekening, Nama, Saldo_Tabungan, Total_Pinjaman_Pokok, Total_Pinjaman_Bunga):
        self.Rekening = int(Rekening)
        self.Nama = Nama
        self.Saldo_Tabungan = Saldo_Tabungan
        self.Total_Pinjaman_Pokok = Total_Pinjaman_Pokok
        self.Total_Pinjaman_Bunga = Total_Pinjaman_Bunga

    def to_dict(self):
        """Mengkonversi objek nasabah ke dictionary (untuk disimpan ke DataFrame)."""
        return {
            "Rekening": self.Rekening,
            "Nama": self.Nama,
            "Saldo_Tabungan": self.Saldo_Tabungan,
            "Total_Pinjaman_Pokok": self.Total_Pinjaman_Pokok,
            "Total_Pinjaman_Bunga": self.Total_Pinjaman_Bunga
        }

class BankSystem:
    
    def __init__(self, nasabah_file="data_nasabah.csv", transaksi_file="data_transaksi.csv"):
        self.NASABAH_FILE = nasabah_file
        self.TRANSAKSI_FILE = transaksi_file
        self.df_nasabah = self._load_nasabah()
        self.df_transaksi = self._load_transaksi()

    def _load_nasabah(self):
        """Memuat data nasabah dari CSV atau membuat data default."""
        try:
            df = pd.read_csv(self.NASABAH_FILE)
            df['Rekening'] = df['Rekening'].astype(int)
        except FileNotFoundError:
            df = pd.DataFrame({
                "Rekening": [1001, 1002, 1003],
                "Nama": ["Budi Santoso", "Citra Dewi", "Ahmad Jaya"],
                "Saldo_Tabungan": [1500000, 2000000, 500000],
                "Total_Pinjaman_Pokok": [0, 1000000, 0],
                "Total_Pinjaman_Bunga": [0, 1050000, 0]
            })
            df.to_csv(self.NASABAH_FILE, index=False)
        return df

    def _load_transaksi(self):
        """
        Memuat data transaksi dari CSV.
        PERBAIKAN: Menggunakan errors='coerce' untuk mengubah entri tanggal yang buruk menjadi NaT (Not a Time),
        memastikan kolom tetap bertipe datetime.
        """
        try:
            df = pd.read_csv(self.TRANSAKSI_FILE)
            # Paksa konversi ke datetime. Jika gagal, isi dengan NaT.
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%Y-%m-%d', errors='coerce') 
        except FileNotFoundError:
            df = pd.DataFrame({
                "Tanggal": [], "Rekening": [], "Jenis": [], 
                "Nominal": [], "Bunga_Pinjaman_%": [], 
                "Kredit": [], "Debit": []
            })
            # Inisialisasi dengan tipe datetime/datetime64
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df.to_csv(self.TRANSAKSI_FILE, index=False)
        return df

    def _save_data(self):
        """Menyimpan semua DataFrame ke CSV."""
        self.df_nasabah.to_csv(self.NASABAH_FILE, index=False)
        self.df_transaksi.to_csv(self.TRANSAKSI_FILE, index=False)

    def search_nasabah(self, search_term):
        """Mencari nasabah berdasarkan nama atau rekening."""
        if not search_term:
            return pd.DataFrame()
        
        try:
            search_rekening = int(search_term)
            filtered = self.df_nasabah[self.df_nasabah['Rekening'] == search_rekening]
        except ValueError:
            filtered = self.df_nasabah[self.df_nasabah['Nama'].str.contains(search_term, case=False, na=False)]
        
        return filtered

    def get_nasabah_data(self, rekening):
        """Mengambil data Nasabah berdasarkan rekening dan mengembalikannya sebagai objek Nasabah."""
        data = self.df_nasabah[self.df_nasabah['Rekening'] == rekening]
        if not data.empty:
            return Nasabah(**data.iloc[0].to_dict()) 
        return None

    def add_new_nasabah(self, nama, setoran_awal, tanggal):
        """Menambahkan nasabah baru dan mencatat setoran awal."""
        new_rekening = self.df_nasabah['Rekening'].max() + 1 if not self.df_nasabah.empty else 1001
        
        data_baru = pd.DataFrame({
            "Rekening": [new_rekening],
            "Nama": [nama.strip()],
            "Saldo_Tabungan": [setoran_awal],
            "Total_Pinjaman_Pokok": [0],
            "Total_Pinjaman_Bunga": [0]
        })
        
        self.df_nasabah = pd.concat([self.df_nasabah, data_baru], ignore_index=True)
        
        self._record_transaction(tanggal, new_rekening, "Setor Awal", setoran_awal, 0.0, 0, setoran_awal)
        
        self._save_data()
        return new_rekening

    def _record_transaction(self, tanggal, rekening, jenis, nominal, bunga, kredit, debit):
        """Fungsi internal untuk mencatat transaksi ke df_transaksi."""
        # Konversi objek date/datetime ke string 'YYYY-MM-DD'
        if isinstance(tanggal, (datetime, pd.Timestamp)):
             tanggal_str = tanggal.strftime('%Y-%m-%d')
        else:
             tanggal_str = str(tanggal)
             
        new_transaction = pd.DataFrame({
            "Tanggal": [tanggal_str],
            "Rekening": [rekening],
            "Jenis": [jenis],
            "Nominal": [nominal],
            "Bunga_Pinjaman_%": [bunga],
            "Kredit": [kredit],
            "Debit": [debit]
        })
        self.df_transaksi = pd.concat([self.df_transaksi, new_transaction], ignore_index=True)

    def process_setor_tunai(self, rekening, nominal, tanggal):
        if nominal <= 0:
            return False, "Nominal setoran harus lebih dari Rp 0."
        self.df_nasabah.loc[self.df_nasabah['Rekening'] == rekening, 'Saldo_Tabungan'] += nominal
        self._record_transaction(tanggal, rekening, "Setor", nominal, 0.0, 0, nominal)
        self._save_data()
        return True, "Setoran berhasil."

    def process_tarik_tunai(self, rekening, nominal, saldo_saat_ini, tanggal):
        if nominal <= 0:
            return False, "Nominal tarikan harus lebih dari Rp 0."
        if nominal > saldo_saat_ini:
            return False, "Saldo tabungan tidak mencukupi."
        self.df_nasabah.loc[self.df_nasabah['Rekening'] == rekening, 'Saldo_Tabungan'] -= nominal
        self._record_transaction(tanggal, rekening, "Tarik", nominal, 0.0, nominal, 0)
        self._save_data()
        return True, "Tarikan berhasil."

    def process_pinjaman(self, rekening, nominal_pinjam, bunga_val, tanggal):
        if nominal_pinjam <= 0:
            return False, "Nominal pinjaman harus lebih dari Rp 0."
        bunga_decimal = bunga_val / 100
        total_pinjaman_bunga = nominal_pinjam + (nominal_pinjam * bunga_decimal)
        self.df_nasabah.loc[self.df_nasabah['Rekening'] == rekening, 'Total_Pinjaman_Pokok'] += nominal_pinjam
        self.df_nasabah.loc[self.df_nasabah['Rekening'] == rekening, 'Total_Pinjaman_Bunga'] += total_pinjaman_bunga
        self._record_transaction(tanggal, rekening, "Pinjam", nominal_pinjam, bunga_val, nominal_pinjam, 0)
        self._save_data()
        return True, f"Pinjaman berhasil dicatat (Total Bayar: Rp {total_pinjaman_bunga:,.0f})."

    def get_riwayat_transaksi(self, rekening):
        df_riwayat = self.df_transaksi[self.df_transaksi['Rekening'] == rekening].sort_values('Tanggal', ascending=False).copy()
        
        # PERBAIKAN: Pastikan Tanggal bertipe datetime sebelum menggunakan .dt
        if not pd.api.types.is_datetime64_any_dtype(df_riwayat['Tanggal']):
             df_riwayat['Tanggal'] = pd.to_datetime(df_riwayat['Tanggal'], errors='coerce') 
             
        return df_riwayat
    
    def get_monthly_transaction_summary(self, rekening):
        df_riwayat = self.get_riwayat_transaksi(rekening)
        
        # PERBAIKAN: Hapus baris dengan NaT (hasil dari errors='coerce')
        df_riwayat = df_riwayat.dropna(subset=['Tanggal'])
        
        if df_riwayat.empty:
            return pd.DataFrame()
            
        # Sekarang aman menggunakan .dt karena kita sudah memastikan tipenya di get_riwayat_transaksi
        df_riwayat['Bulan'] = df_riwayat['Tanggal'].dt.to_period('M')
        df_monthly = df_riwayat.groupby('Bulan').size().reset_index(name='Jumlah Transaksi')
        df_monthly['Bulan'] = df_monthly['Bulan'].astype(str)
        return df_monthly
