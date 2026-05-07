# Wiring Diagram — ESP32 ↔ DHT11

## 1. Pemilihan Modul DHT11

Terdapat dua varian model DHT11:

| Varian          | Pin | Pull-up internal | Rekomendasi |
|-----------------|-----|------------------|-------------|
| **Modul 3-pin** (PCB kecil, label `+ S -` atau `VCC DATA GND`) | 3 | **Ya** (sudah ada resistor 10 kΩ di PCB) | **Dipakai di project ini** |
| **Sensor 4-pin** (berbentuk blok biru polos) | 4 | Tidak | Perlu tambah resistor 10 kΩ antara DATA & VCC |

> Catatan: Biasanya sensor DHT11 modul 3-pin memiliki **LED indikator** di PCB-nya.

## 2. Koneksi Pin

### 2.1 Modul DHT11 (3-pin) — rekomendasi

| DHT11 Pin | ESP32 Pin   | Warna Kabel (saran) |
|-----------|-------------|---------------------|
| `+` / VCC | **3V3**     | Hitam               |
| `S` / DATA| **GPIO 4**  | Putih               |
| `−` / GND | **GND**     | Abu-abu             |

> ⚠️ **Jangan** menggunakan **5V** — DHT11 modul biasanya aman di 3V3, dan input ESP32 hanya tolerate 3V3. Beberapa modul 5V juga aman, tapi **3V3 paling direkomendasikan**.

### 2.2 Sensor DHT11 mentah (4-pin)

| Pin DHT11 | Fungsi          | Ke ESP32     |
|-----------|-----------------|--------------|
| 1         | VCC             | 3V3          |
| 2         | DATA            | GPIO 4       |
| 3         | NC (not connect)| —            |
| 4         | GND             | GND          |

Ditambah **resistor 10 kΩ** antara **VCC** dan **DATA** (pull-up).

## 3. Diagram ASCII

```
                ┌──────────────────────┐
                │         ESP32        │
                │                      │
                │   3V3  ●─┐           │
                │          │           │
                │  GND   ●─┼─┐         │
                │          │  │        │
                │  GPIO4 ●─┼──┼──┐     │
                └──────────┼──┼──┼─────┘
                           │  │  │
                           │  │  │
                ┌──────────┼──┼──┼─────┐
                │   DHT11  │  │  │     │
                │          │  │  │     │
                │   VCC  ●─┘  │  │     │
                │   GND  ●────┘  │     │
                │   DATA ●───────┘     │
                └──────────────────────┘
```

## 4. Kenapa GPIO 4?

- Tidak konflik dengan fungsi boot/flash (GPIO 0, 2, 15).
- Aman selama boot.
- Dekat secara fisik dengan pin 3V3/GND di kebanyakan board ESP32 DevKit.

Alternatif aman: **GPIO 5**, **GPIO 13**, **GPIO 14**, **GPIO 25**, **GPIO 26**, **GPIO 27**, **GPIO 32**, **GPIO 33**.

**Hindari**: GPIO 6-11 (SPI flash internal), GPIO 34-39 (input-only — tidak bisa untuk pull-up).

Jika kamu ganti pin, ubah di `esp32_dht11_client.ino`:
```cpp
#define DHTPIN   4   // ganti ke GPIO lain sesuai wiring
```

## 5. Checklist Sebelum Power-On

- [x] VCC DHT11 ke **3V3** ESP32 (bukan 5V).
- [x] GND tersambung.
- [x] DATA ke GPIO 4 (atau pin yang kamu pilih di kode).
- [x] Kabel tidak longgar (DHT11 sensitif terhadap koneksi buruk).
- [x] ESP32 **tidak** di-colok ke VCC eksternal & USB bersamaan jika tidak perlu.

## 6. Tips Debugging Sensor

Jika pembacaan **NaN**:
1. Lepas & pasang ulang kabel.
2. Ukur tegangan VCC DHT11 dengan multimeter — harus ±3.3V.
3. Untuk sensor 4-pin, pastikan resistor pull-up terpasang.
4. Tambah delay awal `delay(2000)` di `setup()` sebelum `dht.begin()` — DHT11 butuh waktu stabil setelah power-on.
5. Jika tetap NaN, coba GPIO lain (mungkin pin rusak/bertabrakan dengan fungsi lain di board-mu).