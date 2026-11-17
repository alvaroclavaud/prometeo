'use strict';
/* ---------- utilidades ---------- */
const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nf = new Intl.NumberFormat('es-ES', { useGrouping: 'always' }), nf1 = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1, useGrouping: 'always' });
const N = n => nf.format(Math.round(n || 0)), N1 = n => nf1.format(n || 0);
const fFH = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
const fD = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
const fDc = new Intl.DateTimeFormat('es-ES', { timeZone: 'UTC', day: 'numeric', month: 'short' });
const hora = ts => fFH.format(new Date(ts * 60000));
const diaCorto = d => fDc.format(new Date(d + 'T12:00:00Z'));
const pct = (a, b) => b ? Math.round(100 * a / b) : 0;
function toast(t) { const e = $('#toast'); e.textContent = t; e.style.display = 'block'; clearTimeout(toast.t); toast.t = setTimeout(() => e.style.display = 'none', 2600); }
const TONO = { P: 'Positivo', N: 'Negativo', U: 'Neutro' }, POST = { F: 'A favor', C: 'En contra', N: 'Informativo' };
const EMO = { I: 'Ira', M: 'Miedo', E: 'Esperanza', B: 'Burla', O: 'Orgullo', T: 'Tristeza', X: 'Sin emoción marcada' };
const TEMA = { E: 'Economía', V: 'Vivienda', I: 'Inmigración', S: 'Seguridad', C: 'Corrupción y justicia', L: 'Campaña', T: 'Territorial', X: 'Exterior', A: 'Social y sanidad', O: 'Otros' };

/* ---------- estado ---------- */
const D = { dias: {}, hist: {} };            // datos publicados
const S = { vista: 'resumen', rango: '24h', desde: '', hasta: '', pol: null, tema: 'inmigracion', prov: null, mapaModo: 'idx', orden: 'vol', dir: -1, f: { q: '', pol: '', tema: '', tono: '', post: '', solo17: false, pend: false, pag: 1 }, fp: { amb: '', q: '' } };
let CAP = { db: null, sample: null, downloads: null };
const FUERA = !(window.claude && window.claude.use);   // alojado fuera de Claude (web propia): sin IA en el panel, descargas directas
let CFG = { marca: { nombre: 'Prometeo', color: '' }, nivel1: null, extra: [], temasExtra: [], cargos: {}, umbrales: { pico: 2, negativo: 60, portada: 12 }, argumentario: '' };
let CORR = {};                     // correcciones y clasificaciones hechas desde el panel: {idMencion: {clave: 'NCIL'}}
let LEIDAS = {}; let BORR = [];
const P = id => D.pid[id];
const colorP = p => (D.cat.partidos[p.partido] || '#888');
const nivel1 = () => (CFG.nivel1 && CFG.nivel1.length ? CFG.nivel1 : D.cat.nivel1).filter(id => D.pid[id]);
const etq = (m, k) => (CORR[m.id] && CORR[m.id][k]) || (m.c && m.c[k]) || '';
const enlace = m => m.l ? 'https://news.google.com/rss/articles/' + m.l + '?oc=5' : 'https://news.google.com/search?q=' + encodeURIComponent('"' + m.t + '"') + '&hl=es&gl=ES&ceid=ES:es';

/* ---------- carga ---------- */
async function j(f) { const r = await fetch('data/' + f); if (!r.ok) throw new Error(f + ' ' + r.status); return r.json(); }
const MAXD = 31;                   // días de titulares que se cargan como máximo
async function cargarDias(lista) { await Promise.all(lista.slice(-MAXD).filter(d => !D.dias[d]).map(async d => { try { D.dias[d] = (await j('dia-' + d + '.json')).menciones; } catch (e) { D.dias[d] = []; } })); }
async function cargarHist(lista) { await Promise.all(lista.filter(d => !D.serie.dias.includes(d) && !(d in D.hist)).map(async d => { try { D.hist[d] = await j('hist-' + d + '.json'); } catch (e) { D.hist[d] = null; } })); }
const masDias = (d, k) => { const x = new Date(d + 'T12:00:00Z'); x.setUTCDate(x.getUTCDate() + k); return x.toISOString().slice(0, 10); };
function fechas(a, b) { const out = []; for (let d = a; d <= b && out.length < 400; d = masDias(d, 1)) out.push(d); return out; }
function diasRango() {
  const ult = D.est.ultima, pri = D.est.primer || D.serie.dias[0];
  if (S.rango === '24h') return D.serie.dias.slice(-2);
  let a, b = ult;
  if (S.rango === 'pers') { a = S.desde || pri; b = S.hasta && S.hasta < ult ? S.hasta : ult; }
  else a = masDias(ult, -({ '7d': 7, '30d': 30, '1a': 365 }[S.rango] - 1));
  if (a < pri) a = pri;
  return a <= b ? fechas(a, b) : [];
}
function valDia(clave, id, d) { const i = D.serie.dias.indexOf(d); if (i >= 0) return (D.serie[clave][id] || [])[i] || 0; const h = D.hist[d]; return h && h[clave] ? (h[clave][id] || 0) : 0; }
function menciones() {
  const mapa = new Map(), v0 = D.ult.ventana[0];
  for (const d of diasRango().slice(-MAXD)) for (const m of (D.dias[d] || [])) { if (S.rango === '24h' && m.ts < v0) continue; const o = mapa.get(m.id); if (!o || Object.keys(m.c || {}).length > Object.keys(o.c || {}).length) mapa.set(m.id, m); }
  return [...mapa.values()];
}
let ST = null;
function calcular() {
  const dias = diasRango(), ms = menciones(), pol = {};
  for (const p of D.cat.politicos) {
    const u = D.ult.pol[p.id] || {}, s = { n: 0, sent: [0, 0, 0], post: [0, 0, 0], emo: {}, tem: {}, fu: {}, wiki: u.wiki || 0, wiki7: u.wiki7 || 0, agenda17: u.agenda17 || 0 };
    if (S.rango === '24h') Object.assign(s, { vol: u.vol || 0, tit: u.tit || 0, cat: u.cat || 0, m17: u.medios17 || 0, media7: u.media7, tope: u.tope, base: u.base });
    else { s.vol = s.tit = s.cat = 0; dias.forEach(d => { s.vol += valDia('vol', p.id, d); s.tit += valDia('tit', p.id, d); s.cat += valDia('cat', p.id, d); }); s.m17 = null; }
    pol[p.id] = s;
  }
  for (const m of ms) for (const pid of m.p) { const s = pol[pid]; if (!s) continue; s.fu[m.s] = (s.fu[m.s] || 0) + 1; const c = etq(m, pid); if (!c) continue; s.n++; s.sent['PNU'.indexOf(c[0])]++; s.post['FCN'.indexOf(c[1])]++; s.emo[c[2]] = (s.emo[c[2]] || 0) + 1; s.tem[c[3]] = (s.tem[c[3]] || 0) + 1; }
  const tot = Object.values(pol).reduce((a, s) => a + s.vol, 0) || 1;
  for (const s of Object.values(pol)) s.cuota = 100 * s.vol / tot;
  ST = { pol, tot, ms, dias };
}
async function refrescar() { const d = diasRango(); await Promise.all([cargarDias(d), cargarHist(d)]); calcular(); pintar(); }

/* ---------- gráficos ---------- */
function spark(v, w, h, color) {
  w = w || 120; h = h || 32; const mx = Math.max(1, ...v), n = v.length, x = i => 2 + i * (w - 4) / Math.max(1, n - 1), y = a => h - 3 - (a / mx) * (h - 7);
  const pts = v.map((a, i) => x(i).toFixed(1) + ',' + y(a).toFixed(1)).join(' ');
  return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="Evolución"><polygon points="2,${h - 2} ${pts} ${w - 2},${h - 2}" fill="${color || 'var(--ink)'}" opacity=".1"/><polyline points="${pts}" fill="none" stroke="${color || 'var(--ink)'}" stroke-width="1.6"/><circle cx="${x(n - 1).toFixed(1)}" cy="${y(v[n - 1]).toFixed(1)}" r="2.6" fill="${color || 'var(--ink)'}"/></svg>`;
}
function tono(s, n) { if (!n) return '<span class="muted xs">sin clasificar</span>'; return `<span class="tono" title="${s[0]} positivos · ${s[2]} neutros · ${s[1]} negativos (n=${n})"><span class="p" style="width:${100 * s[0] / n}%"></span><span class="u" style="width:${100 * s[2] / n}%"></span><span class="n" style="width:${100 * s[1] / n}%"></span></span>`; }
function lineas(series, labels, alto) {
  const w = 640, h = alto || 190, pl = 44, pr = 10, pt = 10, pb = 24, mx = Math.max(1, ...series.flatMap(s => s.v)), n = labels.length;
  const x = i => pl + i * (w - pl - pr) / Math.max(1, n - 1), y = a => pt + (1 - a / mx) * (h - pt - pb);
  let g = ''; for (let k = 0; k <= 3; k++) { const val = mx * k / 3; g += `<line x1="${pl}" x2="${w - pr}" y1="${y(val)}" y2="${y(val)}" stroke="var(--line)" stroke-width="1"/><text x="${pl - 6}" y="${y(val) + 4}" text-anchor="end">${N(val)}</text>`; }
  const paso = Math.max(1, Math.ceil(n / 8)); labels.forEach((l, i) => { if (i % paso === 0 || i === n - 1) g += `<text x="${x(i)}" y="${h - 6}" text-anchor="middle">${esc(l)}</text>`; });
  for (const s of series) { const pts = s.v.map((a, i) => x(i).toFixed(1) + ',' + y(a).toFixed(1)).join(' '); g += `<polyline points="${pts}" fill="none" stroke="${s.c}" stroke-width="2"/><circle cx="${x(n - 1)}" cy="${y(s.v[n - 1])}" r="3" fill="${s.c}"/>`; }
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto" role="img" aria-label="Serie temporal">${g}</svg>`;
}
function desglose(obj, nombres, n) {
  const e = Object.entries(obj).sort((a, b) => b[1] - a[1]); if (!e.length) return '<p class="muted small">Sin titulares clasificados en este periodo.</p>';
  return e.map(([k, v]) => `<div class="row small" style="gap:8px"><span style="width:150px">${esc(nombres[k] || k)}</span><span class="bar" style="flex:1"><span style="width:${100 * v / e[0][1]}%"></span></span><span class="num" style="width:64px;text-align:right">${v} · ${pct(v, n)} %</span></div>`).join('');
}

/* ---------- piezas ---------- */
const nomP = p => `<span class="row" style="gap:6px;flex-wrap:nowrap"><span class="dot" style="background:${colorP(p)}"></span><span>${esc(p.nombre)}</span></span>`;
function filaMencion(m, foco) {
  const pols = m.p.map(id => P(id)).filter(Boolean);
  const claves = foco ? [foco] : (m.p.length ? m.p : ['_']);
  const chips = claves.map(k => { const c = etq(m, k); if (!c) return `<button class="chip" data-clas="${m.id}" data-k="${k}">Clasificar</button>`; return `<button class="chip ${c[0]}" data-clas="${m.id}" data-k="${k}" title="Cambiar clasificación">${claves.length > 1 && P(k) ? esc(P(k).alias[0]) + ': ' : ''}${TONO[c[0]]} · ${POST[c[1]]}${c[2] !== 'X' ? ' · ' + EMO[c[2]] : ''}</button>`; }).join('');
  return `<div class="men"><a class="t" href="${enlace(m)}" target="_blank" rel="noopener">${esc(m.t)}</a><div class="meta"><b>${esc(m.s)}</b><span>${hora(m.ts)}</span>${pols.map(p => `<span class="chip"><span class="dot" style="background:${colorP(p)}"></span>${esc(p.alias[0])}</span>`).join('')}${m.k.map(k => `<span class="chip">${esc((D.tid[k] || {}).nombre || k)}</span>`).join('')}${chips}<button class="chip" data-imp="${m.id}" title="Preparar una respuesta">Responder</button></div></div>`;
}
function filaAlerta(a) { return `<div class="alerta ${LEIDAS[a.id] ? 'leida' : ''}"><span class="sev s${a.sev}"></span><div style="flex:1"><b>${esc(a.titulo)}</b><p class="small muted">${esc(a.detalle)}</p></div>${a.ref && a.ref.pol ? `<button class="btn sm" data-pol="${a.ref.pol}">Ver</button>` : a.ref && a.ref.tema ? `<button class="btn sm" data-tema="${a.ref.tema}">Ver</button>` : a.ref && a.ref.u ? `<a class="btn sm" href="${esc(a.ref.u)}" target="_blank" rel="noopener">Abrir</a>` : ''}</div>`; }
const alertasVivas = () => D.ult.alertas.filter(a => !LEIDAS[a.id]);

