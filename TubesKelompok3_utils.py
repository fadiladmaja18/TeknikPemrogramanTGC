import streamlit as st

def format_rupiah_auto(key):
    """Memformat input menjadi Rupiah secara otomatis (misal: 1000000 -> 1.000.000)"""
    value = st.session_state.get(key, "")
    clean = value.replace(".", "").replace(",", "").replace("Rp", "").strip()

    if clean == "":
        st.session_state[key] = ""
        return

    if not clean.isdigit():
        return

    number = int(clean)
    formatted = f"{number:,}".replace(",", ".")
    st.session_state[key] = formatted

def parse_rupiah(x):
    """Membersihkan dan mengkonversi string Rupiah (misal: "1.000.000") ke integer (1000000)"""
    try:
        if isinstance(x, str):
            return int(x.replace(".", "").replace("Rp", "").strip())
        return int(x)
    except:
        return 0
