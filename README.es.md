# trend-pattern-report

[Read in English](README.md)

Cada semana encuentra los videos cortos que están creciendo en tu nicho y mide **cómo están editados**: cuánto duran, cada cuánto cortan, qué tan rápido llega la primera palabra y qué dicen en los primeros 3 segundos. El resultado es un reporte y un `rules.json` que puedes seguir (o pasar a una herramienta de edición) para editar tus videos de la misma forma.

Cubre un vacío que ninguna herramienta open source cubre: las de tendencias solo recolectan y los editores automáticos solo editan. Esta convierte los videos en tendencia en reglas de edición.

## Cómo funciona

| Paso | Qué hace | Basado en |
|---|---|---|
| 1. Recolectar | Busca en YouTube tus consultas, deja los videos de los últimos N días de menos de 90 s y los ordena por vistas por día | [yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| 2. Medir | Descarga cada uno en baja resolución, detecta cada corte, transcribe la voz con tiempos por palabra y luego borra el video | [PySceneDetect](https://github.com/Breakthrough/PySceneDetect), [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| 3. Aprender | Las medianas y rangos de cada métrica se vuelven reglas de edición. Opcionalmente, Claude agrupa los ganchos en tipos y escribe las reglas en palabras | [API de Claude](https://platform.claude.com/docs) (opcional) |
| 4. Reportar | Escribe `reports/<año>-W<semana>/report.md`, `data.json` y `rules.json` | |

Métricas por video: duración, número de cortes, cortes por segundo, segundos por toma, momento del primer corte, palabras por minuto, proporción del tiempo hablando, momento de la primera palabra y el texto del gancho.

## Cómo ejecutarlo

Necesita Python 3.10 o superior. No hace falta instalar FFmpeg.

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m trendpattern run --config config.yaml --limit 3 --no-llm
```

Edita `config.yaml` para definir tu nicho (las consultas incluidas son solo un ejemplo). Los campos se explican en los comentarios del archivo.

La búsqueda de YouTube devuelve resultados por relevancia y muchos son antiguos. La herramienta descarta los que quedan fuera de la ventana `days`; si un reporte tiene pocos videos, sube `per_query` o usa consultas más específicas.

### El paso opcional con Claude

Con `ANTHROPIC_API_KEY` definida, el paso 3 también le pide a Claude (`claude-opus-5-5`) que nombre los tipos de gancho y escriba las reglas en palabras, usando solo los números medidos. Sin la clave, o con `--no-llm`, el reporte igual tiene todos los números y la tabla de reglas.

## Ejecución semanal

YouTube bloquea los runners de GitHub ("Sign in to confirm you're not a bot"), así que el reporte semanal de este repositorio corre cada lunes en un runner propio que vive en otro repositorio privado, y guarda el resultado en `reports/`. Mantener ese runner fuera de este repositorio público evita que los pull requests de desconocidos ejecuten código en esa máquina.

En este repositorio, `.github/workflows/weekly.yml` ejecuta las pruebas en cada push y pull request. Su tarea de reporte se puede lanzar a mano desde la pestaña Actions (con `ANTHROPIC_API_KEY` como secreto para el paso con Claude), pero lo más probable es que YouTube la bloquee ahí.

Para correrlo con tu propio horario usa cron, el Programador de tareas de Windows o un runner propio en un repositorio privado que ejecute `python -m trendpattern run` en una copia de este.

## Uso responsable

- Los videos se descargan solo para medirlos y se borran enseguida. El reporte guarda enlaces, metadatos públicos y números derivados; no se redistribuye ningún video.
- Respeta los términos de servicio de cada plataforma y mantén pocas solicitudes (por defecto revisa unos 50 resultados de búsqueda y descarga 8 videos cortos por semana).
- Las reglas describen lo que es común entre los videos en tendencia, no lo que causa las vistas. Compáralas con tus propios datos de retención.

## Pruebas

```bash
python -m pytest -q
```

## Licencia

MIT
