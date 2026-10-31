# =============================================================================
# DASHBOARD BIKE SHARING 🚲 (dengan filter interaktif)
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

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# Kode cuaca di dataset (weathersit) -> teks yang mudah dibaca
CUACA = {
    1: "Cerah / Berawan",
    2: "Berkabut / Mendung",
    3: "Hujan / Salju Ringan",
    4: "Hujan / Salju Lebat",
}

# Pilihan jenis hari -> nilai kolom workingday (1 = hari kerja, 0 = akhir pekan/libur)
# None artinya "tidak difilter" (semua hari dipakai)
PILIHAN_HARI = {"Semua Hari": None, "Hari Kerja": 1, "Akhir Pekan & Libur": 0}


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

    # Tambahkan kolom teks cuaca supaya mudah dipakai untuk filter
    day_df["weather_label"] = day_df["weathersit"].map(CUACA)
    hour_df["weather_label"] = hour_df["weathersit"].map(CUACA)
    return day_df, hour_df


def filter_umum(df, bulan_awal, bulan_akhir, cuaca_dipilih):
    """Filter yang berlaku untuk kedua pertanyaan: rentang bulan dan kondisi cuaca."""
    mask = (
        (df["mnth"] >= bulan_awal)
        & (df["mnth"] <= bulan_akhir)
        & (df["weather_label"].isin(cuaca_dipilih))
    )
    return df[mask]


def filter_jenis_hari(df, pilihan):
    """Filter hari kerja / akhir pekan & libur. Pilihan 'Semua Hari' tidak memfilter apa pun."""
    nilai = PILIHAN_HARI[pilihan]
    if nilai is None:
        return df
    return df[df["workingday"] == nilai]


# -----------------------------------------------------------------------------
# 3. BAGIAN PERTANYAAN 1
# -----------------------------------------------------------------------------
def tampilkan_pertanyaan_1(day_f, keterangan_filter):
    st.header("Pertanyaan 1")
    st.subheader("Berapa persentase pertumbuhan jumlah sewa, pengguna terdaftar, dan pengguna casual dari 2011 ke 2012?")
    st.caption(f"Filter aktif: {keterangan_filter}")

    # Jumlahkan per tahun (yr: 0 = 2011, 1 = 2012). reindex memastikan kedua tahun ada.
    total_tahun = day_f.groupby("yr")[["cnt", "registered", "casual"]].sum().reindex([0, 1])

    # Jika salah satu tahun tidak punya data, pertumbuhan tidak bisa dihitung
    if total_tahun.isna().any().any() or (total_tahun.loc[0] == 0).any():
        st.warning("Data tahun 2011 atau 2012 kosong untuk filter ini, sehingga pertumbuhan tidak bisa dihitung. "
                   "Silakan ubah filter di sidebar.")
        return

    # Jumlah hari yang ikut dihitung pada tiap tahun (untuk catatan di bawah kesimpulan)
    jumlah_hari = day_f.groupby("yr").size().reindex([0, 1])

    total_tahun.index = ["2011", "2012"]
    total_tahun.columns = ["Total Sewa", "Pengguna Terdaftar", "Pengguna Casual"]

    # Rumus pertumbuhan (%) = (nilai 2012 - nilai 2011) / nilai 2011 x 100
    pertumbuhan = (total_tahun.loc["2012"] - total_tahun.loc["2011"]) / total_tahun.loc["2011"] * 100

    # Kartu angka
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

    # Grafik kanan: persentase pertumbuhan (hijau = naik, merah = turun)
    with kanan:
        warna = [WARNA_NAIK if v >= 0 else WARNA_TURUN for v in pertumbuhan.values]
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        batang = ax.bar(pertumbuhan.index, pertumbuhan.values, color=warna)
        ax.bar_label(batang, labels=[format_persen(v) for v in pertumbuhan.values], padding=3, fontsize=10)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel("Pertumbuhan (%)")
        ax.set_title("Persentase Pertumbuhan 2011 → 2012", fontweight="bold")
        ax.margins(y=0.15)
        st.pyplot(fig)
        plt.close(fig)

    # Kesimpulan otomatis (berubah mengikuti filter)
    st.success(
        f"**Kesimpulan:** jumlah sewa berubah **{format_persen(pertumbuhan['Total Sewa'])}**. "
        f"Pengguna terdaftar berubah **{format_persen(pertumbuhan['Pengguna Terdaftar'])}** dan "
        f"pengguna casual berubah **{format_persen(pertumbuhan['Pengguna Casual'])}**. "
        f"Perubahan tertinggi ada pada kelompok **{pertumbuhan.idxmax()}**."
    )
    st.caption(
        f"Jumlah hari yang dihitung — 2011: {int(jumlah_hari[0])} hari, 2012: {int(jumlah_hari[1])} hari. "
        f"Jika jumlah harinya berbeda jauh (misalnya karena filter cuaca), persentase perubahan ikut terpengaruh."
    )

    with st.expander("Lihat tabel perhitungan"):
        tabel = total_tahun.T.copy()
        tabel["Pertumbuhan (%)"] = pertumbuhan.round(2)
        st.dataframe(tabel)


