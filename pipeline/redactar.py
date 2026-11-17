# Informe diario redactado con Gemini (nivel gratuito) a partir de las cifras publicadas en data/ultimo.json.
# Garantías: solo recibe cifras del día; cada número del texto se compara con esas cifras y, si aparece alguno
# que no está en los datos, se pide corregir; si sigue mal, o si Gemini no responde, se queda el informe
# automático que ya escribió prom.py. Nunca impide publicar.
import json, os, re, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

W = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(W, '..', 'data')
KEY = os.environ.get('GEMINI_API_KEY', '').strip()
BASE = 'https://generativelanguage.googleapis.com/v1beta/'
T0 = time.time(); MAX_S = float(os.environ.get('PROM_REDACTA_MIN', '6')) * 60

INSTR = '''Eres analista de una consultora de comunicación política en España. Redacta el informe diario de escucha
social a partir EXCLUSIVAMENTE de los datos JSON que siguen. Reglas obligatorias:
1. Tono neutral y descriptivo, igual para todos los partidos. Sin opiniones, sin predicciones electorales, sin
   recomendaciones de voto y sin adjetivos valorativos sobre las personas.
2. Cada afirmación lleva su cifra o el titular entre comillas latinas «…». No uses ningún número que no esté en
   los datos (puedes escribirlo con formato español: 1.158 o 31,7 %). No calcules porcentajes ni sumas nuevas.
3. Cuando hables de tono, di siempre el tamaño de la muestra (n) y recuerda que describe cómo quedan en los
   titulares, no la opinión pública.
4. No añadas hechos, declaraciones, cargos ni contexto que no estén en los datos. Si un dato falta, no lo menciones.
5. Bluesky es una red pequeña y escorada a la izquierda en España; YouTube y Telegram son canales propios de
   partidos y medios: descríbelos como difusión, no como opinión.
6. Español de España, frases cortas. titular: máximo 140 caracteres. claves: entre 4 y 6, cada una con un título
   breve (t) y 1-3 frases (d). lideres: un párrafo de 2-4 frases por cada persona de nivel1, con su id.
   temas: 1-2 frases por cada tema, con su id. redes: 2-3 frases. vigilar: 3-5 puntos a partir de las alertas.
DATOS:
'''
ESQUEMA = {'type': 'OBJECT', 'properties': {
    'titular': {'type': 'STRING'}, 'entradilla': {'type': 'STRING'},
    'claves': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'t': {'type': 'STRING'}, 'd': {'type': 'STRING'}}, 'required': ['t', 'd']}},
    'lideres': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'id': {'type': 'STRING'}, 'texto': {'type': 'STRING'}}, 'required': ['id', 'texto']}},
    'temas': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'properties': {'id': {'type': 'STRING'}, 'texto': {'type': 'STRING'}}, 'required': ['id', 'texto']}},
    'redes': {'type': 'STRING'}, 'vigilar': {'type': 'ARRAY', 'items': {'type': 'STRING'}}},
    'required': ['titular', 'entradilla', 'claves', 'lideres', 'temas', 'redes', 'vigilar']}

