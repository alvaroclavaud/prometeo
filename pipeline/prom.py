# Prometeo · tratamiento de datos. Uso:
#   python3 prom.py muestra   -> prepara work/muestra.txt para clasificar
#   python3 prom.py publicar  -> genera ../data/*.json a partir de raw.json + etiquetas.txt
import json, re, sys, os, hashlib, collections, glob, unicodedata
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import catalogo as C

TZ = ZoneInfo('Europe/Madrid')
W = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(W, '..', 'data')
raw = json.load(open(os.path.join(W, 'raw.json')))
CAT = C.catalogo(raw['cfg'])
ITEMS = raw['items']                       # [titulo, fuente, dominio, minuto_epoch, enlace]
GEN = datetime.fromisoformat(raw['gen'].replace('Z', '+00:00'))
GEN_MIN = int(GEN.timestamp() // 60)
HOY = GEN.astimezone(TZ).strftime('%Y-%m-%d')
POLS = CAT['politicos']; PID = {p['id']: p for p in POLS}
MED_DOM = {m['dominio']: m['id'] for m in CAT['medios']}
ARE = {p['id']: C.alias_re(p['alias']) for p in POLS}
TRE = {t['id']: re.compile(t['patron'], re.I) for t in CAT['temas']}

def dia(ts): return datetime.fromtimestamp(ts * 60, TZ).strftime('%Y-%m-%d')
def hora(ts): return datetime.fromtimestamp(ts * 60, TZ).hour
def mid(i):
    t = ITEMS[i]; return hashlib.sha1((t[0] + '|' + t[1]).encode()).hexdigest()[:10]
def norm(s):
    s = unicodedata.normalize('NFKD', s.lower()); s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
def medio(dom):
    for d, m in MED_DOM.items():
        if dom == d or dom.endswith('.' + d): return m
    return None
def titular(pid, title):
    if not ARE[pid].search(title): return False
    if pid == 'montero_mj' and 'Irene Montero' in title and 'María Jesús' not in title: return False
    return True
def temas_de(title): return [k for k, r in TRE.items() if r.search(title)]

# --- menciones por político -------------------------------------------------
POL_ITEMS = collections.defaultdict(set); POL_BASE = collections.defaultdict(set); SAT = set()
for k, v in raw['q'].items():
    if not v: continue
    a = k.split(':')
    if a[0] in ('p7', 'p1', 'pd', 'pm'):
        POL_ITEMS[a[1]].update(v)
        if a[0] != 'pm': POL_BASE[a[1]].update(v)
        if a[0] in ('p1', 'pd') and len(v) >= 98: SAT.add((a[1], a[0], a[2] if len(a) > 2 else '24h'))
MIN_TS = GEN_MIN - 8 * 1440
for pid in POL_ITEMS: POL_ITEMS[pid] = {i for i in POL_ITEMS[pid] if MIN_TS <= ITEMS[i][3] <= GEN_MIN + 5}
TEM_ITEMS = collections.defaultdict(set); FOCO = {}
for k, v in raw['q'].items():
    if not v: continue
    a = k.split(':')
    if a[0] in ('t1', 't7'): TEM_ITEMS[a[1]].update(i for i in v if ITEMS[i][3] >= MIN_TS)
    if a[0] == 'tf': FOCO[(a[1], a[2])] = [i for i in v if ITEMS[i][3] >= MIN_TS]
CORPUS = set()                              # agenda de las 17 cabeceras (muestra de 100 por cabecera, 24 h)
for k, v in raw['q'].items():
    if k.startswith('m1:') and v: CORPUS.update(i for i in v if ITEMS[i][3] >= GEN_MIN - 1440)

def en24(i): return ITEMS[i][3] >= GEN_MIN - 1440
def en48(i): return GEN_MIN - 2880 <= ITEMS[i][3] < GEN_MIN - 1440

# --- muestra para clasificar --------------------------------------------------
def construir_muestra():
    filas = []; visto = {}
    def add(tipo, pid, texto, fuente, ref, extra=''):
        key = (tipo, pid, norm(texto)[:90])
        if key in visto: visto[key]['refs'].append(ref); return
        f = {'tipo': tipo, 'pid': pid, 'texto': texto, 'fuente': fuente, 'refs': [ref], 'extra': extra}
        visto[key] = f; filas.append(f)
    n1 = set(CAT['nivel1'])
    for p in POLS:
        pid = p['id']
        its = [i for i in POL_ITEMS.get(pid, ()) if en24(i) and titular(pid, ITEMS[i][0])]
        its.sort(key=lambda i: (0 if medio(ITEMS[i][2]) else 1, -ITEMS[i][3]))
        tope = 80 if pid in n1 else 16; n0 = len(filas)
        for i in its:
            if len(filas) - n0 >= tope and (('m', pid, norm(ITEMS[i][0])[:90]) not in visto): continue
            add('m', pid, ITEMS[i][0], ITEMS[i][1], i)
    for t in CAT['temas']:
        tid = t['id']; its = [i for i in TEM_ITEMS.get(tid, ()) if en24(i) and TRE[tid].search(ITEMS[i][0])]
        its.sort(key=lambda i: (0 if medio(ITEMS[i][2]) else 1, -ITEMS[i][3])); n0 = len(filas)
        for i in its:
            if len(filas) - n0 >= 30: break
            add('t', tid, ITEMS[i][0], ITEMS[i][1], i)
    for k in CAT['nivel1']:
        posts = {}
        for s in ('top', 'latest'):
            for p in raw['bsky'].get(k + ':' + s, []):
                if p[3] >= GEN_MIN - 1440: posts[p[8]] = p
        top = sorted(posts.values(), key=lambda p: -(p[4] + p[5] * 2 + p[6] + p[7]))[:25]
        for p in top: add('b', k, p[0].replace('\n', ' ')[:260], '@' + p[1], p[8], 'me gusta %d · rep %d · resp %d' % (p[4], p[5], p[6]))
    return filas

if __name__ == '__main__' and sys.argv[1:] == ['muestra']:
    filas = construir_muestra()
    json.dump(filas, open(os.path.join(W, 'muestra.json'), 'w'), ensure_ascii=False)
    with open(os.path.join(W, 'muestra.txt'), 'w') as f:
        last = None
        for n, r in enumerate(filas):
            g = (r['tipo'], r['pid'])
            if g != last:
                nombre = PID[r['pid']]['nombre'] if r['pid'] in PID else r['pid']
                f.write('\n## %s · %s\n' % ({'m': 'MEDIOS', 't': 'TEMA', 'b': 'BLUESKY'}[r['tipo']], nombre)); last = g
            f.write('%d|%s — %s\n' % (n, r['texto'], r['fuente']))
    cnt = collections.Counter(r['tipo'] for r in filas)
    print('gen', raw['gen'], 'hoy', HOY, 'filas', len(filas), dict(cnt))
    print('saturadas', sorted(SAT)[:40])
    for p in POLS[:6] + [PID['ayuso'], PID['matute']]:
        its = POL_ITEMS.get(p['id'], ()); print(p['id'], 'total', len(its), '24h', sum(en24(i) for i in its), 'tit24', sum(en24(i) and titular(p['id'], ITEMS[i][0]) for i in its))
    print('corpus17', len(CORPUS), 'chars muestra', os.path.getsize(os.path.join(W, 'muestra.txt')))

PRIMER = '2026-11-08'; PRIMER_INFORME = '2026-11-15'      # inicio del archivo
INICIAL = '--inicial' in sys.argv
REPO = '--repo' in sys.argv          # modo GitHub: ficheros por día natural, fusionados con lo ya publicado
# --- informe automático (sin IA: frases construidas con las cifras del día) -----------
def informe_auto(u):
    PN = {p['id']: p['nombre'] for p in POLS}; PRN = {p['id']: p['nombre'] for p in CAT['provincias']}
    mil = lambda n: f"{int(n):,}".replace(',', '.'); d1 = lambda x: str(x).replace('.', ',')
    rk = sorted(u['pol'].items(), key=lambda x: -x[1]['vol']); n1 = [i for i in CAT['nivel1'] if i in u['pol']]
    def tono(s):
        return ('de %d titulares clasificados, %d son negativos, %d neutros y %d positivos' % (s['n'], s['sent'][1], s['sent'][2], s['sent'][0])) if s['n'] else 'sin titulares clasificados por tono en esta recogida'
    zonas = []
    for t in CAT['temas']:
        c = [(v.get('idx', 0), k) for k, v in u['tem'][t['id']]['prov'].items() if v['n'] >= 12]
        if c:
            x, k = max(c); zonas.append((x, t, k, u['tem'][t['id']]['prov'][k]))
    zonas.sort(key=lambda z: -z[0]); a, sa = rk[0]
    titular = '%s concentra el %s %% de las menciones' % (PN[a], d1(sa['cuota']))
    if zonas: titular += '; %s es la zona más caliente en %s' % (PRN[zonas[0][2]], zonas[0][1]['nombre'].lower())
    claves = [{'t': 'Reparto de la conversación', 'd': 'Los medios españoles publican %s noticias que mencionan a alguien del catálogo en 24 horas. %s suman el %s %%.' % (
        mil(sum(s['vol'] for s in u['pol'].values())), ', '.join('%s (%s)' % (PN[i], mil(u['pol'][i]['vol'])) for i in n1), d1(round(sum(u['pol'][i]['cuota'] for i in n1), 1)))}]
    if u['historias']:
        h = u['historias'][:3]; claves.append({'t': 'Las historias más repetidas', 'd': ' '.join('«%s» (%d medios).' % (x['t'], x['medios']) for x in h)})
    picos = [al for al in u['alertas'] if al['tipo'] == 'pico'][:4]
    if picos: claves.append({'t': 'Quién sube', 'd': ' '.join('%s: %s' % (al['titulo'].replace('Pico de presencia: ', ''), al['detalle']) for al in picos)})
    neg = [al for al in u['alertas'] if al['tipo'] == 'tono'][:3]
    if neg: claves.append({'t': 'Titulares más adversos', 'd': ' '.join('%s: %s' % (al['titulo'].replace('Titulares mayoritariamente negativos: ', ''), al['detalle']) for al in neg)})
    if zonas: claves.append({'t': 'Zonas calientes', 'd': ' '.join('%s en %s: %s%d noticias en %s, %s veces lo esperable por población.' % (z[1]['nombre'], PRN[z[2]], 'al menos ' if z[3]['tope'] else '', z[3]['n'], z[1]['ventana'], d1(z[0])) for z in zonas[:3])})
    wk = sorted([(s['wiki'] / s['wiki7'], i, s) for i, s in u['pol'].items() if s.get('wiki7') and s['wiki'] >= 1500], reverse=True)[:3]
    if wk: claves.append({'t': 'Interés ciudadano', 'd': ' '.join('%s: %s visitas en Wikipedia ayer frente a %s de media.' % (PN[i], mil(s['wiki']), mil(s['wiki7'])) for _, i, s in wk)})
    lideres = []
    for i in n1:
        s = u['pol'][i]; h = next((x for x in u['historias'] if i in x['p']), None)
        lideres.append({'id': i, 'texto': '%s noticias (%s %% de cuota) y %s titulares con su nombre, %d de ellos en %d de las 17 cabeceras. En tono, %s.%s' % (
            mil(s['vol']), d1(s['cuota']), mil(s['tit']), s['cat'], s['medios17'], tono(s), (' Historia más repetida: «%s» (%d medios).' % (h['t'], h['medios'])) if h else '')})
    temas = []
    for t in CAT['temas']:
        s = u['tem'][t['id']]; z = next((z for z in zonas if z[1]['id'] == t['id']), None)
        temas.append({'id': t['id'], 'texto': 'Ocupa el %s %% de los titulares de las 17 cabeceras (%d de %s).%s%s' % (d1(s['agendaPct']), s['agenda17'], mil(u['corpus']['n']),
            (' Zona con más intensidad: %s (%s%d noticias, %s veces lo esperable).' % (PRN[z[2]], 'al menos ' if z[3]['tope'] else '', z[3]['n'], d1(z[0]))) if z else '',
            (' De %d titulares clasificados, %d tienen tono negativo.' % (s['n'], s['sent'][1])) if s['n'] else '')})
    x = u.get('x'); rel = [a_['t'] for a_ in (x['ahora'] if x else []) if a_['p'] or a_['k']][:8]
    b = u['bsky']; redes = 'Bluesky recoge %d publicaciones sobre los candidatos seguidos en profundidad en 24 horas; es una red pequeña y no representa al conjunto del electorado.' % sum(b[i]['n'] for i in n1 if i in b)
    if rel: redes += ' Tendencias de X relacionadas con el catálogo: %s.' % ', '.join(rel)
    if u.get('meneame'): redes += ' En Menéame, lo más votado: «%s» (%d votos, %d comentarios).' % (u['meneame'][0]['t'], u['meneame'][0]['votos'], u['meneame'][0]['com'])
    return {'titular': titular, 'entradilla': 'Informe generado automáticamente con los datos de las últimas 24 horas. Cada cifra procede de las fuentes públicas que se detallan al final.',
            'claves': claves, 'lideres': lideres, 'temas': temas, 'redes': redes, 'vigilar': [al['titulo'] + '. ' + al['detalle'] for al in u['alertas'][:5]],
            'metodo': 'Presencia: noticias de medios españoles indexadas por Google News que mencionan a cada político (hasta 100 por consulta; para el nivel 1 se suma una consulta por cada una de las 17 cabeceras). Tono, postura y emoción: clasificación automática de una muestra de titulares de las últimas 24 horas; describe cómo queda el político en el titular, incluidos los ataques de rivales, y no equivale a opinión pública. Zonas calientes: noticias que relacionan cada tema con cada provincia, comparadas con lo esperable por población. Interés ciudadano: visitas diarias a Wikipedia. X: tendencias de España por horas. Bluesky y Menéame: publicaciones públicas con sus cifras de difusión.'}

# --- publicación -------------------------------------------------------------
COLECTOR_PARCHES = [('if (lite) { out.push([t, s, ts]); continue; }', 'if (lite) { out.push([t, s, ts, dom]); continue; }'), ('return lite ? { n: out.length, top: out.slice(0, 4) } : out;', 'return lite ? { n: out.length, doms: out.map(o => o[3]), top: out.slice(0, 8) } : out;'), ('D.tp[id + \':\' + cod] = await PRO.gn(q + \' "\' + nom + \'" when:\' + w, true);', 'D.tp[id + \':\' + cod] = await PRO.gn(q + \' "\' + nom + \'"\' + (nom === \'León\' ? \' -"León XIV" -Papa\' : \'\') + \' when:\' + w, true);')]
STOP = set('de la el en y a los las del que por con para un una al se su sus lo es no más mas como pero o e ante tras sobre entre sin ya le les este esta estos estas ha han fue ser son muy tambien también cuando donde quien quién qué que cómo como sí si'.split())
def toks(s): return {w for w in norm(s).split() if len(w) > 2 and w not in STOP}
def cargar_aux(src):
    best = None
    for f in ([] if REPO else sorted(glob.glob('/tmp/claude-tool-results/*/*'), key=os.path.getmtime)):   # solo en la recogida antigua por navegador
        try:
            t = json.load(open(f))[0]['text']
            if '"src":"%s"' % src in t[:400]: best = json.loads(t[t.index('---\n') + 4:])
        except Exception: pass
    if best: json.dump(best, open(os.path.join(W, 'aux_%s.json' % src), 'w'), ensure_ascii=False)
    p = os.path.join(W, 'aux_%s.json' % src)
    return json.load(open(p)) if os.path.exists(p) else None
def fuentes_es():
    s = set()
    for its in POL_ITEMS.values():
        for i in its: s.add(ITEMS[i][2])
    return s
def publicar():
    os.makedirs(DATA, exist_ok=True)
    ANT = {}; ARR = [0]
    if REPO and os.path.exists(os.path.join(DATA, 'ultimo.json')):
        try: ANT = json.load(open(os.path.join(DATA, 'ultimo.json')))
        except Exception: ANT = {}
    filas = json.load(open(os.path.join(W, 'muestra.json')))
    et = {}
    etp = os.path.join(W, 'etiquetas.txt')
    for l in (open(etp) if os.path.exists(etp) else []):
        a = l.split()
        if len(a) == 2: et[int(a[0])] = a[1]
    # etiquetas por (item, político) / (item, '_') / post de Bluesky
    LAB = {}; LABB = {}; DESC = set()
    for n, r in enumerate(filas):
        c = et.get(n)
        if not c: continue
        if r['tipo'] == 'b':
            if c != '----': LABB[(r['pid'], r['refs'][0])] = c
            continue
        for i in r['refs']:
            if c == '----': DESC.add((i, r['pid'])); continue
            LAB.setdefault(i, {})[r['pid'] if r['tipo'] == 'm' else '_'] = c
    ES = fuentes_es()
    FUERA = re.compile(r'\.(mx|ar|co|pe|cl|ec|ve|uy|py|bo|do|hn|gt|sv|ni|cr|pa|cu|pr|us|br|pt)$|mexico|milenio|mvsnoticias|univision|telemundo|oem\.com|infobae\.com/america|cnnespanol|elcomercio|larepublica|prensa-latina|eltiempo|elespectador|clarin|lanacion|emol\.|latercera')
    AMBIG = {'24', '14', '19', '16', '46', '26', '45', '18', '49', '37', '23', '50', '47', '41', '29', '40', '28', '08'}
    def es_es(dom, estricto=True):
        if FUERA.search(dom): return False
        return dom in ES or dom.endswith(('.es', '.cat', '.eus', '.gal')) or not estricto
    for src in (() if REPO else ('provincias', 'provleon')):     # repesca de provincias de la recogida antigua por navegador
        aux = cargar_aux(src)
        if aux:
            for k, x in aux['tp'].items():
                if x: raw['tp'][k] = x
    for k, x in list(raw['tp'].items()):
        if x and 'doms' in x:
            cod = k.split(':')[1]; ok = [es_es(d, cod in AMBIG) for d in x['doms']]
            raw['tp'][k] = {'n': sum(ok), 'bruto': x['n'], 'top': [a for a in x['top'] if es_es(a[3], cod in AMBIG)][:4]}
    # ---- tabla de menciones (titulares) ----
    M = {}
    def men(i):
        if i not in M:
            t = ITEMS[i]
            M[i] = {'id': mid(i), 't': t[0], 's': t[1], 'm': medio(t[2]), 'ts': t[3], 'l': t[4], 'p': [], 'k': temas_de(t[0]), 'c': dict(LAB.get(i, {}))}
        return M[i]
    polstats = {}
    dias8 = [(GEN.astimezone(TZ) - timedelta(days=k)).strftime('%Y-%m-%d') for k in range(7, -1, -1)]
    HIST = {}                               # lo ya publicado por día: la cifra de un día nunca baja al recalcularla, porque Google
    if not INICIAL:                         # solo devuelve 100 resultados por consulta y los días pasados se ven peor que en su momento
        for x in dias8:
            fp = os.path.join(DATA, 'hist-%s.json' % x)
            try: HIST[x] = json.load(open(fp)) if os.path.exists(fp) else None
            except Exception: HIST[x] = None
    for p in POLS:
        pid = p['id']; its = POL_ITEMS.get(pid, set())
        its = {i for i in its if (i, pid) not in DESC}
        tit = {i for i in its if titular(pid, ITEMS[i][0])}
        for i in tit: men(i)['p'].append(pid)
        d = {x: [0, 0, 0] for x in dias8}
        for i in its:
            k = dia(ITEMS[i][3])
            if k in d:
                d[k][0] += 1; d[k][1] += (i in tit); d[k][2] += (i in tit and medio(ITEMS[i][2]) is not None)
        for x, h in HIST.items():
            if h:
                for j, campo in enumerate(('vol', 'tit', 'cat')): d[x][j] = max(d[x][j], (h.get(campo) or {}).get(pid) or 0)
        v24 = [i for i in its if en24(i)]; t24 = [i for i in tit if en24(i)]
        base = POL_BASE.get(pid, set()); b24 = sum(1 for i in base if en24(i)); v48 = [i for i in base if en48(i)]
        fu = collections.Counter(ITEMS[i][1] for i in t24)
        horas = [0] * 24
        for i in t24: horas[min(23, (ITEMS[i][3] - (GEN_MIN - 1440)) // 60)] += 1
        se = collections.Counter(); po = collections.Counter(); em = collections.Counter(); te = collections.Counter(); n = 0
        for i in t24:
            c = LAB.get(i, {}).get(pid)
            if c: n += 1; se[c[0]] += 1; po[c[1]] += 1; em[c[2]] += 1; te[c[3]] += 1
        prev = [d[x][0] for x in dias8[:-1]]
        polstats[pid] = {'vol': len(v24), 'tit': len(t24), 'cat': sum(1 for i in t24 if medio(ITEMS[i][2])), 'medios17': len({medio(ITEMS[i][2]) for i in t24 if medio(ITEMS[i][2])}),
            'base': b24, 'prev': len(v48), 'media7': round(sum(prev) / max(1, len(prev)), 1), 'tope': b24 >= 95 or any(s[0] == pid and s[1] == 'p1' for s in SAT),
            'fuentes': fu.most_common(8), 'horas': horas, 'n': n, 'sent': [se['P'], se['N'], se['U']], 'post': [po['F'], po['C'], po['N']],
            'emo': dict(em), 'tem': dict(te), 'agenda17': sum(1 for i in CORPUS if titular(pid, ITEMS[i][0])), 'dias': d}
    tot = sum(s['vol'] for s in polstats.values()) or 1
    for s in polstats.values(): s['cuota'] = round(100 * s['vol'] / tot, 1)
    # ---- temas ----
    temstats = {}
    for t in CAT['temas']:
        tid = t['id']; its = {i for i in TEM_ITEMS.get(tid, set()) if TRE[tid].search(ITEMS[i][0]) and es_es(ITEMS[i][2]) and (i, tid) not in DESC}
        for i in its: men(i)
        t24 = [i for i in its if en24(i)]
        se = collections.Counter(); em = collections.Counter(); n = 0
        for i in t24:
            c = LAB.get(i, {}).get('_')
            if c: n += 1; se[c[0]] += 1; em[c[2]] += 1
        ag = [i for i in CORPUS if TRE[tid].search(ITEMS[i][0])]
        prov = {}; ant = ((ANT.get('tem') or {}).get(tid) or {}).get('prov') or {}
        for pr in CAT['provincias']:
            x = raw['tp'].get(tid + ':' + pr['id'])
            if x: prov[pr['id']] = {'n': x['n'], 'tope': x.get('bruto', x['n']) >= 98 and x['n'] >= 90, 'x100k': round(x['n'] / (pr['pob'] / 100), 1), 'top': [[a[0], a[1], a[2]] for a in x['top'][:3]]}
            elif pr['id'] in ant and (tid + ':' + pr['id']) in raw['tp']:      # consulta que no dio tiempo a hacer: se conserva el último dato publicado
                prov[pr['id']] = {k: v for k, v in ant[pr['id']].items() if k != 'idx'}; ARR[0] += 1
        foco = {}
        for (a, b), v in FOCO.items():
            if a == tid:
                vv = sorted(v, key=lambda i: -ITEMS[i][3]); foco[b] = {'n7': len(v), 'n1': sum(en24(i) for i in v), 'top': [men(i)['id'] for i in vv[:8]]}
                for i in vv[:8]: men(i)['k'] = sorted(set(men(i)['k'] + [tid]))
        if prov:
            import math
            xs = [(math.log(pr['pob']), math.log(prov[pr['id']]['n'] + 1)) for pr in CAT['provincias'] if pr['id'] in prov and not prov[pr['id']]['tope']]
            mx = sum(x for x, _ in xs) / len(xs); my = sum(y for _, y in xs) / len(xs)
            b = sum((x - mx) * (y - my) for x, y in xs) / max(1e-9, sum((x - mx) ** 2 for x, _ in xs)); a = my - b * mx
            for pr in CAT['provincias']:
                if pr['id'] in prov: prov[pr['id']]['idx'] = round((prov[pr['id']]['n'] + 1) / math.exp(a + b * math.log(pr['pob'])), 2)
        temstats[tid] = {'vol': len(t24), 'tope': len(t24) >= 95, 'agenda17': len(ag), 'agendaPct': round(100 * len(ag) / max(1, len(CORPUS)), 1),
            'n': n, 'sent': [se['P'], se['N'], se['U']], 'emo': dict(em), 'prov': prov, 'foco': foco, 'ventana': t['ventana']}
    for i in CORPUS:
        if temas_de(ITEMS[i][0]) or any(titular(p['id'], ITEMS[i][0]) for p in POLS): pass
    # ---- historias del día (agrupación de titulares parecidos, 24 h) ----
    cand = sorted([i for i, m in M.items() if en24(i) and m['p']], key=lambda i: ITEMS[i][3])
    cl = []
    for i in cand:
        tk = toks(ITEMS[i][0])
        if len(tk) < 4: continue
        best = None; bs = 0
        for c in cl:
            j = len(tk & c['tk']) / len(tk | c['tk'])
            if j > bs: bs = j; best = c
        if best and bs >= 0.38: best['its'].append(i); best['tk'] |= tk if len(best['its']) < 4 else set()
        else: cl.append({'tk': set(tk), 'its': [i]})
    hist = []
    for c in sorted(cl, key=lambda c: -len({ITEMS[i][1] for i in c['its']}))[:14]:
        its = c['its']; rep = sorted(its, key=lambda i: (0 if medio(ITEMS[i][2]) else 1, len(ITEMS[i][0])))[0]
        pc = collections.Counter(p for i in its for p in M[i]['p'])
        hist.append({'t': ITEMS[rep][0], 's': ITEMS[rep][1], 'id': M[rep]['id'], 'n': len(its), 'medios': len({ITEMS[i][1] for i in its}), 'p': [p for p, _ in pc.most_common(3)]})
    # ---- Bluesky ----
    bsky = {}
    for k, _q in raw['cfg']['bsky']:
        posts = {}
        for s in ('top', 'latest'):
            for p in raw['bsky'].get(k + ':' + s, []):
                if p[3] >= GEN_MIN - 1440: posts[p[8]] = p
        ps = sorted(posts.values(), key=lambda p: -(p[4] + p[5] + p[6] + p[7]))
        se = collections.Counter(LABB[(k, p[8])][0] for p in ps if (k, p[8]) in LABB); po = collections.Counter(LABB[(k, p[8])][1] for p in ps if (k, p[8]) in LABB)
        bsky[k] = {'n': len(ps), 'tope': len(raw['bsky'].get(k + ':latest', [])) >= 98, 'likes': sum(p[4] for p in ps), 'rep': sum(p[5] for p in ps), 'resp': sum(p[6] for p in ps), 'citas': sum(p[7] for p in ps),
            'nclas': sum(se.values()), 'sent': [se['P'], se['N'], se['U']], 'post': [po['F'], po['C'], po['N']],
            'top': [{'t': p[0][:300], 'a': p[1], 'n': p[2], 'ts': p[3], 'likes': p[4], 'rep': p[5], 'resp': p[6], 'citas': p[7], 'u': 'https://bsky.app/profile/%s/post/%s' % (p[1], p[8]), 'c': LABB.get((k, p[8]), '')} for p in ps[:12]]}
    # ---- Wikipedia ----
    wdias = [v[0] for v in raw['wiki']['sanchez']['v']]
    wiki = {pid: [dict(w['v']).get(d, 0) for d in wdias] for pid, w in raw['wiki'].items()}
    for pid, s in polstats.items():
        w = wiki.get(pid, [])
        s['wiki'] = w[-1] if w else 0; s['wiki7'] = round(sum(w[-8:-1]) / 7) if len(w) > 8 else 0
    # ---- tendencias ----
    def rel_de(txt):
        ps = [p['id'] for p in POLS if titular(p['id'], txt) or p['nombre'].lower() == txt.lower()]
        return ps, temas_de(txt)
    X = cargar_aux('trends24'); G = cargar_aux('gtrends'); ME = cargar_aux('meneame')
    xt = None
    if X:
        ah = []
        for n, (name, cnt) in enumerate(X['ahora']):
            ps, ts = rel_de(name); h = next((x for x in X['hist'] if x[0] == name), None)
            ah.append({'t': name, 'puesto': n + 1, 'horas': min(X['horas'], h[1]) if h else 1, 'p': ps, 'k': ts})
        xt = {'cuando': X['at'], 'horas': X['horas'], 'ahora': ah, 'persistentes': [{'t': x[0], 'horas': min(X['horas'], x[1]), 'mejor': x[2], 'p': rel_de(x[0])[0], 'k': rel_de(x[0])[1]} for x in X['hist'][:40]]}
    gt = [{'t': x['t'], 'trafico': x['tr'], 'noticias': x['news'][:2]} for x in G['items']] if G else []
    mn = []
    if ME:
        for x in ME['items']:
            ps, ts = rel_de(x['t'])
            mn.append({'t': x['t'], 'l': x['l'], 'sub': x['sub'], 'votos': x['v'], 'com': x['c'], 'karma': x['k'], 'clics': x['cl'], 'p': ps, 'k': ts})
        mn.sort(key=lambda x: -x['votos'])
    # ---- YouTube y Telegram ----
    RD = {}
    try: RD = json.load(open(os.path.join(W, 'aux_redes.json'), encoding='utf-8'))
    except Exception: RD = {}
    n1ids = [i for i in CAT['nivel1'] if i in PID]
    def menc_red(textos):
        m = {}
        for pid in n1ids:
            l = [x for x in textos if titular(pid, x['t'])]
            m[pid] = {'n': len(l), 'vistas': sum(x.get('vistas') or 0 for x in l), 'top': sorted(l, key=lambda x: -(x.get('vistas') or 0))[:3]}
        return m
    yt = None
    if RD.get('youtube'):
        cans, todos = [], []
        for c in CAT.get('youtube') or []:
            r = RD['youtube'].get(c.get('clave') or c.get('handle')) or {}
            vids = [{'t': v[1], 'u': 'https://www.youtube.com/watch?v=' + v[0], 'ts': v[2], 'vistas': v[3], 'mg': v[4], 'canal': c['nombre'], 'tipo': c['tipo']} for v in r.get('v', []) if v[2]]
            v7 = [v for v in vids if v['ts'] >= GEN_MIN - 7 * 1440]; todos += v7
            cans.append({'nombre': c['nombre'], 'handle': c.get('handle'), 'tipo': c['tipo'], 'partido': c['partido'], 'ok': 'v' in r, 'error': r.get('error'),
                         'url': ('https://www.youtube.com/@' + c['handle']) if c.get('handle') else 'https://www.youtube.com/channel/' + c.get('id', ''), 'n7': len(v7), 'vistas7': sum(v['vistas'] or 0 for v in v7),
                         'top': max(v7, key=lambda v: v['vistas'] or 0) if v7 else None, 'ultimo': vids[0] if vids else None})
        yt = {'canales': cans, 'n1': menc_red(todos), 'top': sorted(todos, key=lambda v: -(v['vistas'] or 0))[:10]}
    tg = None
    if RD.get('telegram'):
        cans, todos = [], []
        for c in CAT.get('telegram') or []:
            r = RD['telegram'].get(c['canal']) or {}
            ms = [{'t': m[1], 'u': 'https://t.me/%s/%s' % (c['canal'], m[0]), 'ts': m[2], 'vistas': m[3], 'canal': c['nombre'], 'tipo': c['tipo']} for m in r.get('m', []) if m[2]]
            m7 = [m for m in ms if m['ts'] >= GEN_MIN - 7 * 1440]; todos += m7
            vv = [m['vistas'] for m in m7 if m['vistas']]
            cans.append({'nombre': c['nombre'], 'canal': c['canal'], 'tipo': c['tipo'], 'partido': c['partido'], 'ok': 'm' in r, 'error': r.get('error'), 'subs': r.get('subs'),
                         'url': 'https://t.me/s/' + c['canal'], 'n7': len(m7), 'vistasMedia': round(sum(vv) / len(vv)) if vv else 0,
                         'top': max(m7, key=lambda m: m['vistas'] or 0) if m7 else None})
        tg = {'canales': cans, 'n1': menc_red(todos), 'top': sorted(todos, key=lambda m: -(m['vistas'] or 0))[:10]}
    # ---- alertas ----
    al = []
    def alerta(tipo, sev, titulo, detalle, ref=None): al.append({'id': hashlib.sha1((HOY + tipo + titulo).encode()).hexdigest()[:10], 'tipo': tipo, 'sev': sev, 'titulo': titulo, 'detalle': detalle, 'ref': ref, 'fecha': HOY})
    for p in POLS:
        s = polstats[p['id']]
        if s['media7'] >= 5 and s['vol'] >= 20 and s['vol'] >= 2 * s['media7'] and not s['tope']:
            alerta('pico', 2, 'Pico de presencia: %s' % p['nombre'], '%d noticias en 24 h frente a una media de %s al día en la última semana.' % (s['vol'], str(s['media7']).replace('.', ',')), {'pol': p['id']})
        if s['n'] >= 10 and s['sent'][1] / s['n'] >= 0.6:
            alerta('tono', 2, 'Titulares mayoritariamente negativos: %s' % p['nombre'], '%d de %d titulares clasificados en 24 h tienen tono negativo.' % (s['sent'][1], s['n']), {'pol': p['id']})
        if s['medios17'] >= 12:
            alerta('portada', 1, '%s, en titulares de %d de las 17 cabeceras' % (p['nombre'], s['medios17']), '%d titulares en las cabeceras del catálogo en 24 h.' % s['cat'], {'pol': p['id']})
        if s['wiki'] >= 1500 and s['wiki7'] and s['wiki'] >= 2 * s['wiki7']:
            alerta('atencion', 1, 'Sube el interés ciudadano por %s' % p['nombre'], '%s visitas a su página de Wikipedia ayer, frente a %s de media diaria.' % (f"{s['wiki']:,}".replace(',', '.'), f"{s['wiki7']:,}".replace(',', '.')), {'pol': p['id']})
    if xt:
        for a in xt['ahora']:
            if a['p'] or (a['k'] and a['t'].startswith('#')):
                quien = ', '.join(PID[x]['nombre'] for x in a['p']) or ', '.join(next(t['nombre'] for t in CAT['temas'] if t['id'] == k) for k in a['k'])
                alerta('tendencia', 2 if a['puesto'] <= 15 else 1, 'Tendencia en X: %s' % a['t'], 'Puesto %d en España; %d de las últimas %d horas en tendencias. Relacionado con %s.' % (a['puesto'], a['horas'], xt['horas'], quien), {'x': a['t']})
    for t in CAT['temas']:
        pv = temstats[t['id']]['prov']
        if not pv: continue
        cand2 = [(v['idx'], k) for k, v in pv.items() if v['n'] >= 12]
        if cand2:
            x, k = max(cand2); nom = next(p['nombre'] for p in CAT['provincias'] if p['id'] == k)
            if x >= 1.8: alerta('zona', 2, 'Zona caliente de %s: %s' % (t['nombre'].lower(), nom), '%s%d noticias en %s: %s veces lo esperable para una provincia de su tamaño.' % ('Al menos ' if pv[k]['tope'] else '', pv[k]['n'], t['ventana'], str(x).replace('.', ',')), {'tema': t['id'], 'prov': k})
    vistos_u = set()
    for k, b in bsky.items():
        if b['top'] and (b['top'][0]['likes'] + b['top'][0]['rep']) >= 300 and b['top'][0]['u'] not in vistos_u:
            p0 = b['top'][0]; vistos_u.add(p0['u']); alerta('viral', 1, 'Publicación con mucha difusión en Bluesky', '@%s: %d me gusta y %d republicaciones. «%s…»' % (p0['a'], p0['likes'], p0['rep'], p0['t'][:110].replace('\n', ' ')), {'u': p0['u']})
    al.sort(key=lambda a: -a['sev'])
    # ---- ficheros por día ----
    pordia = collections.defaultdict(list)
    if INICIAL:
        for i, m in M.items():
            if m['p'] or m['k']: pordia[dia(m['ts'])].append(m)
    elif REPO:                              # GitHub: hoy y ayer por día natural, fusionados con lo ya publicado
        for i, m in M.items():
            d = dia(m['ts'])
            if (m['p'] or m['k']) and d in dias8[-2:]:
                if not (m['m'] or m['c']): m = dict(m, l='')          # enlaces largos solo en cabeceras del catálogo y clasificados
                pordia[d].append(m)
        for d in dias8[-2:]:
            fp = os.path.join(DATA, 'dia-%s.json' % d)
            if os.path.exists(fp):
                nuevos = {m['id']: m for m in pordia[d]}
                for v in json.load(open(fp))['menciones']:
                    n = nuevos.get(v['id'])
                    if n is None: pordia[d].append(v)
                    else:
                        for k, c in (v.get('c') or {}).items(): n['c'].setdefault(k, c)
                        if v.get('l') and not n.get('l'): n['l'] = v['l']
    else:                                   # recogida diaria: un fichero con las últimas 48 h (el panel quita duplicados)
        for i, m in M.items():
            if (m['p'] or m['k']) and m['ts'] >= GEN_MIN - 2880: pordia[HOY].append(m)
    dias_pub = []
    for d, ms in sorted(pordia.items()):
        if d not in dias8: continue
        ms.sort(key=lambda m: -m['ts'])
        json.dump({'fecha': d, 'menciones': ms}, open(os.path.join(DATA, 'dia-%s.json' % d), 'w'), ensure_ascii=False, separators=(',', ':'))
        dias_pub.append(d)
    for d in (dias8 if INICIAL else dias8[-2:]):   # histórico compacto por fecha
        json.dump({'fecha': d, 'vol': {pid: s['dias'][d][0] for pid, s in polstats.items()}, 'tit': {pid: s['dias'][d][1] for pid, s in polstats.items()}, 'cat': {pid: s['dias'][d][2] for pid, s in polstats.items()}},
                  open(os.path.join(DATA, 'hist-%s.json' % d), 'w'), separators=(',', ':'))
    # ---- serie ----
    serie = {'dias': dias8, 'vol': {pid: [s['dias'][d][0] for d in dias8] for pid, s in polstats.items()}, 'tit': {pid: [s['dias'][d][1] for d in dias8] for pid, s in polstats.items()},
             'cat': {pid: [s['dias'][d][2] for d in dias8] for pid, s in polstats.items()}, 'wikiDias': ['%s-%s-%s' % (d[:4], d[4:6], d[6:8]) for d in wdias], 'wiki': wiki,
             }
    json.dump(serie, open(os.path.join(DATA, 'serie.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    for s in polstats.values(): s.pop('dias')
    med = collections.Counter(medio(ITEMS[i][2]) for i in CORPUS)
    inf_p = os.path.join(W, 'informe.json')
    ult = {'generado': raw['gen'], 'fecha': HOY, 'ventana': [GEN_MIN - 1440, GEN_MIN], 'pol': polstats, 'tem': temstats, 'historias': hist, 'bsky': bsky, 'x': xt, 'google': gt, 'meneame': mn[:25],
           'alertas': al, 'youtube': yt, 'telegram': tg, 'corpus': {'n': len(CORPUS), 'medios': dict(med)},
           'cobertura': {'consultas': len(raw['q']) + len(raw['tp']), 'noticias': len(ITEMS), 'clasificadas': sum(1 for c in et.values() if c != '----'), 'errores': len(raw['err']), 'ms': raw['ms'],
                         'bluesky': sum(b['n'] for b in bsky.values()), 'wikipedia': len(wiki), 'saturadas': sorted({s[0] for s in SAT}), 'provAnteriores': ARR[0],
                         'provGenerado': raw.get('provGenerado') or ((ANT.get('cobertura') or {}).get('provGenerado') if ARR[0] else raw['gen']),
                         'youtube': sum(1 for c in (yt or {}).get('canales', []) if c['ok']), 'telegram': sum(1 for c in (tg or {}).get('canales', []) if c['ok'])},
           'informe': json.load(open(inf_p)) if os.path.exists(inf_p) else None,
           'avisos': sorted(set((raw['cfg'].get('aviso') or []) + (CAT.get('avisos') or [])))}
    if not ult['informe'] or '--auto-informe' in sys.argv: ult['informe'] = informe_auto(ult)
    json.dump(ult, open(os.path.join(DATA, 'ultimo.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    if ult['informe']: json.dump({'fecha': HOY, 'generado': raw['gen'], 'informe': ult['informe']}, open(os.path.join(DATA, 'informe-%s.json' % HOY), 'w'), ensure_ascii=False)
    json.dump(CAT, open(os.path.join(DATA, 'catalogo.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'ultima': HOY, 'generado': raw['gen'], 'primer': PRIMER, 'primerInforme': PRIMER_INFORME}, open(os.path.join(DATA, 'estado.json'), 'w'), ensure_ascii=False)
    # colector reutilizable
    src = raw.get('src')
    if src:
        os.makedirs(os.path.join(W, '..', 'colector'), exist_ok=True)
        for a, b in COLECTOR_PARCHES:
            for k in ('gn', 'run'):
                src[k] = src[k].replace(a, b)
        js = "window.PRO = { S: { status: 'idle', done: 0, total: 0, err: [], phase: '', t0: 0 }, items: [], key: new Map(), data: {} };\nPRO.cfg = " + json.dumps(raw['cfg'], ensure_ascii=False) + ";\n" + ''.join('PRO.%s = %s;\n' % (k, src[k]) for k in ('zz', 'dec', 'add', 'gn', 'pool', 'run')) + "setTimeout(() => { PRO.run().catch(e => { PRO.S.status = 'fail: ' + e.message; }); }, 50);\n'started'\n"
        open(os.path.join(W, '..', 'colector', 'colector.js'), 'w').write(js)
    return ult, M, dias_pub

if __name__ == '__main__' and sys.argv[1:2] == ['publicar']:
    ult, M, dias_pub = publicar()
    print('dias', dias_pub, 'menciones', len(M), 'alertas', len(ult['alertas']))
    for f in sorted(glob.glob(os.path.join(DATA, '*.json'))): print(' ', os.path.basename(f), os.path.getsize(f))
    top = sorted(ult['pol'].items(), key=lambda x: -x[1]['vol'])[:14]
    for pid, s in top: print('%-10s vol %4d tit %3d cat %3d m17 %2d prev %4d med7 %6.1f cuota %4.1f n %3d sent %s post %s wiki %6d/%6d ag17 %d' % (pid, s['vol'], s['tit'], s['cat'], s['medios17'], s['prev'], s['media7'], s['cuota'], s['n'], s['sent'], s['post'], s['wiki'], s['wiki7'], s['agenda17']))
    for tid, t in ult['tem'].items():
        pv = sorted(t['prov'].items(), key=lambda x: -x[1]['x100k'])[:5]
        print(tid, 'vol', t['vol'], 'tope', t['tope'], 'agenda', t['agenda17'], t['agendaPct'], 'sent', t['sent'], 'foco', {k: (v['n7'], v['n1']) for k, v in t['foco'].items()}, 'prov top', [(k, v['n'], v['x100k']) for k, v in pv])
    for a in ult['alertas']: print(' !', a['sev'], a['tipo'], '|', a['titulo'], '|', a['detalle'][:120])
    print('historias'); [print('  ', h['medios'], h['n'], h['p'], h['t'][:110]) for h in ult['historias']]
    print('bsky', {k: (b['n'], b['likes'], b['rep'], b['nclas'], b['sent'], b['post']) for k, b in ult['bsky'].items()})
    print('x ahora rel', [(a['t'], a['puesto'], a['horas']) for a in ult['x']['ahora'] if a['p'] or a['k']] if ult['x'] else None)
    print('google', [g['t'] for g in ult['google']]); print('meneame', [(m['votos'], m['com'], m['t'][:50]) for m in ult['meneame'][:5]])
    print('cobertura', ult['cobertura'])
