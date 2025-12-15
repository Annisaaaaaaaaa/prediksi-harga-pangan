import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pickle

# ======================================================
# KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard Harga Pangan Nasional",
    layout="wide"
)

# ======================================================
# STYLE (FORMAL & PROFESIONAL)
# ======================================================
st.markdown(
    """
    <style>
    /* Background utama */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f2a44;
    }

    /* Text sidebar */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #ffffff;
    }

    /* Input & select sidebar (FIX PUTIH) */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 6px;
    }

    /* Multiselect tag (TAHUN JADI BIRU) */
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 6px;
        font-weight: 500;
    }

    /* Icon X di tag */
    section[data-testid="stSidebar"] .stMultiSelect svg {
        fill: #ffffff !important;
    }

    /* Metric card */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e1e5eb;
        border-radius: 8px;
        padding: 12px;
    }

    /* Judul konten */
    h1, h2, h3 {
        color: #0f2a44;
    }

    /* Caption */
    .stCaption {
        color: #4f5b66;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data
def load_data():
    df = pd.read_csv("data_pangan_bersih.csv")
    df["Komoditas"] = df["Komoditas"].str.strip()
    return df

df = load_data()

# ======================================================
# LOAD MODEL
# ======================================================
with open("model_harga_beras.pkl", "rb") as f:
    model = pickle.load(f)

# ======================================================
# PREPROCESS TANGGAL
# ======================================================
bulan_map = {
    "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
    "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
    "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}

df["Bulan_num"] = df["Bulan"].map(bulan_map)
df["Tanggal"] = pd.to_datetime(
    dict(year=df["Tahun"], month=df["Bulan_num"], day=1)
)

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title("Filter Data")

komoditas_pilih = st.sidebar.selectbox(
    "Komoditas",
    sorted(df["Komoditas"].unique())
)

tahun_pilih = st.sidebar.multiselect(
    "Tahun",
    sorted(df["Tahun"].unique()),
    default=sorted(df["Tahun"].unique())
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Gunakan filter untuk menyesuaikan tampilan data "
    "berdasarkan komoditas dan tahun."
)

# ======================================================
# FILTER DATA
# ======================================================
df_filtered = df[
    (df["Komoditas"] == komoditas_pilih) &
    (df["Tahun"].isin(tahun_pilih))
].sort_values("Tanggal")

# ======================================================
# HEADER UTAMA
# ======================================================
st.title("Dashboard Harga Pangan Nasional")
st.caption("Analisis tren dan prediksi harga pangan berbasis data historis")

# ======================================================
# METRIC CARD
# ======================================================
if not df_filtered.empty:
    col1, col2, col3 = st.columns(3)

    col1.metric("Harga Rata-rata", f"Rp {int(df_filtered['Harga'].mean())}")
    col2.metric("Harga Tertinggi", f"Rp {int(df_filtered['Harga'].max())}")
    col3.metric("Harga Terendah", f"Rp {int(df_filtered['Harga'].min())}")
else:
    st.warning("Data tidak tersedia untuk parameter yang dipilih.")

st.markdown("---")

# ======================================================
# GRAFIK TREN
# ======================================================
st.subheader("Tren Harga")

if df_filtered.empty:
    st.info("Silakan ubah filter untuk menampilkan data.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_filtered["Tanggal"], df_filtered["Harga"], marker="o")
    ax.set_xlabel("Waktu")
    ax.set_ylabel("Harga (Rupiah)")
    ax.set_title(f"Tren Harga {komoditas_pilih}")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ======================================================
# PREDIKSI HARGA
# ======================================================
st.markdown("---")
st.subheader("Prediksi Harga")

if komoditas_pilih.strip().lower() == "beras premium":

    colp1, colp2 = st.columns(2)

    with colp1:
        bulan_pred = st.number_input("Bulan Prediksi", 1, 12, 1)

    with colp2:
        tahun_pred = st.number_input(
            "Tahun Prediksi",
            min_value=int(df["Tahun"].max()),
            max_value=int(df["Tahun"].max()) + 2,
            value=int(df["Tahun"].max())
        )

    df_beras = df[df["Komoditas"].str.lower() == "beras premium"].sort_values("Tanggal")

    index_terakhir = len(df_beras) - 1
    tahun_terakhir = df_beras["Tahun"].iloc[-1]
    bulan_terakhir = df_beras["Bulan_num"].iloc[-1]

    selisih = (tahun_pred - tahun_terakhir) * 12 + (bulan_pred - bulan_terakhir)

    if selisih <= 0:
        st.warning("Periode prediksi harus setelah data terakhir.")
    else:
        hasil = model.predict([[index_terakhir + selisih]])
        st.success(
            f"Perkiraan harga Beras Premium "
            f"pada {bulan_pred:02d}-{tahun_pred} "
            f"adalah Rp {int(hasil[0])}"
        )

else:
    st.info("Prediksi hanya tersedia untuk komoditas Beras Premium.")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption(
    "Data bersifat historis. Prediksi menggunakan regresi linear "
    "sebagai alat bantu analisis, bukan sebagai kepastian."
)
