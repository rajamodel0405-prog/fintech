#!/usr/bin/env python3
"""FinGuard prototype server (standard library only).

Serves index.html / style.css / app.js and a tiny JSON API for the
weekly leaderboard:

    GET  /api/leaderboard   -> {"peers": [{"name": ..., "xp": ...}, ...]}
    POST /api/leaderboard   -> {"name": "...", "xp": 123}  (records the player's XP)

Run:  python3 server.py   then open http://localhost:8000
Data is kept in memory and resets when the server restarts.
"""
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
PORT = 8000
PLAYER = "NovaTech Solutions (you)"

_lock = threading.Lock()
_board = {
    "Priya Textiles": 640,
    "Mehta Traders": 410,
    "Chennai Bakes": 230,
    "Raj Auto Parts": 120,
}
_player_xp = 0


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/leaderboard":
            with _lock:
                peers = [{"name": n, "xp": x} for n, x in _board.items()]
            return self._json({"peers": sorted(peers, key=lambda p: -p["xp"]),
                               "player_xp": _player_xp})
        return super().do_GET()

    def do_POST(self):
        global _player_xp
        if self.path != "/api/leaderboard":
            return self._json({"error": "not found"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            xp = int(json.loads(self.rfile.read(n))["xp"])
        except (ValueError, KeyError, TypeError):
            return self._json({"error": "expected JSON {name, xp}"}, 400)
        with _lock:
            _player_xp = max(0, xp)
        return self._json({"ok": True, "xp": _player_xp})

    def log_message(self, fmt, *args):
        print("•", fmt % args)


if __name__ == "__main__":
    print(f"FinGuard running at http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