/* ---------- vistas ---------- */
const V = {};
V.resumen = () => {
  const inf = D.ult.informe, n1 = nivel1(), cl = Object.values(ST.pol).reduce((a, s) => a + s.n, 0);
  const cuotaTrio = n1.reduce((a, id) => a + ST.pol[id].cuota, 0);
  const rank = D.cat.politicos.map(p => [p, ST.pol[p.id]]).sort((a, b) => b[1].vol - a[1].vol).slice(0, 15), mx = rank[0][1].vol || 1;
  return `
  <div class="row between"><div><h2>${S.rango === '24h' ? 'Últimas 24 horas' : 'Periodo seleccionado'}</h2><p class="muted small">${S.rango === '24h' ? 'Del ' + hora(D.ult.ventana[0]) + ' al ' + hora(D.ult.ventana[1]) : diaCorto(ST.dias[0]) + ' – ' + diaCorto(ST.dias[ST.dias.length - 1]) + ' · ' + ST.dias.length + ' días con datos'}</p></div>
    <form class="row ${CAP.sample ? '' : 'hide'}" id="preg"><input class="inp" id="preg-q" placeholder="Pregunta a los datos: ¿quién sube hoy?" style="width:min(340px,70vw)" aria-label="Pregunta a los datos"><button class="btn pri">Preguntar</button></form></div>
  <div id="resp" class="card hide"></div>
  <div class="grid g4">
    <div class="card tile"><div class="v num">${N(ST.tot)}</div><div class="l">noticias que mencionan a alguien del catálogo</div></div>
    <div class="card tile"><div class="v num">${N1(cuotaTrio)} %</div><div class="l">de la conversación es de ${n1.map(id => esc(P(id).alias[0])).join(', ')}</div></div>
    <div class="card tile"><div class="v num">${N(cl)}</div><div class="l">titulares clasificados por tono y postura</div></div>
    <div class="card tile"><div class="v num">${alertasVivas().length}</div><div class="l">alertas sin revisar <button class="btn sm" id="ver-alertas" style="margin-left:6px">Ver</button></div></div>
  </div>
  ${inf && S.rango === '24h' ? `<div class="card"><h4>Lo que cambió hoy</h4><h3 style="font-size:19px;margin:6px 0 8px">${esc(inf.titular)}</h3><div class="grid g3">${inf.claves.slice(0, 3).map(c => `<div><b>${esc(c.t)}</b><p class="small muted">${esc(c.d)}</p></div>`).join('')}</div><div class="row" style="margin-top:10px"><a class="btn sm" href="#informe">Leer el informe completo</a></div></div>` : ''}
  <div class="grid ${n1.length === 4 ? 'g2' : 'g3'}">${n1.map(id => { const p = P(id), s = ST.pol[id], sv = D.serie.tit[id] || [], h = D.ult.historias.find(x => x.p.includes(id));
    return `<div class="card lider"><div class="row between">${nomP(p)}<button class="btn sm" data-pol="${id}">Detalle</button></div><div class="row between" style="align-items:flex-end"><div><div class="big num">${N(s.vol)}</div><div class="muted small">noticias · ${N1(s.cuota)} % de cuota</div></div>${spark(sv, 120, 36, colorP(p))}</div>
      <div>${tono(s.sent, s.n)}<div class="row between xs muted" style="margin-top:4px"><span>${s.n ? pct(s.sent[0], s.n) + ' % positivo · ' + pct(s.sent[1], s.n) + ' % negativo' : ''}</span><span>n = ${s.n}</span></div></div>
      <div class="kv"><span>Titulares con su nombre</span><span class="num">${N(s.tit)}</span><span>En las 17 cabeceras</span><span class="num">${N(s.cat)}${s.m17 != null ? ' · ' + s.m17 + ' de 17' : ''}</span><span>Postura a favor / en contra</span><span class="num">${s.post[0]} / ${s.post[1]}</span><span>Visitas en Wikipedia (ayer)</span><span class="num">${N(s.wiki)} <span class="${s.wiki >= s.wiki7 ? '' : 'muted'}">(${s.wiki7 ? (s.wiki >= s.wiki7 ? '+' : '') + pct(s.wiki - s.wiki7, s.wiki7) + ' %' : '–'})</span></span></div>
      ${h && S.rango === '24h' ? `<p class="small"><span class="muted">Historia más repetida:</span> ${esc(h.t)} <span class="muted">(${h.medios} medios)</span></p>` : ''}</div>`; }).join('')}</div>
  <div class="grid g21">
    <div class="card"><div class="row between"><h3>Presencia en medios</h3><a class="btn sm" href="#politicos">Ver los ${D.cat.politicos.length}</a></div><p class="muted small" style="margin:2px 0 10px">Noticias de medios españoles que mencionan a cada persona.</p>
      ${rank.map(([p, s], i) => `<div class="row small clic rk" data-pol="${p.id}"><span class="num muted" style="width:18px">${i + 1}</span><span class="nm">${nomP(p)}</span><span class="bar" style="flex:1"><span style="width:${100 * s.vol / mx}%"></span></span><span class="num" style="width:52px;text-align:right">${N(s.vol)}</span><span class="tn">${tono(s.sent, s.n)}</span></div>`).join('')}</div>
    <div class="card"><div class="row between"><h3>Alertas</h3><button class="btn sm" id="ver-alertas2">Todas</button></div><div class="lista">${alertasVivas().slice(0, 6).map(filaAlerta).join('') || '<p class="muted small" style="padding:10px 0">No hay alertas pendientes.</p>'}</div></div>
  </div>
  <div class="grid g2">
    <div class="card"><h3>Historias del día</h3><p class="muted small" style="margin:2px 0 8px">Titulares casi idénticos agrupados: cuántos medios cuentan lo mismo.</p>${D.ult.historias.slice(0, 8).map(h => `<div class="row small" style="padding:6px 0;border-bottom:1px solid var(--line);flex-wrap:nowrap;align-items:flex-start"><span class="chip num">${h.medios} medios</span><span>${esc(h.t)}</span></div>`).join('')}</div>
    <div class="card"><h3>Temas</h3><p class="muted small" style="margin:2px 0 8px">Peso de cada tema en los titulares de las 17 cabeceras y zona con más intensidad.</p>${D.cat.temas.map(t => { const s = D.ult.tem[t.id], z = Object.entries(s.prov || {}).filter(e => e[1].n >= 12).sort((a, b) => b[1].idx - a[1].idx)[0];
      return `<div class="row between small clic" data-tema="${t.id}" style="padding:8px 0;border-bottom:1px solid var(--line);cursor:pointer"><div><b>${esc(t.nombre)}</b><div class="muted xs">${z ? 'Zona caliente: ' + esc(D.prn[z[0]]) + ' (' + N1(z[1].idx) + ' veces lo esperable)' : 'Sin mapa provincial'}</div></div><div style="text-align:right"><span class="num"><b>${N1(s.agendaPct)} %</b></span><div class="muted xs">${s.agenda17} de ${N(D.ult.corpus.n)} titulares</div></div></div>`; }).join('')}</div>
  </div>`;
};
V.politicos = () => {
  if (S.pol && P(S.pol)) return detallePol(S.pol);
  const q = S.fp.q.toLowerCase(), n1 = nivel1();
  let rows = D.cat.politicos.filter(p => (!S.fp.amb || p.ambito === S.fp.amb) && (!q || (p.nombre + ' ' + p.partido + ' ' + p.cargo).toLowerCase().includes(q))).map(p => [p, ST.pol[p.id]]);
  const val = { vol: r => r[1].vol, tit: r => r[1].tit, cat: r => r[1].cat, neg: r => r[1].n ? r[1].sent[1] / r[1].n : -1, wiki: r => r[1].wiki, nom: r => r[0].nombre, var: r => r[1].media7 ? r[1].vol / r[1].media7 : 0 }[S.orden];
  rows.sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * S.dir);
  const mx = Math.max(1, ...rows.map(r => r[1].vol)), amb = [...new Set(D.cat.politicos.map(p => p.ambito))];
  return `<div class="row between"><h2>Políticos</h2><div class="row"><input class="inp" id="fp-q" placeholder="Buscar nombre, partido o cargo" value="${esc(S.fp.q)}" aria-label="Buscar"><div class="seg" id="fp-amb"><button data-a="" class="${S.fp.amb ? '' : 'on'}">Todos</button>${amb.map(a => `<button data-a="${a}" class="${S.fp.amb === a ? 'on' : ''}">${a}</button>`).join('')}</div></div></div>
  <div class="card scroll"><table><thead><tr><th>#</th><th data-o="nom">Nombre</th><th data-o="vol">Noticias</th><th class="r" data-o="var" title="Frente a su media diaria de la última semana">Variación</th><th class="r" data-o="tit">Titulares</th><th class="r" data-o="cat">17 cabeceras</th><th data-o="neg">Tono de titulares</th><th class="r" data-o="wiki">Wikipedia</th><th title="Seguimiento en profundidad">Nivel 1</th></tr></thead><tbody>
  ${rows.map(([p, s], i) => { const v = S.rango === '24h' && s.media7 && !s.tope ? s.vol / s.media7 : null;
    return `<tr class="clic" data-pol="${p.id}"><td class="num muted">${i + 1}</td><td>${nomP(p)}<div class="xs muted">${esc(p.partido)} · ${esc(p.cargo)}</div></td><td><div class="row" style="gap:8px;flex-wrap:nowrap"><span class="bar" style="width:110px"><span style="width:${100 * s.vol / mx}%"></span></span><span class="num">${N(s.vol)}</span></div></td><td class="r num">${v == null ? '<span class="muted">–</span>' : `<span style="color:${v >= 2 ? 'var(--neg)' : 'inherit'}">×${N1(v)}</span>`}</td><td class="r num">${N(s.tit)}</td><td class="r num">${N(s.cat)}</td><td><div class="row" style="gap:6px;flex-wrap:nowrap"><span style="width:80px">${tono(s.sent, s.n)}</span><span class="xs muted num">${s.n ? 'n=' + s.n : ''}</span></div></td><td class="r num">${N(s.wiki)}</td><td><button class="chip ${n1.includes(p.id) ? 'sel' : ''}" data-n1="${p.id}" title="Seguir en profundidad">${n1.includes(p.id) ? 'Sí' : 'No'}</button></td></tr>`; }).join('')}
  </tbody></table></div>
  <p class="muted small">Noticias: medios españoles que mencionan a la persona (Google News). Titulares: su nombre aparece en el titular. Variación: frente a su media diaria de los siete días anteriores; no se calcula cuando la consulta alcanza el tope de 100 resultados. Tono: titulares clasificados con IA; n indica el tamaño de la muestra.</p>`;
};
function detallePol(id) {
  const p = P(id), s = ST.pol[id], u = D.ult.pol[id] || {}, ms = ST.ms.filter(m => m.p.includes(id)).sort((a, b) => b.ts - a.ts), b = D.ult.bsky[id];
  const wd = D.serie.wikiDias, wv = D.serie.wiki[id] || [], fu = Object.entries(s.fu).sort((a, b) => b[1] - a[1]).slice(0, 8);
  return `<div class="row between"><div class="row"><button class="btn sm" data-volver="1">← Todos</button><h2>${esc(p.nombre)}</h2><span class="chip"><span class="dot" style="background:${colorP(p)}"></span>${esc(p.partido)}</span></div><span class="muted small">${esc(p.cargo)} · ${esc(p.territorio)}</span></div>
  <div class="grid g4"><div class="card tile"><div class="v num">${N(s.vol)}</div><div class="l">noticias · ${N1(s.cuota)} % de cuota</div></div><div class="card tile"><div class="v num">${N(s.tit)}</div><div class="l">titulares con su nombre${s.m17 != null ? ' · ' + s.m17 + ' de 17 cabeceras' : ''}</div></div><div class="card tile"><div class="v num">${s.n ? pct(s.sent[1], s.n) + ' %' : '–'}</div><div class="l">titulares negativos (n = ${s.n})</div></div><div class="card tile"><div class="v num">${N(s.wiki)}</div><div class="l">visitas en Wikipedia ayer · media ${N(s.wiki7)}</div></div></div>
  <div class="grid g2">
    <div class="card"><h3>Noticias por día</h3><p class="muted small">Noticias que lo mencionan y titulares con su nombre.</p>${lineas([{ v: D.serie.vol[id] || [], c: 'var(--ink)' }, { v: D.serie.tit[id] || [], c: colorP(p) }], D.serie.dias.map(diaCorto))}<div class="row xs muted"><span><span class="dot" style="background:var(--ink)"></span> Noticias</span><span><span class="dot" style="background:${colorP(p)}"></span> Titulares</span>${u.tope ? '<span>Las consultas diarias tienen un tope de 100 resultados.</span>' : ''}</div></div>
    <div class="card"><h3>Interés ciudadano</h3><p class="muted small">Visitas diarias a su página de Wikipedia, últimos ${wd.length} días.</p>${lineas([{ v: wv, c: colorP(p) }], wd.map(diaCorto))}</div>
  </div>
  <div class="grid g3">
    <div class="card"><h3>Tono y postura</h3><div style="margin:10px 0 6px">${tono(s.sent, s.n)}</div><div class="kv"><span>Positivo</span><span class="num">${s.sent[0]}</span><span>Neutro</span><span class="num">${s.sent[2]}</span><span>Negativo</span><span class="num">${s.sent[1]}</span><span>A favor</span><span class="num">${s.post[0]}</span><span>En contra</span><span class="num">${s.post[1]}</span><span>Informativo</span><span class="num">${s.post[2]}</span></div><p class="xs muted" style="margin-top:8px">El tono describe cómo queda en el titular, incluidos los ataques de rivales. No es una encuesta.</p></div>
    <div class="card"><h3>Emociones</h3><div style="margin-top:8px;display:flex;flex-direction:column;gap:5px">${desglose(s.emo, EMO, s.n)}</div></div>
    <div class="card"><h3>De qué se habla</h3><div style="margin-top:8px;display:flex;flex-direction:column;gap:5px">${desglose(s.tem, TEMA, s.n)}</div></div>
  </div>
  <div class="grid g21">
    <div class="card"><div class="row between"><h3>Titulares (${N(ms.length)})</h3><button class="btn sm ${CAP.sample ? '' : 'hide'}" data-ia-pol="${id}">Clasificar pendientes con IA</button></div><div class="lista">${ms.slice(0, 40).map(m => filaMencion(m, id)).join('') || '<p class="muted small" style="padding:10px 0">Sin titulares en este periodo.</p>'}</div>${ms.length > 40 ? `<p class="small muted" style="margin-top:8px">Se muestran los 40 más recientes. <a href="#menciones" data-ir-men="${id}">Ver todos en Menciones</a>.</p>` : ''}</div>
    <div style="display:flex;flex-direction:column;gap:14px">
      <div class="card"><h3>Medios que más titulan</h3><div style="margin-top:8px;display:flex;flex-direction:column;gap:5px">${fu.map(([k, v]) => `<div class="row small" style="gap:8px"><span style="width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(k)}</span><span class="bar" style="flex:1"><span style="width:${100 * v / fu[0][1]}%"></span></span><span class="num">${v}</span></div>`).join('') || '<p class="muted small">Sin datos.</p>'}</div></div>
      ${b ? `<div class="card"><h3>Bluesky · 24 h</h3><div class="kv" style="margin:8px 0"><span>Publicaciones</span><span class="num">${b.n}${b.tope ? '+' : ''}</span><span>Me gusta</span><span class="num">${N(b.likes)}</span><span>Republicaciones</span><span class="num">${N(b.rep)}</span><span>Más difundidas a favor / en contra</span><span class="num">${b.post[0]} / ${b.post[1]}</span></div>${b.top.slice(0, 4).map(postB).join('')}</div>` : ''}
    </div>
  </div>`;
}
const postB = x => `<div class="men"><a class="t small" href="${esc(x.u)}" target="_blank" rel="noopener">${esc(x.t.slice(0, 220))}${x.t.length > 220 ? '…' : ''}</a><div class="meta"><b>@${esc(x.a)}</b><span>${N(x.likes)} me gusta</span><span>${N(x.rep)} rep.</span><span>${N(x.resp)} resp.</span>${x.c ? `<span class="chip ${x.c[0]}">${POST[x.c[1]]}</span>` : ''}</div></div>`;
V.temas = () => {
  const t = D.tid[S.tema] || D.cat.temas[0], s = D.ult.tem[t.id], inf = D.ult.informe && D.ult.informe.temas.find(x => x.id === t.id);
  const pv = Object.entries(s.prov || {}), hay = pv.length > 0, modo = S.mapaModo, val = e => modo === 'idx' ? e.idx : e.n;
  const esc5 = modo === 'idx' ? [0.75, 1.25, 1.75, 2.5] : (() => { const v = pv.map(e => e[1].n).sort((a, b) => a - b); return [0.2, 0.4, 0.6, 0.8].map(q => v[Math.floor(q * (v.length - 1))] || 0); })();
  const cls = v => esc5.filter(c => v >= c).length, op = [0.1, 0.28, 0.5, 0.74, 1];
  const rk = pv.slice().sort((a, b) => val(b[1]) - val(a[1])).slice(0, 10), sel = S.prov && s.prov && s.prov[S.prov] ? S.prov : (rk[0] || [])[0];
  const ms = ST.ms.filter(m => m.k.includes(t.id)).sort((a, b) => b.ts - a.ts);
  return `<div class="row between"><h2>Temas y zonas calientes</h2><div class="seg" id="tabs-tema">${D.cat.temas.map(x => `<button data-t="${x.id}" class="${x.id === t.id ? 'on' : ''}">${esc(x.nombre)}</button>`).join('')}</div></div>
  <div class="grid g4"><div class="card tile"><div class="v num">${N1(s.agendaPct)} %</div><div class="l">de los titulares de las 17 cabeceras (${s.agenda17} de ${N(D.ult.corpus.n)})</div></div><div class="card tile"><div class="v num">${N(s.vol)}${s.tope ? '+' : ''}</div><div class="l">noticias en medios españoles en 24 h</div></div><div class="card tile"><div class="v num">${s.n ? pct(s.sent[1], s.n) + ' %' : '–'}</div><div class="l">titulares de tono negativo (n = ${s.n})</div></div><div class="card tile"><div class="v" style="font-size:22px">${hay && rk[0] ? esc(D.prn[rk[0][0]]) : esc(t.foco.join(', '))}</div><div class="l">${hay ? 'zona con más ' + (modo === 'idx' ? 'intensidad' : 'noticias') : 'ámbito del tema'}</div></div></div>
  ${inf ? `<div class="aviso">${esc(inf.texto)}</div>` : ''}
  ${hay ? `<div class="grid g21"><div class="card"><div class="row between"><h3>Mapa por provincias · ${esc(s.ventana)}</h3><div class="seg" id="mapa-modo"><button data-m="idx" class="${modo === 'idx' ? 'on' : ''}">Intensidad</button><button data-m="n" class="${modo === 'n' ? 'on' : ''}">Noticias</button></div></div>
      <p class="muted small" style="margin:4px 0 8px">${modo === 'idx' ? 'Cuántas veces más noticias de las esperables para una provincia de su población. 1 = lo normal.' : 'Número de noticias de medios españoles que relacionan el tema con la provincia.'}</p>
      <div class="mapa"><svg viewBox="0 0 ${D.mapa.w} ${D.mapa.h}" role="img" aria-label="Mapa de España por provincias">${D.mapa.prov.map(m => { const e = s.prov[m.id]; return `<path class="pv ${m.id === sel ? 'sel' : ''}" data-prov="${m.id}" d="${m.d}" fill="var(--accent)" fill-opacity="${e ? op[cls(val(e))] : 0.05}"><title>${esc(D.prn[m.id] || m.n)}: ${e ? e.n + (e.tope ? '+' : '') + ' noticias · intensidad ' + N1(e.idx) : 'sin datos'}</title></path>`; }).join('')}${D.mapa.prov.filter(m => m.id === '51' || m.id === '52').map(m => { const e = s.prov[m.id]; return `<circle class="pv ${m.id === sel ? 'sel' : ''}" data-prov="${m.id}" cx="${m.c[0]}" cy="${m.c[1] + (m.id === '51' ? 12 : 10)}" r="8" fill="var(--accent)" fill-opacity="${e ? op[cls(val(e))] : 0.05}" style="stroke:var(--ink);stroke-width:1;cursor:pointer"><title>${esc(D.prn[m.id])}: ${e ? e.n + (e.tope ? '+' : '') + ' noticias · intensidad ' + N1(e.idx) : 'sin datos'}</title></circle><text x="${m.c[0] + 12}" y="${m.c[1] + (m.id === '51' ? 16 : 14)}">${esc(D.prn[m.id])}</text>`; }).join('')}<path class="borde" d="${D.mapa.borde}"/></svg></div>
      <div class="ley" style="margin-top:6px"><span>Menos</span>${op.map(o => `<i style="background:var(--accent);opacity:${o}"></i>`).join('')}<span>Más</span><span style="margin-left:10px">${modo === 'idx' ? 'Cortes: ' + esc5.map(N1).join(' · ') : 'Cortes: ' + esc5.join(' · ') + ' noticias'}</span></div></div>
    <div style="display:flex;flex-direction:column;gap:14px"><div class="card"><h3>Provincias con más ${modo === 'idx' ? 'intensidad' : 'noticias'}</h3><div style="margin-top:8px;display:flex;flex-direction:column;gap:5px">${rk.map(([k, e]) => `<div class="row small clic" data-prov="${k}" style="gap:8px;cursor:pointer;flex-wrap:nowrap"><span style="width:130px;${k === sel ? 'font-weight:600' : ''}">${esc(D.prn[k])}</span><span class="bar" style="flex:1"><span style="width:${100 * val(e) / val(rk[0][1])}%;background:var(--accent)"></span></span><span class="num" style="width:92px;text-align:right">${modo === 'idx' ? '×' + N1(e.idx) + ' · ' : ''}${e.n}${e.tope ? '+' : ''}</span></div>`).join('')}</div></div>
      ${sel ? `<div class="card"><h3>${esc(D.prn[sel])}</h3><p class="muted small">${s.prov[sel].n}${s.prov[sel].tope ? ' o más' : ''} noticias · intensidad ×${N1(s.prov[sel].idx)}</p>${s.prov[sel].top.map(x => `<div class="men"><a class="t small" target="_blank" rel="noopener" href="https://news.google.com/search?q=${encodeURIComponent('"' + x[0] + '"')}&hl=es&gl=ES&ceid=ES:es">${esc(x[0])}</a><div class="meta"><b>${esc(x[1])}</b><span>${hora(x[2])}</span></div></div>`).join('') || '<p class="muted small">Sin titulares de muestra.</p>'}</div>` : ''}</div></div>` : ''}
  ${Object.keys(s.foco || {}).length ? `<div class="grid g2">${Object.entries(s.foco).map(([k, f]) => `<div class="card"><div class="row between"><h3>Foco: ${esc(k)}</h3><span class="muted small num">${f.n7} noticias en 7 días · ${f.n1} en 24 h</span></div><div class="lista">${f.top.map(idm => mPorId(idm)).filter(Boolean).slice(0, 5).map(m => filaMencion(m, '_')).join('')}</div></div>`).join('')}</div>` : ''}
  <div class="card"><h3>Titulares del tema (${N(ms.length)})</h3><div class="lista">${ms.slice(0, 30).map(m => filaMencion(m, m.p.length ? null : '_')).join('') || '<p class="muted small" style="padding:10px 0">Sin titulares en este periodo.</p>'}</div></div>`;
};
function mPorId(id) { for (const d of Object.keys(D.dias)) { const m = D.dias[d].find(x => x.id === id); if (m) return m; } return null; }
function filtradas() {
  const f = S.f, q = f.q.toLowerCase();
  return ST.ms.filter(m => (!q || (m.t + ' ' + m.s).toLowerCase().includes(q)) && (!f.pol || m.p.includes(f.pol)) && (!f.tema || m.k.includes(f.tema)) && (!f.solo17 || m.m) &&
    (!f.pend || (m.p.length ? m.p : ['_']).some(k => !etq(m, k))) && (!f.tono || (m.p.length ? m.p : ['_']).some(k => etq(m, k)[0] === f.tono)) && (!f.post || (m.p.length ? m.p : ['_']).some(k => etq(m, k)[1] === f.post))).sort((a, b) => b.ts - a.ts);
}
V.menciones = () => {
  const f = S.f, ms = filtradas(), pp = 50, tot = Math.max(1, Math.ceil(ms.length / pp)); f.pag = Math.min(f.pag, tot);
  const opt = (v, t, s) => `<option value="${v}" ${s === v ? 'selected' : ''}>${esc(t)}</option>`;
  return `<div class="row between"><h2>Menciones</h2><div class="row"><button class="btn sm ${CAP.sample ? '' : 'hide'}" id="ia-lista">Clasificar con IA las pendientes de esta lista</button><button class="btn sm ${CAP.downloads || FUERA ? '' : 'hide'}" id="csv">Descargar CSV</button></div></div>
  <div class="card row"><input class="inp" id="f-q" placeholder="Buscar en titulares y medios" value="${esc(f.q)}" style="flex:1;min-width:200px" aria-label="Buscar">
    <select class="inp" id="f-pol" aria-label="Político">${opt('', 'Todos los políticos', f.pol)}${D.cat.politicos.map(p => opt(p.id, p.nombre, f.pol)).join('')}</select>
    <select class="inp" id="f-tema" aria-label="Tema">${opt('', 'Todos los temas', f.tema)}${D.cat.temas.map(t => opt(t.id, t.nombre, f.tema)).join('')}</select>
    <select class="inp" id="f-tono" aria-label="Tono">${opt('', 'Cualquier tono', f.tono)}${Object.entries(TONO).map(([k, v]) => opt(k, v, f.tono)).join('')}</select>
    <select class="inp" id="f-post" aria-label="Postura">${opt('', 'Cualquier postura', f.post)}${Object.entries(POST).map(([k, v]) => opt(k, v, f.post)).join('')}</select>
    <label class="row small"><input type="checkbox" id="f-17" ${f.solo17 ? 'checked' : ''}> Solo las 17 cabeceras</label><label class="row small"><input type="checkbox" id="f-pend" ${f.pend ? 'checked' : ''}> Sin clasificar</label></div>
  <div class="card"><div class="row between small muted"><span>${N(ms.length)} titulares · página ${f.pag} de ${tot}</span><span class="row"><button class="btn sm" id="pg-a" ${f.pag <= 1 ? 'disabled' : ''}>Anterior</button><button class="btn sm" id="pg-s" ${f.pag >= tot ? 'disabled' : ''}>Siguiente</button></span></div>
    <div class="lista">${ms.slice((f.pag - 1) * pp, f.pag * pp).map(m => filaMencion(m, f.pol || null)).join('') || '<p class="muted" style="padding:20px 0">Nada coincide con estos filtros.</p>'}</div></div>`;
};
V.redes = () => {
  const x = D.ult.x, b = D.ult.bsky;
  return `<h2>Redes y tendencias</h2>
  <div class="aviso">X no ofrece lectura gratuita de publicaciones, así que aquí se siguen sus tendencias hora a hora. Bluesky, Menéame y los canales públicos de YouTube y Telegram sí se leen completos. Ninguna de estas redes representa al conjunto del electorado: sirven para ver qué contenidos y argumentos se difunden.</div>
  ${x ? `<div class="card"><div class="row between"><h3>Tendencias en X · España</h3><span class="muted small">Últimas ${x.horas} horas</span></div><p class="muted small" style="margin:4px 0 8px">Ahora mismo. En color, las relacionadas con el catálogo o los temas.</p><div class="x">${x.ahora.map(a => `<span class="chip ${a.p.length || a.k.length ? 'rel' : ''}" title="Puesto ${a.puesto} · ${a.horas} h en tendencias">${a.puesto}. ${esc(a.t)}</span>`).join('')}</div>
    <h4 style="margin:14px 0 6px">Las que más horas llevan</h4><div class="x">${x.persistentes.slice(0, 24).map(a => `<span class="chip ${a.p.length || a.k.length ? 'rel' : ''}">${esc(a.t)} · ${a.horas} h</span>`).join('')}</div></div>` : ''}
  <div class="grid ${nivel1().length === 4 ? 'g2' : 'g3'}">${nivel1().filter(id => b[id]).map(id => { const p = P(id), s = b[id]; return `<div class="card"><div class="row between">${nomP(p)}<span class="muted small">Bluesky · 24 h</span></div><div class="kv" style="margin:8px 0"><span>Publicaciones</span><span class="num">${s.n}${s.tope ? '+' : ''}</span><span>Me gusta</span><span class="num">${N(s.likes)}</span><span>Republicaciones</span><span class="num">${N(s.rep)}</span><span>Respuestas</span><span class="num">${N(s.resp)}</span><span>Más difundidas: a favor / en contra</span><span class="num">${s.post[0]} / ${s.post[1]} (n=${s.nclas})</span></div>${s.top.slice(0, 3).map(postB).join('')}</div>`; }).join('')}</div>
  <div class="grid g2">${vRed(D.ult.youtube, 'YouTube', 'yt', 'Vídeos')}${vRed(D.ult.telegram, 'Telegram', 'tg', 'Mensajes')}</div>
  <div class="grid g2">
    <div class="card"><h3>Menéame · lo más votado</h3><div class="lista">${D.ult.meneame.slice(0, 10).map(m => `<div class="men"><a class="t small" href="${esc(m.l)}" target="_blank" rel="noopener">${m.t.replace(/&#34;/g, '"').replace(/</g, '&lt;')}</a><div class="meta"><span class="num"><b>${N(m.votos)}</b> votos</span><span class="num">${N(m.com)} comentarios</span><span>${esc(m.sub)}</span>${m.p.map(id => `<span class="chip">${esc(P(id).alias[0])}</span>`).join('')}</div></div>`).join('')}</div></div>
    <div class="card"><h3>Búsquedas en alza en Google · España</h3><div class="lista">${D.ult.google.map(g => `<div class="men"><div class="row between"><b>${esc(g.t)}</b><span class="chip num">${esc(g.trafico)} búsquedas</span></div>${g.noticias.slice(0, 1).map(n => `<a class="t small muted" href="${esc(n[2])}" target="_blank" rel="noopener">${esc(n[0])} · ${esc(n[1])}</a>`).join('')}</div>`).join('')}</div>
      <h3 style="margin-top:14px">Temas en Bluesky · 24 h</h3>${D.cat.temas.filter(t => b[t.id]).map(t => `<div class="row between small" style="padding:6px 0;border-bottom:1px solid var(--line)"><span>${esc(t.nombre)}</span><span class="num muted">${b[t.id].n}${b[t.id].tope ? '+' : ''} publicaciones · ${N(b[t.id].likes)} me gusta</span></div>`).join('')}</div>
  </div>`;
};
function vRed(r, nombre, unidad, pieza) {
  if (!r) return `<div class="card"><h3>${nombre}</h3><p class="muted small">Sin datos en esta recogida.</p></div>`;
  const ok = r.canales.filter(c => c.ok), mal = r.canales.filter(c => !c.ok), n1 = nivel1().filter(id => r.n1 && r.n1[id]);
  const fila = c => `<tr><td><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.nombre)}</a><div class="xs muted">${esc(c.tipo)}${c.partido ? ' · ' + esc(c.partido) : ''}${c.subs ? ' · ' + N(c.subs) + ' suscriptores' : ''}</div></td><td class="r num">${c.n7}</td><td class="r num">${N(unidad === 'yt' ? c.vistas7 : c.vistasMedia)}</td><td class="small">${c.top ? `<a href="${esc(c.top.u)}" target="_blank" rel="noopener">${esc(c.top.t.slice(0, 90))}</a> <span class="muted num">· ${N(c.top.vistas || 0)}</span>` : '<span class="muted">–</span>'}</td></tr>`;
  return `<div class="card"><div class="row between"><h3>${nombre} · canales públicos</h3><span class="muted small">Últimos 7 días</span></div>
    <div class="scroll"><table><thead><tr><th>Canal</th><th class="r">${pieza}</th><th class="r">${unidad === 'yt' ? 'Visualizaciones' : 'Vistas medias'}</th><th>Lo más visto</th></tr></thead><tbody>${ok.sort((a, b) => (unidad === 'yt' ? b.vistas7 - a.vistas7 : b.vistasMedia - a.vistasMedia)).map(fila).join('')}</tbody></table></div>
    ${n1.length ? `<h4 style="margin:14px 0 6px">Menciones del nivel 1</h4><div class="kv">${n1.map(id => `<span>${esc(P(id).nombre)}</span><span class="num">${r.n1[id].n} ${(r.n1[id].n === 1 ? pieza.slice(0, -1) : pieza).toLowerCase()} · ${N(r.n1[id].vistas)} visualizaciones</span>`).join('')}</div>` : ''}
    ${mal.length ? `<p class="xs muted" style="margin-top:8px">Sin datos en esta recogida: ${mal.map(c => esc(c.nombre)).join(', ')}.</p>` : ''}</div>`;
}
V.informe = () => {
  const i = D.inf || D.ult.informe; if (!i) return '<h2>Informe diario</h2><p class="muted">Todavía no hay informe para esta fecha.</p>';
  return `<div class="row between"><h2>Informe diario</h2><div class="row"><select class="inp" id="inf-fecha" aria-label="Fecha del informe">${fechas(masDias(D.est.ultima, -13) < (D.est.primerInforme || D.est.ultima) ? (D.est.primerInforme || D.est.ultima) : masDias(D.est.ultima, -13), D.est.ultima).reverse().map(d => `<option value="${d}" ${d === (D.infFecha || D.ult.fecha) ? 'selected' : ''}>${diaCorto(d)}</option>`).join('')}</select><button class="btn sm" id="inf-copiar">Copiar texto</button><button class="btn sm pri ${CAP.downloads || FUERA ? '' : 'hide'}" id="inf-pdf">Descargar PDF</button></div></div>
  <article class="card doc"><p class="muted small" style="text-transform:capitalize">${fD.format(new Date((D.infFecha || D.ult.fecha) + 'T12:00:00Z'))} · ${esc(CFG.marca.nombre)}</p><h2 style="margin:6px 0 10px">${esc(i.titular)}</h2>${i.autor ? `<p class="xs muted">Redactado con IA (${esc(i.autor)}) a partir de las cifras del día; cada número se ha comprobado contra los datos. Revísalo antes de difundirlo.</p>` : ''}<p>${esc(i.entradilla)}</p>
    <h3>Claves</h3>${i.claves.map(c => `<p><b>${esc(c.t)}.</b> ${esc(c.d)}</p>`).join('')}
    <h3>Seguimiento en profundidad</h3>${i.lideres.map(l => `<p><b>${esc((P(l.id) || {}).nombre || l.id)}.</b> ${esc(l.texto)}</p>`).join('')}
    <h3>Temas</h3>${i.temas.map(l => `<p><b>${esc((D.tid[l.id] || {}).nombre || l.id)}.</b> ${esc(l.texto)}</p>`).join('')}
    <h3>Redes</h3><p>${esc(i.redes)}</p>
    <h3>Qué vigilar</h3><ul style="margin:0 0 10px;padding-left:20px">${i.vigilar.map(v => `<li>${esc(v)}</li>`).join('')}</ul>
    <h3>Cómo se ha medido</h3><p class="small muted">${esc(i.metodo)}</p></article>`;
};
function textoInforme() { const i = D.inf || D.ult.informe; return [i.titular, '', i.entradilla, '', 'CLAVES', ...i.claves.map(c => '• ' + c.t + '. ' + c.d), '', 'SEGUIMIENTO EN PROFUNDIDAD', ...i.lideres.map(l => '• ' + ((P(l.id) || {}).nombre || l.id) + '. ' + l.texto), '', 'TEMAS', ...i.temas.map(l => '• ' + ((D.tid[l.id] || {}).nombre || l.id) + '. ' + l.texto), '', 'REDES', i.redes, '', 'QUÉ VIGILAR', ...i.vigilar.map(v => '• ' + v), '', 'CÓMO SE HA MEDIDO', i.metodo].join('\n'); }
const TARJ = [
  { id: 'ranking', t: 'Ranking de presencia', texto: () => { const r = D.cat.politicos.map(p => [p, D.ult.pol[p.id]]).sort((a, b) => b[1].vol - a[1].vol).slice(0, 3); return `¿De quién hablan los medios? En las últimas 24 horas, ${r[0][0].nombre} aparece en ${N(r[0][1].vol)} noticias, por delante de ${r[1][0].nombre} (${N(r[1][1].vol)}) y ${r[2][0].nombre} (${N(r[2][1].vol)}). Datos de ${CFG.marca.nombre} sobre medios españoles. #29N`; } },
  { id: 'tono', t: 'Tono de los titulares', texto: () => { const a = nivel1().map(id => `${P(id).alias[0]}: ${pct(D.ult.pol[id].sent[1], D.ult.pol[id].n)} % negativos`).join(' · '); return `Así tratan los titulares a los candidatos en el día de campaña: ${a}. Muestra de titulares de las últimas 24 horas clasificados por ${CFG.marca.nombre}. #29N`; } },
  { id: 'zona', t: 'Zona caliente', texto: () => { const t = D.tid.inmigracion, s = D.ult.tem.inmigracion, z = Object.entries(s.prov).sort((a, b) => b[1].idx - a[1].idx)[0]; return `${D.prn[z[0]]} es hoy la zona caliente de la conversación sobre ${t.nombre.toLowerCase()}: ${z[1].tope ? 'más de ' : ''}${z[1].n} noticias en ${s.ventana}, ${N1(z[1].idx)} veces lo esperable para su población. Mapa de ${CFG.marca.nombre}.`; } }
];
V.tarjetas = () => `<div class="row between"><h2>Tarjetas para redes</h2><span class="muted small">1080 × 1080 · con los datos de hoy</span></div>
  <p class="muted small">Imágenes listas para publicar en las cuentas de ${esc(CFG.marca.nombre)}, con un texto sugerido que puedes editar. La publicación es manual.</p>
  <div class="grid g3">${TARJ.map(t => `<div class="card tarj"><h3>${t.t}</h3><canvas id="cv-${t.id}" width="1080" height="1080"></canvas><textarea id="tx-${t.id}" aria-label="Texto sugerido">${esc(t.texto())}</textarea><div class="row"><button class="btn sm pri ${CAP.downloads || FUERA ? '' : 'hide'}" data-png="${t.id}">Descargar imagen</button><button class="btn sm" data-copiar="tx-${t.id}">Copiar texto</button><button class="btn sm ${CAP.sample ? '' : 'hide'}" data-ia-tx="${t.id}">Mejorar con IA</button></div></div>`).join('')}</div>`;
