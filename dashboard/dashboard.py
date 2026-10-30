# =============================================================================
# DASHBOARD BIKE SHARING 🚲
# Dibuat dengan Streamlit dari dataset Bike Sharing (day.csv dan hour.csv)
#
# Cara menjalankan:  streamlit run dashboard.py
# =============================================================================

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PENGATURAN HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)
sns.set_theme(style="whitegrid")

# Lokasi folder tempat dashboard.py berada (supaya file csv selalu ketemu)
BASE_DIR = Path(__file__).parent

# -----------------------------------------------------------------------------
# 2. KAMUS PELABELAN
# Dataset menyimpan kategori dalam bentuk angka (1, 2, 3, ...).
# Kita ubah menjadi teks agar mudah dibaca di grafik.
# -----------------------------------------------------------------------------
# CATATAN: dokumentasi dataset menulis 1=semi, 2=panas, 3=gugur, 4=dingin. Namun jika dicek ke
# tanggalnya, season 1 dimulai 1 Januari (suhu rata-rata terendah) dan season 3 jatuh pada
# Juni-September (suhu tertinggi). Jadi label di bawah ini disesuaikan dengan kalender sebenarnya.
SEASON_MAP = {1: "Musim Dingin", 2: "Musim Semi", 3: "Musim Panas", 4: "Musim Gugur"}
WEATHER_MAP = {
    1: "Cerah / Berawan",
    2: "Berkabut / Mendung",
    3: "Hujan / Salju Ringan",
    4: "Hujan / Salju Lebat",
}
WEEKDAY_MAP = {0: "Minggu", 1: "Senin", 2: "Selasa", 3: "Rabu", 4: "Kamis", 5: "Jumat", 6: "Sabtu"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

SEASON_ORDER = list(SEASON_MAP.values())
WEATHER_ORDER = list(WEATHER_MAP.values())
WEEKDAY_ORDER = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
TIME_ORDER = ["Dini Hari (00-05)", "Pagi (06-10)", "Siang (11-14)", "Sore (15-18)", "Malam (19-23)"]
TEMP_ORDER = ["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-30°C)", "Panas (>30°C)"]
DAY_TYPE_ORDER = ["Hari Kerja", "Akhir Pekan / Libur"]


# -----------------------------------------------------------------------------
# 3. FUNGSI BANTU
# -----------------------------------------------------------------------------
def format_angka(nilai):
    """Ubah 1234567 menjadi '1.234.567' (format Indonesia)."""
    return f"{nilai:,.0f}".replace(",", ".")


def kategori_waktu(jam):
    """Kelompokkan jam (0-23) menjadi bagian hari."""
    if jam <= 5:
        return TIME_ORDER[0]
    if jam <= 10:
        return TIME_ORDER[1]
    if jam <= 14:
        return TIME_ORDER[2]
    if jam <= 18:
        return TIME_ORDER[3]
    return TIME_ORDER[4]


def kategori_suhu(suhu_celsius):
    """Kelompokkan suhu (°C) menjadi kategori."""
    if suhu_celsius < 10:
        return TEMP_ORDER[0]
    if suhu_celsius < 20:
        return TEMP_ORDER[1]
    if suhu_celsius <= 30:
        return TEMP_ORDER[2]
    return TEMP_ORDER[3]


def siapkan_data(df):
    """Bersihkan & tambahkan kolom label yang dibutuhkan (dipakai untuk day dan hour)."""
    df = df.copy()
    df["dteday"] = pd.to_datetime(df["dteday"])

    # Label teks untuk kolom kategori
    df["season_label"] = df["season"].map(SEASON_MAP)
    df["weather_label"] = df["weathersit"].map(WEATHER_MAP)
    df["weekday_label"] = df["weekday"].map(WEEKDAY_MAP)
    df["year_label"] = df["yr"].map({0: "2011", 1: "2012"})
    df["day_type"] = df["workingday"].map({1: DAY_TYPE_ORDER[0], 0: DAY_TYPE_ORDER[1]})

    # Nilai suhu, kelembapan, dan angin di dataset sudah dinormalisasi (0-1).
    # Kita kembalikan ke satuan aslinya (sesuai dokumentasi dataset).
    df["temp_c"] = df["temp"] * 41          # suhu dalam °C
    df["hum_pct"] = df["hum"] * 100         # kelembapan dalam %
    df["wind_kmh"] = df["windspeed"] * 67   # kecepatan angin
    return df


@st.cache_data
def muat_data():
    """Baca day.csv dan hour.csv. Hasilnya disimpan di cache agar dashboard cepat."""
    day_df = siapkan_data(pd.read_csv(BASE_DIR / "day.csv"))
    hour_df = siapkan_data(pd.read_csv(BASE_DIR / "hour.csv"))

    # Kolom tambahan khusus data per jam / per hari
    hour_df["time_category"] = hour_df["hr"].apply(kategori_waktu)
    day_df["temp_category"] = day_df["temp_c"].apply(kategori_suhu)
    return day_df, hour_df


def filter_data(df, tgl_awal, tgl_akhir, musim, tipe_hari):
    """Terapkan filter dari sidebar ke sebuah dataframe."""
    mask = (
        (df["dteday"] >= pd.Timestamp(tgl_awal))
        & (df["dteday"] <= pd.Timestamp(tgl_akhir))
        & (df["season_label"].isin(musim))
        & (df["day_type"].isin(tipe_hari))
    )
    return df[mask]


def buat_bar(ax, kategori, nilai, warna, judul, label_x="", label_y="Rata-rata penyewaan"):
    """Buat bar chart sederhana dengan angka di atas batang."""
    batang = ax.bar(kategori, nilai, color=warna)
    ax.bar_label(batang, labels=[format_angka(v) for v in nilai], padding=3, fontsize=9)
    ax.set_title(judul, fontsize=12, fontweight="bold")
    ax.set_xlabel(label_x)
    ax.set_ylabel(label_y)
    ax.margins(y=0.12)
    ax.ticklabel_format(axis="y", style="plain")  # hindari notasi ilmiah (1e6)


# -----------------------------------------------------------------------------
# 4. MUAT DATA
# -----------------------------------------------------------------------------
day_df, hour_df = muat_data()

# -----------------------------------------------------------------------------
# 5. SIDEBAR (FILTER INTERAKTIF)
# -----------------------------------------------------------------------------
st.sidebar.header("🔎 Filter Data")

tgl_min = day_df["dteday"].min().date()
tgl_max = day_df["dteday"].max().date()

rentang = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(tgl_min, tgl_max),
    min_value=tgl_min,
    max_value=tgl_max,
)

