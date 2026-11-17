#!/usr/bin/env python3
# Prometeo · recogida en servidor (GitHub Actions). Todas las fuentes son públicas y gratuitas.
# Genera pipeline/raw.json con el mismo formato que el colector de navegador (colector/colector.js).
import json, os, re, sys, time, html, threading, collections, random
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from email.utils import parsedate_to_datetime
import requests

W = os.path.dirname(os.path.abspath(__file__))
import seguimiento
C = seguimiento.config()          # qué se sigue: ../seguimiento.yml (con la última versión buena si tiene errores)
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36', 'Accept-Language': 'es-ES,es;q=0.9'})
WIKI_UA = {'User-Agent': 'PrometeoEscucha/1.0 (panel de escucha social; https://github.com/' + os.environ.get('GITHUB_REPOSITORY', 'prometeo') + ')'}
ERR, ITEMS, KEY, LOCK = [], [], {}, threading.Lock()
PROVG = [None]
NOW = datetime.now(timezone.utc); T0 = time.time()
PAUSA = float(os.environ.get('PROM_PAUSA', '0.9'))        # pausa mínima entre consultas a Google News (segundos)
HILOS = int(os.environ.get('PROM_HILOS', '1'))            # un solo hilo: Google frena menos un ritmo constante que las ráfagas
PAUSA_MAX = 4.0
MAX_MIN = float(os.environ.get('PROM_MAX_MIN', '20'))     # pasado este tiempo se dejan las consultas no esenciales (provincias)
TOPE_MIN = float(os.environ.get('PROM_TOPE_MIN', '30'))   # pasado este tiempo sin lo esencial se abandona sin publicar nada
FRENO = {'pausa': PAUSA, 'abortar': False}                # si Google frena, baja el ritmo; si no responde nada, se abandona pronto
ESENCIAL = ('p7', 'p1', 'pd', 'm1', 't1', 't7')
def minutos(): return (time.time() - T0) / 60
def resumen():
    c = collections.Counter(e.split(' ')[0] for e in ERR)
    if c: print('errores por tipo:', dict(c), '· pausa actual %.2f s' % FRENO['pausa'], flush=True)

def day(k): return (NOW - timedelta(days=k)).strftime('%Y-%m-%d')
def dec(s): return html.unescape(re.sub(r'<!\[CDATA\[|\]\]>', '', s or '')).replace('\xa0', ' ').strip()
def g(b, pat):
    m = re.search(pat, b, re.S); return dec(m.group(1)) if m else ''
def add(t, s, dom, ts, l):
    k = t + '|' + s
    with LOCK:
        i = KEY.get(k)
        if i is None:
            i = len(ITEMS); ITEMS.append([t, s, dom, ts, l]); KEY[k] = i
        return i

def gn(q, lite=False, opcional=False):
    """Una consulta a Google News RSS (edición España). Devuelve índices de noticias o, en modo ligero, recuento y dominios.
    Devuelve None si no hubo respuesta válida (o si la consulta era opcional y ya no queda tiempo)."""
    u = 'https://news.google.com/rss/search?q=' + quote(q) + '&hl=es&gl=ES&ceid=ES:es'
    for a in range(3):
        if FRENO['abortar'] or (opcional and minutos() > MAX_MIN): return None
        if minutos() > TOPE_MIN: FRENO['abortar'] = True; return None
        try:
            r = S.get(u, timeout=30)
            if r.status_code == 200 and '<rss' in r.text[:800]:
                out = []
                for b in re.findall(r'<item>(.*?)</item>', r.text, re.S):
                    t = g(b, r'<title>(.*?)</title>'); s = g(b, r'<source[^>]*>(.*?)</source>')
                    dom = re.sub(r'/.*$', '', re.sub(r'^https?://(www\.)?', '', g(b, r'<source url="([^"]*)"')))
                    if s and t.endswith(' - ' + s): t = t[:-(len(s) + 3)]
                    try: ts = round(parsedate_to_datetime(g(b, r'<pubDate>(.*?)</pubDate>')).timestamp() / 60)
                    except Exception: continue
                    if lite: out.append([t, s, ts, dom]); continue
                    l = re.sub(r'\?oc=5$', '', g(b, r'<link>(.*?)</link>').replace('https://news.google.com/rss/articles/', ''))
                    out.append(add(t, s, dom, ts, l))
                FRENO['pausa'] = max(PAUSA, FRENO['pausa'] * 0.97)
                return {'n': len(out), 'doms': [o[3] for o in out], 'top': out[:8]} if lite else out
            ERR.append('%s %s' % (r.status_code, q[:50]))
            FRENO['pausa'] = min(PAUSA_MAX, FRENO['pausa'] * 1.5)
            if not ITEMS and len(ERR) >= 9: FRENO['abortar'] = True; return None      # ni una respuesta válida: no merece la pena insistir
            time.sleep(8 * (a + 1) + random.uniform(0, 4))
        except Exception as e:
            ERR.append('X %s %s' % (type(e).__name__, q[:50])); time.sleep(6)
    return None