# -----------------------------------------------------------------------------
# 4. BAGIAN PERTANYAAN 2
# -----------------------------------------------------------------------------
def tampilkan_pertanyaan_2(hour_f, tahun, tipe_hari, keterangan_filter):
    st.header("Pertanyaan 2")
    st.subheader(
        f"Pada {tipe_hari.lower()} tahun {tahun}, pada jam berapa rata-rata penyewaan "
        f"mulai meningkat dibanding jam sebelumnya?"
    )
    st.caption(f"Filter aktif: {keterangan_filter}")

    if hour_f.empty:
        st.warning("Tidak ada data untuk filter ini. Silakan ubah filter di sidebar.")
        return

    # Rata-rata sewa per jam. reindex(range(24)) memastikan semua jam 0-23 ada
    # (jam yang tidak punya data diisi NaN / kosong).
    rata_per_jam = hour_f.groupby("hr")["cnt"].mean().reindex(range(24))

    # Selisih rata-rata dibanding jam sebelumnya (jam 0 tidak punya jam sebelumnya)
    selisih = rata_per_jam.diff()

    # Jam dengan rata-rata terendah (titik dasar)
    jam_terendah = int(rata_per_jam.idxmin())

    # Jam pertama setelah titik terendah yang nilainya naik dibanding jam sebelumnya
    kandidat = selisih[(selisih.index > jam_terendah) & (selisih > 0)]
    jam_mulai_naik = int(kandidat.index[0]) if len(kandidat) > 0 else None

    # Jam dengan lonjakan terbesar dibanding jam sebelumnya
    jam_lonjakan = int(selisih.idxmax()) if selisih.notna().any() else None

    # Hitung sampai jam berapa kenaikan berlanjut tanpa putus
    jam_akhir_naik = jam_mulai_naik
    if jam_mulai_naik is not None:
        while jam_akhir_naik + 1 in selisih.index and selisih[jam_akhir_naik + 1] > 0:
            jam_akhir_naik += 1

    kiri, kanan = st.columns(2)

    # Grafik kiri: rata-rata penyewaan per jam
    with kiri:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(rata_per_jam.index, rata_per_jam.values, marker="o", color=WARNA_2012, linewidth=2.5)
        if jam_mulai_naik is not None:
            ax.axvline(jam_mulai_naik, color=WARNA_NAIK, linestyle="--", label=f"Mulai naik: jam {jam_mulai_naik:02d}.00")
            ax.legend()
        ax.set_xticks(range(0, 24))
        ax.set_xlabel("Jam (0-23)")
        ax.set_ylabel("Rata-rata penyewaan")
        ax.set_title(f"Rata-rata Penyewaan per Jam ({tipe_hari} {tahun})", fontweight="bold")
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

    # Kesimpulan otomatis (berubah mengikuti filter)
    if jam_mulai_naik is None:
        st.info(f"Titik terendah ada pada pukul {jam_terendah:02d}.00, dan tidak ada kenaikan setelahnya "
                f"pada data terpilih.")
    else:
        st.success(
            f"**Kesimpulan:** titik terendah ada pada pukul **{jam_terendah:02d}.00** "
            f"({rata_per_jam[jam_terendah]:.1f} sewa/jam). Rata-rata penyewaan **mulai meningkat pada pukul "
            f"{jam_mulai_naik:02d}.00** ({selisih[jam_mulai_naik]:+.1f} dibanding jam sebelumnya), lalu terus naik "
            f"sampai pukul **{jam_akhir_naik:02d}.00**. Lonjakan terbesar dibanding jam sebelumnya terjadi pada "
            f"pukul **{jam_lonjakan:02d}.00** ({selisih[jam_lonjakan]:+.1f})."
        )
        jam_berikutnya = jam_mulai_naik + 1
        if jam_berikutnya in selisih.index and pd.notna(selisih[jam_berikutnya]):
            st.caption(
                f"Catatan: kenaikan pada pukul {jam_mulai_naik:02d}.00 sebesar {selisih[jam_mulai_naik]:+.1f}. "
                f"Pada pukul {jam_berikutnya:02d}.00 perubahannya {selisih[jam_berikutnya]:+.1f}."
            )

    with st.expander("Lihat tabel per jam"):
        tabel_jam = pd.DataFrame({
            "Jam": [f"{j:02d}.00" for j in rata_per_jam.index],
            "Rata-rata Sewa": rata_per_jam.round(1).values,
            "Selisih dari Jam Sebelumnya": selisih.round(1).values,
        })
        st.dataframe(tabel_jam)


