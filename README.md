# Bike Sharing Dashboard 🚲✨

Dashboard interaktif berbasis Streamlit untuk menganalisis **Bike Sharing Dataset**
(`day.csv` dan `hour.csv`, periode 2011–2012).

## Isi Folder
```
dashboard/
├── dashboard.py       # kode dashboard Streamlit
├── day.csv            # data penyewaan harian
├── hour.csv           # data penyewaan per jam
├── requirements.txt   # daftar library
├── README.md          # petunjuk ini
└── url.txt            # tautan dashboard yang sudah di-deploy
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
Pastikan terminal berada di dalam folder `dashboard`, lalu jalankan:
```
cd dashboard
streamlit run dashboard.py
```
Dashboard akan terbuka otomatis di browser (biasanya `http://localhost:8501`).
