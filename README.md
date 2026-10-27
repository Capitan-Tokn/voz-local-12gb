# Tu voz con IA en tu PC · voz local en 12 GB de VRAM

El flujo de voz del vídeo de [Capitán Tokn](https://www.youtube.com/@CapitanTokn), tal cual lo uso para narrar los vídeos.
Le das un guion con etiquetas de tono, como en ElevenLabs, y te devuelve cada bloque **con tu voz**, generado, nivelado
y revisado. Todo en tu PC. **No se entrena nada:** el modelo imita una grabación tuya de un minuto, al momento.

Probado en una RTX 4070 de 12 GB, Windows 11 y Python 3.12.

## En 4 pasos

1. **Graba tu voz** leyendo [`TEXTO_PARA_GRABAR.md`](TEXTO_PARA_GRABAR.md) y guárdala como `referencia/mi_voz.wav`. Es el paso que más importa: ver abajo.
2. **Instala** (abajo).
3. **Genera:** `python voz_local.py ejemplo_guion.txt salida`
4. **Revisa:** `python revisar_voz.py salida` comprueba con Whisper que cada bloque dice lo que pone el guion.

El nivelado va dentro del paso 3: no tienes que hacer nada.

## Instalar

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

La primera vez descarga el modelo (Qwen3-TTS 1.7B, unos 4,5 GB). Necesitas `ffmpeg` en el PATH.

**Si Windows te bloquea Python** («Una directiva de Control de aplicaciones bloqueó este archivo», error 4551): pasa con
el Python que descargan algunos instaladores, como `uv`, porque no está firmado. Crea el entorno con el Python oficial de
[python.org](https://www.python.org/downloads/), que sí lo está, como en el comando de arriba. No desactives la protección de Windows.

## El guion

```
## 01_entrada
[curious] ¿Cuánto pagas cada mes por una voz que ni siquiera es tuya? [short pause] Yo lo he medido.
## 02_explicacion
[serious] Los primeros resultados fueron un desastre.
```

- `## nombre` separa bloques: sale un `.wav` por bloque, listo para el montaje.
- Las etiquetas `[...]` marcan dónde se trocea, y **no se leen**. `[short pause]`, `[pause]` y `[long pause]` meten silencio de verdad (0,35 / 0,7 / 1,2 s).
- [`pronunciacion.json`](pronunciacion.json): palabras que el modelo dice mal y cómo escribírselas. Tu guion no cambia.
- Si un bloque sale mal: `python voz_local.py guion.txt salida --solo 02_explicacion --semilla 7`

## Lo que medí (para que vayas directo a lo que funciona)

Investigué 15 modelos de voz abiertos y probé 4 en la 4070. Las notas son a ciegas, de 1 a 5, puestas por mí: es mi oído, no un laboratorio.

| Modelo | Acento / entonación / naturalidad | Segundos de cálculo por segundo de voz | VRAM pico | Licencia | |
| --- | --- | --- | --- | --- | --- |
| **Qwen3-TTS 1.7B + grabación larga** | **5 / 5 / 5** | 3,5 | 4,7 GB | Apache 2.0 | ✓ el que uso |
| Higgs Audio V3 (4B) | 5 / 4 / 4 | 2,1 | 8,3 GB | uso de creador, citando a Boson AI | ✕ sobreactúa |
| Chatterbox (castellano) | 4 / 4 / 3 | 1,3 | 3,9 GB | MIT | ✕ se le escapa el acento |
| Qwen3-TTS 0.6B | 3 / 3 / 2 | 3,6 | 2,7 GB | Apache 2.0 | ✕ no aprovecha la grabación |
| Kokoro | — | — | — | Apache 2.0 | ✕ Windows lo bloquea |

Un vídeo de 7 minutos son unos **25 minutos de gráfica**. En luz, medido solo en la gráfica: unos 19 Wh por cada 7 minutos de voz,
menos de un céntimo.

## Los 3 errores que me costaron una tarde

1. **Grabación de ejemplo tranquila → todo sale tranquilo.** Con 14 s de un párrafo leído sin emoción, el modelo devolvía todo
   plano. Con ~1 minuto variado (pregunta, entusiasmo, tono serio), mismo modelo y mismo texto, el tono se mueve casi el doble:
   de 3,05 a 5,45 semitonos en la misma frase.
2. **Windows bloquea el Python sin firmar.** Ver *Instalar*.
3. **Traducir las etiquetas a los controles de expresividad empeora.** Probé a mapear `[excited]` a más intensidad, `[serious]`
   a menos, etc. en Chatterbox: la entonación bajó de 3 a 2. La emoción la pone la grabación, no el control.

Y uno que casi nadie cuenta: al final de las frases largas, Qwen3 a veces baja el volumen hasta 8 dB.
[`nivelado.py`](nivelado.py) sube **solo** esas caídas. La diferencia entre frases pasa de 10 dB a 3 dB, sin aplastar las exclamaciones.

## Qué hay aquí

| Archivo | Para qué |
| --- | --- |
| [`voz_local.py`](voz_local.py) | Guion → un `.wav` por bloque (24 kHz, −18 LUFS) + `informe.json` |
| [`nivelado.py`](nivelado.py) | Sube solo las caídas de volumen entre frases |
| [`revisar_voz.py`](revisar_voz.py) | Whisper comprueba cada bloque y marca los que no dicen lo que pone |
| [`grabador/`](grabador) | Grabador en el navegador: `python grabador/servidor.py` y abre http://localhost:8765 |
| [`pruebas/`](pruebas) | Los audios del vídeo con sus notas: antes y después, Higgs, Chatterbox y el nivelado. Escúchalos tú |
| [`TEXTO_PARA_GRABAR.md`](TEXTO_PARA_GRABAR.md) | El texto para tu grabación, y cómo grabarlo |
| [`referencia/`](referencia) | Aquí va `mi_voz.wav` (no se sube a git) junto a `mi_voz.txt`, lo que dices palabra por palabra |

## La norma

Clona tu voz, o una creada por ti. **La de otra persona, nunca sin su permiso.**

Y lo más útil: dale este repositorio a tu IA, dile qué gráfica tienes y pídele que te lo adapte.

Úsalo como quieras.

— [Capitán Tokn](https://www.youtube.com/@CapitanTokn)