V.impacto = () => {
  const neg = ST.ms.filter(m => m.p.some(k => etq(m, k)[0] === 'N')).slice(0, 400), sel = S.imp ? mPorId(S.imp) : null;
  return `<h2>Impacto</h2>
  <div class="aviso">Borradores de respuesta redactados con IA a partir de tu argumentario. Nada se publica solo: una persona revisa, aprueba y publica desde las cuentas oficiales. Las respuestas masivas desde cuentas falsas no forman parte de esta herramienta.</div>
  <div class="grid g2"><div class="card"><h3>Argumentario y tono</h3><p class="muted small" style="margin:4px 0 8px">Mensajes clave, datos que se pueden citar y líneas que no se cruzan. La IA no saldrá de aquí.</p><textarea id="arg" style="min-height:170px" placeholder="Ejemplo: Hablamos en nombre de… Tres mensajes: 1)… 2)… 3)… Tono: firme y respetuoso, sin descalificar. Nunca mencionar…">${esc(CFG.argumentario)}</textarea><div class="row" style="margin-top:8px"><button class="btn sm pri" id="arg-guardar">Guardar argumentario</button><span class="muted small" id="arg-ok"></span></div></div>
    <div class="card"><h3>Redactar una respuesta</h3><div class="field" style="margin:8px 0"><label for="imp-sel">Titular o publicación a responder</label><select id="imp-sel"><option value="">Elige un titular negativo reciente…</option>${neg.slice(0, 120).map(m => `<option value="${m.id}" ${S.imp === m.id ? 'selected' : ''}>${esc(m.t.slice(0, 110))} — ${esc(m.s)}</option>`).join('')}</select></div>
      ${sel ? `<p class="small"><b>${esc(sel.s)}:</b> ${esc(sel.t)}</p>` : ''}
      <div class="row" style="margin:8px 0"><select class="inp" id="imp-canal" aria-label="Canal"><option>X</option><option>Bluesky</option><option>Instagram</option><option>Nota de prensa</option></select><button class="btn pri" id="imp-redactar" ${CAP.sample && sel ? '' : 'disabled'}>Redactar borrador</button></div>
      ${CAP.sample ? '' : '<p class="muted small">La redacción con IA está disponible en la versión del panel dentro de Claude. Aquí puedes escribir y guardar respuestas a mano.</p>'}
      <textarea id="imp-borrador" placeholder="Aquí aparecerá el borrador. Puedes editarlo antes de aprobarlo.">${esc(S.impTxt || '')}</textarea><div class="row" style="margin-top:8px"><button class="btn sm" id="imp-guardar">Guardar como borrador</button><button class="btn sm" id="imp-aprobar">Aprobar</button><button class="btn sm" data-copiar="imp-borrador">Copiar</button></div></div></div>
  <div class="card"><h3>Respuestas guardadas</h3><div class="lista">${BORR.length ? BORR.slice().reverse().map((b, i) => `<div class="men"><div class="row between"><span class="chip ${b.estado === 'aprobada' ? 'P' : ''}">${b.estado === 'aprobada' ? 'Aprobada' : 'Borrador'}</span><span class="muted xs">${esc(b.canal)} · ${esc(b.fecha)}</span></div><p class="small muted">${esc(b.origen)}</p><p>${esc(b.texto)}</p></div>`).join('') : '<p class="muted small" style="padding:10px 0">Todavía no hay respuestas guardadas.</p>'}</div></div>`;
};
V.ajustes = () => {
  const c = D.ult.cobertura, f = [['Medios españoles (Google News)', 'Activa', c.consultas + ' consultas · ' + N(c.noticias) + ' noticias de 7 días'], ['Las 17 cabeceras del piloto', 'Activa', N(D.ult.corpus.n) + ' titulares de 24 h'], ['Bluesky', 'Activa', N(c.bluesky) + ' publicaciones con sus cifras de difusión'], ['Wikipedia (interés ciudadano)', 'Activa', c.wikipedia + ' páginas · 92 días de histórico'], ['X · tendencias de España', 'Activa', 'Tendencias por horas; no se leen publicaciones'], ['Menéame', 'Activa', 'Votos y comentarios de portada'], ['Google · búsquedas en alza', 'Activa', 'Búsquedas del día en España'], ['YouTube · canales públicos', D.ult.youtube ? 'Activa' : 'Sin datos', (c.youtube || 0) + ' canales con vídeos, visualizaciones y «me gusta»'], ['Telegram · canales públicos', D.ult.telegram ? 'Activa' : 'Sin datos', (c.telegram || 0) + ' canales con mensajes y visualizaciones'], ['X · lectura de publicaciones', 'No disponible gratis', 'Su API cobra por cada lectura'], ['Facebook e Instagram de terceros', 'No disponible', 'Meta solo lo permite tras revisar la aplicación'], ['LinkedIn y TikTok', 'No disponible', 'No ofrecen acceso de escucha']];
  return `<h2>Ajustes</h2>
  <div class="grid g2">
    <div class="card"><h3>Marca</h3><p class="muted small" style="margin:4px 0 10px">Nombre, color y logo del panel, los informes y las tarjetas.</p><div class="grid g2"><div class="field"><label for="m-nombre">Nombre</label><input id="m-nombre" value="${esc(CFG.marca.nombre)}"></div><div class="field"><label for="m-color">Color de marca</label><input id="m-color" type="color" value="${esc(CFG.marca.color || '#d4500f')}" style="height:38px;padding:2px"></div></div><div class="field" style="margin-top:10px"><label for="m-logo">Logo (imagen cuadrada, opcional)</label><input id="m-logo" type="file" accept="image/*"></div><div class="row" style="margin-top:10px"><button class="btn sm pri" id="m-guardar">Guardar marca</button><button class="btn sm" id="m-reset">Restablecer</button></div></div>
    <div class="card"><h3>Alertas</h3><p class="muted small" style="margin:4px 0 10px">Umbrales que se aplican en la siguiente recogida.</p><div class="grid g3"><div class="field"><label for="u-pico">Pico: veces sobre su media</label><input id="u-pico" type="number" step="0.5" min="1.5" value="${CFG.umbrales.pico}"></div><div class="field"><label for="u-neg">% de titulares negativos</label><input id="u-neg" type="number" step="5" min="30" max="100" value="${CFG.umbrales.negativo}"></div><div class="field"><label for="u-port">Cabeceras para «en portada»</label><input id="u-port" type="number" min="3" max="17" value="${CFG.umbrales.portada}"></div></div><div class="row" style="margin-top:10px"><button class="btn sm pri" id="u-guardar">Guardar umbrales</button></div></div>
  </div>
  <div class="card"><div class="row between"><h3>Seguimiento en profundidad (nivel 1)</h3><span class="muted small">Hasta 5 personas</span></div><p class="muted small" style="margin:4px 0 10px">Para estas personas se consulta además cada una de las 17 cabeceras, Bluesky, YouTube y Telegram. Se cambia aquí o desde la tabla de Políticos.</p><div class="x">${D.cat.politicos.map(p => `<button class="chip ${nivel1().includes(p.id) ? 'sel' : ''}" data-n1="${p.id}">${esc(p.nombre)}</button>`).join('')}</div></div>
  <div class="grid g2">
    <div class="card"><h3>Añadir al catálogo</h3><p class="muted small" style="margin:4px 0 10px">${FUERA ? `En esta web los cambios solo se guardan en tu navegador. Para que la recogida los use, edita <a href="https://github.com/alvaroclavaud/prometeo/edit/main/seguimiento.yml" target="_blank" rel="noopener">seguimiento.yml</a> (o hazlo desde el panel de Claude).` : 'Personas, temas y cargos. Se copian al fichero de seguimiento en la siguiente actualización y entran en la recogida siguiente.'}</p><div class="grid g2"><div class="field"><label for="n-nombre">Nombre</label><input id="n-nombre" placeholder="Nombre y apellidos"></div><div class="field"><label for="n-partido">Partido</label><input id="n-partido" placeholder="Partido"></div><div class="field"><label for="n-cargo">Cargo</label><input id="n-cargo" placeholder="Cargo"></div><div class="field"><label for="n-terr">Territorio</label><input id="n-terr" placeholder="España"></div></div><div class="row" style="margin-top:10px"><button class="btn sm pri" id="n-add">Añadir persona</button></div>
      <div class="grid g2" style="margin-top:14px"><div class="field"><label for="t-nombre">Tema nuevo</label><input id="t-nombre" placeholder="Por ejemplo: Sanidad"></div><div class="field"><label for="t-pal">Palabras clave</label><input id="t-pal" placeholder="listas de espera, médicos, hospital"></div></div><div class="row" style="margin-top:10px"><button class="btn sm pri" id="t-add">Añadir tema</button></div>
      <div class="grid g2" style="margin-top:14px"><div class="field"><label for="c-pol">Cambiar el cargo de</label><select class="inp" id="c-pol">${D.cat.politicos.map(p => `<option value="${p.id}">${esc(p.nombre)}</option>`).join('')}</select></div><div class="field"><label for="c-cargo">Cargo nuevo</label><input id="c-cargo" placeholder="Por ejemplo: Exministro de Transportes"></div></div><div class="row" style="margin-top:10px"><button class="btn sm pri" id="c-guardar">Guardar cargo</button></div>
      <div style="margin-top:12px" class="x">${CFG.extra.map((e, i) => `<span class="chip">${esc(e.nombre)} <button class="chip" data-del-extra="${i}" aria-label="Quitar">×</button></span>`).join('')}${CFG.temasExtra.map((e, i) => `<span class="chip">Tema: ${esc(e.nombre)} <button class="chip" data-del-tema="${i}" aria-label="Quitar">×</button></span>`).join('')}${Object.entries(CFG.cargos || {}).map(([k, v]) => `<span class="chip">${esc((P(k) || {}).nombre || k)}: ${esc(v)} <button class="chip" data-del-cargo="${k}" aria-label="Quitar">×</button></span>`).join('')}</div></div>
    <div class="card"><h3>Fuentes y cobertura</h3><div class="scroll"><table><thead><tr><th>Fuente</th><th>Estado</th><th>Detalle</th></tr></thead><tbody>${f.map(r => `<tr><td>${r[0]}</td><td><span class="chip ${r[1] === 'Activa' ? 'P' : ''}">${r[1]}</span></td><td class="small muted">${r[2]}</td></tr>`).join('')}</tbody></table></div><p class="muted small" style="margin-top:8px">Última recogida: ${fFH.format(new Date(D.ult.generado))} · ${c.errores} errores · ${N(c.clasificadas)} textos clasificados.</p></div>
  </div>
  <div class="card"><h3>Catálogo (${D.cat.politicos.length} personas, ${D.cat.medios.length} cabeceras, ${D.cat.temas.length} temas)</h3><p class="small muted" style="margin:6px 0">Cabeceras: ${D.cat.medios.map(m => esc(m.nombre)).join(' · ')}</p><p class="small muted">Temas: ${D.cat.temas.map(t => esc(t.nombre) + ' (' + esc(t.foco.join(', ')) + ')').join(' · ')}</p></div>`;
};

