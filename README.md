# Prometeo · escucha social y política

Panel de escucha social de Prometeo Consultores. Todo funciona con fuentes públicas y servicios gratuitos.

## Qué se sigue: `seguimiento.yml`
Es el único fichero que hay que tocar para cambiar personas, cargos, partidos y colores, nivel 1 (seguimiento en profundidad, hasta 5), cabeceras, temas, canales de YouTube y canales de Telegram. Se edita en GitHub con el lápiz («Edit this file») y la siguiente recogida ya lo usa. Si tiene un error, la recogida sigue con la última versión buena (`data/seguimiento.json`) y el panel muestra el aviso con la línea del error.

Desde el panel de Claude (Ajustes) también se puede cambiar el nivel 1, añadir personas o temas y cambiar cargos: la tarea de Claude copia esos cambios a `pipeline/ajustes-panel.json` antes de cada recogida y se aplican encima de `seguimiento.yml`.

## Cómo funciona
- **Panel**: `index.html` (estructura), `app.js` (código) y `app.css` (estilos). Lee los ficheros de `data/`. Web pública: https://alvaroclavaud.github.io/prometeo/
- **Reloj**: la tarea programada de Claude «Prometeo · reloj y copia al panel» lanza la recogida a las 6:13, 12:13, 18:13 y 23:13 (hora peninsular española), espera a que termine y copia los datos al panel de Claude. Si una recogida falla, la relanza una vez.
- **Respaldo**: `.github/workflows/recogida.yml` también se despierta cada hora por su cuenta (el programador de GitHub llega tarde o no llega, por eso no es el reloj principal). El paso «Turno» solo recoge si los datos publicados son anteriores al último turno previsto. A mano: pestaña *Actions* → *Recogida de Prometeo* → *Run workflow*.
- **Qué recoge** (`pipeline/recoger.py`): Google News (medios españoles y las 17 cabeceras del piloto), Bluesky, visitas de Wikipedia, tendencias de X en España, Menéame, búsquedas en alza de Google, y los últimos vídeos y mensajes de canales públicos de YouTube y Telegram.
- **Qué calcula** (`pipeline/prom.py`): presencia y cuota por político, titulares, zonas calientes por provincia, historias del día, YouTube y Telegram, alertas e informe automático.
- **Tono y postura** (`pipeline/clasificar.py`) e **informe redactado** (`pipeline/redactar.py`): nivel gratuito de Gemini con el secreto `GEMINI_API_KEY`. Cada cifra del informe redactado se comprueba contra los datos; si aparece alguna que no está, se queda el informe automático.

## Reglas para que no falle
- Un solo hilo a Google News con pausa adaptativa: si Google frena (errores 429), baja el ritmo; si no responde nada, se abandona sin publicar y el siguiente turno lo reintenta desde otro servidor.
- Personas, cabeceras y temas son esenciales: si falta alguno tras la repesca, no se publica nada. El mapa por provincias se renueva como mucho cada 9 horas y, si no da tiempo, conserva el último.
- Control de calidad: si salen menos de la mitad de noticias que en la recogida anterior, no se publica.
- La clasificación, el informe con Gemini, YouTube y Telegram nunca impiden publicar.
- Las cifras de un día ya publicado no bajan al recalcularlo.
- Antes de publicar se comprueba que todos los JSON son válidos; el envío a GitHub se reintenta cuatro veces.

## Límites
- Google News devuelve como máximo 100 resultados por consulta.
- X no permite leer publicaciones gratis: se siguen sus tendencias.
- YouTube y Telegram: solo canales públicos de la lista y sus últimos vídeos o mensajes (unos 15-20 por canal).
- Facebook, Instagram, LinkedIn y TikTok no ofrecen acceso de escucha gratuito.