musim_pilihan = st.sidebar.multiselect("Musim", options=SEASON_ORDER, default=SEASON_ORDER)
tipe_hari_pilihan = st.sidebar.multiselect(
    "Jenis Hari", options=DAY_TYPE_ORDER, default=DAY_TYPE_ORDER
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Filter berlaku untuk semua grafik. "
    "Dataset: Bike Sharing (Washington D.C., 2011–2012)."
)

# Saat pengguna baru memilih tanggal awal, date_input hanya mengembalikan 1 tanggal
if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
    st.info("Silakan pilih **tanggal akhir** pada filter di sidebar.")
    st.stop()

tgl_awal, tgl_akhir = rentang
day_f = filter_data(day_df, tgl_awal, tgl_akhir, musim_pilihan, tipe_hari_pilihan)
hour_f = filter_data(hour_df, tgl_awal, tgl_akhir, musim_pilihan, tipe_hari_pilihan)

if day_f.empty or hour_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah filter di sidebar.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. JUDUL & RINGKASAN (KPI)
# -----------------------------------------------------------------------------
st.title("🚲 Bike Sharing Dashboard")
st.markdown(
    "Dashboard ini menampilkan pola penyewaan sepeda berdasarkan **waktu, musim, cuaca, "
    "jenis pengguna, dan suhu**. Gunakan filter di sidebar untuk menjelajahi data."
)

