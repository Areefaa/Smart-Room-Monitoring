"""
===========================================================
 Dashboard Monitoring Ruangan - Flask Server
-----------------------------------------------------------
 Peran : SERVER (laptop / PC)
 Tugas :
   1. Menerima data dari ESP32 via HTTP POST /sensor-data
   2. Menyimpan riwayat data di memori (list in-memory)
   3. Menampilkan dashboard di `/` (auto-refresh)
   4. Menyediakan endpoint JSON `/api/latest` & `/api/history`

 Cara jalan:
   python app.py

 Default bind: 0.0.0.0:5020 (akses LAN)
===========================================================
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from flask import Flask, jsonify, render_template, request

MAX_HISTORY = 200
HOST = "0.0.0.0"
PORT = 5020

app = Flask(__name__)

# Penyimpanan sederhana di memori (bukan database). Restart => data hilang.
_history: deque[dict] = deque(maxlen=MAX_HISTORY)


# ------------------------------------------------------------
# ROUTE: Dashboard utama
# ------------------------------------------------------------
@app.route("/", methods=["GET"])
def dashboard():
    latest = _history[-1] if _history else None
    return render_template(
        "dashboard.html",
        latest=latest,
        history=list(_history),
        total=len(_history),
    )


# ------------------------------------------------------------
# ROUTE: Endpoint utama yang dipanggil ESP32
# ------------------------------------------------------------
@app.route("/sensor-data", methods=["POST"])
def receive_sensor_data():
    data = request.get_json(silent=True) or {}

    # Validasi minimal
    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
    except (KeyError, TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Payload harus JSON dengan field 'temperature' & 'humidity' (number)."
        }), 400

    record = {
        "device_id": str(data.get("device_id", "unknown")),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_ip": request.remote_addr,
    }
    _history.append(record)

    app.logger.info(
        "[RECV] %s | %s | suhu=%.1fC | RH=%.1f%%",
        record["timestamp"], record["source_ip"],
        record["temperature"], record["humidity"],
    )

    return jsonify({"status": "ok", "received": record}), 200


# ------------------------------------------------------------
# ROUTE: JSON API (opsional, untuk integrasi lain)
# ------------------------------------------------------------
@app.route("/api/latest", methods=["GET"])
def api_latest():
    if not _history:
        return jsonify({"status": "empty"}), 200
    return jsonify({"status": "ok", "data": _history[-1]}), 200


@app.route("/api/history", methods=["GET"])
def api_history():
    return jsonify({"status": "ok", "count": len(_history), "data": list(_history)}), 200


# ------------------------------------------------------------
# Health check
# ------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "records": len(_history)}), 200


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    print(f"Dashboard Monitoring berjalan di http://{HOST}:{PORT}")
    print(f"  Dashboard  : http://<IP-LAPTOP>:{PORT}/")
    print(f"  ESP32 POST : http://<IP-LAPTOP>:{PORT}/sensor-data")
    app.run(host=HOST, port=PORT, debug=False)