/* ---------- tarjetas (canvas) ---------- */
function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
function dibujar(id) {
  const cv = $('#cv-' + id); if (!cv) return; const c = cv.getContext('2d'), W = 1080, ac = css('--accent') || '#d4500f', ink = '#151a22', mu = '#5b6473';
  c.fillStyle = '#f6f7f9'; c.fillRect(0, 0, W, W); c.fillStyle = ac; c.fillRect(0, 0, W, 18);
  c.fillStyle = ink; c.font = '800 64px Archivo, Arial'; c.textBaseline = 'top';
  const tit = { ranking: '¿De quién hablan los medios?', tono: 'Cómo los tratan los titulares', zona: 'Zona caliente' }[id]; c.fillText(tit, 70, 80);
  c.fillStyle = mu; c.font = '500 30px IBM Plex Sans, Arial'; c.fillText('Últimas 24 horas · ' + fD.format(new Date(D.ult.generado)), 70, 162);
  if (id === 'ranking') { const r = D.cat.politicos.map(p => [p, D.ult.pol[p.id]]).sort((a, b) => b[1].vol - a[1].vol).slice(0, 8), mx = r[0][1].vol;
    r.forEach(([p, s], i) => { const y = 250 + i * 88; c.fillStyle = ink; c.font = '600 34px IBM Plex Sans, Arial'; c.fillText(p.nombre, 70, y); c.fillStyle = '#e3e6ec'; c.fillRect(70, y + 46, 800, 20); c.fillStyle = i < 3 ? ac : ink; c.fillRect(70, y + 46, Math.max(8, 800 * s.vol / mx), 20); c.fillStyle = ink; c.font = '700 34px Archivo, Arial'; c.textAlign = 'right'; c.fillText(N(s.vol), 1010, y + 30); c.textAlign = 'left'; });
    c.fillStyle = mu; c.font = '400 26px IBM Plex Sans, Arial'; c.fillText('Noticias de medios españoles que mencionan a cada político.', 70, 968); }
  if (id === 'tono') { nivel1().slice(0, 4).forEach((pid, i) => { const p = P(pid), s = D.ult.pol[pid], y = 280 + i * 200, n = s.n || 1; c.fillStyle = ink; c.font = '700 44px Archivo, Arial'; c.fillText(p.nombre, 70, y);
      let x = 70; [[s.sent[0], '#1b7f4d'], [s.sent[2], '#a7afbb'], [s.sent[1], '#c23a2b']].forEach(([v, col]) => { const w = 940 * v / n; c.fillStyle = col; c.fillRect(x, y + 66, w, 46); x += w; });
      c.fillStyle = mu; c.font = '500 28px IBM Plex Sans, Arial'; c.fillText(pct(s.sent[0], n) + ' % positivos · ' + pct(s.sent[2], n) + ' % neutros · ' + pct(s.sent[1], n) + ' % negativos · ' + s.n + ' titulares', 70, y + 126); });
    c.fillStyle = mu; c.font = '400 26px IBM Plex Sans, Arial'; c.fillText('Titulares de 24 horas clasificados con IA. No es una encuesta.', 70, 968); }
  if (id === 'zona') { const s = D.ult.tem.inmigracion, k = 1080 / D.mapa.w * 0.78; c.save(); c.translate(120, 225); c.scale(k, k);
    const vals = [0.75, 1.25, 1.75, 2.5], op = [0.1, 0.28, 0.5, 0.74, 1];
    for (const m of D.mapa.prov) { const e = s.prov[m.id]; c.globalAlpha = e ? op[vals.filter(v => e.idx >= v).length] : 0.05; c.fillStyle = ac; c.fill(new Path2D(m.d)); c.globalAlpha = 1; c.strokeStyle = '#f6f7f9'; c.lineWidth = 1; c.stroke(new Path2D(m.d)); }
    const ce = D.mapa.prov.find(m => m.id === '51'); if (ce) { c.fillStyle = ac; c.beginPath(); c.arc(ce.c[0], ce.c[1] + 12, 9, 0, 6.3); c.fill(); c.strokeStyle = ink; c.lineWidth = 1.5; c.stroke(); c.fillStyle = ink; c.font = '600 15px IBM Plex Sans, Arial'; c.fillText('Ceuta', ce.c[0] + 14, ce.c[1] + 4); }
    c.restore(); const z = Object.entries(s.prov).sort((a, b) => b[1].idx - a[1].idx)[0]; c.fillStyle = ink; c.font = '700 40px Archivo, Arial'; c.fillText('Inmigración: ' + D.prn[z[0]] + ', ×' + N1(z[1].idx) + ' lo esperable', 70, 900);
    c.fillStyle = mu; c.font = '400 26px IBM Plex Sans, Arial'; c.fillText('Noticias por provincia en ' + s.ventana + ', ajustadas por población.', 70, 968); }
  c.fillStyle = ac; c.fillRect(70, 1018, 14, 14); c.fillStyle = ink; c.font = '700 28px Archivo, Arial'; c.fillText(CFG.marca.nombre, 96, 1010);
}

