# Prometeo · escucha social y política

Panel de escucha social de Prometeo Consultores. Todo funciona con fuentes públicas y servicios gratuitos.

- **Panel**: `index.html` (página única). Lee los ficheros de `data/`.
- **Recogida automática**: `.github/workflows/recogida.yml` se ejecuta tres veces al día en GitHub Actions y también a mano desde la pestaña *Actions* → *Recogida de Prometeo* → *Run workflow*.
- **Qué recoge** (`pipeline/recoger.py`): Google News (medios españoles y las 17 cabeceras del piloto), Bluesky, visitas de Wikipedia, tendencias de X en España, Menéame y búsquedas en alza de Google.
- **Qué calcula** (`pipeline/prom.py`): presencia y cuota por político, titulares, zonas calientes por provincia, historias del día, alertas e informe diario.
- **Tono y postura** (`pipeline/clasificar.py`): se clasifican con el nivel gratuito de Gemini si el repositorio tiene el secreto `GEMINI_API_KEY`. Sin él, el panel funciona igual y muestra los titulares como «sin clasificar».

## Cambiar a quién y qué se sigue
- `pipeline/config.json`: consultas de cada político (`pol`), nivel 1 (`n1`), cabeceras (`med`), temas (`tem`) y provincias.
- `pipeline/catalogo.py`: nombre, partido, cargo y alias en titulares de cada persona; nombres de temas y cabeceras.

## Límites
- Google News devuelve como máximo 100 resultados por consulta.
- X no permite leer publicaciones gratis: se siguen sus tendencias.
- Facebook, Instagram, LinkedIn y TikTok no ofrecen acceso de escucha gratuito.
