# Lee y valida seguimiento.yml (el único fichero que se edita para cambiar qué se sigue) y produce:
#   config()   → consultas para la recogida (mismo formato que usa recoger.py)
#   catalogo() → catálogo que lee el panel (data/catalogo.json)
# Si el fichero tiene un error, se usa la última versión buena (data/seguimiento.json) y se deja el aviso
# en AVISO para que el panel lo muestre. Nunca debe impedir una recogida.
import json, os, re, unicodedata

W = os.path.dirname(os.path.abspath(__file__))
YML = os.path.join(W, '..', 'seguimiento.yml')
BUENA = os.path.join(W, '..', 'data', 'seguimiento.json')
AJUSTES = os.path.join(W, 'ajustes-panel.json')     # cambios hechos desde el panel de Claude (los copia la tarea de Claude)
AVISO = []

PROV = [  # código INE, nombre, población aprox. (miles, INE 2024 redondeado)
 ('01','Álava',340),('02','Albacete',390),('03','Alicante',1990),('04','Almería',760),('05','Ávila',160),('06','Badajoz',665),('07','Illes Balears',1230),
 ('08','Barcelona',5880),('09','Burgos',360),('10','Cáceres',388),('11','Cádiz',1255),('12','Castellón',615),('13','Ciudad Real',492),('14','Córdoba',770),
 ('15','A Coruña',1130),('16','Cuenca',198),('17','Girona',820),('18','Granada',935),('19','Guadalajara',280),('20','Gipuzkoa',730),('21','Huelva',535),
 ('22','Huesca',228),('23','Jaén',620),('24','León',447),('25','Lleida',450),('26','La Rioja',325),('27','Lugo',325),('28','Madrid',7000),
 ('29','Málaga',1775),('30','Murcia',1570),('31','Navarra',678),('32','Ourense',304),('33','Asturias',1010),('34','Palencia',158),('35','Las Palmas',1160),
 ('36','Pontevedra',945),('37','Salamanca',327),('38','Santa Cruz de Tenerife',1080),('39','Cantabria',590),('40','Segovia',157),('41','Sevilla',1970),('42','Soria',90),
 ('43','Tarragona',850),('44','Teruel',135),('45','Toledo',740),('46','Valencia',2710),('47','Valladolid',525),('48','Bizkaia',1155),('49','Zamora',166),
 ('50','Zaragoza',990),('51','Ceuta',83),('52','Melilla',86),
]
AMBITOS = ('Gobierno', 'Oposición', 'Autonómico', 'Local', 'Otros')
PROV_CONSULTA = {'07': 'Baleares', '38': 'Tenerife'}   # nombre que se usa en la búsqueda, si difiere

def slug(t):
    t = unicodedata.normalize('NFD', t.lower()); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '_', t).strip('_')[:30] or 'x'

class Malo(Exception): pass

