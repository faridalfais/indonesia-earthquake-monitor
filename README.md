Indonesia Earthquake Monitor
Interactive dashboard untuk melihat dan menganalisis data gempa BMKG.
Project
	
Source	BMKG
Language	Python
Dashboard	Streamlit
Data	Earthquake records
Visualization	Plotly, PyDeck
Deployment	Streamlit Cloud


Alur pengerjaan
BMKG Data
   ↓
Requests
   ↓
Pandas
   ↓
Cleaning & Processing
   ↓
Analysis
   ↓
Charts + Map
   ↓
Streamlit Dashboard
Yang dianalisis
- Jumlah gempa berdasarkan waktu
- Distribusi magnitude
- Kedalaman gempa
- Aktivitas berdasarkan wilayah
- Lokasi gempa pada peta
- Status tsunami
Dashboard
Filter → Map → Charts → Data Table
Pengguna bisa memilih periode, magnitude minimum, wilayah, dan status tsunami untuk melihat data yang sesuai.
Hasil
Data gempa yang awalnya berupa data mentah BMKG diubah menjadi dashboard interaktif yang bisa digunakan untuk eksplorasi data tanpa perlu membuka atau menjalankan kode Python.
Stack: Python · Pandas · NumPy · Requests · Plotly · PyDeck · Streamlit · GitHub
