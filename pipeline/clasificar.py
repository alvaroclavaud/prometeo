#!/usr/bin/env python3
# Prometeo · clasificación de titulares con un modelo gratuito (Gemini, nivel gratuito de Google AI Studio).
# Lee pipeline/muestra.json y escribe pipeline/etiquetas.txt. Sin clave (secreto GEMINI_API_KEY) no clasifica y el panel
# muestra los titulares como «sin clasificar». Nunca debe impedir la publicación: tiene un límite de tiempo, guarda lo que
# lleva tras cada lote y no vuelve a enviar al modelo los titulares que ya están clasificados en data/.
import glob, json, os, re, sys, time
import requests

W = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get('GEMINI_API_KEY', '').strip()
BASE = 'https://generativelanguage.googleapis.com/v1beta/'
LOTE = int(os.environ.get('PROM_LOTE', '60')); ESPERA = float(os.environ.get('PROM_ESPERA', '5'))
T0 = time.time(); MAX_MIN = float(os.environ.get('PROM_CLAS_MIN', '16'))          # minutos como máximo dedicados a clasificar
def queda(): return MAX_MIN * 60 - (time.time() - T0)
OK = re.compile(r'^([PNU][FCN][IMEBOTX][EVISCLTXAO]|----)$')
INSTR = '''Clasificas titulares de prensa y publicaciones de redes sobre política española para una plataforma de escucha social.
Aplica exactamente el mismo criterio a todos los partidos. Para cada línea numerada devuelve un objeto con cuatro campos:
- tono: cómo queda la persona indicada entre corchetes en ese texto: "positivo", "negativo" o "neutro". Usa "no_aplica" si el texto no trata de esa persona o tema (homónimos, noticias de otros países).
- postura: actitud del titular o de quien habla hacia esa persona: "favor", "contra" o "informativo".
- emocion: emoción dominante del texto: "ira", "miedo", "esperanza", "burla", "orgullo", "tristeza" o "ninguna".
- tema: "economia", "vivienda", "inmigracion", "seguridad", "justicia" (corrupción y tribunales), "campana" (elecciones, mítines, sondeos, pactos), "territorial", "exterior", "social" (sanidad, educación, igualdad) u "otros".
Criterio: declaraciones propias de la persona, sin más = neutro / informativo. Ataques o críticas de rivales que el titular reproduce = negativo / contra. Apoyos y elogios = positivo / favor. Malas noticias para la persona contadas sin opinar = negativo / informativo.
Sé estricto con "positivo": solo cuando un tercero apoya o elogia a la persona, se le reconoce un logro o hay una buena noticia objetiva para ella (una encuesta favorable, una victoria). Una promesa, un anuncio o un acto de gobierno contado sin valorar es neutro.
Ejemplos:
[Alberto Núñez Feijóo] Feijóo promete bajar impuestos a los autónomos -> neutro, informativo
[Alberto Núñez Feijóo] Rueda asegura que Feijóo «merece la pena» -> positivo, favor
[Pedro Sánchez] Tellado llama a Sánchez «el Kirchner de España» -> negativo, contra
[Pedro Sánchez] El Gobierno de Sánchez aprueba una ayuda para el campo -> neutro, informativo
[Santiago Abascal] Abascal acusa al Gobierno de ser una mafia -> neutro, informativo (él es quien ataca)
[Pedro Sánchez] Un sondeo da a Sánchez su peor resultado -> negativo, informativo
Si la línea es de un TEMA (no de una persona), valora el tono general de la noticia y pon postura "informativo".
Responde solo con JSON: {"r":[{"tono":"...","postura":"...","emocion":"...","tema":"..."}, ...]} con un objeto por línea, en el mismo orden y sin saltarte ninguna.'''
MAPA = [{'positivo': 'P', 'negativo': 'N', 'neutro': 'U'}, {'favor': 'F', 'contra': 'C', 'informativo': 'N'},
        {'ira': 'I', 'miedo': 'M', 'esperanza': 'E', 'burla': 'B', 'orgullo': 'O', 'tristeza': 'T', 'ninguna': 'X'},
        {'economia': 'E', 'vivienda': 'V', 'inmigracion': 'I', 'seguridad': 'S', 'justicia': 'C', 'campana': 'L', 'territorial': 'T', 'exterior': 'X', 'social': 'A', 'otros': 'O'}]
