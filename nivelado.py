"""Sube solo las caídas de volumen entre frases, sin tocar la entonación.

Qwen3 a veces deja caer el volumen al final de una frase larga (medido: -27/-31 dB contra -23 dB del resto).
Un tramo con voz (separado por silencios) que queda más de 3 dB por debajo de la mediana se sube hasta 1 dB
por debajo de ella (tope +8 dB). El resto no se toca: el contraste entre una frase normal y una exclamación es
intencionado. La ganancia cambia con rampas de 30 ms y dentro de cada tramo no se toca nada.
"""
import librosa
import numpy as np

TOPE_DB, RAMPA_S, CAIDA_DB = 8.0, 0.03, 3.0


def nivelar(y, sr):
    """-> (audio nivelado, [(inicio_s, fin_s, dB_antes, dB_después)…] de los tramos que se han subido)"""
    tramos = [(s, e) for s, e in librosa.effects.split(y, top_db=40, frame_length=1024, hop_length=256) if e - s > 0.15 * sr]
    if not tramos:
        return y, []
    nivel = [20 * np.log10(np.sqrt((y[s:e] ** 2).mean()) + 1e-9) for s, e in tramos]
    objetivo = float(np.median(nivel))
    ganancia, subidos = np.ones_like(y), []
    for (s, e), n in zip(tramos, nivel):
        if n >= objetivo - CAIDA_DB:
            continue
        sub = min(objetivo - 1 - n, TOPE_DB)
        g = 10 ** (sub / 20)
        ganancia[max(0, s - int(RAMPA_S * sr)):e] = g      # la rampa empieza en el silencio de antes, no en la voz
        subidos.append((s / sr, e / sr, n, n + sub))
    rampa = np.hanning(int(2 * RAMPA_S * sr))
    ganancia = np.convolve(ganancia, rampa / rampa.sum(), mode="same")
    return (y * ganancia).astype(np.float32), subidos