def validar(d):
    """Comprueba y completa los valores por defecto. Lanza Malo con un mensaje en castellano si algo no cuadra."""
    if not isinstance(d, dict): raise Malo('el fichero no tiene secciones (elecciones, nivel1, personas, …)')
    for k in ('personas', 'medios', 'temas'):
        if not isinstance(d.get(k), list) or not d[k]: raise Malo('falta la sección «%s» o está vacía' % k)
    ids = set(); out = []
    for n, p in enumerate(d['personas'], 1):
        if not isinstance(p, dict) or not p.get('nombre'): raise Malo('la persona n.º %d no tiene «nombre»' % n)
        p = dict(p); p['nombre'] = str(p['nombre']).strip()
        p['id'] = slug(str(p.get('id') or p['nombre']))
        if p['id'] in ids: raise Malo('el id «%s» está repetido' % p['id'])
        ids.add(p['id'])
        p['partido'] = str(p.get('partido') or 'Independiente').strip()
        p['ambito'] = str(p.get('ambito') or 'Otros').strip()
        if p['ambito'] not in AMBITOS: p['ambito'] = 'Otros'
        p['cargo'] = str(p.get('cargo') or '').strip(); p['territorio'] = str(p.get('territorio') or 'España').strip()
        al = p.get('alias') or [p['nombre']]
        if isinstance(al, str): al = [a.strip() for a in al.split(',') if a.strip()]
        p['alias'] = [str(a).strip() for a in al if str(a).strip()] or [p['nombre']]
        p['consulta'] = str(p.get('consulta') or '"%s"' % p['nombre']).strip()
        p['wiki'] = str(p.get('wiki') or p['nombre']).strip()
        p['bluesky'] = str(p.get('bluesky') or p['alias'][0]).strip()
        out.append(p)
    d['personas'] = out
    n1 = [slug(str(x)) for x in (d.get('nivel1') or [])]
    malos = [x for x in n1 if x not in ids]
    if malos: raise Malo('en nivel1 hay ids que no están en personas: %s' % ', '.join(malos))
    if len(n1) > 5: raise Malo('nivel1 admite como mucho 5 personas (hay %d)' % len(n1))
    d['nivel1'] = n1
    med = []
    for m in d['medios']:
        if not isinstance(m, dict) or not m.get('dominio'): raise Malo('hay un medio sin «dominio»')
        med.append({'id': slug(str(m.get('id') or m['dominio'].split('.')[0])), 'nombre': str(m.get('nombre') or m['dominio']), 'dominio': str(m['dominio']).strip().lower(), 'tipo': str(m.get('tipo') or 'Prensa')})
    d['medios'] = med
    tem = []
    for t in d['temas']:
        if not isinstance(t, dict) or not t.get('nombre'): raise Malo('hay un tema sin «nombre»')
        t = dict(t); t['id'] = slug(str(t.get('id') or t['nombre']))
        t['consulta'] = str(t.get('consulta') or t['nombre'])
        try: re.compile(str(t.get('patron') or re.escape(t['nombre'])), re.I)
        except re.error as e: raise Malo('el patrón del tema «%s» no es válido (%s)' % (t['nombre'], e))
        t['patron'] = str(t.get('patron') or re.escape(t['nombre'].lower()))
        f = t.get('foco') or []
        t['foco'] = [str(x) for x in ([f] if isinstance(f, str) else f)]
        m = str(t.get('mapa') or '').strip()
        if m not in ('', '1d', '2d', '7d'): raise Malo('el mapa del tema «%s» debe ser 7d, 2d, 1d o vacío' % t['nombre'])
        t['mapa'] = m; t['bluesky'] = str(t.get('bluesky') or '').strip()
        tem.append(t)
    d['temas'] = tem
    par = d.get('partidos') or {}
    if not isinstance(par, dict): raise Malo('«partidos» debe ser una lista de nombre: color')
    d['partidos'] = {str(k): str(v) for k, v in par.items()}
    for p in out: d['partidos'].setdefault(p['partido'], '#8a8f98')
    el = d.get('elecciones') or {}
    d['elecciones'] = {'nombre': str(el.get('nombre') or ''), 'fecha': str(el.get('fecha') or ''), 'inicio_campana': str(el.get('inicio_campana') or '')}
    for red, campo in (('youtube', 'handle'), ('telegram', 'canal')):
        l = []
        for c in d.get(red) or []:
            if isinstance(c, dict) and c.get(campo):
                l.append({'nombre': str(c.get('nombre') or c[campo]), campo: str(c[campo]).lstrip('@').strip(), 'tipo': str(c.get('tipo') or 'otro'), 'partido': str(c.get('partido') or '')})
        d[red] = l
    return d

def aplicar_ajustes(d):
    """Cambios guardados desde el panel de Claude: nivel 1, cargos, personas y temas añadidos."""
    if not os.path.exists(AJUSTES): return d
    try: a = json.load(open(AJUSTES, encoding='utf-8'))
    except Exception as e: AVISO.append('No se pudieron leer los ajustes del panel (%s); se ignoran.' % type(e).__name__); return d
    ids = {p['id'] for p in d['personas']}
    for e in a.get('extra') or []:
        n = str(e.get('nombre') or '').strip()
        if n and slug(n) not in ids:
            d['personas'].append({'id': slug(n), 'nombre': n, 'partido': str(e.get('partido') or 'Independiente'), 'ambito': 'Otros', 'cargo': str(e.get('cargo') or ''),
                                  'territorio': str(e.get('territorio') or 'España'), 'alias': [n], 'consulta': '"%s"' % n, 'wiki': n, 'bluesky': n, 'panel': True})
            ids.add(slug(n))
    for pid, cargo in (a.get('cargos') or {}).items():
        for p in d['personas']:
            if p['id'] == pid and str(cargo).strip(): p['cargo'] = str(cargo).strip()
    tids = {t['id'] for t in d['temas']}
    for e in a.get('temasExtra') or []:
        n = str(e.get('nombre') or '').strip(); pal = [x.strip() for x in str(e.get('palabras') or n).split(',') if x.strip()] or [n]
        if n and slug(n) not in tids:
            d['temas'].append({'id': slug(n), 'nombre': n, 'consulta': '(' + ' OR '.join(('"%s"' % x) if ' ' in x else x for x in pal) + ')',
                               'patron': '|'.join(re.escape(x.lower()) for x in pal), 'foco': [], 'mapa': '', 'bluesky': pal[0], 'panel': True})
            tids.add(slug(n))
    n1 = [x for x in (a.get('nivel1') or []) if x in ids]
    if n1: d['nivel1'] = n1[:5]
    return d

