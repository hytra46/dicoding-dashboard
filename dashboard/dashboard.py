# =============================================================================
# DASHBOARD BIKE SHARING 🚲
# Menjawab 2 pertanyaan bisnis:
#   1. Berapa persen pertumbuhan jumlah sewa, pengguna registered, dan pengguna
#      casual dari tahun 2011 ke 2012?
#   2. Pada hari kerja tahun 2012, jam berapa rata-rata penyewaan mulai
#      meningkat dibandingkan jam sebelumnya?
#
# Cara menjalankan:  streamlit run dashboard.py
# =============================================================================

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PENGATURAN DASAR
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

# Lokasi folder tempat dashboard.py berada (supaya file csv selalu ketemu)
BASE_DIR = Path(__file__).parent

WARNA_2011 = "#4C72B0"   # biru
WARNA_2012 = "#DD8452"   # oranye
WARNA_NAIK = "#2E8B57"   # hijau
WARNA_TURUN = "#CD5C5C"  # merah


# -----------------------------------------------------------------------------
# 2. FUNGSI BANTU
# -----------------------------------------------------------------------------
def format_angka(nilai):
    """Ubah 1234567 menjadi '1.234.567' (format Indonesia)."""
    return f"{nilai:,.0f}".replace(",", ".")


def format_persen(nilai, tanda=True):
    """Ubah 64.883 menjadi '+64,88%' (koma sebagai pemisah desimal)."""
    teks = f"{nilai:+.2f}%" if tanda else f"{nilai:.2f}%"
    return teks.replace(".", ",")


@st.cache_data
def muat_data():
    """Baca day.csv dan hour.csv. Hasilnya disimpan di cache agar dashboard cepat."""
    day_df = pd.read_csv(BASE_DIR / "day.csv")
    hour_df = pd.read_csv(BASE_DIR / "hour.csv")
    return day_df, hour_df


# -----------------------------------------------------------------------------
# 3. SIAPKAN DATA
# -----------------------------------------------------------------------------
day_df, hour_df = muat_data()

# --- Pertanyaan 1: total sewa per tahun (yr: 0 = 2011, 1 = 2012) ---------------
total_tahun = day_df.groupby("yr")[["cnt", "registered", "casual"]].sum()
total_tahun.index = ["2011", "2012"]
total_tahun.columns = ["Total Sewa", "Pengguna Terdaftar", "Pengguna Casual"]

# Rumus pertumbuhan (%) = (nilai 2012 - nilai 2011) / nilai 2011 x 100
pertumbuhan = (total_tahun.loc["2012"] - total_tahun.loc["2011"]) / total_tahun.loc["2011"] * 100

# --- Pertanyaan 2: rata-rata sewa per jam, hari kerja, tahun 2012 --------------
data_2012_kerja = hour_df[(hour_df["yr"] == 1) & (hour_df["workingday"] == 1)]
rata_per_jam = data_2012_kerja.groupby("hr")["cnt"].mean()

# Selisih rata-rata dibanding jam sebelumnya (jam 0 tidak punya jam sebelumnya)
selisih = rata_per_jam.diff()

# Jam terendah (dasar), lalu jam pertama setelahnya yang nilainya naik
jam_terendah = int(rata_per_jam.idxmin())
jam_mulai_naik = jam_terendah + 1  # jam setelah titik terendah

# Hitung berapa jam berturut-turut kenaikan berlanjut sejak jam_mulai_naik
jam_akhir_naik = jam_mulai_naik
while jam_akhir_naik + 1 in selisih.index and selisih[jam_akhir_naik + 1] > 0:
    jam_akhir_naik += 1

# Jam dengan lonjakan terbesar dibanding jam sebelumnya
jam_lonjakan = int(selisih.idxmax())

