# Las pruebas del vídeo, para que las escuches tú

Todo lo de esta carpeta se generó en mi PC (RTX 4070, 12 GB), con la misma voz de referencia: una voz diseñada por mí.
Son los mismos recortes que suenan en el vídeo, sin tocar más que el volumen. El volumen se ajustó con una ganancia
fija, igual para todos, para no esconder ni las caídas ni las frases planas.

Las notas son a ciegas, de 1 a 5 (acento / entonación / naturalidad), y las puse yo. Es mi oído, no un laboratorio.

## La grabación de ejemplo lo decide casi todo

Qwen3-TTS 1.7B y mismo texto. Solo cambia la grabación de ejemplo que imita:

| Audio | Grabación de ejemplo | Lo medido |
| --- | --- | --- |
| [`01_antes_grabacion_tranquila.mp3`](01_antes_grabacion_tranquila.mp3) | 14 s de un párrafo tranquilo | El tono se mueve 3,05 semitonos en la frase |
| [`02_despues_grabacion_52s.mp3`](02_despues_grabacion_52s.mp3) | 52 s variados (pregunta, entusiasmo, tono serio) | 5,45 semitonos, casi el doble |
| [`03_grabacion_tranquila_todo_plano.mp3`](03_grabacion_tranquila_todo_plano.mp3) | La tranquila, en otro texto | Fíjate en «y lo encontré»: sin chispa |

## Los otros modelos

| Audio | Modelo | Notas | Por qué no lo uso |
| --- | --- | --- | --- |
| [`04_higgs_sobreactua.mp3`](04_higgs_sobreactua.mp3) | Higgs Audio V3 4B, de [Boson AI](https://www.boson.ai/) | 5 / 4 / 4 | Entiende emociones escritas en el texto, pero sobreactúa |
| [`05_chatterbox_acento.mp3`](05_chatterbox_acento.mp3) | Chatterbox (castellano) | 4 / 4 / 3 | Es el más rápido, pero se le escapa el acento |

## Error 3: traducir las etiquetas a los controles de expresividad

Chatterbox con el mismo texto. Con `[excited]` traducido a más intensidad, `[serious]` a menos, etc., la entonación
bajó de 3 a 2:

- [`06_chatterbox_sin_controles.mp3`](06_chatterbox_sin_controles.mp3): 3 / 3 / 2
- [`07_chatterbox_con_controles.mp3`](07_chatterbox_con_controles.mp3): 3 / 2 / 2

## Paso 4: el nivelado

Qwen3-TTS 1.7B. Al final de «…buscando qué estaba haciendo mal» la voz se apaga. [`nivelado.py`](../nivelado.py) sube solo esa caída.
En el texto completo, la diferencia de volumen entre frases pasa de 10,1 dB a 3,1 dB:

- [`08_qwen_sin_nivelar.mp3`](08_qwen_sin_nivelar.mp3)
- [`09_qwen_nivelado.mp3`](09_qwen_nivelado.mp3)
