// Prometeo · recogidas auxiliares. Cada bloque se ejecuta en la pestaña indicada y deja el resultado en el cuerpo de la página
// (con relleno para que la lectura de texto se guarde como fichero). Después: leer el texto de la página con max_chars alto.

// ===== [x] Tendencias de X en España · navegar antes a https://trends24.in/spain/ =====
(() => {
  const cards = [...document.querySelectorAll('.list-container, .trend-card')].slice(0, 26).map(c => ({ h: (c.querySelector('h3, .title, .trend-card__time')?.textContent || '').trim(), ts: c.querySelector('[data-timestamp]')?.getAttribute('data-timestamp') || '', l: [...c.querySelectorAll('li')].slice(0, 50).map(li => { const a = li.querySelector('a'); const n = li.querySelector('.tweet-count'); return [(a ? a.textContent : li.textContent).trim(), n ? (n.getAttribute('data-count') || n.textContent).trim() : '']; }) }));
  const agg = {}; cards.forEach((c, ci) => c.l.forEach(([n, cnt], ri) => { const a = agg[n] = agg[n] || { h: 0, best: 99, first: ci, cnt: '' }; a.h++; a.best = Math.min(a.best, ri + 1); a.first = Math.min(a.first, ci); if (cnt && !a.cnt) a.cnt = cnt; }));
  const out = { src: 'trends24', at: new Date().toISOString(), horas: cards.length, ahora: cards[0] ? cards[0].l : [], etiquetaAhora: cards[0] ? cards[0].h : '', hist: Object.entries(agg).map(([n, a]) => [n, a.h, a.best, a.first, a.cnt]).sort((x, y) => y[1] - x[1]), pad: 'x'.repeat(56000) };
  document.body.textContent = JSON.stringify(out); return 'ok ' + out.hist.length;
})();

// ===== [google] Búsquedas en alza · navegar antes a https://trends.google.com/robots.txt =====
(async () => {
  const dec = s => (s || '').replace(/<!\[CDATA\[|\]\]>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&apos;/g, "'").trim();
  const r = await fetch('/trending/rss?geo=ES', { credentials: 'omit' }); const x = await r.text();
  const items = [...x.matchAll(/<item>([\s\S]*?)<\/item>/g)].map(m => { const b = m[1], g = re => { const k = b.match(re); return k ? dec(k[1]) : ''; }; return { t: g(/<title>([\s\S]*?)<\/title>/), tr: g(/<ht:approx_traffic>([\s\S]*?)<\/ht:approx_traffic>/), d: g(/<pubDate>([\s\S]*?)<\/pubDate>/), news: [...b.matchAll(/<ht:news_item>([\s\S]*?)<\/ht:news_item>/g)].slice(0, 2).map(n => [dec((n[1].match(/<ht:news_item_title>([\s\S]*?)<\/ht:news_item_title>/) || [])[1]), dec((n[1].match(/<ht:news_item_source>([\s\S]*?)<\/ht:news_item_source>/) || [])[1]), dec((n[1].match(/<ht:news_item_url>([\s\S]*?)<\/ht:news_item_url>/) || [])[1])]) }; });
  document.body.textContent = JSON.stringify({ src: 'gtrends', at: new Date().toISOString(), status: r.status, items, pad: 'x'.repeat(56000) }); return 'ok ' + items.length;
})();

// ===== [meneame] Portada de Menéame · navegar antes a https://www.meneame.net/robots.txt =====
(async () => {
  const dec = s => (s || '').replace(/<!\[CDATA\[|\]\]>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&apos;/g, "'").trim();
  const r = await fetch('/rss', { credentials: 'omit' }); const x = await r.text();
  const items = [...x.matchAll(/<item>([\s\S]*?)<\/item>/g)].map(m => { const b = m[1], g = re => { const k = b.match(re); return k ? dec(k[1]) : ''; }; return { t: g(/<title>([\s\S]*?)<\/title>/), l: g(/<link>([\s\S]*?)<\/link>/), d: g(/<pubDate>([\s\S]*?)<\/pubDate>/), sub: g(/<meneame:sub>([\s\S]*?)<\/meneame:sub>/), v: +g(/<meneame:votes>([\s\S]*?)<\/meneame:votes>/), neg: +g(/<meneame:negatives>([\s\S]*?)<\/meneame:negatives>/), k: +g(/<meneame:karma>([\s\S]*?)<\/meneame:karma>/), c: +g(/<meneame:comments>([\s\S]*?)<\/meneame:comments>/), cl: +g(/<meneame:clicks>([\s\S]*?)<\/meneame:clicks>/) }; });
  document.body.textContent = JSON.stringify({ src: 'meneame', at: new Date().toISOString(), status: r.status, items, pad: 'x'.repeat(56000) }); return 'ok ' + items.length;
})();
