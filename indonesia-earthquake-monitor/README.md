# Indonesia Earthquake Monitor

Dashboard analitik gempa bumi Indonesia berbasis data resmi **BMKG** (Badan Meteorologi, Klimatologi, dan Geofisika).

Dibuat sebagai proyek portofolio Data Analyst / Python.

---

## Fitur

| Fitur | Keterangan |
|-------|------------|
| **Data BMKG real-time** | Mengambil data dari tiga endpoint resmi BMKG secara otomatis |
| **KPI Cards** | Total kejadian, magnitudo terbesar, rata-rata kedalaman, potensi tsunami |
| **Peta interaktif** | PyDeck ScatterplotLayer – ukuran sesuai magnitudo, warna sesuai status tsunami |
| **Filter dinamis** | Magnitudo minimum, rentang tanggal, status tsunami |
| **6 grafik analitik** | Aktivitas waktu, distribusi magnitudo, aktivitas wilayah, distribusi kedalaman, magnitudo vs kedalaman, status tsunami |
| **Tabel data** | Tabel gempa terbaru dan tabel data lengkap yang dapat difilter |
| **Auto-refresh** | Data diperbarui otomatis setiap 5 menit |
| **Error handling** | Graceful error saat BMKG tidak dapat dijangkau |

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** – framework dashboard
- **Pandas / NumPy** – pemrosesan dan analisis data
- **Requests** – HTTP client untuk BMKG API
- **Plotly** – grafik interaktif
- **PyDeck** – peta 3D berbasis WebGL

---

## Struktur Proyek

```
indonesia-earthquake-monitor/
├── app.py                  # Aplikasi utama Streamlit
├── requirements.txt        # Dependensi Python
├── README.md
├── .gitignore
│
├── data/
│   └── README.md           # Catatan tentang data
│
├── src/
│   ├── __init__.py
│   ├── bmkg_api.py         # Fetcher & cache BMKG API
│   ├── data_processing.py  # Normalisasi DataFrame
│   ├── analysis.py         # Fungsi statistik & analitik
│   ├── charts.py           # Komponen grafik Plotly
│   ├── map.py              # Peta PyDeck
│   └── ui.py               # Komponen UI Streamlit
│
└── .streamlit/
    └── config.toml         # Konfigurasi tema Streamlit
```

---

## Instalasi

```bash
# Clone / unduh proyek
git clone <repo-url>
cd indonesia-earthquake-monitor

# Buat virtual environment (disarankan)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# Instal dependensi
pip install -r requirements.txt
```

---

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Buka browser di: `http://localhost:8501`

---

## Sumber Data BMKG

Data diambil dari tiga endpoint resmi BMKG Open Data:

| Endpoint | Keterangan |
|----------|------------|
| `autogempa.json` | Satu gempa terbaru yang signifikan |
| `gempaterkini.json` | 15 gempa M≥5.0 terbaru |
| `gempadirasakan.json` | 15 gempa yang dirasakan terbaru |

Base URL: `https://data.bmkg.go.id/DataMKG/TEWS/`

---

## Keterbatasan Data

- BMKG hanya menyediakan **~15 rekaman terbaru** per endpoint (bukan data historis penuh)
- Kolom `Potensi` (status tsunami) hanya tersedia di endpoint `gempaterkini`
- Data ini **tidak cocok untuk keputusan darurat** — selalu ikuti instruksi resmi BMKG
- Dashboard memperbarui data setiap ±5 menit; bukan real-time sepenuhnya

---

## Tujuan Portofolio

Proyek ini mendemonstrasikan:
- Konsumsi REST API publik dan penanganan error yang robust
- Normalisasi dan pembersihan data JSON → Pandas DataFrame
- Analisis data eksploratif (EDA) dengan Pandas/NumPy
- Visualisasi data interaktif dengan Plotly dan PyDeck
- Pembuatan dashboard profesional dengan Streamlit
- Arsitektur kode modular dan mudah dipelihara

---

## Lisensi

MIT — bebas digunakan untuk tujuan pribadi dan portofolio.

Attribution: Data © BMKG Republik Indonesia.
