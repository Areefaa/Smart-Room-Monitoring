# Smart Monitoring Room dengan ESP32 sebagai Client

> **Room Temperature and Humidity Monitoring Dashboard with ESP32 as Client**

Project Komunikasi Data & Jaringan Komputer yang mendemonstrasikan komunikasi client–server berbasis HTTP antara mikrokontroler ESP32 (sebagai client) dan Flask server di laptop/PC (sebagai server). ESP32 membaca data suhu & kelembaban dari sensor DHT11, lalu mengirimkannya ke server melalui HTTP POST dalam format JSON. Server menampilkannya pada dashboard web yang auto-refresh.

- Kelompok 5:
  - Vytis Rabbani Rex (23/511414/PA/21789)
  - Aufa Akmal Bunaya (23/515767/PA/22027)
  - Ahmad Firdaus Zen Omar Idrus (23/521171/PA/22406)
  - Nawal Arifah Herman (23/523349/PA/22520)
  - Ihsan Hammam (24/532900/PA/22551)

- Akun GitHub:
  - [`Rexyxy`](https://github.com/Rexyxy)
  - [`aufaakmalbunaya`](https://github.com/aufaakmalbunaya)
  - [`zenomar`](https://github.com/zenomar)
  - [`Areefaa`](https://github.com/Areefaa)
  - [`ihsadk`](https://github.com/ihsadk)

- Repository        : [`https://github.com/Areefaa/Smart-Room-Monitoring.git`](https://github.com/Areefaa/Smart-Room-Monitoring.git)

---

## 1. Deskripsi Project
Tujuan project ini adalah mengimplementasikan pola komunikasi client–server pada lingkungan IoT sederhana:
- ESP32 (Client)    : membaca suhu & kelembaban tiap 5 detik, lalu mengirim ke server.
- Laptop/PC (Server): menerima data, menyimpan riwayat di memori, dan menampilkannya di dashboard web.
- Browser           : pengguna dapat melihat data real-time di dashboard.

Project ini menunjukkan bagaimana dua perangkat berbeda (mikrokontroler dan PC) dapat bertukar data lewat jaringan WiFi dengan protokol HTTP dan payload JSON.


## 2. Tools & Komponen
### Hardware
| Komponen              | Jumlah | Keterangan |
|-----------------------|--------|------------|
| ESP32 Dev Module      | 1      | Mikrokontroler + WiFi |
| Sensor DHT11          | 1      | Suhu & kelembaban |
| Kabel jumper          | 3–4    | Female-to-female / sesuai header |
| Laptop/PC             | 1      | Menjalankan Flask server |
| Kabel USB             | 1      | ESP32 ↔ laptop (upload + serial monitor) |

### Software
- Arduino IDE
- ESP32 Board Package (via Boards Manager)
- Library DHT sensor library by Adafruit + Adafruit Unified Sensor
- Python 3.10+
- Flask ≥ 3.0
- Browser
- WiFi lokal yang sama untuk ESP32 & laptop


## 3. Arsitektur Sistem
```
┌───────────────┐   I²C/1-Wire   ┌─────────────┐    WiFi (HTTP POST + JSON)   ┌──────────────────┐     HTTP GET  ┌─────────────┐
│  DHT11 Sensor │ ─────────────▶│   ESP32      │ ───────────────────────────▶│  Flask Server    │ ◀────────────│   Browser    │
│ (Suhu & RH)   │                │  (Client)   │                              │  (Laptop / PC)   │               │ (Dashboard) │
└───────────────┘                └─────────────┘                              └──────────────────┘               └─────────────┘
                                                                                       │
                                                                                       └── menyimpan riwayat (in-memory deque)
```

Aliran data:
1. DHT11            → ESP32 (via pin GPIO4, protokol 1-Wire).
2. ESP32            → Flask server (via WiFi, HTTP POST `/sensor-data`, body JSON).
3. Flask server     → Browser (via HTTP GET `/`, render HTML dashboard dengan data terbaru).


## 4. Wiring Diagram (ESP32 ↔ DHT11)

| DHT11 Pin | ESP32 Pin    | Kabel    |
|-----------|--------------|----------|
| VCC (+)   | 3V3          | Hitam    |
| DATA (S)  | GPIO 4       | Putih    |
| GND (−)   | GND          | Abu-abu  |

> Sensor DHT11 raw (4-pin) membutuhkan tambahan resistor 10 kΩ antara `VCC` dan `DATA` sebagai pull-up.
```
Diagram ASCII:
   ESP32                          DHT11
┌──────────┐                   ┌──────────┐
│   3V3 ───┼──────── VCC ──────┤ +        │
│  GPIO4 ──┼──────── DATA ─────┤ S (data) │
│   GND ───┼──────── GND ──────┤ -        │
└──────────┘                   └──────────┘
```

## 5. Struktur Folder
```
dashboard-monitoring-esp32/
├── README.md
├── .gitignore
├── firmware/
│   └── esp32_dht11_client/
│       └── esp32_dht11_client.ino      # Kode ESP32 (client)
├── server/
│   ├── app.py                          # Flask server
│   ├── requirements.txt
│   ├── templates/
│   │   └── dashboard.html              # Dashboard UI
│   └── static/                         # (reserved untuk asset)
├── docs/
│   ├── wiring-diagram.md
│   └── tutorial.md                     # Tutorial lengkap
└── screenshots/                        # Bukti eksekusi
    └── dashboard.png                   
```

## 6. Cara Menjalankan Project
### 6.1 Persiapan di Laptop (Server)

```bash
# 1. Clone repo
git clone https://github.com/Areefaa/Smart-Room-Monitoring.git
cd dashboard-monitoring-esp32/server

# 2. Buat virtual env 
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Jalankan server
python app.py
```

Server akan listening di `http://0.0.0.0:5020`. Catat IP LAN laptop kamu:
- Windows → `ipconfig` → cari "IPv4 Address" (contoh `10.6.6.41`).
- Linux/macOS → `ip a` / `ifconfig`.

> ⚠️ Firewall Windows mungkin akan meminta izin saat pertama kali; klik Allow.

### 6.2 Persiapan di ESP32 (Client)

1. Buka Arduino IDE → File → Preferences → Additional Boards URL:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
2. Tools → Board → Boards Manager → cari `esp32` → install.
3. Tools → Manage Libraries → cari & install:
   - `DHT sensor library` by Adafruit
   - `Adafruit Unified Sensor`
4. Buka `firmware/esp32_dht11_client/esp32_dht11_client.ino`.
5. Edit tiga baris berikut sesuai lingkunganmu:
   ```cpp
   const char* WIFI_SSID     = "NAMA_WIFI_ANDA";
   const char* WIFI_PASSWORD = "PASSWORD_WIFI_ANDA";
   const char* SERVER_URL    = "http://<IP-LAPTOP>:5020/sensor-data"; // IP laptop
   ```
6. Tools → Board → pilih ESP32 Dev Module (atau board ESP32 yang sesuai).
7. Tools → Port → pilih COM yang muncul saat ESP32 ditancapkan.
8. Klik Upload (→).
9. Buka Serial Monitor (115200 baud) untuk melihat log.

### 6.3 Verifikasi
- Di serial monitor ESP32 akan muncul:
  ```
  [DHT11] Suhu: 29.5 C | Kelembaban: 70.0 %
  [HTTP] POST http://<IP-LAPTOP>:5020/sensor-data -> {"device_id":"esp32-01","temperature":29.5,"humidity":70.0}
  [HTTP] Response code: 200
  ```
- Buka browser di laptop → `http://<IP-LAPTOP>:5020/` → dashboard tampil dengan data suhu, kelembaban, dan riwayat 10 data terakhir (auto-refresh tiap 5 detik).

---

## 7. Alur Komunikasi

1. ESP32 connect ke WiFi (WPA2) menggunakan library `WiFi.h`.
2. Tiap 5 detik, ESP32 baca DHT11 (`dht.readTemperature()`, `dht.readHumidity()`).
3. ESP32 menyusun JSON dan mengirim HTTP POST ke endpoint `/sensor-data` server.
4. Flask menerima JSON, memvalidasi, menyimpan ke `deque` (riwayat max 200 entri).
5. Browser membuka `http://<IP-LAPTOP>:5020/` → Flask me-render `dashboard.html` dengan data terbaru.
6. Halaman auto-refresh tiap 5 detik via `<meta http-equiv="refresh" content="5">`.

---

## 8. Contoh API Request
### 8.1 Request dari ESP32 (JSON payload)
```json
POST /sensor-data HTTP/1.1
Host: 192.168.1.10:5020
Content-Type: application/json

{
  "device_id": "esp32-01",
  "temperature": 29.5,
  "humidity": 70
}
```

### 8.2 Response dari server

```json
{
  "status": "ok",
  "received": {
    "device_id": "esp32-01",
    "temperature": 29.5,
    "humidity": 70.0,
    "timestamp": "2025-05-07 08:55:15",
    "source_ip": "10.8.126.169"
  }
}
```

### 8.3 Uji manual dengan `curl` (tanpa ESP32)
```bash
curl -X POST http://<IP-LAPTOP>:5020/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"device_id":"manual","temperature":28.3,"humidity":65}'
```

### 8.4 Endpoint tambahan
| Endpoint         | Method | Deskripsi                                     |
|------------------|--------|-----------------------------------------------|
| `/`              | GET    | Dashboard HTML (auto-refresh 5 s)             |
| `/sensor-data`   | POST   | Terima data sensor (dipanggil ESP32)          |
| `/api/latest`    | GET    | JSON data terbaru                             |
| `/api/history`   | GET    | JSON seluruh riwayat (max 200)                |
| `/health`        | GET    | Health check                                  |

---

## 9. Testing & Troubleshooting
| Masalah                                  | Kemungkinan Penyebab                                  | Solusi                                                                 |
|------------------------------------------|-------------------------------------------------------|------------------------------------------------------------------------|
| ESP32 tidak connect WiFi                 | SSID/password salah, WiFi 5 GHz, sinyal lemah         | Cek SSID/password, pastikan WiFi **2.4 GHz** (ESP32 tidak 5 GHz)       |
| ESP32 connect tapi POST gagal            | IP server salah / beda subnet / firewall              | `ping <IP-laptop>` dari HP; matikan firewall / Allow port 5020         |
| Server tidak menerima data               | Flask tidak running, port conflict                    | Cek terminal Flask; ganti `PORT` di `app.py` jika bentrok              |
| IP laptop berubah-ubah                   | DHCP memberi IP baru tiap hari                        | Set **IP statis** di router / di pengaturan WiFi laptop                |
| DHT11 membaca `NaN`                      | Wiring longgar, VCC kurang, pull-up hilang, pin salah | Cek GPIO (pakai GPIO4), kencangkan kabel, tambah resistor 10 kΩ        |
| Dashboard tidak bisa diakses HP lain     | Flask bind ke `127.0.0.1`                             | Pastikan `app.run(host="0.0.0.0")` — sudah di-set default              |
| `[HTTP] POST gagal: connection refused`  | Port Flask belum listening, firewall blok             | Jalankan `python app.py` dulu; Allow Python di Windows Firewall        |
| Data lama terus muncul di dashboard      | Browser cache                                         | Hard-reload (Ctrl+F5)                                                  |
| Error `Board ESP32 not found`            | Boards package belum ter-install                      | Boards Manager → cari "esp32" → install                                |

---

## 10. Server Versi Stdlib (untuk Server Paten `10.6.6.41`)

Selain `server/app.py` (Flask), repo ini menyediakan **`server/server_stdlib.py`** — versi server yang **tidak butuh `pip install` apa pun**, hanya pakai modul stdlib bawaan Python (`http.server`, `json`, `collections`, `datetime`).

Versi ini dibuat khusus untuk server "paten" kelompok di IP `10.6.6.41:5020` — server tersebut tidak bisa di-install paket pip eksternal (Flask, Jinja2, dll). Untuk laptop/PC biasa silakan tetap pakai versi Flask di `app.py`.

### 10.1 Perbandingan Singkat

| Aspek          | `server/app.py` (Flask)                              | `server/server_stdlib.py` (Stdlib)                  |
|----------------|------------------------------------------------------|-----------------------------------------------------|
| Dependency     | `Flask >= 3.0` (perlu `pip install -r requirements.txt`) | **Tidak ada** — Python 3.6+ standar saja           |
| Endpoint       | Sama: `/`, `/sensor-data`, `/api/latest`, `/api/history`, `/health` | Sama persis                              |
| Template HTML  | `templates/dashboard.html` (Jinja2)                  | HTML inline di kode (`render_dashboard()` f-string) |
| Multi-client   | Flask dev server (multi-threaded by default)         | `ThreadingHTTPServer` (1 thread per request)        |
| Cocok untuk    | Laptop dev / lab                                     | Server locked / paten / tanpa akses pip             |
| Cara jalan     | `pip install -r requirements.txt && python app.py`   | `python3 server_stdlib.py`                          |

Kedua versi mendengarkan di port `5020` dan menerima format JSON yang sama dari ESP32. **ESP32 tidak perlu tahu versi mana yang aktif** — POST ke URL yang sama, hasilnya identik.

### 10.2 Penjelasan Kode `server/server_stdlib.py`

File ini berisi 251 baris dan dibagi ke 4 bagian utama: **import & konstanta**, **`render_dashboard()`**, **class `SensorHandler`**, dan **`main()`**.

#### a) Import & Konstanta
```python
import json, logging, sys
from collections import deque
from datetime import datetime, timedelta, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WIB        = timezone(timedelta(hours=7), name="WIB")
HOST       = "0.0.0.0"
PORT       = 5020
MAX_HISTORY = 200
_history: "deque[dict]" = deque(maxlen=MAX_HISTORY)
```
- **`http.server`** + **`ThreadingHTTPServer`** — modul stdlib untuk membangun HTTP server multi-thread tanpa framework eksternal.
- **`WIB`** — timezone fixed offset +7 jam. Server `10.6.6.41` jam OS-nya UTC; tanpa timezone explicit, dashboard akan tampil mundur 7 jam dari jam dinding Indonesia. Dengan `datetime.now(WIB)` kita memaksa output WIB tanpa harus mengubah setting OS server.
- **`_history`** — `deque` dengan `maxlen=200` untuk menyimpan 200 record sensor terbaru di RAM. Saat penuh, entri terlama otomatis di-drop (FIFO). Tidak persistent ke disk — restart server = data hilang (sesuai sifat demo).
- **`HOST = "0.0.0.0"`** — bind ke semua network interface, sehingga ESP32 dari LAN bisa connect. Kalau diset ke `"127.0.0.1"`, hanya localhost yang bisa connect (ESP32 ditolak).

#### b) `render_dashboard()` — menyusun HTML dashboard
Mengembalikan dashboard sebagai string HTML. Versi Flask memakai Jinja2 template `dashboard.html`; di sini HTML disusun manual dengan **f-string** Python supaya tidak butuh library template apa pun.
- Kalau `_history` kosong → tampil placeholder *"Menunggu data pertama dari ESP32..."*.
- Kalau ada data → render kartu suhu + kelembaban (font besar), meta-info (`device_id`, `timestamp`, `source_ip`, `total_records`), dan tabel 10 record terakhir.
- CSS dark-theme di-embed langsung dalam `<style>` (tidak butuh folder `static/`).
- Auto-refresh tiap 5 detik via `<meta http-equiv="refresh" content="5">`, tanpa JavaScript.
- Semua nilai user-supplied di-`escape()` untuk mencegah HTML injection.

#### c) Class `SensorHandler(BaseHTTPRequestHandler)`
Class yang menangani setiap HTTP request masuk. Mengikuti pola stdlib: satu method per HTTP verb.

**`do_GET()`** — handle GET (dashboard + read-only API):
| Path            | Response                                                |
|-----------------|---------------------------------------------------------|
| `/`             | HTML dashboard (`Content-Type: text/html`)              |
| `/api/latest`   | JSON record terbaru                                     |
| `/api/history`  | JSON list seluruh `_history` (max 200)                  |
| `/health`       | `{"status":"ok", "records": N}` — untuk monitoring     |
| lainnya         | 404 Not Found                                           |

**`do_POST()`** — handle POST dari ESP32 ke `/sensor-data`:
1. Baca header `Content-Length` untuk mengetahui ukuran body.
2. Baca body sejumlah byte itu, decode UTF-8, parse sebagai JSON.
3. Validasi field wajib: `temperature` dan `humidity` harus ada & numerik.
4. Tambah field server-side: `timestamp = datetime.now(WIB)` dan `source_ip = self.client_address[0]` (IP asal ESP32, untuk verifikasi visual di dashboard).
5. Append record ke `_history`.
6. Return JSON `{"status":"ok", "received": {...}}` dengan HTTP 200.
7. Kalau JSON malformed / field hilang → return HTTP 400 dengan pesan error yang menjelaskan apa yang salah.

**`log_message()`** di-override supaya logging tidak nge-spam stderr default `BaseHTTPRequestHandler` — dialihkan ke modul `logging` standar dengan format timestamp + level.

#### d) `main()` — entry point
```python
def main():
    server = ThreadingHTTPServer((HOST, PORT), SensorHandler)
    print(f"[BOOT] Server stdlib started at http://{HOST}:{PORT}/")
    server.serve_forever()
```
- **`ThreadingHTTPServer`** (bukan `HTTPServer` biasa) — spawn thread baru per request. Penting karena ESP32 mengirim POST tiap 5 detik **bersamaan** dengan browser yang refresh dashboard. Tanpa threading, request akan di-handle berurutan, browser bisa hang saat ESP32 sedang POST.
- **`serve_forever()`** — blocking loop, server jalan terus sampai dapat sinyal `SIGINT` / `SIGTERM` atau di-kill manual.

### 10.3 Cara Deploy ke `10.6.6.41`
```bash
# 1. Upload (pilih salah satu)
scp server/server_stdlib.py user@10.6.6.41:~/dashboard.py    # via scp
# atau via WinSCP (Windows) drag-and-drop
# atau paste manual via `nano ~/dashboard.py` di PuTTY

# 2. Login dan jalankan secara persisten
ssh user@10.6.6.41
nohup python3 ~/dashboard.py > ~/dashboard.log 2>&1 &
disown
exit

# 3. Verifikasi (dari laptop satu LAN)
curl http://10.6.6.41:5020/health
# -> {"status":"ok", "records": 0}
```

Tidak perlu `pip install`, tidak perlu virtual env, tidak perlu `sudo` — Python 3.6+ bawaan sistem sudah cukup.

Untuk akses dari jaringan luar (mis. WiFi rumah ESP32 berbeda dengan LAN UGM tempat `10.6.6.41` berada), gunakan **Tailscale Funnel** di mesin tambahan yang satu LAN dengan `10.6.6.41` — mesin itu meng-expose `10.6.6.41:5020` ke URL HTTPS publik, dan `SERVER_URL` di firmware ESP32 diarahkan ke URL tersebut.

---

## 11. Screenshot Dashboard
> _Screenshot aktual setelah demo berjalan tertera pada Repository._
![Dashboard Screenshot](screenshots/dashboard.png)

---

## 12. Riwayat Commit

Sesuai syarat tugas GitHub (ks-skj-github):

1. `Initial commit: README, .gitignore, struktur folder`
2. `Add ESP32 firmware (WiFi + DHT11 + HTTP POST JSON)`
3. `Add Flask server + dashboard HTML`
4. `Add documentation (tutorial, wiring diagram, screenshot)`

---

## 13. Kesimpulan

- Komunikasi client–server berbasis HTTP berhasil diimplementasikan antara ESP32 dan Flask.
- Sensor DHT11 dibaca setiap 5 detik oleh ESP32, lalu dikirim via WiFi dalam format JSON.
- Server Flask menyimpan riwayat dan menyajikan dashboard web yang auto-refresh.
- Syarat tugas GitHub (repo publik, README, `.gitignore`, ≥3 commits, push ke GitHub) terpenuhi.

---

## 14. Pembagian Tugas

| Nama           | Jobdesk                              |
|----------------|--------------------------------------|
| Rifa  (523349) | Project Manager, Github Repo Manager |
| Aufa  (515767) | Arsitektur Sistem, Wiring, PE        |
| Vytis (511414) | Alur Komunikasi, Firmware ESP32      |
| Ihsan (532900) | Flask Server, Dashboard Route        |
| Zeno  (521171) | Hasil Dashboard, Troubleshooting     |

---

## Lisensi

Project ini dibuat untuk keperluan pembelajaran dan dapat digunakan secara bebas.