ESQUEMA = {'type': 'OBJECT', 'properties': {'r': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {
    'tono': {'type': 'STRING', 'enum': ['positivo', 'negativo', 'neutro', 'no_aplica']}, 'postura': {'type': 'STRING', 'enum': list(MAPA[1])},
    'emocion': {'type': 'STRING', 'enum': list(MAPA[2])}, 'tema': {'type': 'STRING', 'enum': list(MAPA[3])}}, 'required': ['tono', 'postura', 'emocion', 'tema']}}}, 'required': ['r']}
def norm(x):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD', str(x or '').lower().strip()) if not unicodedata.combining(c)).replace(' ', '_')
def codigo(o):
    """Convierte la respuesta del modelo en el código de 4 letras. Tono y postura son obligatorios; emoción y tema tienen valor por defecto."""
    if not isinstance(o, dict): return None
    t = norm(o.get('tono'))
    if t.startswith('no'): return '----'
    a, b = MAPA[0].get(t), MAPA[1].get(norm(o.get('postura')).replace('a_favor', 'favor').replace('en_contra', 'contra'))
    if not a or not b: return None
    return a + b + MAPA[2].get(norm(o.get('emocion')), 'X') + MAPA[3].get(norm(o.get('tema')), 'O')

def modelos():
    if os.environ.get('GEMINI_MODEL'): return [os.environ['GEMINI_MODEL'] if os.environ['GEMINI_MODEL'].startswith('models/') else 'models/' + os.environ['GEMINI_MODEL']]
    r = requests.get(BASE + 'models?pageSize=200', headers={'x-goog-api-key': KEY}, timeout=30)
    r.raise_for_status()
    ms = [m['name'] for m in r.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', []) and 'flash' in m['name']
          and not re.search(r'image|tts|audio|live|embed|native|robot|computer', m['name'])]
    lite = sorted([m for m in ms if 'lite' in m], reverse=True); resto = sorted([m for m in ms if 'lite' not in m], reverse=True)
    pref = [m for m in lite if m.endswith('latest')] + [m for m in lite if not m.endswith('latest')] + resto
    return pref[:6]

def previas():
    """Etiquetas ya publicadas en data/dia-*.json, por (persona o '_' si es un tema, titular)."""
    out = {}
    if os.environ.get('PROM_RECLASIFICAR'): return out
    for fp in sorted(glob.glob(os.path.join(W, '..', 'data', 'dia-*.json')))[-3:]:
        try:
            for m in json.load(open(fp, encoding='utf-8'))['menciones']:
                for k, c in (m.get('c') or {}).items():
                    if OK.match(c): out[(k, m['t'])] = c
        except Exception as e: print('  aviso: no se pudo leer', os.path.basename(fp), repr(e)[:60])
    return out

class Agotado(Exception): pass

def motivo(r):
    try: e = r.json().get('error', {}); return '%s %s' % (e.get('status', r.status_code), (e.get('message') or '')[:140])
    except Exception: return '%s %s' % (r.status_code, r.text[:140])

def pedir(modelo, texto):
    for intento in range(3):
        if queda() <= 0: raise RuntimeError('sin tiempo')
        cfg = {'temperature': 0, 'responseMimeType': 'application/json'}
        if pedir.esquema: cfg['responseSchema'] = ESQUEMA
        try: r = requests.post(BASE + modelo + ':generateContent', headers={'x-goog-api-key': KEY}, timeout=90, json={'contents': [{'parts': [{'text': texto}]}], 'generationConfig': cfg})
        except requests.RequestException as e:
            if intento == 2: raise RuntimeError('sin respuesta: ' + type(e).__name__)
            time.sleep(10); continue
        if r.status_code == 400 and pedir.esquema: pedir.esquema = False; continue      # modelo sin soporte de esquema: se pide sin él
        if r.status_code == 200:
            try: return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']).get('r', [])
            except Exception: return []
        if r.status_code == 429:
            m = motivo(r)
            if re.search(r'per ?day|PerDay|daily', m, re.I) or intento: raise Agotado(m)      # cuota del día agotada: se pasa a otro modelo
            time.sleep(max(0, min(25, queda()))); continue                                     # límite por minuto: una espera y otro intento
        if r.status_code in (500, 503): time.sleep(max(0, min(10 * (intento + 1), queda()))); continue
        raise RuntimeError(motivo(r))
    raise Agotado('sin respuesta tras 3 intentos')

