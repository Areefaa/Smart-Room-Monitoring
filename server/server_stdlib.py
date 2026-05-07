"""
============================================================
 Dashboard Monitoring Ruangan - Server (STDLIB ONLY)
------------------------------------------------------------
 Versi server YANG TIDAK BUTUH pip / Flask / library eksternal.
 Hanya pakai modul standar Python 3 (http.server, json, urllib, ...).

 Cocok untuk server "paten" / locked / tanpa akses pip-install.

 Fitur sama dengan versi Flask:
   POST /sensor-data   -> terima data ESP32 (JSON in, JSON out)
   GET  /              -> HTML dashboard (auto-refresh 5 s)
   GET  /api/latest    -> JSON data terbaru
   GET  /api/history   -> JSON seluruh riwayat
   GET  /health        -> health check

 Cara jalan (tanpa instalasi apapun):
   python3 server_stdlib.py

 Default bind: 0.0.0.0:5020 (akses LAN)
============================================================
"""

import json
import logging
import sys
from collections import deque
from datetime import datetime, timedelta, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Timezone WIB (UTC+7). Server 10.6.6.41 jam sistemnya kemungkinan UTC,
# jadi kita hard-code offset +7 supaya timestamp di dashboard match jam
# dinding Indonesia tanpa perlu mengubah setting OS server.
WIB = timezone(timedelta(hours=7), name="WIB")

HOST = "0.0.0.0"   # ganti ke "10.6.6.41" jika ingin bind hanya ke 1 IP
PORT = 5020
MAX_HISTORY = 200

_history: "deque[dict]" = deque(maxlen=MAX_HISTORY)


# ============================================================
# HTML Template (tanpa Jinja2 -- pakai f-string biasa)
# ============================================================
def render_dashboard() -> str:
    latest = _history[-1] if _history else None
    total = len(_history)

    if latest is None:
        body = (
            '<div class="empty">'
            '<h2>Menunggu data pertama dari ESP32...</h2>'
            '<p>Pastikan ESP32 mengirim HTTP POST ke '
            f'<code>http://&lt;IP-server&gt;:{PORT}/sensor-data</code></p>'
            '</div>'
        )
        status_pill = '<div class="status-pill offline">MENUNGGU DATA ESP32</div>'
    else:
        # Latest cards
        body = (
            '<section class="cards">'
            '  <div class="card temperature">'
            '    <div class="label">Suhu</div>'
            f'    <div class="value">{latest["temperature"]:.1f}<span class="unit">&deg;C</span></div>'
            '  </div>'
            '  <div class="card humidity">'
            '    <div class="label">Kelembaban</div>'
            f'    <div class="value">{latest["humidity"]:.1f}<span class="unit">%RH</span></div>'
            '  </div>'
            '</section>'
            '<div class="meta">'
            f'  <div class="meta-item"><span class="k">Device ID</span><span class="v">{escape(latest["device_id"])}</span></div>'
            f'  <div class="meta-item"><span class="k">Last Update</span><span class="v">{escape(latest["timestamp"])}</span></div>'
            f'  <div class="meta-item"><span class="k">Source IP</span><span class="v">{escape(latest["source_ip"])}</span></div>'
            f'  <div class="meta-item"><span class="k">Total Records</span><span class="v">{total}</span></div>'
            '</div>'
            '<h2 style="margin-top: 32px;">Riwayat (10 terbaru)</h2>'
            '<table>'
            '  <thead>'
            '    <tr><th>Waktu</th><th>Device</th><th>Suhu (&deg;C)</th><th>Kelembaban (%)</th><th>Source IP</th></tr>'
            '  </thead><tbody>'
        )
        for r in list(_history)[-10:][::-1]:
            body += (
                '<tr>'
                f'<td>{escape(r["timestamp"])}</td>'
                f'<td>{escape(r["device_id"])}</td>'
                f'<td>{r["temperature"]:.1f}</td>'
                f'<td>{r["humidity"]:.1f}</td>'
                f'<td>{escape(r["source_ip"])}</td>'
                '</tr>'
            )
        body += '</tbody></table>'
        status_pill = f'<div class="status-pill">ONLINE &middot; {total} data</div>'

    css = """
    :root{--bg:#0f172a;--card:#1e293b;--accent:#38bdf8;--accent-2:#fbbf24;--ok:#22c55e;--warn:#ef4444;--text:#e2e8f0;--muted:#94a3b8}
    *{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(160deg,#0f172a 0%,#1e293b 100%);color:var(--text);min-height:100vh}
    header{padding:24px 32px;border-bottom:1px solid #334155;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
    header h1{margin:0;font-size:1.6rem}header .subtitle{color:var(--muted);font-size:.9rem}
    .status-pill{padding:6px 14px;border-radius:999px;background:var(--ok);color:#052e16;font-weight:600;font-size:.85rem}
    .status-pill.offline{background:var(--warn);color:#450a0a}
    main{padding:32px;max-width:1100px;margin:0 auto}
    .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin-bottom:32px}
    .card{background:var(--card);border:1px solid #334155;border-radius:16px;padding:24px;box-shadow:0 8px 24px rgba(0,0,0,.2)}
    .card .label{color:var(--muted);font-size:.9rem;text-transform:uppercase;letter-spacing:1px}
    .card .value{font-size:3.2rem;font-weight:700;margin:8px 0;color:var(--accent)}
    .card.humidity .value{color:var(--accent-2)}.card .unit{font-size:1.2rem;color:var(--muted);margin-left:6px}
    .meta{background:var(--card);border:1px solid #334155;border-radius:16px;padding:20px 24px;margin-bottom:24px;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
    .meta-item{display:flex;flex-direction:column}.meta-item .k{color:var(--muted);font-size:.8rem}
    .meta-item .v{font-family:"SF Mono",Consolas,monospace;font-size:.95rem}
    table{width:100%;border-collapse:collapse;background:var(--card);border-radius:16px;overflow:hidden}
    th,td{text-align:left;padding:12px 16px;border-bottom:1px solid #334155;font-size:.92rem}
    th{background:#0f172a;color:var(--muted);font-weight:600;text-transform:uppercase;font-size:.78rem;letter-spacing:1px}
    tr:last-child td{border-bottom:none}
    .empty{text-align:center;padding:60px 20px;color:var(--muted);background:var(--card);border-radius:16px;border:2px dashed #334155}
    footer{text-align:center;padding:24px;color:var(--muted);font-size:.85rem}
    """

    return f"""<!DOCTYPE html>
<html lang="id"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="5">
<title>Dashboard Monitoring Ruangan</title>
<style>{css}</style></head><body>
<header>
  <div><h1>Dashboard Monitoring Ruangan</h1>
  <div class="subtitle">ESP32 + DHT11 &middot; Auto-refresh tiap 5 detik &middot; Stdlib server</div></div>
  {status_pill}
</header><main>{body}</main>
<footer>Dashboard Monitoring Ruangan &middot; Python stdlib (no pip)</footer>
</body></html>"""


