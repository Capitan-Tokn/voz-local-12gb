"""Guion con etiquetas -> un audio por bloque con tu voz, generado en tu PC.

Receta (la que mejor puntuó a ciegas en las pruebas de Capitán Tokn, RTX 4070 de 12 GB):
  Qwen3-TTS 1.7B Base clonando una grabación de ejemplo LARGA Y VARIADA (~1 min con pregunta, entusiasmo y tono
  serio: la entonación sale de esa grabación, no de las etiquetas) + nivelado de las caídas de volumen.
  No se entrena nada: el modelo imita la grabación al momento.

Formato del guion (las etiquetas al estilo ElevenLabs marcan dónde se trocea; las pausas meten silencio real):
  ## 01_gancho
  [curious] ¿Cuánto pagas cada mes…? [short pause] Yo, seis euros.
  ## 02_problema
  …
Sin líneas «## nombre», todo el archivo es un bloque con el nombre del archivo.

Uso: python voz_local.py <guion.txt> <carpeta_salida> [--ref RUTA_SIN_EXTENSION] [--solo NOMBRE] [--semilla N]
  --ref  grabación de ejemplo: RUTA.wav + RUTA.txt con lo que dice, palabra por palabra (por defecto referencia/mi_voz)
Salida: <carpeta>/<bloque>.wav (24 kHz, -18 LUFS) + informe.json con tiempos y lo que se ha nivelado.
"""
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

from nivelado import nivelar

AQUI = Path(__file__).resolve().parent
REFERENCIA = AQUI / "referencia" / "mi_voz"
MODELO = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
PAUSAS = {"short pause": 0.35, "pause": 0.7, "long pause": 1.2}
JUNTA = 0.12          # silencio entre trozos de un mismo bloque (lo que se usó en las pruebas)
MAX_CARACTERES = 300  # trozos más largos se parten por frases: generar mucho de golpe repite o se corta


def bloques(texto, nombre_archivo):
    partes = re.split(r"^##\s*(.+)$", texto, flags=re.M)
    if len(partes) == 1:
        return [(nombre_archivo, texto.strip())]
    return [(partes[i].strip(), partes[i + 1].strip()) for i in range(1, len(partes), 2) if partes[i + 1].strip()]


def trozos(texto):
    """[('PAUSA', s) | ('TEXTO', frase)…]: se corta en cada etiqueta; las de estilo no se leen."""
    salida = []
    for parte in re.split(r"(\[[^\]]+\])", texto):
        parte = " ".join(parte.split())
        if not parte:
            continue
        if parte.startswith("["):
            if parte[1:-1].strip().lower() in PAUSAS:
                salida.append(("PAUSA", PAUSAS[parte[1:-1].strip().lower()]))
            continue
        frases, actual = re.split(r"(?<=[.!?…])\s+", parte), ""
        for f in frases:
            if actual and len(actual) + len(f) > MAX_CARACTERES:
                salida.append(("TEXTO", actual))
                actual = ""
            actual = f"{actual} {f}".strip()
        if actual:
            salida.append(("TEXTO", actual))
    return salida


def main():
    guion, carpeta = Path(sys.argv[1]), Path(sys.argv[2])
    arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    solo, semilla = arg("--solo", None), int(arg("--semilla", "1234"))
    ref = Path(arg("--ref", str(REFERENCIA)))
    if not ref.with_suffix(".wav").exists() or not ref.with_suffix(".txt").exists():
        sys.exit(f"Falta la grabación de ejemplo: {ref}.wav y {ref}.txt (mira TEXTO_PARA_GRABAR.md)")
    pron = {k: v for k, v in json.loads((AQUI / "pronunciacion.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
    carpeta.mkdir(parents=True, exist_ok=True)
    informe_path = carpeta / "informe.json"
    informe = json.loads(informe_path.read_text(encoding="utf-8")) if informe_path.exists() else {}

    t0 = time.time()
    modelo = Qwen3TTSModel.from_pretrained(MODELO, device_map="cuda:0", dtype=torch.bfloat16)
    prompt = modelo.create_voice_clone_prompt(ref_audio=str(ref.with_suffix(".wav")),
                                              ref_text=ref.with_suffix(".txt").read_text(encoding="utf-8").strip())
    print(f"modelo cargado en {time.time() - t0:.0f} s", flush=True)

    for nombre, texto in bloques(guion.read_text(encoding="utf-8"), guion.stem):
        if solo and nombre != solo:
            continue
        t1, piezas, sr = time.time(), [], 24000
        for tipo, contenido in trozos(texto):
            if tipo == "PAUSA":
                piezas.append(np.zeros(int(contenido * sr), np.float32))
                continue
            for mal, bien in pron.items():
                contenido = re.sub(rf"\b{re.escape(mal)}\b", bien, contenido)
            torch.manual_seed(semilla)
            wavs, sr = modelo.generate_voice_clone(text=contenido, language="Spanish", voice_clone_prompt=prompt)
            piezas += [np.asarray(wavs[0], dtype=np.float32), np.zeros(int(JUNTA * sr), np.float32)]
            print(f"   {nombre}: {contenido[:70]}", flush=True)
        audio, subidos = nivelar(np.concatenate(piezas), sr)
        with tempfile.TemporaryDirectory() as tmp:
            crudo = Path(tmp) / "crudo.wav"
            sf.write(crudo, audio, sr)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-af", "loudnorm=I=-18:TP=-1.5:LRA=11",
                            "-ar", str(sr), str(carpeta / f"{nombre}.wav")], check=True)
        informe[nombre] = {"texto": texto, "duracion_s": round(len(audio) / sr, 1), "generado_en_s": round(time.time() - t1, 1),
                           "semilla": semilla, "modelo": MODELO, "referencia": ref.name,
                           "nivelado": [f"{a:.1f}-{b:.1f} s: {x:.1f} -> {y:.1f} dB" for a, b, x, y in subidos]}
        informe_path.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{nombre}.wav: {informe[nombre]['duracion_s']} s en {informe[nombre]['generado_en_s']} s"
              + (f" · nivelado {len(subidos)} tramo(s)" if subidos else ""), flush=True)


if __name__ == "__main__":
    main()