total_sewa = day_f["cnt"].sum()
total_casual = day_f["casual"].sum()
total_registered = day_f["registered"].sum()

kol1, kol2, kol3, kol4 = st.columns(4)
kol1.metric("Total Penyewaan", format_angka(total_sewa))
kol2.metric("Rata-rata per Hari", format_angka(day_f["cnt"].mean()))
kol3.metric(
    "Pengguna Terdaftar (Registered)",
    format_angka(total_registered),
    f"{total_registered / total_sewa:.0%} dari total",
    delta_color="off",
)
kol4.metric(
    "Pengguna Kasual (Casual)",
    format_angka(total_casual),
    f"{total_casual / total_sewa:.0%} dari total",
    delta_color="off",
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. TAB VISUALISASI
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 Tren Bulanan",
        "🌦️ Musim & Cuaca",
        "⏰ Pola per Jam",
        "👥 Jenis Pengguna",
        "🌡️ Suhu & Kondisi Udara",
    ]
)

# ---------------------------- TAB 1: TREN BULANAN ----------------------------
with tab1:
    st.subheader("Bagaimana tren penyewaan sepeda dari bulan ke bulan?")

    kiri, kanan = st.columns([2, 1])

    bulanan = day_f.groupby(["year_label", "mnth"], as_index=False)["cnt"].sum()
    with kiri:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        sns.lineplot(data=bulanan, x="mnth", y="cnt", hue="year_label", marker="o", linewidth=2.5, ax=ax)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MONTH_NAMES)
        ax.set_title("Total Penyewaan per Bulan", fontsize=12, fontweight="bold")
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Total penyewaan")
        ax.legend(title="Tahun")
        st.pyplot(fig)
        plt.close(fig)

    tahunan = day_f.groupby("year_label")["cnt"].sum().sort_index()
    with kanan:
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
        buat_bar(ax, tahunan.index, tahunan.values, ["#4C72B0", "#DD8452"][: len(tahunan)],
                 "Total Penyewaan per Tahun", "Tahun", "Total penyewaan")
        st.pyplot(fig)
        plt.close(fig)

    bulan_puncak = bulanan.groupby("mnth")["cnt"].sum().idxmax()
    teks = f"Bulan dengan penyewaan tertinggi pada data terpilih adalah **{MONTH_NAMES[bulan_puncak - 1]}**."
    if len(tahunan) == 2 and tahunan.iloc[0] > 0:
        naik = (tahunan.iloc[1] - tahunan.iloc[0]) / tahunan.iloc[0]
        teks += f" Total penyewaan 2012 berubah **{naik:+.0%}** dibandingkan 2011."
    st.info(teks)

# ---------------------------- TAB 2: MUSIM & CUACA ---------------------------
with tab2:
    st.subheader("Bagaimana pengaruh musim dan cuaca terhadap penyewaan sepeda?")

    kiri, kanan = st.columns(2)

    per_musim = day_f.groupby("season_label")["cnt"].mean().reindex(SEASON_ORDER).dropna()
    with kiri:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        buat_bar(ax, per_musim.index, per_musim.values,
                 ["#6495ED", "#8FBC8F", "#F4A460", "#CD853F"][: len(per_musim)],
                 "Rata-rata Penyewaan Harian per Musim", "Musim")
        st.pyplot(fig)
        plt.close(fig)

    per_cuaca = day_f.groupby("weather_label")["cnt"].mean().reindex(WEATHER_ORDER).dropna()
    with kanan:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        buat_bar(ax, per_cuaca.index, per_cuaca.values, ["#87CEEB", "#B0B0B0", "#4682B4", "#2F4F4F"][: len(per_cuaca)],
                 "Rata-rata Penyewaan Harian per Kondisi Cuaca", "Kondisi cuaca")
        ax.tick_params(axis="x", labelsize=9)
        st.pyplot(fig)
        plt.close(fig)

    st.info(
        f"Musim paling ramai: **{per_musim.idxmax()}** "
        f"({format_angka(per_musim.max())} sewa/hari). "
        f"Kondisi cuaca paling ramai: **{per_cuaca.idxmax()}** "
        f"({format_angka(per_cuaca.max())} sewa/hari)."
    )
    st.caption(
        "Catatan: pada data harian (day.csv) tidak ada hari dengan cuaca 'Hujan / Salju Lebat', "
        "sehingga kategori tersebut hanya muncul jika datanya tersedia."
    )