def datos(u, cat):
    P = {p['id']: p for p in cat['politicos']}; T = {t['id']: t for t in cat['temas']}; PR = {p['id']: p['nombre'] for p in cat['provincias']}
    n1 = [i for i in cat['nivel1'] if i in u['pol']]
    loc = datetime.fromisoformat(u['generado'].replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Madrid'))
    def per(i):
        s = u['pol'][i]; n = s['n'] or 0
        d = {'id': i, 'nombre': P[i]['nombre'], 'partido': P[i]['partido'], 'cargo': P[i]['cargo'], 'noticias24h': s['vol'], 'cuota_pct': s['cuota'],
             'titulares_con_su_nombre': s['tit'], 'titulares_en_17_cabeceras': s['cat'], 'cabeceras_con_titular': s['medios17'],
             'media_diaria_7dias': s['media7'], 'visitas_wikipedia_ayer': s['wiki'], 'visitas_wikipedia_media7': s['wiki7']}
        if n: d['tono'] = {'n': n, 'positivos': s['sent'][0], 'negativos': s['sent'][1], 'neutros': s['sent'][2],
                           'pct_negativos': round(100 * s['sent'][1] / n), 'pct_positivos': round(100 * s['sent'][0] / n)}
        h = next((x for x in u['historias'] if i in x['p']), None)
        if h: d['historia_mas_repetida'] = {'titular': h['t'], 'medios': h['medios']}
        b = (u.get('bsky') or {}).get(i)
        if b: d['bluesky_24h'] = {'publicaciones': b['n'], 'me_gusta': b['likes'], 'republicaciones': b['rep']}
        for red in ('youtube', 'telegram'):
            r = ((u.get(red) or {}).get('n1') or {}).get(i)
            if r and r['n']: d[red + '_7dias'] = {'piezas_que_le_mencionan': r['n'], 'visualizaciones': r['vistas']}
        return d
    temas = []
    for tid, s in u['tem'].items():
        if tid not in T: continue
        d = {'id': tid, 'nombre': T[tid]['nombre'], 'pct_titulares_17_cabeceras': s.get('agendaPct'), 'titulares_17_cabeceras': s.get('agenda17')}
        if s.get('n'): d['tono'] = {'n': s['n'], 'negativos': s['sent'][1]}
        z = sorted([(v.get('idx', 0), k, v) for k, v in (s.get('prov') or {}).items() if v.get('n', 0) >= 12], key=lambda x: -x[0])[:2]
        if z: d['zonas_calientes'] = [{'provincia': PR.get(k, k), 'noticias': v['n'], 'veces_lo_esperable': x, 'ventana': T[tid].get('ventana')} for x, k, v in z]
        temas.append(d)
    rk = sorted(u['pol'].items(), key=lambda x: -x[1]['vol'])[:8]
    out = {'fecha': u['fecha'], 'hora_datos': loc.strftime('%H:%M'), 'elecciones': cat.get('elecciones'),
           'noticias_24h_catalogo': sum(s['vol'] for s in u['pol'].values()), 'titulares_17_cabeceras_24h': (u.get('corpus') or {}).get('n'), 'nivel1': [per(i) for i in n1],
           'ranking_presencia': [{'nombre': P[i]['nombre'], 'partido': P[i]['partido'], 'noticias24h': s['vol'], 'cuota_pct': s['cuota']} for i, s in rk if i in P],
           'temas': temas, 'historias_mas_repetidas': [{'titular': h['t'], 'medios': h['medios'], 'personas': [P[p]['nombre'] for p in h['p'] if p in P]} for h in u['historias'][:6]],
           'alertas': [{'titulo': a['titulo'], 'detalle': a['detalle']} for a in u['alertas'][:8]]}
    try: out['dias_hasta_elecciones'] = (datetime.fromisoformat(cat['elecciones']['fecha']).date() - loc.date()).days
    except Exception: pass
    x = u.get('x')
    if x: out['tendencias_x_relacionadas'] = [{'tendencia': a['t'], 'puesto': a['puesto']} for a in x['ahora'] if a['p'] or a['k']][:8]
    if u.get('meneame'): m = u['meneame'][0]; out['meneame_lo_mas_votado'] = {'titular': m['t'], 'votos': m['votos'], 'comentarios': m['com']}
    for red in ('youtube', 'telegram'):
        r = u.get(red)
        if r and r.get('top'): out[red + '_mas_visto_7dias'] = [{'canal': v['canal'], 'titulo': v['t'][:160], 'visualizaciones': v['vistas']} for v in r['top'][:5] if v.get('vistas')]
    return out, n1

def numeros_permitidos(obj):
    ok = set()
    def add(v):
        if isinstance(v, bool): return
        if isinstance(v, (int, float)):
            ok.update({float(v), float(round(v)), float(round(v, 1))})
        elif isinstance(v, str):
            for t in re.findall(r'\d+(?:[.,]\d+)*', v): ok.add(norm_num(t))
        elif isinstance(v, dict): [add(x) for x in v.values()]
        elif isinstance(v, list): [add(x) for x in v]
    add(obj)
    ok.update(float(n) for n in range(0, 11)); ok.update({17.0, 24.0, 48.0, 100.0})
    return ok

def norm_num(t):
    if ',' in t: t = t.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(\.\d{3})+', t): t = t.replace('.', '')
    try: return float(t)
    except ValueError: return -1.0

def textos(inf):
    yield inf['titular']; yield inf['entradilla']; yield inf['redes']
    for c in inf['claves']: yield c['t']; yield c['d']
    for l in inf['lideres']: yield l['texto']
    for t in inf['temas']: yield t['texto']
    for v in inf['vigilar']: yield v

def cifras_raras(inf, ok):
    malas = []
    for tx in textos(inf):
        for t in re.findall(r'\d+(?:[.,]\d+)*', re.sub(r'\b\d{1,2}-N\b|\b20\d\d\b', '', tx)):
            if norm_num(t) not in ok: malas.append(t)
    return sorted(set(malas))

def modelos():
    if os.environ.get('GEMINI_MODEL_INFORME'): return ['models/' + os.environ['GEMINI_MODEL_INFORME'].replace('models/', '')]
    r = requests.get(BASE + 'models?pageSize=200', headers={'x-goog-api-key': KEY}, timeout=30); r.raise_for_status()
    ms = [m['name'] for m in r.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', []) and 'flash' in m['name']
          and not re.search(r'image|tts|audio|live|embed|native|robot|computer|preview|exp', m['name'])]
    pref = sorted([m for m in ms if 'lite' not in m and m.endswith('latest')], reverse=True) + sorted([m for m in ms if 'lite' not in m and not m.endswith('latest')], reverse=True) \
         + sorted([m for m in ms if 'lite' in m], reverse=True)
    return pref[:6]

def pedir(modelo, texto):
    for intento in range(3):
        if time.time() - T0 > MAX_S: raise RuntimeError('sin tiempo')
        try:
            r = requests.post(BASE + modelo + ':generateContent', headers={'x-goog-api-key': KEY}, timeout=120,
                              json={'contents': [{'parts': [{'text': texto}]}], 'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json', 'responseSchema': ESQUEMA}})
        except requests.RequestException: time.sleep(10); continue
        if r.status_code == 429:                       # cuota: se pasa enseguida al siguiente modelo
            try: e = r.json().get('error', {}); raise RuntimeError('cuota agotada: %s' % (e.get('message') or '')[:120])
            except ValueError: raise RuntimeError('cuota agotada')
        if r.status_code in (500, 503): time.sleep(10 * (intento + 1)); continue
        if r.status_code != 200: raise RuntimeError('HTTP %d %s' % (r.status_code, r.text[:160]))
        c = r.json().get('candidates') or []
        if not c: raise RuntimeError('respuesta vacía')
        return json.loads(''.join(p.get('text', '') for p in c[0].get('content', {}).get('parts', [])))
    raise RuntimeError('sin respuesta')

