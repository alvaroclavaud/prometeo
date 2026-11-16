window.PRO = { S: { status: 'idle', done: 0, total: 0, err: [], phase: '', t0: 0 }, items: [], key: new Map(), data: {} };
PRO.cfg = {"pol": [["sanchez", "\"Pedro Sánchez\"", "Pedro Sánchez"], ["feijoo", "\"Feijóo\"", "Alberto Núñez Feijóo"], ["abascal", "\"Abascal\"", "Santiago Abascal"], ["cuerpo", "\"Carlos Cuerpo\"", "Carlos Cuerpo"], ["diaz", "\"Yolanda Díaz\"", "Yolanda Díaz"], ["aagesen", "\"Sara Aagesen\"", "Sara Aagesen"], ["bolanos", "\"Félix Bolaños\"", "Félix Bolaños"], ["espana", "\"Arcadi España\"", "Arcadi España"], ["albares", "\"Albares\"", "José Manuel Albares"], ["robles", "\"Margarita Robles\"", "Margarita Robles"], ["marlaska", "\"Marlaska\"", "Fernando Grande-Marlaska"], ["puente", "\"Óscar Puente\"", "Óscar Puente"], ["garcia", "\"Mónica García\" (Sanidad OR ministra OR \"Más Madrid\")", "Mónica García Gómez"], ["cerdan", "\"Santos Cerdán\"", "Santos Cerdán"], ["gamarra", "\"Cuca Gamarra\"", "Cuca Gamarra"], ["tellado", "\"Tellado\"", "Miguel Tellado"], ["millan", "\"Pepa Millán\"", "Pepa Millán"], ["ayuso", "\"Ayuso\"", "Isabel Díaz Ayuso"], ["moreno", "\"Juanma Moreno\" OR \"Moreno Bonilla\"", "Juan Manuel Moreno"], ["illa", "\"Salvador Illa\"", "Salvador Illa"], ["pradales", "\"Pradales\"", "Imanol Pradales"], ["rueda", "\"Alfonso Rueda\"", "Alfonso Rueda"], ["page", "\"García-Page\"", "Emiliano García-Page"], ["mazon", "\"Mazón\"", "Carlos Mazón"], ["puigdemont", "\"Puigdemont\"", "Carles Puigdemont"], ["rufian", "\"Rufián\"", "Gabriel Rufián"], ["nogueras", "\"Míriam Nogueras\"", "Míriam Nogueras"], ["otegi", "\"Otegi\"", "Arnaldo Otegi"], ["esteban", "\"Aitor Esteban\"", "Aitor Esteban"], ["belarra", "\"Belarra\"", "Ione Belarra"], ["montero_mj", "\"María Jesús Montero\"", "María Jesús Montero"], ["alegria", "\"Pilar Alegría\"", "Pilar Alegría"], ["urtasun", "\"Urtasun\"", "Ernest Urtasun"], ["saiz", "\"Elma Saiz\"", "Elma Saiz"], ["torres", "\"Ángel Víctor Torres\"", "Ángel Víctor Torres"], ["redondo", "\"Ana Redondo\" (ministra OR Igualdad)", "Ana Redondo"], ["semper", "\"Sémper\"", "Borja Sémper"], ["funez", "\"Carmen Fúnez\"", "Carmen Fúnez"], ["bendodo", "\"Bendodo\"", "Elías Bendodo"], ["buxade", "\"Buxadé\"", "Jorge Buxadé"], ["garriga", "\"Ignacio Garriga\"", "Ignacio Garriga"], ["almeida", "\"Martínez-Almeida\" OR (\"Almeida\" alcalde Madrid)", "José Luis Martínez-Almeida"], ["collboni", "\"Collboni\"", "Jaume Collboni"], ["guardiola", "\"María Guardiola\"", "María Guardiola"], ["azcon", "\"Azcón\"", "Jorge Azcón"], ["prohens", "\"Prohens\"", "Marga Prohens"], ["clavijo", "\"Fernando Clavijo\"", "Fernando Clavijo"], ["aragones", "\"Pere Aragonès\"", "Pere Aragonès"], ["matute", "\"Oskar Matute\"", "Oskar Matute"], ["montero_i", "\"Irene Montero\"", "Irene Montero"]], "n1": ["sanchez", "feijoo", "abascal"], "med": [["elespanol", "elespanol.com"], ["as", "as.com"], ["elmundo", "elmundo.es"], ["elpais", "elpais.com"], ["marca", "marca.com"], ["abc", "abc.es"], ["elconfidencial", "elconfidencial.com"], ["elperiodico", "elperiodico.com"], ["rtve", "rtve.es"], ["okdiario", "okdiario.com"], ["20minutos", "20minutos.es"], ["antena3", "antena3.com"], ["ser", "cadenaser.com"], ["lasexta", "lasexta.com"], ["cope", "cope.es"], ["telecinco", "telecinco.es"], ["ondacero", "ondacero.es"]], "tem": [["inseguridad", "(inseguridad OR delincuencia OR criminalidad OR robos)", ["Ceuta"], "7d"], ["economia", "(economía OR empleo OR paro OR vivienda OR inflación)", ["Madrid", "Barcelona"], "2d"], ["inmigracion", "(inmigración OR inmigrantes OR migrantes OR pateras OR cayucos)", [], "7d"], ["campana", "(elecciones generales OR \"29-N\" OR campaña electoral OR sondeo)", [], ""]], "prov": [["01", "Álava"], ["02", "Albacete"], ["03", "Alicante"], ["04", "Almería"], ["05", "Ávila"], ["06", "Badajoz"], ["07", "Baleares"], ["08", "Barcelona"], ["09", "Burgos"], ["10", "Cáceres"], ["11", "Cádiz"], ["12", "Castellón"], ["13", "Ciudad Real"], ["14", "Córdoba"], ["15", "A Coruña"], ["16", "Cuenca"], ["17", "Girona"], ["18", "Granada"], ["19", "Guadalajara"], ["20", "Gipuzkoa"], ["21", "Huelva"], ["22", "Huesca"], ["23", "Jaén"], ["24", "León"], ["25", "Lleida"], ["26", "La Rioja"], ["27", "Lugo"], ["28", "Madrid"], ["29", "Málaga"], ["30", "Murcia"], ["31", "Navarra"], ["32", "Ourense"], ["33", "Asturias"], ["34", "Palencia"], ["35", "Las Palmas"], ["36", "Pontevedra"], ["37", "Salamanca"], ["38", "Tenerife"], ["39", "Cantabria"], ["40", "Segovia"], ["41", "Sevilla"], ["42", "Soria"], ["43", "Tarragona"], ["44", "Teruel"], ["45", "Toledo"], ["46", "Valencia"], ["47", "Valladolid"], ["48", "Bizkaia"], ["49", "Zamora"], ["50", "Zaragoza"], ["51", "Ceuta"], ["52", "Melilla"]], "bsky": [["sanchez", "\"Pedro Sánchez\""], ["feijoo", "Feijóo"], ["abascal", "Abascal"], ["inseguridad", "inseguridad"], ["economia", "vivienda"], ["inmigracion", "inmigración"], ["campana", "elecciones generales"]]};
PRO.zz = ms => new Promise(z => setTimeout(z, ms));
PRO.dec = s => (s || '').replace(/<!\[CDATA\[|\]\]>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ').trim();
PRO.add = (t, s, dom, ts, l) => { const k = t + '|' + s; let i = PRO.key.get(k); if (i === undefined) { i = PRO.items.length; PRO.items.push([t, s, dom, ts, l]); PRO.key.set(k, i); } return i; };
PRO.gn = async (q, lite) => {
 const u = '/rss/search?q=' + encodeURIComponent(q) + '&hl=es&gl=ES&ceid=ES:es';
 for (let a = 0; a < 3; a++) {
 try {
 const r = await fetch(u, { credentials: 'omit' });
 if (r.status === 200) {
 const x = await r.text(), out = [];
 for (const m of x.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
 const b = m[1], g = re => { const k = b.match(re); return k ? PRO.dec(k[1]) : ''; };
 let t = g(/<title>([\s\S]*?)<\/title>/); const s = g(/<source[^>]*>([\s\S]*?)<\/source>/);
 const dom = g(/<source url="([^"]*)"/).replace(/^https?:\/\/(www\.)?/, '').replace(/\/.*$/, '');
 if (s && t.endsWith(' - ' + s)) t = t.slice(0, -(s.length + 3));
 const ts = Math.round(Date.parse(g(/<pubDate>([\s\S]*?)<\/pubDate>/)) / 60000);
 if (lite) { out.push([t, s, ts, dom]); continue; }
 const l = g(/<link>([\s\S]*?)<\/link>/).replace('https://news.google.com/rss/articles/', '').replace(/\?oc=5$/, '');
 out.push(PRO.add(t, s, dom, ts, l));
 }
 return lite ? { n: out.length, doms: out.map(o => o[3]), top: out.slice(0, 8) } : out;
 }
 PRO.S.err.push(r.status + ' ' + q.slice(0, 50)); await PRO.zz(20000 * (a + 1));
 } catch (e) { PRO.S.err.push('X ' + e.message + ' ' + q.slice(0, 50)); await PRO.zz(6000); }
 }
 return null;
};
PRO.pool = async (jobs, n) => { let i = 0; const w = async () => { while (i < jobs.length) { const j = jobs[i++]; try { await j(); } catch (e) { PRO.S.err.push('J ' + e.message); } PRO.S.done++; await PRO.zz(150); } }; await Promise.all(Array.from({ length: n }, w)); };
PRO.run = async () => {
 const S = PRO.S, C = PRO.cfg, D = PRO.data = { q: {}, tp: {}, bsky: {}, wiki: {}, wikiMap: {} };
 S.status = 'run'; S.t0 = Date.now(); S.done = 0; S.err = [];
 const day = k => new Date(Date.now() - k * 864e5).toISOString().slice(0, 10);
 const qOf = id => C.pol.find(p => p[0] === id)[1];
 let J = []; const Q = (name, q) => J.push(async () => { D.q[name] = await PRO.gn(q); });
 for (const [id, q] of C.pol) Q('p7:' + id, q + ' when:7d');
 for (const id of C.n1) for (const [mid, dom] of C.med) Q('pm:' + id + ':' + mid, qOf(id) + ' site:' + dom + ' when:1d');
 for (const [mid, dom] of C.med) Q('m1:' + mid, 'site:' + dom + ' when:1d');
 for (const [id, q, foco] of C.tem) { Q('t1:' + id, q + ' when:1d'); Q('t7:' + id, q + ' when:7d'); for (const f of foco) Q('tf:' + id + ':' + f, q + ' "' + f + '" when:7d'); }
 S.total = J.length; S.phase = 'A'; await PRO.pool(J, 3);
 J = [];
 for (const [id, q] of C.pol) { const r = D.q['p7:' + id]; if (r && r.length >= 95) { Q('p1:' + id, q + ' when:1d'); for (let k = 1; k <= 6; k++) Q('pd:' + id + ':' + day(k), q + ' after:' + day(k) + ' before:' + day(k - 1)); } }
 S.total += J.length; S.phase = 'A2'; await PRO.pool(J, 3);
 J = [];
 for (const [id, q, foco, w] of C.tem) if (w) for (const [cod, nom] of C.prov) J.push(async () => { D.tp[id + ':' + cod] = await PRO.gn(q + ' "' + nom + '"' + (nom === 'León' ? ' -"León XIV" -Papa' : '') + ' when:' + w, true); });
 S.total += J.length; S.phase = 'B'; await PRO.pool(J, 3);
 J = [];
 const since = new Date(Date.now() - 864e5).toISOString();
 const bs = async (k, q, sort, extra) => { const r = await fetch('https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=' + encodeURIComponent(q) + '&sort=' + sort + '&limit=100&lang=es' + extra); if (r.status !== 200) { S.err.push('bsky ' + r.status + ' ' + q); return; } const j = await r.json(); D.bsky[k + ':' + sort] = (j.posts || []).map(p => [((p.record && p.record.text) || '').slice(0, 400), p.author.handle, p.author.displayName || '', Math.round(Date.parse((p.record && p.record.createdAt) || p.indexedAt) / 60000), p.likeCount || 0, p.repostCount || 0, p.replyCount || 0, p.quoteCount || 0, p.uri.split('/').pop(), (p.author.did || '')]); };
 for (const [k, q] of C.bsky) { J.push(() => bs(k, q, 'latest', '')); J.push(() => bs(k, q, 'top', '&since=' + encodeURIComponent(since))); }
 const ymd = k => day(k).replace(/-/g, '');
 J.push(async () => { const r = await fetch('https://es.wikipedia.org/w/api.php?action=query&redirects=1&format=json&origin=*&titles=' + encodeURIComponent(C.pol.map(p => p[2]).join('|'))); const j = await r.json(); const m = {}; for (const x of (j.query.normalized || [])) m[x.from] = x.to; for (const x of (j.query.redirects || [])) m[x.from] = x.to; const miss = Object.values(j.query.pages || {}).filter(p => p.missing !== undefined).map(p => p.title); D.wikiMap = { m, miss }; });
 S.total += J.length; S.phase = 'C'; await PRO.pool(J, 2);
 J = [];
 for (const [id, q, w] of C.pol) J.push(async () => { let t = w; const m = D.wikiMap.m || {}; for (let i = 0; i < 3 && m[t]; i++) t = m[t]; const r = await fetch('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/es.wikipedia/all-access/user/' + encodeURIComponent(t.replace(/ /g, '_')) + '/daily/' + ymd(92) + '00/' + ymd(1) + '00'); if (r.status !== 200) { S.err.push('wiki ' + r.status + ' ' + t); return; } const j = await r.json(); D.wiki[id] = { t, v: (j.items || []).map(x => [x.timestamp.slice(0, 8), x.views]) }; });
 S.total += J.length; S.phase = 'D'; await PRO.pool(J, 4);
 S.phase = 'fin'; S.ms = Date.now() - S.t0;
 PRO.out = JSON.stringify({ cfg: C, gen: new Date().toISOString(), items: PRO.items, q: D.q, tp: D.tp, bsky: D.bsky, wiki: D.wiki, wikiMap: D.wikiMap, err: S.err, ms: S.ms, src: { zz: PRO.zz.toString(), dec: PRO.dec.toString(), add: PRO.add.toString(), gn: PRO.gn.toString(), pool: PRO.pool.toString(), run: PRO.run.toString() } });
 S.len = PRO.out.length; S.status = 'done';
};
setTimeout(() => { PRO.run().catch(e => { PRO.S.status = 'fail: ' + e.message; }); }, 50);
'started'