# ---------------------------- TAB 3: POLA PER JAM ----------------------------
with tab3:
    st.subheader("Pada jam berapa penyewaan sepeda paling ramai?")

    per_jam = hour_f.groupby(["day_type", "hr"], as_index=False)["cnt"].mean()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    sns.lineplot(data=per_jam, x="hr", y="cnt", hue="day_type", hue_order=[d for d in DAY_TYPE_ORDER if d in per_jam["day_type"].unique()],
                 marker="o", linewidth=2.5, ax=ax)
    ax.set_xticks(range(0, 24))
    ax.set_title("Rata-rata Penyewaan per Jam", fontsize=12, fontweight="bold")
    ax.set_xlabel("Jam (0-23)")
    ax.set_ylabel("Rata-rata penyewaan")
    ax.legend(title="Jenis hari")
    st.pyplot(fig)
    plt.close(fig)

    kiri, kanan = st.columns(2)
    per_waktu = hour_f.groupby("time_category")["cnt"].mean().reindex(TIME_ORDER).dropna()
    with kiri:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        buat_bar(ax, per_waktu.index, per_waktu.values,
                 ["#2F4F4F", "#F0C05A", "#E8985E", "#D1603D", "#5B6C8F"][: len(per_waktu)],
                 "Rata-rata Penyewaan per Bagian Hari", "Bagian hari", "Rata-rata penyewaan per jam")
        ax.tick_params(axis="x", labelsize=8)
        st.pyplot(fig)
        plt.close(fig)

    with kanan:
        st.markdown("#### Jam puncak")
        for tipe in DAY_TYPE_ORDER:
            sub = per_jam[per_jam["day_type"] == tipe]
            if not sub.empty:
                baris = sub.loc[sub["cnt"].idxmax()]
                st.metric(f"{tipe}", f"Pukul {int(baris['hr']):02d}.00", f"{format_angka(baris['cnt'])} sewa/jam", delta_color="off")
        st.caption(
            "Pada hari kerja biasanya terlihat dua puncak (jam berangkat & pulang kerja), "
            "sedangkan pada akhir pekan/libur pola cenderung satu puncak di siang hari."
        )

