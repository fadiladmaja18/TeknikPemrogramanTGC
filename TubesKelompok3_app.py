import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from utils import format_rupiah_auto, parse_rupiah
from backend import BankSystem, Nasabah

# --- Initial Setup ---
st.set_page_config(layout="wide", page_title="🏦 Aplikasi Bank Teller OOP")

# Inisialisasi BankSystem di session state agar state backend tetap terjaga
if 'bank_system' not in st.session_state:
    st.session_state['bank_system'] = BankSystem()

bank_system = st.session_state['bank_system']

# --- Styling Function ---
def apply_custom_style():
    """Menerapkan gaya kustom Streamlit untuk tampilan yang lebih menarik."""
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #007BFF; /* Biru */
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        .stMetric {
            background-color: #e9ecef; /* Abu-abu terang */
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #28A745; /* Hijau untuk indikator */
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        h1 { color: #343A40; } /* Abu-abu gelap */
        h2 { color: #495057; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

st.title("🏦 Aplikasi Bank Teller ")
st.caption("Aplikasi simulasi bank dengan pemisahan logika Front-end dan Back-end.")


# --- Sidebar: Pencarian Nasabah ---
def render_sidebar():
    """Mengelola logika pencarian dan tampilan info nasabah di sidebar."""
    st.sidebar.header("🔍 Cari Nasabah")
    
    # Menghapus cache data Streamlit untuk memastikan data terbaru terload
    st.cache_data.clear()

    search_term = st.sidebar.text_input("Nama / Rekening", key="search_term_sidebar").strip()
    
    current_nasabah = None
    selected_rekening = None

    if search_term:
        filtered_nasabah = bank_system.search_nasabah(search_term)
    else:
        filtered_nasabah = pd.DataFrame()

    st.sidebar.subheader("Hasil")
    
    if not filtered_nasabah.empty:
        st.sidebar.dataframe(filtered_nasabah[['Rekening', 'Nama']], hide_index=True, use_container_width=True)
        
        rekening_options = filtered_nasabah['Rekening'].astype(str) + " - " + filtered_nasabah['Nama']
        selected_option = st.sidebar.selectbox("Pilih Nasabah:", rekening_options, key="selected_nasabah_key", index=0)
        
        if selected_option:
            selected_rekening = int(selected_option.split(" - ")[0])
            current_nasabah = bank_system.get_nasabah_data(selected_rekening)
            
            # Tampilkan Ringkasan Nasabah
            st.sidebar.write("---")
            st.sidebar.subheader(f"Info: {current_nasabah.Nama}")
            col1, col2 = st.sidebar.columns(2)
            col1.metric("Rekening", current_nasabah.Rekening)
            col2.metric("Pinjaman Pokok", f"Rp {current_nasabah.Total_Pinjaman_Pokok:,.0f}".replace(",", "."))
            st.sidebar.metric("Saldo Tabungan", f"Rp {current_nasabah.Saldo_Tabungan:,.0f}".replace(",", "."))
            st.sidebar.metric("Total Kewajiban Pinjaman", f"Rp {current_nasabah.Total_Pinjaman_Bunga:,.0f}".replace(",", "."))
            
    else:
        st.sidebar.info("Masukkan nama/rekening atau daftarkan nasabah baru.")
        
    return current_nasabah, selected_rekening

current_nasabah, selected_rekening = render_sidebar()


# --- Main Content: Transactions ---

st.header("Input Transaksi Teller")

# Tabs untuk navigasi transaksi
tab_daftar, tab_setor, tab_tarik, tab_pinjam = st.tabs(["🆕 Daftar Nasabah Baru", "💵 Setor Tunai (Debit)", "💳 Tarik Tunai (Kredit)", "💰 Pinjaman Baru (Kredit)"])

# Input Tanggal (Diatur di session state untuk konsistensi di semua tab)
if 'tanggal_transaksi_state' not in st.session_state:
    st.session_state.tanggal_transaksi_state = datetime.now().date()
tanggal_transaksi = st.date_input("Tanggal Transaksi", value=st.session_state.tanggal_transaksi_state, key="tanggal_transaksi")


# 1. TAB: Daftar Nasabah Baru
with tab_daftar:
    st.subheader("Registrasi Akun Baru")
    
    nama_nasabah_baru = st.text_input("Nama Lengkap Nasabah", key="nama_baru_key")
    setoran_awal_raw = st.text_input("Setoran Awal (Rp)", placeholder="Rp 100.000 (Min. Rp 100.000)", key="setoran_awal_key", on_change=format_rupiah_auto, args=("setoran_awal_key",))
    setoran_awal = parse_rupiah(setoran_awal_raw)
    
    if st.button("Proses Pendaftaran & Buka Rekening", key="btn_daftar"):
        if not nama_nasabah_baru.strip():
            st.error("Nama nasabah tidak boleh kosong.")
        elif setoran_awal < 100000:
            st.error("Setoran awal minimal adalah Rp 100.000.")
        else:
            new_rekening = bank_system.add_new_nasabah(nama_nasabah_baru, setoran_awal, tanggal_transaksi)
            st.success(f"✅ Nasabah **{nama_nasabah_baru.strip()}** berhasil didaftarkan!")
            st.info(f"Nomor Rekening Baru: **{new_rekening}**")
            st.balloons()
            st.rerun() 

# Logika Transaksi hanya berjalan jika nasabah telah dipilih
if current_nasabah is not None:
    
    # 2. TAB: Setor Tunai (Debit)
    with tab_setor:
        st.subheader(f"Setor ke Rek. {current_nasabah.Rekening} ({current_nasabah.Nama})")
        nominal_setor_raw = st.text_input("Nominal Setor (Rp)", placeholder="Rp 0", key="nominal_setor_key", on_change=format_rupiah_auto, args=("nominal_setor_key",))
        nominal_setor = parse_rupiah(nominal_setor_raw)
        
        if st.button("Proses Setor Tunai", key="btn_setor"):
            success, message = bank_system.process_setor_tunai(selected_rekening, nominal_setor, tanggal_transaksi)
            if success:
                st.success(f"{message} Saldo baru: Rp {bank_system.get_nasabah_data(selected_rekening).Saldo_Tabungan:,.0f}".replace(",", "."))
                st.rerun()
            else:
                st.error(message)

    # 3. TAB: Tarik Tunai (Kredit)
    with tab_tarik:
        st.subheader(f"Tarik dari Rek. {current_nasabah.Rekening} ({current_nasabah.Nama})")
        nominal_tarik_raw = st.text_input("Nominal Tarik (Rp)", placeholder="Rp 0", key="nominal_tarik_key", on_change=format_rupiah_auto, args=("nominal_tarik_key",))
        nominal_tarik = parse_rupiah(nominal_tarik_raw)
        
        if st.button("Proses Tarik Tunai", key="btn_tarik"):
            success, message = bank_system.process_tarik_tunai(
                selected_rekening, nominal_tarik, current_nasabah.Saldo_Tabungan, tanggal_transaksi
            )
            if success:
                st.success(f"{message} Saldo baru: Rp {bank_system.get_nasabah_data(selected_rekening).Saldo_Tabungan:,.0f}".replace(",", "."))
                st.rerun()
            else:
                st.error(message)

    # 4. TAB: Pinjaman Baru (Kredit)
    with tab_pinjam:
        st.subheader(f"Pengajuan Pinjaman untuk Rek. {current_nasabah.Rekening} ({current_nasabah.Nama})")
        
        nominal_pinjam_raw = st.text_input("Nominal Pinjaman Pokok (Rp)", placeholder="Rp 0", key="nominal_pinjam_key", on_change=format_rupiah_auto, args=("nominal_pinjam_key",))
        bunga_pinjam_raw = st.text_input("Bunga Pinjaman yang Ditetapkan (%)", placeholder="0.0", key="bunga_pinjam_key")
        
        nominal_pinjam = parse_rupiah(nominal_pinjam_raw)
        try:
            bunga_pinjam_val = float(bunga_pinjam_raw.replace(",", "."))
        except:
            bunga_pinjam_val = 0.0
            
        bunga_pinjam_decimal = bunga_pinjam_val / 100
        total_pinjaman_bunga = nominal_pinjam + (nominal_pinjam * bunga_pinjam_decimal)
        
        st.info(f"Total yang harus dibayar nasabah (Pokok + Bunga): **Rp {total_pinjaman_bunga:,.0f}**".replace(",", "."))
        
        if st.button("Proses Pinjaman", key="btn_pinjam"):
            success, message = bank_system.process_pinjaman(
                selected_rekening, nominal_pinjam, bunga_pinjam_val, tanggal_transaksi
            )
            if success:
                st.success(message.replace(",", "."))
                st.rerun()
            else:
                st.error(message)
                
else:
    # Info jika nasabah belum dipilih di tab transaksi
    with tab_setor, tab_tarik, tab_pinjam:
        st.warning("Pilih nasabah di sidebar untuk melanjutkan transaksi.")


# --- Riwayat dan Analisis ---
st.write("---")
st.header("📊 Riwayat Transaksi & Analisis")

if current_nasabah is not None:
    st.subheader(f"Riwayat Transaksi: {current_nasabah.Nama} (Rek. {current_nasabah.Rekening})")
    
    df_riwayat = bank_system.get_riwayat_transaksi(selected_rekening)
    
    if not df_riwayat.empty:
        # Tampilan Riwayat Transaksi
        df_display = df_riwayat.copy()
        df_display['Tanggal'] = df_display['Tanggal'].dt.strftime('%Y-%m-%d')
        for col in ['Nominal', 'Kredit', 'Debit']:
             df_display[col] = df_display[col].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))

        st.dataframe(df_display[['Tanggal', 'Jenis', 'Nominal', 'Bunga_Pinjaman_%', 'Kredit', 'Debit']], 
                     hide_index=True, use_container_width=True)

        # Chart: Jumlah Transaksi Tiap Bulan
        st.subheader("Jumlah Transaksi Per Bulan")
        df_monthly = bank_system.get_monthly_transaction_summary(selected_rekening)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df_monthly["Bulan"], df_monthly["Jumlah Transaksi"], color='#28A745') # Hijau
        ax.set_title(f"Frekuensi Transaksi Bulanan ({current_nasabah.Nama})", fontsize=14)
        ax.set_xlabel("Bulan (Tahun-Bulan)")
        ax.set_ylabel("Jumlah Transaksi")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
        
    else:
        st.info("Belum ada riwayat transaksi untuk nasabah ini.")