/* ---------- IA en el panel ---------- */
async function iaClasificar(lista, foco) {
  if (!CAP.sample) return; const pend = [];
  for (const m of lista) for (const k of (foco ? [foco] : (m.p.length ? m.p : ['_']))) if (!etq(m, k)) pend.push([m, k]);
  if (!pend.length) return toast('No hay titulares pendientes en esta lista.');
  const lote = pend.slice(0, 60); toast('Clasificando ' + lote.length + ' titulares…');
  const instr = 'Clasifica titulares de prensa española sobre política. Para cada línea devuelve un código de 4 letras: 1) tono hacia la persona indicada (P positivo, N negativo, U neutro); 2) postura del titular o de quien habla hacia esa persona (F a favor, C en contra, N informativo); 3) emoción dominante (I ira, M miedo, E esperanza, B burla, O orgullo, T tristeza, X ninguna); 4) tema (E economía, V vivienda, I inmigración, S seguridad, C corrupción o justicia, L campaña electoral, T territorial, X exterior, A social o sanidad, O otros). Si la línea indica «tema», valora el tono general de la noticia. Responde solo con JSON: {"r":["NCIL",...]} en el mismo orden.\n\n' + lote.map(([m, k], i) => (i + 1) + '. [' + (P(k) ? P(k).nombre : 'tema') + '] ' + m.t + ' — ' + m.s).join('\n');
  try { const out = await CAP.sample.json(instr, { modelTier: 'quick' }); const r = (out && out.r) || []; let n = 0;
    lote.forEach(([m, k], i) => { const c = String(r[i] || '').toUpperCase(); if (/^[PNU][FCN][IMEBOTX][EVISCLTXAO]$/.test(c)) { (CORR[m.id] = CORR[m.id] || {})[k] = c; n++; } });
    await guardar('clasif/panel', { mapa: CORR }); calcular(); pintar(); toast(n + ' titulares clasificados' + (pend.length > lote.length ? '. Quedan ' + (pend.length - lote.length) + '.' : '.'));
  } catch (e) { toast(e && e.code === 'rate_limited' ? 'Límite de uso alcanzado. Prueba más tarde.' : 'No se pudo clasificar ahora.'); }
}
function contexto() {
  const top = D.cat.politicos.map(p => [p, ST.pol[p.id]]).sort((a, b) => b[1].vol - a[1].vol).slice(0, 20).map(([p, s]) => `${p.nombre} (${p.partido}): ${s.vol} noticias, ${s.tit} titulares, tono +${s.sent[0]}/=${s.sent[2]}/-${s.sent[1]} (n=${s.n}), postura favor ${s.post[0]} contra ${s.post[1]}, Wikipedia ${s.wiki} (media ${s.wiki7})`).join('\n');
  const tem = D.cat.temas.map(t => { const s = D.ult.tem[t.id], z = Object.entries(s.prov || {}).sort((a, b) => b[1].idx - a[1].idx).slice(0, 3).map(e => D.prn[e[0]] + ' ×' + e[1].idx).join(', '); return `${t.nombre}: ${s.agendaPct}% de titulares de las 17 cabeceras; zonas calientes: ${z || 'n/d'}`; }).join('\n');
  return `Periodo: ${S.rango}. Fecha de los datos: ${D.ult.generado}.\nPOLÍTICOS\n${top}\nTEMAS\n${tem}\nHISTORIAS DEL DÍA\n${D.ult.historias.map(h => h.medios + ' medios: ' + h.t).join('\n')}\nALERTAS\n${D.ult.alertas.map(a => a.titulo + '. ' + a.detalle).join('\n')}\nTENDENCIAS X\n${D.ult.x ? D.ult.x.ahora.slice(0, 25).map(a => a.t).join(', ') : ''}`;
}