# -----------------------------------------------------------------------------
# 4. JUDUL
# -----------------------------------------------------------------------------
st.title("🚲 Bike Sharing Dashboard")
st.markdown("Dashboard ini menjawab dua pertanyaan bisnis berdasarkan data penyewaan sepeda 2011–2012.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 5. PERTANYAAN 1: PERTUMBUHAN 2011 -> 2012
# -----------------------------------------------------------------------------
st.header("Pertanyaan 1")
st.subheader("Berapa persentase pertumbuhan jumlah sewa, pengguna terdaftar, dan pengguna casual dari 2011 ke 2012?")

kolom = st.columns(3)
for tempat, nama in zip(kolom, total_tahun.columns):
    tempat.metric(
        label=f"{nama} (2012)",
        value=format_angka(total_tahun.loc["2012", nama]),
        delta=f"{format_persen(pertumbuhan[nama])} dari 2011",
    )

kiri, kanan = st.columns(2)

# Grafik kiri: perbandingan jumlah 2011 vs 2012
with kiri:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    posisi = range(len(total_tahun.columns))
    lebar = 0.38
    batang_2011 = ax.bar([p - lebar / 2 for p in posisi], total_tahun.loc["2011"], lebar, label="2011", color=WARNA_2011)
    batang_2012 = ax.bar([p + lebar / 2 for p in posisi], total_tahun.loc["2012"], lebar, label="2012", color=WARNA_2012)
    ax.bar_label(batang_2011, labels=[format_angka(v) for v in total_tahun.loc["2011"]], padding=3, fontsize=8)
    ax.bar_label(batang_2012, labels=[format_angka(v) for v in total_tahun.loc["2012"]], padding=3, fontsize=8)
    ax.set_xticks(list(posisi))
    ax.set_xticklabels(total_tahun.columns)
    ax.set_ylabel("Jumlah penyewaan")
    ax.set_title("Jumlah Penyewaan 2011 vs 2012", fontweight="bold")
    ax.ticklabel_format(axis="y", style="plain")
    ax.margins(y=0.12)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

# Grafik kanan: persentase pertumbuhan
with kanan:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    batang = ax.bar(pertumbuhan.index, pertumbuhan.values, color=WARNA_NAIK)
    ax.bar_label(batang, labels=[format_persen(v) for v in pertumbuhan.values], padding=3, fontsize=10)
    ax.set_ylabel("Pertumbuhan (%)")
    ax.set_title("Persentase Pertumbuhan 2011 → 2012", fontweight="bold")
    ax.margins(y=0.15)
    st.pyplot(fig)
    plt.close(fig)

# Kesimpulan otomatis
tertinggi = pertumbuhan.idxmax()
st.success(
    f"**Kesimpulan:** jumlah sewa tumbuh **{format_persen(pertumbuhan['Total Sewa'], tanda=False)}**. "
    f"Pengguna terdaftar tumbuh **{format_persen(pertumbuhan['Pengguna Terdaftar'], tanda=False)}** dan "
    f"pengguna casual tumbuh **{format_persen(pertumbuhan['Pengguna Casual'], tanda=False)}**. "
    f"Pertumbuhan tertinggi ada pada kelompok **{tertinggi}**."
)

with st.expander("Lihat tabel perhitungan"):
    tabel = total_tahun.T.copy()
    tabel["Pertumbuhan (%)"] = pertumbuhan.round(2)
    st.dataframe(tabel)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. PERTANYAAN 2: JAM MULAI NAIK PADA HARI KERJA 2012
# -----------------------------------------------------------------------------
st.header("Pertanyaan 2")
st.subheader("Pada hari kerja tahun 2012, pada jam berapa rata-rata penyewaan mulai meningkat dibanding jam sebelumnya?")

kiri, kanan = st.columns(2)

# Grafik kiri: rata-rata penyewaan per jam
with kiri:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(rata_per_jam.index, rata_per_jam.values, marker="o", color=WARNA_2012, linewidth=2.5)
    ax.axvline(jam_mulai_naik, color=WARNA_NAIK, linestyle="--", label=f"Mulai naik: jam {jam_mulai_naik:02d}.00")
    ax.set_xticks(range(0, 24))
    ax.set_xlabel("Jam (0-23)")
    ax.set_ylabel("Rata-rata penyewaan")
    ax.set_title("Rata-rata Penyewaan per Jam (Hari Kerja 2012)", fontweight="bold")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

# Grafik kanan: selisih dibanding jam sebelumnya (hijau = naik, merah = turun)
with kanan:
    selisih_valid = selisih.dropna()
    warna = [WARNA_NAIK if v > 0 else WARNA_TURUN for v in selisih_valid.values]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(selisih_valid.index, selisih_valid.values, color=warna)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(0, 24))
    ax.set_xlabel("Jam (0-23)")
    ax.set_ylabel("Selisih dibanding jam sebelumnya")
    ax.set_title("Perubahan dari Jam Sebelumnya (Hijau = Naik)", fontweight="bold")
    st.pyplot(fig)
    plt.close(fig)

# Kesimpulan otomatis
st.success(
    f"**Kesimpulan:** titik terendah ada pada pukul **{jam_terendah:02d}.00** "
    f"({rata_per_jam[jam_terendah]:.1f} sewa/jam). Rata-rata penyewaan **mulai meningkat pada pukul "
    f"{jam_mulai_naik:02d}.00** ({selisih[jam_mulai_naik]:+.1f} dibanding jam sebelumnya), lalu terus naik "
    f"sampai pukul **{jam_akhir_naik:02d}.00**. Lonjakan terbesar dibanding jam sebelumnya terjadi pada "
    f"pukul **{jam_lonjakan:02d}.00** ({selisih[jam_lonjakan]:+.1f})."
)

st.caption(
    f"Catatan: kenaikan pada pukul {jam_mulai_naik:02d}.00 masih sangat kecil ({selisih[jam_mulai_naik]:+.1f}). "
    f"Kenaikan yang jelas terlihat pada pukul {jam_mulai_naik + 1:02d}.00 ({selisih[jam_mulai_naik + 1]:+.1f}) "
    f"dan setelahnya."
)

with st.expander("Lihat tabel per jam"):
    tabel_jam = pd.DataFrame({
        "Jam": [f"{j:02d}.00" for j in rata_per_jam.index],
        "Rata-rata Sewa": rata_per_jam.round(1).values,
        "Selisih dari Jam Sebelumnya": selisih.round(1).values,
    })
    st.dataframe(tabel_jam)

st.caption("Sumber data: Bike Sharing Dataset (Kaggle) • Dashboard dibuat dengan Streamlit.")
