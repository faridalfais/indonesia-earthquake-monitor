# Data Directory

Data dalam proyek ini diambil secara langsung dari API resmi BMKG saat runtime.
Tidak ada file data statis yang disimpan di direktori ini.

## Endpoints

- `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json`
- `https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json`
- `https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json`

Data di-cache secara in-memory oleh Streamlit selama 5 menit untuk mengurangi
beban pada server BMKG.
