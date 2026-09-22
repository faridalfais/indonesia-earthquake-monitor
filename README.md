# Indonesia Earthquake Monitor

Interactive dashboard untuk melihat dan menganalisis data gempa bumi berdasarkan data BMKG.

## Project Overview

| | |
|---|---|
| **Data Source** | BMKG |
| **Language** | Python |
| **Dashboard** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Plotly, PyDeck |
| **API Request** | Requests |
| **Deployment** | Streamlit Community Cloud |

## Tujuan

Project ini dibuat untuk mengolah data gempa BMKG menjadi dashboard yang lebih mudah digunakan untuk melihat aktivitas gempa berdasarkan waktu, magnitude, kedalaman, wilayah, dan lokasi.

## Data Workflow

**BMKG → Data Collection → Data Cleaning → Data Processing → Analysis → Visualization → Dashboard**

## Analisis

Dashboard menyediakan beberapa analisis:

- Jumlah gempa berdasarkan waktu
- Distribusi magnitude
- Distribusi kedalaman
- Aktivitas berdasarkan wilayah
- Lokasi gempa pada peta
- Status tsunami

## Dashboard

Dashboard dilengkapi dengan:

- Filter tanggal
- Filter minimum magnitude
- Filter wilayah
- Filter status tsunami
- Interactive earthquake map
- Charts
- Data table

## Tech Stack

- Python
- Pandas
- NumPy
- Requests
- Plotly
- PyDeck
- Streamlit

## Project Structure

```text
indonesia-earthquake-monitor/
├── app.py
├── requirements.txt
├── README.md
├── data/
├── src/
│   ├── bmkg_api.py
│   ├── data_processing.py
│   ├── analysis.py
│   ├── charts.py
│   ├── map.py
│   └── ui.py
└── .streamlit/
    └── config.toml