_CACHE = {}
def cargar():
    if 'd' in _CACHE: return _CACHE['d']
    d = None
    try:
        import yaml
        txt = open(YML, encoding='utf-8').read()
        d = validar(yaml.safe_load(txt))
        os.makedirs(os.path.dirname(BUENA), exist_ok=True)
        json.dump(d, open(BUENA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    except Exception as e:
        linea = ''
        m = getattr(e, 'problem_mark', None)
        if m is not None: linea = ' (línea %d)' % (m.line + 1)
        AVISO.append('seguimiento.yml tiene un error%s: %s. Se usa la última versión buena.' % (linea, str(e).split('\n')[0][:160]))
        print('AVISO:', AVISO[-1])
        try: d = validar(json.load(open(BUENA, encoding='utf-8')))
        except Exception: raise SystemExit('No hay ninguna versión buena de seguimiento.yml: no se puede recoger.')
    d = aplicar_ajustes(d)
    _CACHE['d'] = d
    return d

def config():
    """Consultas para recoger.py: mismas claves que el antiguo config.json más youtube y telegram."""
    d = cargar()
    win = {'7d': '7d', '2d': '2d', '1d': '1d', '': ''}
    return {'pol': [[p['id'], p['consulta'], p['wiki']] for p in d['personas']], 'n1': d['nivel1'],
            'med': [[m['id'], m['dominio']] for m in d['medios']],
            'tem': [[t['id'], t['consulta'], [f for f in t['foco'] if f != 'España'], win[t['mapa']]] for t in d['temas']],
            'prov': [[c, PROV_CONSULTA.get(c, n)] for c, n, _ in PROV],
            'bsky': [[p['id'], p['bluesky']] for p in d['personas'] if p['id'] in d['nivel1']] + [[t['id'], t['bluesky']] for t in d['temas'] if t['bluesky']],
            'yt': d.get('youtube') or [], 'tg': d.get('telegram') or [], 'aviso': AVISO[:]}

def catalogo(cfg=None):
    d = cargar(); vent = {'7d': '7 días', '2d': '2 días', '1d': '24 horas', '': ''}
    return {'politicos': [{'id': p['id'], 'nombre': p['nombre'], 'partido': p['partido'], 'ambito': p['ambito'], 'cargo': p['cargo'], 'territorio': p['territorio'],
                           'alias': p['alias'], 'consulta': p['consulta'], 'wiki': p['wiki']} for p in d['personas']],
            'partidos': d['partidos'], 'medios': d['medios'],
            'temas': [{'id': t['id'], 'nombre': t['nombre'], 'foco': t['foco'], 'patron': t['patron'], 'ventana': vent[t['mapa']], 'consulta': t['consulta']} for t in d['temas']],
            'provincias': [{'id': c, 'nombre': n, 'pob': p} for c, n, p in PROV],
            'nivel1': d['nivel1'], 'elecciones': d['elecciones'],
            'youtube': d.get('youtube') or [], 'telegram': d.get('telegram') or [], 'avisos': AVISO[:]}

if __name__ == '__main__':
    c = config(); k = catalogo()
    print('personas', len(k['politicos']), '· nivel1', k['nivel1'], '· medios', len(k['medios']), '· temas', [t['id'] for t in k['temas']],
          '· youtube', len(c['yt']), '· telegram', len(c['tg']), '· avisos', AVISO)
