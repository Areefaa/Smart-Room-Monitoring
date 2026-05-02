# Tutorial Lengkap — Dashboard Monitoring Ruangan (ESP32 + DHT11 + Flask)

Tutorial ini memandu kamu dari nol sampai dashboard berjalan, untuk tugas mata kuliah **Komunikasi Data & Jaringan Komputer** (Kelompok 5, Project Manager **Nawal Arifah**, akun GitHub **`aufaakmalbunaya`**).

---

## 1. Konsep Client–Server di Project Ini

| Peran    | Perangkat                  | Bahasa/Library                         | Tugas utama |
|----------|----------------------------|----------------------------------------|-------------|
| **Client** | ESP32 + DHT11            | Arduino C++ (`WiFi.h`, `HTTPClient.h`, `DHT.h`) | Baca sensor → kirim HTTP POST ke server |
| **Server** | Laptop/PC                | Python + Flask                         | Terima data → simpan → tampilkan dashboard |
| **Viewer** | Browser (PC/HP)          | HTML + CSS                             | Melihat dashboard |

**Protokol**: HTTP 1.1 · **Port**: 5020 · **Format payload**: JSON · **Jaringan**: WiFi 2.4 GHz yang sama untuk client & server.

---

## 2. Arsitektur Sistem

```
DHT11  →  ESP32 (Client)  →  WiFi Router  →  Laptop Flask (Server)  →  Browser (Dashboard)
```

**Detail per-tahap:**
1. **DHT11 → ESP32**: protokol 1-Wire pada GPIO 4.
2. **ESP32 → Server**: TCP/IP → HTTP POST `/sensor-data` dengan body JSON.
3. **Server → Browser**: HTTP GET `/` → response HTML (auto-refresh 5 s).

---

## 3. Wiring ESP32 ↔ DHT11

| DHT11 | ESP32  |
|-------|--------|
| VCC   | 3V3    |
| DATA  | GPIO 4 |
| GND   | GND    |

Detail: [`wiring-diagram.md`](wiring-diagram.md).

---

## 4. Menyiapkan Software di Laptop

### 4.1 Python & Flask

**Windows (PowerShell):**
```powershell
# Pastikan Python 3.10+ terpasang
python --version

# Masuk folder server
cd dashboard-monitoring-esp32\server

# Buat virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install Flask
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
cd dashboard-monitoring-esp32/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Jalankan Server

```bash
python app.py
```

Output yang diharapkan:
```
Dashboard Monitoring berjalan di http://0.0.0.0:5020
  Dashboard  : http://<IP-LAPTOP>:5020/
  ESP32 POST : http://<IP-LAPTOP>:5020/sensor-data
 * Running on http://0.0.0.0:5020
```

Biarkan terminal ini tetap terbuka — server harus tetap jalan selama ESP32 mengirim data.

### 4.3 Cek IP LAN Laptop

- **Windows**: `ipconfig` → cari "IPv4 Address" di adapter WiFi.
- **Linux/macOS**: `ip addr` atau `ifconfig`.

Catat IP ini (contoh: `192.168.1.10`). Angka ini yang akan dipakai di kode ESP32.

### 4.4 Izinkan di Firewall (Windows)

Saat pertama kali Python/Flask dibuka, Windows akan menampilkan prompt **"Allow access"** — pilih **Private network** dan **Allow**. Jika tidak muncul, buka:
```
Control Panel → System and Security → Windows Defender Firewall → Allow an app
→ cari "Python" → centang "Private"
```

---

## 5. Menyiapkan Arduino IDE untuk ESP32

### 5.1 Install Board Package

1. Buka **Arduino IDE 2.x**.
2. **File → Preferences** → **Additional Boards Manager URLs**:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. **Tools → Board → Boards Manager** → cari `esp32` → klik **Install** pada "esp32 by Espressif Systems".

### 5.2 Install Library Sensor

**Tools → Manage Libraries**, cari & install:
- **DHT sensor library** by Adafruit (latest)
- **Adafruit Unified Sensor** (dependency otomatis)

### 5.3 Buka Sketch

Buka file `firmware/esp32_dht11_client/esp32_dht11_client.ino` di Arduino IDE.

### 5.4 Edit Konfigurasi

Tiga baris berikut **WAJIB** diganti:

```cpp
const char* WIFI_SSID     = "NAMA_WIFI_ANDA";
const char* WIFI_PASSWORD = "PASSWORD_WIFI_ANDA";
const char* SERVER_URL    = "http://192.168.1.10:5020/sensor-data"; // IP laptop
```

> ⚠️ ESP32 hanya bisa connect ke WiFi **2.4 GHz** (bukan 5 GHz). Jika routermu dual-band, gunakan SSID 2.4 GHz-nya.

### 5.5 Pilih Board & Port

- **Tools → Board → ESP32 Arduino → ESP32 Dev Module**
- **Tools → Port** → COMx (Windows) atau `/dev/ttyUSB0` (Linux) — yang muncul saat ESP32 dicolok.

Jika port tidak muncul, install driver **CP210x** (Silabs) atau **CH340** (tergantung chip USB ESP32-mu).

### 5.6 Upload

1. Klik tombol **Upload** (→).
2. Jika macet di `Connecting....`, tekan tombol **BOOT** pada ESP32 sampai upload mulai jalan.
3. Tunggu sampai "Leaving..." / "Hard resetting via RTS pin".

### 5.7 Buka Serial Monitor

- **Tools → Serial Monitor**
- Pilih baud rate **115200**.
- Output yang diharapkan:
  ```
  === ESP32 DHT11 Client ===
  Menghubungkan ke WiFi: MyWiFi ...
  ....
  Terhubung. IP ESP32: 192.168.1.42
  [DHT11] Suhu: 29.5 C | Kelembaban: 70.0 %
  [HTTP] POST http://192.168.1.10:5020/sensor-data -> {"device_id":"esp32-01","temperature":29.5,"humidity":70.0}
  [HTTP] Response code: 200
  [HTTP] Response body: {"received":{"device_id":"esp32-01","humidity":70.0,...},"status":"ok"}
  ```

---

## 6. Alur Komunikasi (End-to-End)

```
ESP32                            Flask Server                        Browser
  │                                    │                                │
  │  (5 detik sekali)                  │                                │
  │  baca DHT11 → suhu, RH              │                                │
  │                                    │                                │
  │  POST /sensor-data + JSON          │                                │
  │──────────────────────────────────▶│                                │
  │                                    │  validasi JSON                 │
  │                                    │  simpan ke deque (max 200)     │
  │  200 OK + {status:"ok"}             │                                │
  │◀──────────────────────────────────│                                │
  │                                    │                                │
  │                                    │      GET /                     │
  │                                    │◀───────────────────────────────│
  │                                    │  render dashboard.html         │
  │                                    │───────────────────────────────▶│
  │                                    │                                │
  │  (loop selama 5 detik)             │                                │  (auto-refresh 5 s)