# ============================================================
# HTTP Handler
# ============================================================
class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "DashboardESP32/1.0"

    # ---------- helper untuk respons JSON ----------
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status_code: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------- GET routes ----------
    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send_html(200, render_dashboard())
        elif self.path == "/api/latest":
            if not _history:
                self._send_json(200, {"status": "empty"})
            else:
                self._send_json(200, {"status": "ok", "data": _history[-1]})
        elif self.path == "/api/history":
            self._send_json(200, {
                "status": "ok",
                "count": len(_history),
                "data": list(_history),
            })
        elif self.path == "/health":
            self._send_json(200, {"status": "ok", "records": len(_history)})
        else:
            self._send_json(404, {"status": "error", "message": "Not found"})

    # ---------- POST routes ----------
    def do_POST(self) -> None:
        if self.path != "/sensor-data":
            self._send_json(404, {"status": "error", "message": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length > 0 else b""

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"status": "error", "message": "Body bukan JSON valid"})
            return

        try:
            temperature = float(data["temperature"])
            humidity = float(data["humidity"])
        except (KeyError, TypeError, ValueError):
            self._send_json(400, {
                "status": "error",
                "message": "Payload harus JSON dengan 'temperature' & 'humidity' (number)."
            })
            return

        record = {
            "device_id": str(data.get("device_id", "unknown")),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "timestamp": datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": self.client_address[0],
        }
        _history.append(record)

        logging.info(
            "[RECV] %s | %s | suhu=%.1fC | RH=%.1f%%",
            record["timestamp"], record["source_ip"],
            record["temperature"], record["humidity"],
        )

        self._send_json(200, {"status": "ok", "received": record})

    # quieter access log (override default yang verbose)
    def log_message(self, format: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), format % args)


# ============================================================
# Main
# ============================================================
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Dashboard Monitoring (stdlib) berjalan di http://{HOST}:{PORT}")
    print(f"  Dashboard  : http://<IP-server>:{PORT}/")
    print(f"  ESP32 POST : http://<IP-server>:{PORT}/sensor-data")
    print("Tekan Ctrl+C untuk berhenti.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