# ---------------------------- TAB 4: JENIS PENGGUNA --------------------------
with tab4:
    st.subheader("Bagaimana perbedaan pengguna Casual dan Registered?")

    kiri, kanan = st.columns(2)

    per_tipe = day_f.groupby("day_type")[["casual", "registered"]].mean().reindex(DAY_TYPE_ORDER).dropna()
    with kiri:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        per_tipe.plot(kind="bar", ax=ax, color=["#E8985E", "#4C72B0"], rot=0)
        for kontainer in ax.containers:
            ax.bar_label(kontainer, labels=[format_angka(v) for v in kontainer.datavalues], padding=3, fontsize=9)
        ax.set_title("Rata-rata Penyewaan Harian: Hari Kerja vs Akhir Pekan/Libur", fontsize=11, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("Rata-rata penyewaan")
        ax.legend(["Casual", "Registered"])
        ax.margins(y=0.12)
        st.pyplot(fig)
        plt.close(fig)

    per_hari = day_f.groupby("weekday_label")[["casual", "registered"]].mean().reindex(WEEKDAY_ORDER).dropna()
    with kanan:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        per_hari.plot(kind="bar", stacked=True, ax=ax, color=["#E8985E", "#4C72B0"], rot=30)
        ax.set_title("Rata-rata Penyewaan Harian per Hari dalam Seminggu", fontsize=11, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("Rata-rata penyewaan")
        ax.set_ylim(0, per_hari.sum(axis=1).max() * 1.2)
        ax.legend(["Casual", "Registered"], loc="upper left", ncol=2)
        st.pyplot(fig)
        plt.close(fig)

    persen_casual = total_casual / total_sewa
    st.info(
        f"Pada data terpilih, **{persen_casual:.0%}** penyewaan dilakukan pengguna casual dan "
        f"**{1 - persen_casual:.0%}** oleh pengguna registered."
    )

# ---------------------------- TAB 5: SUHU & KONDISI UDARA --------------------
with tab5:
    st.subheader("Bagaimana pengaruh suhu, kelembapan, dan angin terhadap penyewaan?")

    kiri, kanan = st.columns(2)

    with kiri:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        sns.regplot(data=day_f, x="temp_c", y="cnt", ax=ax,
                    scatter_kws={"alpha": 0.5, "s": 25}, line_kws={"color": "crimson"})
        ax.set_title("Suhu vs Jumlah Penyewaan Harian", fontsize=12, fontweight="bold")
        ax.set_xlabel("Suhu (°C)")
        ax.set_ylabel("Jumlah penyewaan")
        st.pyplot(fig)
        plt.close(fig)

    per_suhu = day_f.groupby("temp_category")["cnt"].mean().reindex(TEMP_ORDER).dropna()
    with kanan:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        buat_bar(ax, per_suhu.index, per_suhu.values, ["#6495ED", "#8FBC8F", "#F4A460", "#CD5C5C"][: len(per_suhu)],
                 "Rata-rata Penyewaan Harian per Kategori Suhu", "Kategori suhu")
        ax.tick_params(axis="x", labelsize=9)
        st.pyplot(fig)
        plt.close(fig)

    # Korelasi hanya dihitung jika datanya cukup bervariasi
    def korelasi(kolom):
        if len(day_f) > 2 and day_f[kolom].std() > 0 and day_f["cnt"].std() > 0:
            return f"{day_f[kolom].corr(day_f['cnt']):+.2f}"
        return "-"

    k1, k2, k3 = st.columns(3)
    k1.metric("Korelasi Suhu dengan Penyewaan", korelasi("temp_c"))
    k2.metric("Korelasi Kelembapan dengan Penyewaan", korelasi("hum_pct"))
    k3.metric("Korelasi Kecepatan Angin dengan Penyewaan", korelasi("wind_kmh"))
    st.caption(
        "Korelasi bernilai antara -1 sampai +1. Positif berarti makin tinggi nilainya, makin banyak "
        "penyewaan; negatif berarti sebaliknya. Korelasi bukan bukti sebab-akibat."
    )

# -----------------------------------------------------------------------------
# 8. DATA MENTAH (OPSIONAL)
# -----------------------------------------------------------------------------
with st.expander("📄 Lihat data harian (hasil filter)"):
    tabel = day_f[["dteday", "season_label", "weather_label", "temp_c", "hum_pct", "wind_kmh",
                   "casual", "registered", "cnt"]].copy()
    tabel["dteday"] = tabel["dteday"].dt.strftime("%Y-%m-%d")
    tabel[["temp_c", "hum_pct", "wind_kmh"]] = tabel[["temp_c", "hum_pct", "wind_kmh"]].round(1)
    tabel = tabel.rename(columns={
        "dteday": "Tanggal", "season_label": "Musim", "weather_label": "Cuaca",
        "temp_c": "Suhu (°C)", "hum_pct": "Kelembapan (%)", "wind_kmh": "Angin",
        "casual": "Casual", "registered": "Registered", "cnt": "Total",
    })
    st.dataframe(tabel)

st.caption("Sumber data: Bike Sharing Dataset (Kaggle) • Dashboard dibuat dengan Streamlit.")