/* ---------- base de datos del panel ---------- */
async function leer(path) { if (!CAP.db) return null; try { const r = await CAP.db.doc(path).get(); if (!r) return null; if (typeof r.data === 'function') return r.exists === false ? null : r.data(); if (r.exists === false) return null; return ('data' in r && r.data && typeof r.data === 'object') ? r.data : r; } catch (e) { return null; } }
async function guardar(path, data) { try { localStorage.setItem('prometeo:' + path, JSON.stringify(data)); } catch (e) { } if (!CAP.db) return false; try { await CAP.db.doc(path).set(data); return true; } catch (e) { return false; } }
function local(path) { try { return JSON.parse(localStorage.getItem('prometeo:' + path) || 'null'); } catch (e) { return null; } }
async function cargarConfig() {
  const lee = async p => (await leer(p)) || local(p);
  const [a, c, l, b] = await Promise.all([lee('config/ajustes'), lee('clasif/panel'), lee('estado/alertas'), lee('impacto/borradores')]);
  if (a) CFG = Object.assign(CFG, a, { marca: Object.assign(CFG.marca, a.marca || {}), umbrales: Object.assign(CFG.umbrales, a.umbrales || {}) });
  if (c && c.mapa) CORR = c.mapa; if (l && l.leidas) LEIDAS = l.leidas; if (b && b.items) BORR = b.items;
  Object.entries(CFG.cargos || {}).forEach(([k, v]) => { if (D.pid && D.pid[k]) D.pid[k].cargo = v; });
  aplicarMarca();
}
const guardarCfg = () => guardar('config/ajustes', CFG);
function aplicarMarca() {
  $('#marca-nombre').textContent = CFG.marca.nombre || 'Prometeo'; document.title = CFG.marca.nombre || 'Prometeo';
  if (CFG.marca.color) { document.documentElement.style.setProperty('--accent', CFG.marca.color); const h = CFG.marca.color.replace('#', ''), l = (parseInt(h.slice(0, 2), 16) * 299 + parseInt(h.slice(2, 4), 16) * 587 + parseInt(h.slice(4, 6), 16) * 114) / 1000; document.documentElement.style.setProperty('--accent-ink', l > 150 ? '#151a22' : '#ffffff'); }
  else { document.documentElement.style.removeProperty('--accent'); document.documentElement.style.removeProperty('--accent-ink'); }
  if (CFG.marca.logo) $('#marca-logo').innerHTML = '<img alt="" src="' + CFG.marca.logo + '">';
}