pedir.esquema = True

def main():
    filas = json.load(open(os.path.join(W, 'muestra.json'))); sal = os.path.join(W, 'etiquetas.txt')
    if not KEY:
        open(sal, 'w').close(); print('Sin GEMINI_API_KEY: los titulares quedan sin clasificar.'); return
    try: cand = modelos()
    except Exception as e:
        open(sal, 'w').close(); print('No se pudo consultar la lista de modelos:', repr(e)[:120]); return
    import seguimiento; nombres = {p[0]: p[2] for p in seguimiento.config()['pol']}
    et, modelo = {}, None
    ya = previas()
    for n, r in enumerate(filas):
        c = ya.get((r['pid'] if r['tipo'] == 'm' else '_', r['texto'])) if r['tipo'] in ('m', 't') else None
        if c: et[n] = c
    n1 = set(seguimiento.config()['n1'])
    prio = lambda n: (0 if filas[n]['tipo'] == 'm' and filas[n]['pid'] in n1 else 1 if filas[n]['tipo'] == 'm' else 2 if filas[n]['tipo'] == 't' else 3, n)
    pend = sorted((n for n in range(len(filas)) if n not in et), key=prio)     # primero el nivel 1: si la cuota se acaba, lo importante ya está
    print('Filas: %d · ya clasificadas en recogidas anteriores: %d · nuevas: %d' % (len(filas), len(et), len(pend)), flush=True)
    def guardar():
        with open(sal, 'w') as f:
            for n in sorted(et): f.write('%d %s\n' % (n, et[n]))
    guardar(); vivos = list(cand)
    for a in range(0, len(pend), LOTE):
        if queda() < 45: print('Se acabó el tiempo de clasificación: quedan %d filas sin clasificar.' % (len(pend) - a)); break
        idx = pend[a:a + LOTE]; lote = [filas[n] for n in idx]
        lin = ['%d. [%s] %s — %s' % (i + 1, ('TEMA: ' + r['pid']) if r['tipo'] == 't' else (('BLUESKY sobre ' if r['tipo'] == 'b' else '') + nombres.get(r['pid'], r['pid'])), r['texto'], r['fuente']) for i, r in enumerate(lote)]
        texto = INSTR + '\n\n' + '\n'.join(lin)
        res = None
        while vivos and res is None:
            m = vivos[0]
            try: res = pedir(m, texto); modelo = m
            except Exception as e: print('  modelo', m, 'no disponible:', str(e)[:160]); vivos.pop(0)
        if res is None: print('Clasificación interrumpida: quedan %d filas sin clasificar.' % (len(pend) - a)); break
        if len(res) != len(lote): print('  aviso: el modelo devolvió', len(res), 'respuestas para', len(lote), 'filas; se descarta el lote'); res = []
        for i, o in enumerate(res):
            c = codigo(o)
            if c and OK.match(c): et[idx[i]] = c
        guardar()
        print('  lote %d de %d · %d etiquetas · %s · %.1f min' % (a // LOTE + 1, (len(pend) + LOTE - 1) // LOTE, len(et), modelo, (time.time() - T0) / 60), flush=True)
        if a + LOTE < len(pend): time.sleep(ESPERA)
    guardar()
    print('Clasificadas', len(et), 'de', len(filas), 'filas (%d reutilizadas) con' % (len(filas) - len(pend)), modelo)

if __name__ == '__main__':
    main()