def pool(jobs, n=None):
    def w(j):
        t = time.time()
        try: j()
        except Exception as e: ERR.append('J ' + repr(e)[:90])
        if time.time() - t > 0.05: time.sleep(FRENO['pausa'] * random.uniform(0.8, 1.25))
    with ThreadPoolExecutor(n or HILOS) as ex: list(ex.map(w, jobs))

def minuto(s):
    try: return round(datetime.fromisoformat(re.sub(r'(\.\d{6})\d+', r'\1', s.replace('Z', '+00:00'))).timestamp() / 60)
    except Exception: return round(NOW.timestamp() / 60)

def principal():
    Q, TP, BS, WK, WM = {}, {}, {}, {}, {'m': {}, 'miss': []}
    qof = {p[0]: p[1] for p in C['pol']}
    QQ = {}
    def J(name, q):
        QQ[name] = q; return lambda: Q.__setitem__(name, gn(q))
    def repesca(fase):
        """Segunda vuelta, despacio y de una en una, para las consultas que no obtuvieron respuesta. Sin lo esencial no se publica."""
        pend = [k for k in QQ if Q.get(k) is None]
        if pend: print(fase, 'repesca de', len(pend), 'consultas', flush=True)
        for k in pend:
            if minutos() > TOPE_MIN: break
            time.sleep(4); Q[k] = gn(QQ[k])
        falta = [k for k in QQ if Q.get(k) is None and k.split(':')[0] in ESENCIAL]
        if falta:
            resumen(); print('Google News no ha dado los datos esenciales (%d consultas sin respuesta: %s). No se publica nada.' % (len(falta), ', '.join(falta[:8]))); sys.exit(2)
    # A · políticos (7 días), nivel 1 por cabecera, cabeceras y temas
    jobs = [J('p7:' + p[0], p[1] + ' when:7d') for p in C['pol']]
    jobs += [J('pm:%s:%s' % (i, m[0]), '%s site:%s when:1d' % (qof[i], m[1])) for i in C['n1'] for m in C['med']]
    jobs += [J('m1:' + m[0], 'site:%s when:1d' % m[1]) for m in C['med']]
    for t in C['tem']:
        jobs += [J('t1:' + t[0], t[1] + ' when:1d'), J('t7:' + t[0], t[1] + ' when:7d')]
        jobs += [J('tf:%s:%s' % (t[0], f), '%s "%s" when:7d' % (t[1], f)) for f in t[2]]
    pool(jobs); print('A', len(jobs), 'consultas ·', len(ITEMS), 'noticias ·', len(ERR), 'errores · %.1f min' % minutos(), flush=True)
    if len(ITEMS) < 300 or FRENO['abortar']:
        resumen(); print('Google News no responde con normalidad desde este servidor. No se publica nada.', ERR[:5]); sys.exit(2)
    repesca('A')
    # A2 · quienes alcanzan el tope de 100 resultados: 24 h y día a día
    jobs = []
    for p in C['pol']:
        r = Q.get('p7:' + p[0])
        if r and len(r) >= 95:
            jobs.append(J('p1:' + p[0], p[1] + ' when:1d'))
            jobs += [J('pd:%s:%s' % (p[0], day(k)), '%s after:%s before:%s' % (p[1], day(k), day(k - 1))) for k in range(1, 7)]
    pool(jobs); repesca('A2'); print('A2', len(jobs), 'consultas ·', len(ERR), 'errores · %.1f min' % minutos(), flush=True)
    # B · temas por provincia (el mapa se renueva cada 9 horas como mucho; entre medias se conserva el último)
    def Jp(key, q): return lambda: TP.__setitem__(key, gn(q, True, True))
    claves = [('%s:%s' % (t[0], c), '%s "%s"%s when:%s' % (t[1], n, ' -"León XIV" -Papa' if n == 'León' else '', t[3])) for t in C['tem'] if t[3] for c, n in C['prov']]
    edad = 99.0
    try:
        u = json.load(open(os.path.join(W, '..', 'data', 'ultimo.json')))
        pg = (u.get('cobertura') or {}).get('provGenerado')
        prev = {t: set((v.get('prov') or {}).keys()) for t, v in (u.get('tem') or {}).items()}
        completo = all(k.split(':')[1] in prev.get(k.split(':')[0], ()) for k, _ in claves)
        if pg and completo: edad = (NOW - datetime.fromisoformat(pg.replace('Z', '+00:00'))).total_seconds() / 3600
    except Exception: pass
    if edad < float(os.environ.get('PROM_PROV_HORAS', '9')) and not os.environ.get('PROM_PROV_SIEMPRE'):
        for k, _ in claves: TP[k] = None
        PROVG[0] = pg
        print('B mapa por provincias: se conserva el de hace %.1f h' % edad, flush=True)
    else:
        pool([Jp(k, q) for k, q in claves]); sin = sum(1 for v in TP.values() if v is None)
        PROVG[0] = NOW.strftime('%Y-%m-%dT%H:%M:%S.000Z') if sin < len(claves) / 2 else pg if edad < 99 else None
        print('B', len(claves), 'consultas ·', sin, 'sin hacer (se conserva el último dato) · %.1f min' % minutos(), flush=True)
    # C · Bluesky
    since = (NOW - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    def bs(k, q, sort, extra=''):
        r = S.get('https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=%s&sort=%s&limit=100&lang=es%s' % (quote(q), sort, extra), timeout=30)
        if r.status_code != 200: ERR.append('bsky %s %s' % (r.status_code, q)); return
        BS[k + ':' + sort] = [[((p.get('record') or {}).get('text') or '')[:400], p['author']['handle'], p['author'].get('displayName') or '', minuto((p.get('record') or {}).get('createdAt') or p.get('indexedAt') or ''),
                               p.get('likeCount', 0), p.get('repostCount', 0), p.get('replyCount', 0), p.get('quoteCount', 0), p['uri'].split('/')[-1], p['author'].get('did', '')] for p in r.json().get('posts', [])]
    jobs = []
    for k, q in C['bsky']:
        jobs += [lambda k=k, q=q: bs(k, q, 'latest'), lambda k=k, q=q: bs(k, q, 'top', '&since=' + quote(since))]
    pool(jobs, 2); print('C bluesky', len(BS), flush=True)
    # D · Wikipedia (interés ciudadano)
    try:
        j = S.get('https://es.wikipedia.org/w/api.php', params={'action': 'query', 'redirects': 1, 'format': 'json', 'titles': '|'.join(p[2] for p in C['pol'])}, headers=WIKI_UA, timeout=30).json()
        for x in j['query'].get('normalized', []) + j['query'].get('redirects', []): WM['m'][x['from']] = x['to']
        WM['miss'] = [p['title'] for p in j['query'].get('pages', {}).values() if 'missing' in p]
    except Exception as e: ERR.append('wikimap ' + repr(e)[:60])
    ymd = lambda k: day(k).replace('-', '')
    def wk(pid, t):
        for _ in range(3):
            if t in WM['m']: t = WM['m'][t]
        r = S.get('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/es.wikipedia/all-access/user/%s/daily/%s00/%s00' % (quote(t.replace(' ', '_'), safe=''), ymd(92), ymd(1)), headers=WIKI_UA, timeout=30)
        if r.status_code != 200: ERR.append('wiki %s %s' % (r.status_code, t)); return
        WK[pid] = {'t': t, 'v': [[x['timestamp'][:8], x['views']] for x in r.json().get('items', [])]}
    pool([lambda p=p: wk(p[0], p[2]) for p in C['pol']], 4); print('D wikipedia', len(WK), flush=True)
    resumen()
    try:
        ant = (json.load(open(os.path.join(W, '..', 'data', 'ultimo.json'))).get('cobertura') or {}).get('noticias') or 0
        if ant and len(ITEMS) < 0.5 * ant and not os.environ.get('PROM_SIN_CONTROL'):
            print('Control de calidad: %d noticias frente a %d en la recogida anterior. Parece una recogida a medias: no se publica.' % (len(ITEMS), ant)); sys.exit(2)
    except (OSError, ValueError): pass
    raw = {'cfg': C, 'provGenerado': PROVG[0], 'gen': NOW.strftime('%Y-%m-%dT%H:%M:%S.000Z'), 'items': ITEMS, 'q': Q, 'tp': TP, 'bsky': BS, 'wiki': WK, 'wikiMap': WM, 'err': ERR, 'ms': int((time.time() - T0) * 1000),
           'fallidas': [k for k, v in list(Q.items()) + list(TP.items()) if v is None]}
    json.dump(raw, open(os.path.join(W, 'raw.json'), 'w'), ensure_ascii=False)
    print('raw.json ·', len(ITEMS), 'noticias ·', len(Q) + len(TP), 'consultas ·', len(ERR), 'errores ·', raw['ms'] // 1000, 's', flush=True)

def youtube():
    """Últimos vídeos de cada canal público (fuente RSS de YouTube): título, fecha, visualizaciones y «me gusta»."""
    cache_p = os.path.join(W, '..', 'data', 'canales.json')
    try: cache = json.load(open(cache_p))
    except Exception: cache = {}
    H = {'Cookie': 'CONSENT=YES+cb; SOCS=CAI', 'Accept-Language': 'es-ES,es;q=0.9'}
    out = {}
    for c in C.get('yt') or []:
        h = c['handle']; cid = cache.get('yt:' + h)
        try:
            if not cid:
                if h.startswith('UC') and len(h) == 24: cid = h
                else:
                    t = S.get('https://www.youtube.com/@' + quote(h), headers=H, timeout=30).text
                    m = re.search(r'"(?:externalId|channelId)":"(UC[0-9A-Za-z_-]{22})"', t) or re.search(r'youtube\.com/channel/(UC[0-9A-Za-z_-]{22})', t)
                    cid = m.group(1) if m else None
                if cid: cache['yt:' + h] = cid
            if not cid: out[h] = {'error': 'canal no encontrado'}; continue
            x = S.get('https://www.youtube.com/feeds/videos.xml?channel_id=' + cid, headers=H, timeout=30)
            if x.status_code != 200: out[h] = {'error': 'HTTP %d' % x.status_code}; continue
            v = []
            for e in re.findall(r'<entry>(.*?)</entry>', x.text, re.S):
                vid = g(e, r'<yt:videoId>(.*?)</yt:videoId>'); vi = re.search(r'<media:statistics views="(\d+)"', e); lk = re.search(r'<media:starRating count="(\d+)"', e)
                v.append([vid, g(e, r'<title>(.*?)</title>'), minuto(g(e, r'<published>(.*?)</published>')), int(vi.group(1)) if vi else None, int(lk.group(1)) if lk else None])
            out[h] = {'id': cid, 'titulo': g(x.text, r'<title>(.*?)</title>'), 'v': v}
        except Exception as e: out[h] = {'error': type(e).__name__}
        time.sleep(0.5)
    try: json.dump(cache, open(cache_p, 'w'), indent=1)
    except OSError: pass
    ok = sum(1 for v in out.values() if 'v' in v)
    print('E YouTube', ok, 'de', len(out), 'canales', [h for h, v in out.items() if 'error' in v], flush=True)
    return out

def telegram():
    """Últimos mensajes de cada canal público de Telegram (vista web t.me/s/canal): texto, fecha y visualizaciones."""
    from bs4 import BeautifulSoup
    def cifra(t):
        t = (t or '').strip().replace(',', '.'); m = re.match(r'([\d.]+)\s*([KM]?)', t, re.I)
        if not m: return None
        try: n = float(m.group(1)) if m.group(2) else float(m.group(1).replace('.', ''))
        except ValueError: return None
        return int(n * {'K': 1e3, 'M': 1e6}.get(m.group(2).upper(), 1))
    out = {}
    for c in C.get('tg') or []:
        k = c['canal']
        try:
            r = S.get('https://t.me/s/' + quote(k), timeout=30)
            if r.status_code != 200 or 'tgme_channel_info' not in r.text: out[k] = {'error': 'canal no encontrado o privado'}; continue
            so = BeautifulSoup(r.text, 'html.parser'); subs = None
            for ct in so.select('.tgme_channel_info_counter'):
                if 'subscriber' in ct.get_text() or 'suscript' in ct.get_text(): subs = cifra(ct.select_one('.counter_value').get_text() if ct.select_one('.counter_value') else '')
            ms = []
            for m in so.select('.tgme_widget_message[data-post]'):
                tx = m.select_one('.tgme_widget_message_text'); vw = m.select_one('.tgme_widget_message_views'); tm = m.select_one('time[datetime]')
                ms.append([m['data-post'].split('/')[-1], (tx.get_text(' ', strip=True) if tx else '')[:400], minuto(tm['datetime']) if tm else None, cifra(vw.get_text() if vw else '')])
            ti = so.select_one('.tgme_channel_info_header_title')
            out[k] = {'titulo': ti.get_text(strip=True) if ti else k, 'subs': subs, 'm': ms}
        except Exception as e: out[k] = {'error': type(e).__name__}
        time.sleep(0.5)
    ok = sum(1 for v in out.values() if 'm' in v)
    print('F Telegram', ok, 'de', len(out), 'canales', [h for h, v in out.items() if 'error' in v], flush=True)
    return out

def redes():
    """YouTube y Telegram van aparte: si fallan, la recogida principal se publica igual."""
    d = {}
    for nombre, f in (('youtube', youtube), ('telegram', telegram)):
        try: d[nombre] = f()
        except Exception as e: print(nombre, 'no disponible', repr(e)[:80]); d[nombre] = {}
    json.dump(d, open(os.path.join(W, 'aux_redes.json'), 'w'), ensure_ascii=False)

def auxiliares():
    """Tendencias de X (trends24), búsquedas en alza (Google Trends) y Menéame. Si una falla, se sigue sin ella."""
    def guardar(src, d):
        d.update({'src': src, 'at': datetime.now(timezone.utc).isoformat()}); json.dump(d, open(os.path.join(W, 'aux_%s.json' % src), 'w'), ensure_ascii=False)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(S.get('https://trends24.in/spain/', timeout=30).text, 'html.parser'); cards = []
        for c in soup.select('.list-container, .trend-card')[:26]:
            l = []
            for li in c.select('li')[:50]:
                a = li.select_one('a'); n = li.select_one('.tweet-count')
                l.append([(a.get_text() if a else li.get_text()).strip(), (n.get('data-count') or n.get_text()).strip() if n else ''])
            if l: cards.append(l)
        agg = {}
        for ci, l in enumerate(cards):
            for ri, (n, cnt) in enumerate(l):
                a = agg.setdefault(n, [0, 99, ci, '']); a[0] += 1; a[1] = min(a[1], ri + 1); a[3] = a[3] or cnt
        if cards: guardar('trends24', {'horas': len(cards), 'ahora': cards[0], 'hist': sorted([[n] + a for n, a in agg.items()], key=lambda x: -x[1])})
        print('X tendencias', len(cards), 'horas')
    except Exception as e: print('X tendencias: no disponible', repr(e)[:80])
    try:
        x = S.get('https://trends.google.com/trending/rss?geo=ES', timeout=30).text; items = []
        for b in re.findall(r'<item>(.*?)</item>', x, re.S):
            items.append({'t': g(b, r'<title>(.*?)</title>'), 'tr': g(b, r'<ht:approx_traffic>(.*?)</ht:approx_traffic>'), 'd': g(b, r'<pubDate>(.*?)</pubDate>'),
                          'news': [[g(n, r'<ht:news_item_title>(.*?)</ht:news_item_title>'), g(n, r'<ht:news_item_source>(.*?)</ht:news_item_source>'), g(n, r'<ht:news_item_url>(.*?)</ht:news_item_url>')] for n in re.findall(r'<ht:news_item>(.*?)</ht:news_item>', b, re.S)[:2]]})
        if items: guardar('gtrends', {'items': items})
        print('Google Trends', len(items))
    except Exception as e: print('Google Trends: no disponible', repr(e)[:80])
    try:
        x = S.get('https://www.meneame.net/rss', timeout=30).text; items = []
        num = lambda b, tag: int(re.sub(r'\D', '', g(b, r'<meneame:%s>(.*?)</meneame:%s>' % (tag, tag))) or 0)
        for b in re.findall(r'<item>(.*?)</item>', x, re.S):
            items.append({'t': g(b, r'<title>(.*?)</title>'), 'l': g(b, r'<link>(.*?)</link>'), 'd': g(b, r'<pubDate>(.*?)</pubDate>'), 'sub': g(b, r'<meneame:sub>(.*?)</meneame:sub>'),
                          'v': num(b, 'votes'), 'neg': num(b, 'negatives'), 'k': num(b, 'karma'), 'c': num(b, 'comments'), 'cl': num(b, 'clicks')})
        if items: guardar('meneame', {'items': items})
        print('Menéame', len(items))
    except Exception as e: print('Menéame: no disponible', repr(e)[:80])

if __name__ == '__main__':
    for f in ('aux_trends24.json', 'aux_gtrends.json', 'aux_meneame.json', 'aux_redes.json'):
        try: os.remove(os.path.join(W, f))
        except OSError: pass
    if C.get('aviso'): print('AVISO:', ' '.join(C['aviso']))
    principal(); auxiliares(); redes()