# -----------------------------------------------------------------------------
# 5. MUAT DATA
# -----------------------------------------------------------------------------
day_df, hour_df = muat_data()

# -----------------------------------------------------------------------------
# 6. SIDEBAR (FILTER INTERAKTIF)
# Setiap kali pengguna mengubah filter, Streamlit menjalankan ulang file ini
# dari atas, sehingga semua grafik otomatis ikut berubah.
# -----------------------------------------------------------------------------
st.sidebar.header("🔎 Filter Data")

# --- Filter umum: berlaku untuk Pertanyaan 1 dan 2 ---
st.sidebar.subheader("Filter Umum")
bulan_awal_nama, bulan_akhir_nama = st.sidebar.select_slider(
    "Rentang Bulan",
    options=BULAN,
    value=(BULAN[0], BULAN[-1]),
)
bulan_awal = BULAN.index(bulan_awal_nama) + 1    # "Jan" -> 1
bulan_akhir = BULAN.index(bulan_akhir_nama) + 1  # "Des" -> 12

cuaca_dipilih = st.sidebar.multiselect(
    "Kondisi Cuaca",
    options=list(CUACA.values()),
    default=list(CUACA.values()),
)
st.sidebar.caption("Kategori 'Hujan / Salju Lebat' hanya ada pada data per jam (hour.csv).")

# --- Filter khusus Pertanyaan 1 ---
st.sidebar.subheader("Khusus Pertanyaan 1")
hari_p1 = st.sidebar.radio("Jenis Hari", list(PILIHAN_HARI.keys()), index=0, key="hari_p1")

# --- Filter khusus Pertanyaan 2 ---
st.sidebar.subheader("Khusus Pertanyaan 2")
tahun_p2 = st.sidebar.radio("Tahun", ["2011", "2012"], index=1, key="tahun_p2")
hari_p2 = st.sidebar.radio("Jenis Hari", list(PILIHAN_HARI.keys()), index=1, key="hari_p2")

st.sidebar.markdown("---")
st.sidebar.caption("Untuk mengembalikan semua filter ke awal, muat ulang halaman (F5).")

# Jika semua cuaca dihapus, tidak ada data yang bisa ditampilkan
if not cuaca_dipilih:
    st.title("🚲 Bike Sharing Dashboard")
    st.warning("Pilih minimal satu kondisi cuaca di sidebar.")
    st.stop()

# -----------------------------------------------------------------------------
# 7. TERAPKAN FILTER KE DATA
# -----------------------------------------------------------------------------
# Pertanyaan 1 memakai data harian (day.csv)
day_f = filter_umum(day_df, bulan_awal, bulan_akhir, cuaca_dipilih)
day_f = filter_jenis_hari(day_f, hari_p1)

# Pertanyaan 2 memakai data per jam (hour.csv)
hour_f = filter_umum(hour_df, bulan_awal, bulan_akhir, cuaca_dipilih)
hour_f = hour_f[hour_f["yr"] == int(tahun_p2) - 2011]   # 2011 -> 0, 2012 -> 1
hour_f = filter_jenis_hari(hour_f, hari_p2)

# Keterangan singkat filter yang sedang aktif (ditampilkan di bawah judul tiap pertanyaan)
ket_umum = f"bulan {bulan_awal_nama}–{bulan_akhir_nama}, {len(cuaca_dipilih)} dari {len(CUACA)} kategori cuaca"

# -----------------------------------------------------------------------------
# 8. TAMPILKAN DASHBOARD
# -----------------------------------------------------------------------------
st.title("🚲 Bike Sharing Dashboard")
st.markdown(
    "Dashboard ini menjawab dua pertanyaan bisnis berdasarkan data penyewaan sepeda 2011–2012. "
    "Gunakan **filter di sidebar** (sebelah kiri) untuk menjelajahi data."
)
st.markdown("---")

tampilkan_pertanyaan_1(day_f, f"{ket_umum}, {hari_p1.lower()}")
st.markdown("---")
tampilkan_pertanyaan_2(hour_f, tahun_p2, hari_p2, f"{ket_umum}, {hari_p2.lower()} tahun {tahun_p2}")

st.caption("Sumber data: Bike Sharing Dataset (Kaggle) • Dashboard dibuat dengan Streamlit.")