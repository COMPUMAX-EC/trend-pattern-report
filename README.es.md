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

## Ejecución semanal en GitHub Actions

`.github/workflows/weekly.yml` corre cada lunes (y cuando quieras desde la pestaña Actions), ejecuta las pruebas, arma el reporte y lo guarda en `reports/`. Agrega `ANTHROPIC_API_KEY` como secreto del repositorio para activar el paso con Claude.

YouTube a veces bloquea las descargas desde los runners de GitHub. Si el reporte marca todos los videos como omitidos, ejecútalo en un runner propio (cambia `runs-on: ubuntu-latest` por `runs-on: self-hosted`) o en tu computadora.

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