```

---

## 7. Contoh JSON yang Dikirim ESP32

```json
{
  "device_id": "esp32-01",
  "temperature": 29.5,
  "humidity": 70
}
```

Response server:
```json
{
  "status": "ok",
  "received": {
    "device_id": "esp32-01",
    "temperature": 29.5,
    "humidity": 70.0,
    "timestamp": "2025-05-01 10:30:15",
    "source_ip": "192.168.1.42"
  }
}
```

---

## 8. Testing Tanpa Hardware (Simulasi)

Jika ESP32 belum tersedia, kamu bisa simulasikan client dengan `curl`:

```bash
# POST tunggal
curl -X POST http://localhost:5020/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"device_id":"sim","temperature":28.3,"humidity":65}'

# Loop 20× tiap 3 detik (Bash)
for i in {1..20}; do
  T=$(python -c "import random;print(round(random.uniform(26,32),1))")
  H=$(python -c "import random;print(round(random.uniform(55,80),1))")
  curl -s -X POST http://localhost:5020/sensor-data \
    -H "Content-Type: application/json" \
    -d "{\"device_id\":\"sim\",\"temperature\":$T,\"humidity\":$H}"
  echo
  sleep 3
done
```

**Windows PowerShell:**
```powershell
1..20 | ForEach-Object {
  $t = [math]::Round((Get-Random -Min 26.0 -Max 32.0),1)
  $h = [math]::Round((Get-Random -Min 55.0 -Max 80.0),1)
  $body = @{device_id="sim"; temperature=$t; humidity=$h} | ConvertTo-Json
  Invoke-RestMethod -Uri http://localhost:5020/sensor-data -Method Post -Body $body -ContentType 'application/json'
  Start-Sleep -Seconds 3
}
```

---

## 9. Troubleshooting

Lihat tabel lengkap di [`../README.md` bagian 9](../README.md#9-testing--troubleshooting). Ringkasan paling sering:

1. **ESP32 tidak connect WiFi** → pastikan **2.4 GHz**, SSID/password benar.
2. **POST gagal** → cek `ping <IP-laptop>` dari HP; Allow Python di firewall.
3. **DHT11 NaN** → wiring longgar, pin salah, atau pull-up hilang.
4. **IP laptop berubah** → set IP statis atau update `SERVER_URL` di sketch tiap hari.
5. **Dashboard kosong** → ESP32 belum kirim; cek serial monitor.

---

## 10. Push ke GitHub (syarat tugas)

```bash
cd dashboard-monitoring-esp32
git init
git add README.md .gitignore
git commit -m "Initial commit: README, .gitignore, struktur folder"

git add firmware/
git commit -m "Add ESP32 firmware (WiFi + DHT11 + HTTP POST JSON)"

git add server/
git commit -m "Add Flask server + dashboard HTML"

git add docs/ screenshots/
git commit -m "Add documentation (tutorial, wiring diagram, screenshot)"

# Buat repo di github.com (Public, jangan init README)
git remote add origin https://github.com/aufaakmalbunaya/dashboard-monitoring-esp32.git
git branch -M main
git push -u origin main
# Saat ditanya password → paste Personal Access Token (PAT), bukan password akun.
```

**Checklist tugas GitHub:**
- [x] Repo public
- [x] README.md lengkap
- [x] .gitignore ada
- [x] ≥ 3 commits dengan pesan deskriptif
- [x] Push berhasil — tampil di browser

---

## 11. Pengembangan Lanjutan

- Simpan data ke **SQLite** agar tidak hilang saat server restart.
- Tambah **grafik real-time** (Chart.js) di dashboard.
- Tambah **threshold alert** (mis. notifikasi bila suhu > 35 °C).
- Tambah **autentikasi API** (API key di header).
- Migrasi ke **MQTT** untuk arsitektur IoT yang lebih scalable.
- Deploy server ke **cloud** (Render, Railway, PythonAnywhere).

Selamat mengerjakan! 🎯
