# Prometeo · escucha social y política

Panel de escucha social de Prometeo Consultores. Todo funciona con fuentes públicas y servicios gratuitos.

- **Panel**: `index.html` (página única). Lee los ficheros de `data/`.
- **Recogida automática**: `.github/workflows/recogida.yml` recoge cuatro veces al día (6:12, 12:12, 18:12 y 23:12, hora peninsular española, todo el año) en GitHub Actions y también a mano desde la pestaña *Actions* → *Recogida de Prometeo* → *Run workflow*. El programador de GitHub puede retrasarse, así que el flujo se despierta cada hora: si los datos publicados son anteriores al último turno previsto (por un retraso o porque un turno falló), recoge en ese momento; si están al día, termina en segundos. Nunca publica datos incompletos de personas o temas; si no da tiempo a consultar todas las provincias, conserva el último dato del mapa.
- **Qué recoge** (`pipeline/recoger.py`): Google News (medios españoles y las 17 cabeceras del piloto), Bluesky, visitas de Wikipedia, tendencias de X en España, Menéame y búsquedas en alza de Google.
- **Qué calcula** (`pipeline/prom.py`): presencia y cuota por político, titulares, zonas calientes por provincia, historias del día, alertas e informe diario.
- **Tono y postura** (`pipeline/clasificar.py`): se clasifican con el nivel gratuito de Gemini si el repositorio tiene el secreto `GEMINI_API_KEY`. Sin él, el panel funciona igual y muestra los titulares como «sin clasificar». Los titulares ya clasificados no se vuelven a enviar al modelo, y un fallo o un límite de uso del modelo no impide publicar la recogida.

## Cambiar a quién y qué se sigue
- `pipeline/config.json`: consultas de cada político (`pol`), nivel 1 (`n1`), cabeceras (`med`), temas (`tem`) y provincias.
- `pipeline/catalogo.py`: nombre, partido, cargo y alias en titulares de cada persona; nombres de temas y cabeceras.

## Límites
- Google News devuelve como máximo 100 resultados por consulta.
- X no permite leer publicaciones gratis: se siguen sus tendencias.
- Facebook, Instagram, LinkedIn y TikTok no ofrecen acceso de escucha gratuito.
