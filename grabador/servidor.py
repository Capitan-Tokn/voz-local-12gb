"""Grabador local de la voz para clonar: sirve grabador.html y guarda lo que se graba en ../referencia.

Uso: python servidor.py   ->  abre http://localhost:8765 en Chrome (localhost cuenta como sitio seguro: deja usar el micro)
Cada toma se guarda tal cual (webm/opus del navegador) y además en wav 48 kHz mono, que es lo que leen los modelos.
Solo escucha en 127.0.0.1: nadie de fuera de este PC puede abrirlo.
"""
import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI.parent / "referencia"
DESTINO.mkdir(exist_ok=True)
PUERTO = 8765


class Grabador(BaseHTTPRequestHandler):
    def _responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._responder(200, (AQUI / "grabador.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/tomas":
            tomas = sorted(p.name for p in DESTINO.glob("voz_*.wav"))
            return self._responder(200, {"tomas": tomas})
        self._responder(404, {"error": "no existe"})

    def do_POST(self):
        if self.path != "/guardar":
            return self._responder(404, {"error": "no existe"})
        n = int(self.headers.get("Content-Length", 0))
        if not 0 < n < 60_000_000:
            return self._responder(400, {"error": "tamaño no válido"})
        cuerpo = self.rfile.read(n)
        nombre = time.strftime("voz_%Y%m%d_%H%M%S")
        bruto = DESTINO / f"{nombre}.webm"
        bruto.write_bytes(cuerpo)
        wav = DESTINO / f"{nombre}.wav"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)],
                           capture_output=True, text=True)
        if r.returncode:
            return self._responder(500, {"error": "no se pudo convertir", "detalle": r.stderr[-300:]})
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]))
        print(f"guardada {wav.name} ({dur:.1f} s)", flush=True)
        self._responder(200, {"archivo": wav.name, "segundos": round(dur, 1)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Grabador en http://localhost:{PUERTO}  (guarda en {DESTINO})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Grabador).serve_forever()
