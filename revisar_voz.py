"""Revisa los audios de voz_local.py antes del montaje: ¿dice lo que pone el guion?

Whisper large-v3 transcribe cada bloque y se compara letra a letra con el texto (sin etiquetas). Por debajo del 90 %
de parecido se marca para escucharlo: puede haberse comido o repetido algo.
Uso: python revisar_voz.py <carpeta_salida>   (necesita faster-whisper; la primera vez descarga el modelo, ~3 GB)
"""
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

from faster_whisper import WhisperModel

UMBRAL = 0.90
AQUI = Path(__file__).resolve().parent


UNI = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete " \
      "dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete " \
      "veintiocho veintinueve".split()
DEC = "_ _ _ treinta cuarenta cincuenta sesenta setenta ochenta noventa".split()
CEN = "_ ciento doscientos trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos".split()


def en_letra(n):
    """Entero (0-999999) en palabras: Whisper escribe «1700» donde el guion dice «mil setecientos»."""
    if n < 30:
        return UNI[n]
    if n < 100:
        return DEC[n // 10] + ("" if n % 10 == 0 else " y " + UNI[n % 10])
    if n < 1000:
        return "cien" if n == 100 else CEN[n // 100] + ("" if n % 100 == 0 else " " + en_letra(n % 100))
    miles, resto = divmod(n, 1000)
    return ("mil" if miles == 1 else en_letra(miles) + " mil") + ("" if resto == 0 else " " + en_letra(resto))


def cifras_a_letra(s):
    s = re.sub(r"(\d+),(\d+)", lambda m: f"{m[1]} coma {m[2]}", s)
    s = re.sub(r"(\d+)\.(\d+)", lambda m: f"{m[1]} punto {m[2]}", s)
    return re.sub(r"\d+", lambda m: en_letra(int(m[0])) if int(m[0]) < 1_000_000 else m[0], s)


def norm(s):
    s = cifras_a_letra(re.sub(r"\[[^\]]+\]", "", s))
    return re.sub(r"[^a-z0-9ñ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())


carpeta = Path(sys.argv[1])
informe_path = carpeta / "informe.json"
informe = json.loads(informe_path.read_text(encoding="utf-8"))
pron = {k: v for k, v in json.loads((AQUI / "pronunciacion.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
modelo = WhisperModel("large-v3", device="cuda", compute_type="float16")
malos = 0
for nombre, datos in informe.items():
    texto = datos["texto"]
    for mal, bien in pron.items():
        if not mal.isdigit():   # las cifras ya las iguala cifras_a_letra (Whisper escribe «4070», no «cuarenta setenta»)
            texto = re.sub(rf"\b{re.escape(mal)}\b", bien, texto)
    segs, _ = modelo.transcribe(str(carpeta / f"{nombre}.wav"), language="es", beam_size=5)
    oido = " ".join(s.text for s in segs).strip()
    parecido = difflib.SequenceMatcher(None, norm(oido), norm(texto), autojunk=False).ratio()
    datos.update({"oido": oido, "parecido": round(parecido, 3)})
    ok = parecido >= UMBRAL
    malos += not ok
    print(f"{'OK ' if ok else 'MAL'} {nombre:20s} {parecido:.0%}" + ("" if ok else f"\n     oído: {oido}"), flush=True)
informe_path.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(informe) - malos} de {len(informe)} bloques bien" + (": regenera los MAL con --solo NOMBRE --semilla otra" if malos else ""))