def completar(inf, auto, n1, tids):
    """Forma mínima garantizada: si falta una persona o un tema, se usa el texto del informe automático."""
    inf['titular'] = (inf.get('titular') or auto['titular']).strip()[:180]
    inf['entradilla'] = (inf.get('entradilla') or auto['entradilla']).strip()
    inf['claves'] = [c for c in inf.get('claves') or [] if c.get('t') and c.get('d')][:6] or auto['claves']
    li = {l.get('id'): l.get('texto', '').strip() for l in inf.get('lideres') or []}; la = {l['id']: l['texto'] for l in auto['lideres']}
    inf['lideres'] = [{'id': i, 'texto': li.get(i) or la.get(i, '')} for i in n1]
    te = {t.get('id'): t.get('texto', '').strip() for t in inf.get('temas') or []}; ta = {t['id']: t['texto'] for t in auto['temas']}
    inf['temas'] = [{'id': i, 'texto': te.get(i) or ta.get(i, '')} for i in tids]
    inf['redes'] = (inf.get('redes') or auto['redes']).strip()
    inf['vigilar'] = [v for v in inf.get('vigilar') or [] if v][:5] or auto['vigilar']
    return inf

def main():
    if not KEY: print('Sin GEMINI_API_KEY: se queda el informe automático.'); return
    up = os.path.join(DATA, 'ultimo.json'); u = json.load(open(up, encoding='utf-8')); cat = json.load(open(os.path.join(DATA, 'catalogo.json'), encoding='utf-8'))
    auto = u['informe']; d, n1 = datos(u, cat); tids = [t['id'] for t in cat['temas'] if t['id'] in u['tem']]
    ok = numeros_permitidos(d) | numeros_permitidos(auto)       # el informe automático sale de los mismos datos
    base = INSTR + json.dumps(d, ensure_ascii=False)
    try: cand = modelos()
    except Exception as e: print('Gemini no disponible (%s): se queda el informe automático.' % type(e).__name__); return
    for modelo in cand:
        texto = base
        for intento in range(2):
            try: inf = completar(pedir(modelo, texto), auto, n1, tids)
            except Exception as e: print('  %s: %s' % (modelo, str(e)[:120])); break
            malas = cifras_raras(inf, ok)
            if not malas:
                inf['metodo'] = auto['metodo'] + ' Texto redactado con IA (%s) a partir de estas cifras; cada número se ha comprobado automáticamente contra los datos del día. Conviene revisarlo antes de difundirlo.' % modelo.replace('models/', '')
                inf['autor'] = modelo.replace('models/', ''); u['informe'] = inf
                json.dump(u, open(up, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
                json.dump({'fecha': u['fecha'], 'generado': u['generado'], 'informe': inf}, open(os.path.join(DATA, 'informe-%s.json' % u['fecha']), 'w', encoding='utf-8'), ensure_ascii=False)
                print('Informe redactado con %s en %.0f s.' % (modelo, time.time() - T0)); return
            print('  %s: cifras que no están en los datos: %s' % (modelo, ', '.join(malas[:10])))
            texto = base + '\n\nTu respuesta anterior incluía cifras que NO están en los datos (%s). Vuelve a redactarlo usando solo cifras que aparezcan literalmente en los datos.' % ', '.join(malas[:15])
    print('No se pudo redactar un informe fiable con Gemini: se queda el informe automático.')

if __name__ == '__main__':
    try: main()
    except Exception as e: print('Redacción con Gemini interrumpida (%s): se queda el informe automático.' % repr(e)[:120])