/* ---------- pintar y eventos ---------- */
function pintar() {
  const v = V[S.vista] ? S.vista : 'resumen';
  $$('#nav a').forEach(a => a.classList.toggle('on', a.dataset.v === v));
  $$('#rango button').forEach(b => b.classList.toggle('on', b.dataset.r === S.rango)); $('#pers').classList.toggle('hide', S.rango !== 'pers');
  const pri = D.est.primer || D.serie.dias[0], disp = fechas(pri, D.est.ultima).length, pide = { '7d': 7, '30d': 30, '1a': 365 }[S.rango];
  $('#rango-nota').textContent = pide && pide > disp ? 'El archivo empieza el ' + diaCorto(pri) + ': hay ' + disp + ' días.' : (ST && ST.dias.length > MAXD ? 'Titulares: últimos ' + MAXD + ' días del periodo.' : '');
  const na = alertasVivas().length; $('#n-alertas').textContent = na; $('#n-alertas').classList.toggle('hide', !na);
  $('#vista').innerHTML = avisoGeneral() + V[v]();
  if (v === 'tarjetas') (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => TARJ.forEach(t => dibujar(t.id)));
}
function avisoGeneral() {
  const h = (Date.now() - new Date(D.ult.generado).getTime()) / 36e5, c = D.ult.cobertura || {}, l = [];
  if (h > 8) l.push(`Los datos son de hace ${Math.round(h)} horas (${fFH.format(new Date(D.ult.generado))}). La siguiente recogida los pondrá al día.`);
  (D.ult.avisos || []).forEach(a => l.push(esc(a)));
  if (c.provAnteriores > 20 && c.provGenerado && (Date.now() - new Date(c.provGenerado).getTime()) / 36e5 > 20) l.push('El mapa por provincias no se ha podido renovar en las últimas recogidas: muestra datos anteriores.');
  return l.length ? `<div class="aviso" style="margin-bottom:12px;border-left-color:var(--neg)">${l.join('<br>')}</div>` : '';
}
function ir(v) { if (location.hash !== '#' + v) location.hash = v; else { S.vista = v; pintar(); } }
function abrirAlertas() { $('#drawer').innerHTML = `<div class="row between"><h3>Alertas</h3><div class="row"><button class="btn sm" id="leer-todas">Marcar todas como revisadas</button><button class="btn sm" id="cerrar">Cerrar</button></div></div><p class="muted small" style="margin:6px 0 10px">Picos de presencia, tono negativo, portadas, tendencias, zonas calientes e interés ciudadano. También llegan por correo con el informe diario.</p><div class="lista">${D.ult.alertas.map(filaAlerta).join('')}</div>`; $('#drawer').classList.add('on'); $('#velo').classList.add('on'); }
function cerrarDrawer() { $('#drawer').classList.remove('on'); $('#velo').classList.remove('on'); }
function popClas(mid, k) {
  const m = mPorId(mid); if (!m) return; const c = etq(m, k) || 'UNXO';
  const grupo = (i, obj) => `<div class="x" data-g="${i}">${Object.entries(obj).map(([a, t]) => `<button class="chip ${c[i] === a ? 'sel' : ''}" data-v="${a}">${t}</button>`).join('')}</div>`;
  $('#drawer').innerHTML = `<div class="row between"><h3>Clasificación</h3><button class="btn sm" id="cerrar">Cerrar</button></div><p class="small" style="margin:8px 0"><b>${esc(m.s)}:</b> ${esc(m.t)}</p><p class="muted small">${P(k) ? 'Respecto a ' + esc(P(k).nombre) : 'Tono general de la noticia'}</p><h4 style="margin:12px 0 6px">Tono</h4>${grupo(0, TONO)}<h4 style="margin:12px 0 6px">Postura</h4>${grupo(1, POST)}<h4 style="margin:12px 0 6px">Emoción</h4>${grupo(2, EMO)}<h4 style="margin:12px 0 6px">Tema</h4>${grupo(3, TEMA)}<div class="row" style="margin-top:16px"><button class="btn pri" id="clas-ok" data-mid="${mid}" data-k="${k}">Guardar</button></div><p class="muted xs" style="margin-top:10px">Tus correcciones se guardan y cuentan en todas las cifras del panel.</p>`;
  $('#drawer').classList.add('on'); $('#velo').classList.add('on');
}
document.addEventListener('click', async e => {
  const t = e.target.closest('button,a,[data-pol],[data-tema],[data-prov],th[data-o]'); if (!t) return;
  const d = t.dataset;
  if (t.closest('#rango') && d.r) { S.rango = d.r; if (d.r === 'pers' && !S.desde) { S.desde = D.est.primer || D.serie.dias[0]; S.hasta = D.est.ultima; $('#f-desde').value = S.desde; $('#f-hasta').value = S.hasta; } return refrescar(); }
  if (t.id === 'btn-alertas' || t.id === 'ver-alertas' || t.id === 'ver-alertas2') return abrirAlertas();
  if (t.id === 'cerrar') return cerrarDrawer();
  if (t.id === 'leer-todas') { D.ult.alertas.forEach(a => LEIDAS[a.id] = 1); await guardar('estado/alertas', { leidas: LEIDAS }); cerrarDrawer(); return pintar(); }
  if (d.clas) { e.preventDefault(); return popClas(d.clas, d.k); }
  if (t.closest('[data-g]') && d.v) { $$('.chip', t.closest('[data-g]')).forEach(x => x.classList.remove('sel')); return t.classList.add('sel'); }
  if (t.id === 'clas-ok') { const c = [0, 1, 2, 3].map(i => ($(`[data-g="${i}"] .sel`, $('#drawer')) || {}).dataset.v).join(''); (CORR[d.mid] = CORR[d.mid] || {})[d.k] = c; await guardar('clasif/panel', { mapa: CORR }); cerrarDrawer(); calcular(); pintar(); return toast('Clasificación guardada.'); }
  if (d.imp) { S.imp = d.imp; S.impTxt = ''; return ir('impacto'); }
  if (d.n1) { e.stopPropagation(); let n = nivel1().slice(); if (n.includes(d.n1)) n = n.filter(x => x !== d.n1); else if (n.length < 5) n.push(d.n1); else return toast('Máximo 5 personas en nivel 1.'); CFG.nivel1 = n; await guardarCfg(); pintar(); return toast('Nivel 1 actualizado. Se aplica en la siguiente recogida.'); }
  if (d.volver) { S.pol = null; return pintar(); }
  if (d.irMen) { S.f.pol = d.irMen; S.f.pag = 1; return; }
  if (d.pol) { cerrarDrawer(); S.pol = d.pol; if (S.vista !== 'politicos') return ir('politicos'); pintar(); return window.scrollTo(0, 0); }
  if (d.tema) { cerrarDrawer(); S.tema = d.tema; S.prov = null; return ir('temas'); }
  if (d.t && t.closest('#tabs-tema')) { S.tema = d.t; S.prov = null; return pintar(); }
  if (d.m && t.closest('#mapa-modo')) { S.mapaModo = d.m; return pintar(); }
  if (d.prov) { S.prov = d.prov; return pintar(); }
  if (d.o) { if (S.orden === d.o) S.dir *= -1; else { S.orden = d.o; S.dir = d.o === 'nom' ? 1 : -1; } return pintar(); }
  if (t.closest('#fp-amb')) { S.fp.amb = d.a; return pintar(); }
  if (t.id === 'pg-a') { S.f.pag--; return pintar(); } if (t.id === 'pg-s') { S.f.pag++; return pintar(); }
  if (t.id === 'ia-lista') return iaClasificar(filtradas(), S.f.pol || null);
  if (d.iaPol) return iaClasificar(ST.ms.filter(m => m.p.includes(d.iaPol)), d.iaPol);
  if (t.id === 'csv') { const q = s => '"' + String(s).replace(/"/g, '""') + '"'; const filas = [['fecha', 'medio', 'titular', 'politicos', 'temas', 'clasificacion', 'enlace'].join(';')].concat(filtradas().map(m => [hora(m.ts), q(m.s), q(m.t), q(m.p.map(k => P(k).nombre).join(', ')), q(m.k.join(', ')), q((m.p.length ? m.p : ['_']).map(k => etq(m, k)).join(' ')), q(enlace(m))].join(';'))); return bajar('prometeo-menciones.csv', new Blob(['﻿' + filas.join('\n')], { type: 'text/csv' })); }
  if (d.copiar) { const el = $('#' + d.copiar); try { await navigator.clipboard.writeText(el.value); toast('Texto copiado.'); } catch (x) { el.select(); toast('Selecciona y copia el texto.'); } return; }
  if (t.id === 'inf-copiar') { try { await navigator.clipboard.writeText(textoInforme()); toast('Informe copiado.'); } catch (x) { toast('No se pudo copiar.'); } return; }
  if (t.id === 'inf-pdf') return pdfInforme();
  if (d.png) { $('#cv-' + d.png).toBlob(b => bajar('prometeo-' + d.png + '-' + D.ult.fecha + '.png', b), 'image/png'); return; }
  if (d.iaTx) { const ta = $('#tx-' + d.iaTx); t.disabled = true; try { const r = await CAP.sample('Reescribe este texto para publicarlo en redes sociales desde la cuenta de una consultora de análisis político. Tono neutral y profesional, sin opinar ni tomar partido, máximo 270 caracteres, conserva todas las cifras tal cual. Devuelve solo el texto.\n\n' + ta.value, { modelTier: 'quick' }); if (r && r.text) ta.value = r.text.trim(); } catch (x) { toast('No se pudo generar ahora.'); } t.disabled = false; return; }
  if (t.id === 'arg-guardar') { CFG.argumentario = $('#arg').value; const ok = await guardarCfg(); $('#arg-ok').textContent = ok ? 'Guardado.' : 'Guardado en este navegador.'; return; }
  if (t.id === 'imp-redactar') { const m = mPorId(S.imp); if (!m) return; t.disabled = true; t.textContent = 'Redactando…'; CFG.argumentario = $('#arg').value;
    try { const r = await CAP.sample('Eres el redactor de respuestas de un equipo de comunicación política. Redacta UNA respuesta para ' + $('#imp-canal').value + ' al siguiente titular. Reglas: usa solo los mensajes y datos del argumentario; no inventes cifras ni hechos; tono firme y respetuoso, sin insultos ni descalificaciones personales; no finjas ser un ciudadano anónimo: habla como cuenta oficial; si el argumentario no da para responder, dilo en una línea en lugar de inventar. Longitud adecuada al canal (X y Bluesky: máximo 270 caracteres). Devuelve solo el texto.\n\nARGUMENTARIO:\n' + (CFG.argumentario || '(vacío)') + '\n\nTITULAR (' + m.s + '): ' + m.t, { modelTier: 'default' }); S.impTxt = (r && r.text || '').trim(); } catch (x) { toast('No se pudo redactar ahora.'); }
    return pintar(); }
  if (t.id === 'imp-guardar' || t.id === 'imp-aprobar') { const tx = $('#imp-borrador').value.trim(); if (!tx) return toast('Escribe o genera un texto primero.'); const m = S.imp ? mPorId(S.imp) : null; BORR.push({ texto: tx, estado: t.id === 'imp-aprobar' ? 'aprobada' : 'borrador', canal: $('#imp-canal').value, fecha: fFH.format(new Date()), origen: m ? m.s + ': ' + m.t : 'Sin titular asociado' }); BORR = BORR.slice(-60); await guardar('impacto/borradores', { items: BORR }); S.impTxt = ''; pintar(); return toast(t.id === 'imp-aprobar' ? 'Respuesta aprobada. Publícala desde la cuenta oficial.' : 'Borrador guardado.'); }
  if (t.id === 'm-guardar') { CFG.marca.nombre = $('#m-nombre').value.trim() || 'Prometeo'; CFG.marca.color = $('#m-color').value; await guardarCfg(); aplicarMarca(); pintar(); return toast('Marca guardada.'); }
  if (t.id === 'm-reset') { CFG.marca = { nombre: 'Prometeo', color: '' }; $('#marca-logo').innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 2c1 4-3 5-3 9a3 3 0 0 0 6 0c0-1-.4-1.8-.8-2.5C17 10 19 12.600 19 15.500A7 7 0 0 1 5 15.500C5 10 10 8 12 2z"/></svg>'; await guardarCfg(); aplicarMarca(); pintar(); return; }
  if (t.id === 'u-guardar') { CFG.umbrales = { pico: +$('#u-pico').value || 2, negativo: +$('#u-neg').value || 60, portada: +$('#u-port').value || 12 }; await guardarCfg(); return toast('Umbrales guardados.'); }
  if (t.id === 'n-add') { const n = $('#n-nombre').value.trim(); if (!n) return toast('Escribe el nombre.'); CFG.extra.push({ nombre: n, partido: $('#n-partido').value.trim(), cargo: $('#n-cargo').value.trim(), territorio: $('#n-terr').value.trim() || 'España' }); await guardarCfg(); pintar(); return toast('Añadido. Entrará en la siguiente recogida.'); }
  if (t.id === 't-add') { const n = $('#t-nombre').value.trim(); if (!n) return toast('Escribe el nombre del tema.'); CFG.temasExtra.push({ nombre: n, palabras: $('#t-pal').value.trim() }); await guardarCfg(); pintar(); return toast('Tema añadido. Entrará en la siguiente recogida.'); }
  if (t.id === 'c-guardar') { const v = $('#c-cargo').value.trim(), k = $('#c-pol').value; if (!v) return toast('Escribe el cargo.'); CFG.cargos = Object.assign({}, CFG.cargos, { [k]: v }); if (D.pid[k]) D.pid[k].cargo = v; await guardarCfg(); pintar(); return toast('Cargo guardado.'); }
  if (d.delCargo) { const c = Object.assign({}, CFG.cargos); delete c[d.delCargo]; CFG.cargos = c; await guardarCfg(); return pintar(); }
  if (d.delExtra) { CFG.extra.splice(+d.delExtra, 1); await guardarCfg(); return pintar(); }
  if (d.delTema) { CFG.temasExtra.splice(+d.delTema, 1); await guardarCfg(); return pintar(); }
});
document.addEventListener('input', e => { const t = e.target;
  if (t.id === 'f-q') { S.f.q = t.value; S.f.pag = 1; clearTimeout(pintar.t); pintar.t = setTimeout(() => { pintar(); const i = $('#f-q'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }, 250); }
  if (t.id === 'fp-q') { S.fp.q = t.value; clearTimeout(pintar.t); pintar.t = setTimeout(() => { pintar(); const i = $('#fp-q'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }, 250); }
  if (t.id === 'imp-borrador') S.impTxt = t.value;
});
document.addEventListener('change', async e => { const t = e.target;
  if (t.id === 'f-pol') { S.f.pol = t.value; S.f.pag = 1; pintar(); } if (t.id === 'f-tema') { S.f.tema = t.value; S.f.pag = 1; pintar(); } if (t.id === 'f-tono') { S.f.tono = t.value; S.f.pag = 1; pintar(); } if (t.id === 'f-post') { S.f.post = t.value; S.f.pag = 1; pintar(); }
  if (t.id === 'f-17') { S.f.solo17 = t.checked; S.f.pag = 1; pintar(); } if (t.id === 'f-pend') { S.f.pend = t.checked; S.f.pag = 1; pintar(); }
  if (t.id === 'f-desde' || t.id === 'f-hasta') { S.desde = $('#f-desde').value; S.hasta = $('#f-hasta').value; refrescar(); }
  if (t.id === 'imp-sel') { S.imp = t.value; S.impTxt = ''; pintar(); }
  if (t.id === 'inf-fecha') { D.infFecha = t.value; try { D.inf = (await j('informe-' + t.value + '.json')).informe; } catch (x) { D.inf = null; } pintar(); }
  if (t.id === 'm-logo' && t.files[0]) { const img = new Image(); img.onload = async () => { const c = document.createElement('canvas'); c.width = c.height = 96; const k = Math.min(img.width, img.height); c.getContext('2d').drawImage(img, (img.width - k) / 2, (img.height - k) / 2, k, k, 0, 0, 96, 96); CFG.marca.logo = c.toDataURL('image/png'); await guardarCfg(); aplicarMarca(); toast('Logo guardado.'); }; img.src = URL.createObjectURL(t.files[0]); }
});
document.addEventListener('submit', async e => { if (e.target.id !== 'preg') return; e.preventDefault(); const q = $('#preg-q').value.trim(); if (!q || !CAP.sample) return; const r = $('#resp'); r.classList.remove('hide'); r.innerHTML = '<p class="muted">Pensando…</p>';
  try { const out = await CAP.sample('Eres el analista de una plataforma de escucha social y política. Responde en español, en 2 a 5 frases, solo con los datos que siguen; cita cifras; no opines ni tomes partido por ningún partido; si los datos no bastan, dilo.\n\nDATOS\n' + contexto() + '\n\nPREGUNTA: ' + q, { onText: ({ text }) => { r.innerHTML = '<h4>Respuesta</h4><p style="margin-top:6px;white-space:pre-wrap">' + esc(text) + '</p>'; } }); r.innerHTML = '<h4>Respuesta</h4><p style="margin-top:6px;white-space:pre-wrap">' + esc(out.text) + '</p>'; }
  catch (x) { r.innerHTML = '<p class="muted">No se pudo responder ahora. Inténtalo de nuevo en un momento.</p>'; } });
$('#velo').addEventListener('click', cerrarDrawer);
window.addEventListener('hashchange', () => { const v = location.hash.slice(1); if (V[v]) { S.vista = v; if (v !== 'politicos') S.pol = null; pintar(); window.scrollTo(0, 0); } });

/* ---------- descargas ---------- */
async function bajar(nombre, blob) {
  if (CAP.downloads) { try { await CAP.downloads.save({ filename: nombre, data: blob }); } catch (e) { toast('Descarga cancelada.'); } return; }
  if (!FUERA) return toast('La descarga se activa al abrir el panel con tu cuenta.');
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = nombre; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
function script(src) { return new Promise((ok, ko) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = ko; document.head.appendChild(s); }); }
async function pdfInforme() {
  toast('Preparando el PDF…');
  try { if (!window.pdfMake) { await script('https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js'); await script('https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js'); }
    const i = D.inf || D.ult.informe, f = D.infFecha || D.ult.fecha, ac = css('--accent') || '#d4500f', H = t => ({ text: t, style: 'h' });
    const top = D.cat.politicos.map(p => [p, D.ult.pol[p.id]]).sort((a, b) => b[1].vol - a[1].vol).slice(0, 12);
    const def = { pageMargins: [48, 56, 48, 56], defaultStyle: { fontSize: 10.5, lineHeight: 1.3 }, styles: { h: { fontSize: 13, bold: true, margin: [0, 14, 0, 5] }, m: { color: '#666', fontSize: 9 } },
      footer: (p, n) => ({ text: CFG.marca.nombre + ' · Informe diario · ' + p + ' de ' + n, alignment: 'center', color: '#888', fontSize: 8, margin: [0, 20, 0, 0] }),
      content: [{ text: CFG.marca.nombre.toUpperCase(), color: ac, bold: true, fontSize: 10, characterSpacing: 1.5 }, { text: 'Informe diario · ' + fD.format(new Date(f + 'T12:00:00Z')), style: 'm', margin: [0, 2, 0, 10] }, { text: i.titular, fontSize: 18, bold: true, margin: [0, 0, 0, 8] }, { text: i.entradilla },
        H('Claves'), ...i.claves.map(c => ({ text: [{ text: c.t + '. ', bold: true }, c.d], margin: [0, 0, 0, 5] })),
        ...(f === D.ult.fecha ? [H('Presencia en medios · últimas 24 horas'), { table: { headerRows: 1, widths: ['*', 50, 50, 60, 70], body: [['Político', 'Noticias', 'Titulares', '17 cabeceras', 'Negativos'].map(t => ({ text: t, bold: true, fontSize: 9 })), ...top.map(([p, s]) => [p.nombre + ' (' + p.partido + ')', N(s.vol), N(s.tit), N(s.cat), s.n ? pct(s.sent[1], s.n) + ' % (n=' + s.n + ')' : '–'])] }, layout: 'lightHorizontalLines', fontSize: 9.5 }] : []),
        H('Seguimiento en profundidad'), ...i.lideres.map(l => ({ text: [{ text: ((P(l.id) || {}).nombre || l.id) + '. ', bold: true }, l.texto], margin: [0, 0, 0, 5] })),
        H('Temas'), ...i.temas.map(l => ({ text: [{ text: ((D.tid[l.id] || {}).nombre || l.id) + '. ', bold: true }, l.texto], margin: [0, 0, 0, 5] })),
        H('Redes'), { text: i.redes }, H('Qué vigilar'), { ul: i.vigilar }, H('Cómo se ha medido'), { text: i.metodo, style: 'm' }] };
    pdfMake.createPdf(def).getBlob(b => bajar('informe-' + f + '.pdf', b));
  } catch (e) { toast('No se pudo crear el PDF. Usa «Copiar texto».'); }
}

/* ---------- arranque ---------- */
(async function () {
  try {
    const [est, cat, ult, serie, mapa] = await Promise.all([j('estado.json'), j('catalogo.json'), j('ultimo.json'), j('serie.json'), j('mapa.json')]);
    Object.assign(D, { est, cat, ult, serie, mapa }); D.pid = Object.fromEntries(cat.politicos.map(p => [p.id, p])); D.tid = Object.fromEntries(cat.temas.map(t => [t.id, t])); D.prn = Object.fromEntries(cat.provincias.map(p => [p.id, p.nombre]));
    const el = cat.elecciones, faltan = Math.ceil((new Date(el.fecha + 'T00:00:00+01:00') - Date.now()) / 864e5);
    $('#cuenta').innerHTML = faltan > 0 ? `Faltan <b class="num">${faltan}</b> días para el 29-N` : faltan === 0 ? '<b>Hoy se vota</b>' : '';
    $('#pie-fecha').textContent = 'Datos: ' + fFH.format(new Date(ult.generado)); $('#pie-cob').textContent = N(ult.cobertura.noticias) + ' noticias · ' + ult.cobertura.consultas + ' consultas';
    const v = location.hash.slice(1); if (V[v]) S.vista = v;
    Object.assign(CFG, local('config/ajustes') || {}); aplicarMarca();
    await refrescar();
    if (window.claude && window.claude.use) {
      const [db, sample, downloads] = await Promise.all(['db', 'sample', 'downloads'].map(n => window.claude.use(n).catch(() => null)));
      CAP = { db, sample, downloads }; await cargarConfig(); calcular(); pintar();
    }
  } catch (e) { $('#vista').innerHTML = '<div class="card"><h3>No se han podido cargar los datos</h3><p class="muted" style="margin-top:6px">Vuelve a abrir el panel en unos minutos. Detalle: ' + esc(e.message) + '</p></div>'; }
})();
