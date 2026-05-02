/**
 * ============================================================
 *  Project : Dashboard Monitoring Ruangan dengan ESP32
 *  Role    : CLIENT (ESP32)
 *  Task    : Membaca suhu & kelembaban dari sensor DHT11,
 *            lalu mengirimkannya ke server lokal via HTTP POST
 *            (request body berformat JSON).
 * ============================================================
 *
 *  Library yang dibutuhkan (Arduino IDE > Library Manager):
 *    - WiFi            (bawaan ESP32)
 *    - HTTPClient      (bawaan ESP32)
 *    - DHT sensor library by Adafruit
 *    - Adafruit Unified Sensor (dependency dari DHT)
 *
 *  Board: ESP32 Dev Module (pilih di Tools > Board).
 * ============================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// ------------ KONFIGURASI WiFi ------------
const char* WIFI_SSID     = "UGM-Hotspot-Maskam";
const char* WIFI_PASSWORD = "";

// ------------ KONFIGURASI SERVER ----------
// Ganti dengan IP laptop/PC yang menjalankan Flask.
// Cek dengan `ipconfig` (Windows) atau `ifconfig`/`ip a` (Linux/macOS).
const char* SERVER_URL = "http://10.6.6.41:5020/sensor-data";

// ------------ KONFIGURASI SENSOR ----------
#define DHTPIN   4        // GPIO4 untuk data DHT11
#define DHTTYPE  DHT11    // ganti ke DHT22 jika pakai sensor DHT22
DHT dht(DHTPIN, DHTTYPE);

// Interval kirim data (ms). 5 detik cukup untuk demo.
const unsigned long SEND_INTERVAL_MS = 5000;
unsigned long lastSendMs = 0;

// ------------ SETUP ------------------------
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("=== ESP32 DHT11 Client ===");

  dht.begin();
  connectWiFi();
}

// ------------ LOOP -------------------------
void loop() {
  // Reconnect WiFi jika putus
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (millis() - lastSendMs >= SEND_INTERVAL_MS) {
    lastSendMs = millis();

    float temperature = dht.readTemperature();   // Celsius
    float humidity    = dht.readHumidity();      // %RH

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("[DHT11] Gagal membaca sensor (NaN). Cek wiring/power.");
      return;
    }

    Serial.printf("[DHT11] Suhu: %.1f C | Kelembaban: %.1f %%\n",
                  temperature, humidity);

    sendSensorData(temperature, humidity);
  }
}

// ------------ FUNGSI: WiFi -----------------
void connectWiFi() {
  Serial.printf("Menghubungkan ke WiFi: %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Terhubung. IP ESP32: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Gagal terhubung ke WiFi (timeout 20 detik).");
  }
}

// ------------ FUNGSI: HTTP POST JSON -------
void sendSensorData(float temperature, float humidity) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi tidak siap, skip kirim.");
    return;
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  // Susun payload JSON secara manual (tanpa ArduinoJson, agar minim dependency)
  String payload = "{";
  payload += "\"device_id\":\"esp32-01\",";
  payload += "\"temperature\":" + String(temperature, 1) + ",";
  payload += "\"humidity\":"    + String(humidity, 1);
  payload += "}";

  Serial.print("[HTTP] POST ");
  Serial.print(SERVER_URL);
  Serial.print(" -> ");
  Serial.println(payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    Serial.printf("[HTTP] Response code: %d\n", httpCode);
    String response = http.getString();
    Serial.print("[HTTP] Response body: ");
    Serial.println(response);
  } else {
    Serial.printf("[HTTP] POST gagal: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
}
