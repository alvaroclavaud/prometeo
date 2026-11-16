#!/usr/bin/env python3
# Prometeo · clasificación de titulares con un modelo gratuito (Gemini, nivel gratuito de Google AI Studio).
# Lee pipeline/muestra.json y escribe pipeline/etiquetas.txt. Sin clave (secreto GEMINI_API_KEY) no clasifica y el panel
# muestra los titulares como «sin clasificar».
import json, os, re, sys, time
import requests

W = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get('GEMINI_API_KEY', '').strip()
BASE = 'https://generativelanguage.googleapis.com/v1beta/'
LOTE = int(os.environ.get('PROM_LOTE', '30')); ESPERA = float(os.environ.get('PROM_ESPERA', '7'))
OK = re.compile(r'^([PNU][FCN][IMEBOTX][EVISCLTXAO]|----)$')
INSTR = '''Clasificas titulares de prensa y publicaciones de redes sobre política española para una plataforma de escucha social.
Aplica exactamente el mismo criterio a todos los partidos. Para cada línea numerada devuelve un objeto con cuatro campos:
- tono: cómo queda la persona indicada entre corchetes en ese texto: "positivo", "negativo" o "neutro". Usa "no_aplica" si el texto no trata de esa persona o tema (homónimos, noticias de otros países).
- postura: actitud del titular o de quien habla hacia esa persona: "favor", "contra" o "informativo".
- emocion: emoción dominante del texto: "ira", "miedo", "esperanza", "burla", "orgullo", "tristeza" o "ninguna".
- tema: "economia", "vivienda", "inmigracion", "seguridad", "justicia" (corrupción y tribunales), "campana" (elecciones, mítines, sondeos, pactos), "territorial", "exterior", "social" (sanidad, educación, igualdad) u "otros".
Criterio: declaraciones propias de la persona, sin más = neutro / informativo. Ataques o críticas de rivales que el titular reproduce = negativo / contra. Apoyos y elogios = positivo / favor. Malas noticias para la persona contadas sin opinar = negativo / informativo.
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

def pedir(modelo, texto):
    for intento in range(4):
        cfg = {'temperature': 0, 'responseMimeType': 'application/json'}
        if pedir.esquema: cfg['responseSchema'] = ESQUEMA
        r = requests.post(BASE + modelo + ':generateContent', headers={'x-goog-api-key': KEY}, timeout=120, json={'contents': [{'parts': [{'text': texto}]}], 'generationConfig': cfg})
        if r.status_code == 400 and pedir.esquema: pedir.esquema = False; continue      # modelo sin soporte de esquema: se pide sin él
        if r.status_code == 200:
            try: return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text']).get('r', [])
            except Exception: return []
        if r.status_code in (429, 500, 503): time.sleep(30 * (intento + 1)); continue
        raise RuntimeError('%s %s' % (r.status_code, r.text[:160]))
    raise RuntimeError('límite de uso del modelo')

pedir.esquema = True

def main():
    filas = json.load(open(os.path.join(W, 'muestra.json'))); sal = os.path.join(W, 'etiquetas.txt')
    if not KEY:
        open(sal, 'w').close(); print('Sin GEMINI_API_KEY: los titulares quedan sin clasificar.'); return
    try: cand = modelos()
    except Exception as e:
        open(sal, 'w').close(); print('No se pudo consultar la lista de modelos:', repr(e)[:120]); return
    nombres = {p[0]: p[2] for p in json.load(open(os.path.join(W, 'config.json')))['pol']}
    et, modelo = {}, None
    for a in range(0, len(filas), LOTE):
        lote = filas[a:a + LOTE]
        lin = ['%d. [%s] %s — %s' % (i + 1, ('TEMA: ' + r['pid']) if r['tipo'] == 't' else (('BLUESKY sobre ' if r['tipo'] == 'b' else '') + nombres.get(r['pid'], r['pid'])), r['texto'], r['fuente']) for i, r in enumerate(lote)]
        texto = INSTR + '\n\n' + '\n'.join(lin)
        res = None
        for m in ([modelo] if modelo else cand):
            try: res = pedir(m, texto); modelo = m; break
            except Exception as e: print('  modelo', m, 'no disponible:', repr(e)[:100])
        if res is None: print('Clasificación interrumpida en la fila', a); break
        if len(res) != len(lote): print('  aviso: el modelo devolvió', len(res), 'respuestas para', len(lote), 'filas; se descarta el lote'); res = []
        for i, o in enumerate(res):
            c = codigo(o)
            if c and OK.match(c): et[a + i] = c
        print('  filas %d-%d · %d etiquetas · %s' % (a, a + len(lote) - 1, len(et), modelo), flush=True)
        time.sleep(ESPERA)
    with open(sal, 'w') as f:
        for n in sorted(et): f.write('%d %s\n' % (n, et[n]))
    print('Clasificadas', len(et), 'de', len(filas), 'filas con', modelo)

if __name__ == '__main__':
    main()
