import { select, zoom, zoomIdentity, geoMercator, geoPath, geoCentroid } from 'd3';
import { feature } from 'topojson-client';
import atlasText from './assets/countries.topojson?raw';
import capitals from './assets/capitals.json';
import { categories } from './data.js';

const atlas = JSON.parse(atlasText);
const countries = feature(atlas, atlas.objects.features).features;
const labels = { POL: 'POLSKA', BLR: 'BIAŁORUŚ', UKR: 'UKRAINA', LTU: 'LITWA', LVA: 'ŁOTWA', EST: 'ESTONIA', DEU: 'NIEMCY', CZE: 'CZECHY', SVK: 'SŁOWACJA', SWE: 'SZWECJA' };

export function mapPoints(report) {
  if (!report) return [];
  const byId = new Map(report.incidents.map(e => [e.id, e]));
  const points = report.geojson.features.map(f => ({ id: f.id, coordinates: f.geometry.coordinates, event: byId.get(f.id), national: false }));
  for (const e of report.incidents) {
    if (e.location.precision !== 'country' || e.location.geometry) continue;
    const capital = capitals.find(c => c.country_code === e.country);
    if (capital) points.push({ id: e.id, coordinates: capital.coordinates, event: e, national: true, capital: capital.name });
  }
  return points;
}

export function initializeMaps(root, getReport, getSelected, onSelect, icons, onExpand) {
  const slots = [...root.querySelectorAll('[data-map-slot]')];
  const runtime = new WeakMap();
  let camera = { zoom: 1, center: null };
  function paint(slot, r, transform) {
    const { w, h } = r, element = slot.querySelector('.r-map');
    const svg = select(element).attr('viewBox', `0 0 ${w} ${h}`); svg.selectAll('*').remove();
    svg.append('title').text('Sygnały z opublikowanego raportu');
    svg.append('desc').text('Punkty pokazują udokumentowane lokalizacje. Flagi w stolicach reprezentują informacje dotyczące całego kraju.');
    const base = r.projection, t = base.translate();
    const projection = geoMercator().center(base.center()).scale(base.scale() * transform.k).translate([t[0] * transform.k + transform.x, t[1] * transform.k + transform.y]);
    const path = geoPath(projection), clip = `map-${slot.dataset.mapSlot}`;
    svg.append('defs').append('clipPath').attr('id', clip).append('rect').attr('width', w).attr('height', h);
    const layer = svg.append('g').attr('clip-path', `url(#${clip})`);
    layer.selectAll('path').data(countries).join('path').attr('d', path);
    const points = mapPoints(getReport()).map(p => ({ ...p, xy: projection(p.coordinates) })).filter(p => p.xy[0] >= 18 && p.xy[0] <= w - 18 && p.xy[1] >= 18 && p.xy[1] <= h - 18);
    const occupied = points.map(p => ({ x: p.xy[0] - 20, y: p.xy[1] - 20, width: 40, height: 52 }));
    occupied.push({ x: w - 64, y: 0, width: 64, height: 220 });
    for (const country of countries.filter(c => labels[c.properties.id])) {
      const p = projection(geoCentroid(country)); if (p[0] < 30 || p[0] > w - 30 || p[1] < 16 || p[1] > h - 16) continue;
      const label = layer.append('text').attr('x', p[0]).attr('y', p[1]).attr('text-anchor', 'middle').text(labels[country.properties.id]);
      const box = label.node().getBBox();
      if (occupied.some(b => box.x < b.x + b.width + 4 && box.x + box.width > b.x - 4 && box.y < b.y + b.height + 4 && box.y + box.height > b.y - 4)) label.remove(); else occupied.push(box);
    }
    const clusters = [];
    for (const p of points) {
      const group = clusters.find(c => Math.hypot(c.xy[0] - p.xy[0], c.xy[1] - p.xy[1]) < 44);
      if (group) group.points.push(p); else clusters.push({ xy: p.xy, points: [p] });
    }
    const markers = slot.querySelector('.r-map-markers'); markers.replaceChildren();
    for (const group of clusters) {
      const first = group.points[0], national = group.points.find(p => p.national), ids = group.points.map(p => p.id);
      const button = document.createElement('button'); button.type = 'button'; button.className = 'r-marker'; button.dataset.pointIds = ids.join(',');
      button.style.left = `${group.xy[0]}px`; button.style.top = `${group.xy[1]}px`; button.dataset.national = String(Boolean(national));
      button.setAttribute('aria-pressed', String(ids.includes(getSelected())));
      button.setAttribute('aria-label', group.points.map(p => `${p.event.title}${p.national ? ', informacja o zasięgu krajowym' : ''}`).join('; '));
      const glyph = document.createElement('span'); glyph.className = 'r-marker-glyph';
      if (ids.length > 1 && !national) glyph.textContent = String(ids.length);
      else { const i = document.createElement('i'); i.dataset.lucide = national ? 'flag' : (categories[first.event.category]?.icon ?? 'circle-dot'); i.setAttribute('aria-hidden', 'true'); glyph.append(i); }
      button.append(glyph);
      if (national) { const label = document.createElement('span'); label.className = 'r-marker-label'; label.textContent = national.capital; button.append(label); }
      if (national && ids.length > 1) { const n = document.createElement('span'); n.className = 'r-marker-count'; n.textContent = String(ids.length); button.append(n); }
      button.addEventListener('click', () => onSelect(ids)); markers.append(button);
    }
    slot.querySelector('[data-map-zoom]').textContent = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 }).format(transform.k) + '×';
    slot.querySelector('[data-map-action=in]').disabled = transform.k >= 6 - 1e-6;
    slot.querySelector('[data-map-action=out]').disabled = transform.k <= .5 + 1e-6;
    icons();
  }
  function draw(slot) {
    const stage = slot.querySelector('.r-map-stage'), w = stage.clientWidth, h = stage.clientHeight;
    if (w < 10) return;
    let r = runtime.get(slot);
    if (!r) {
      r = { stage, syncing: false }; runtime.set(slot, r);
      r.zoom = zoom().scaleExtent([.5, 6]).touchable(() => true)
        .filter(e => !e.target.closest('button') && !e.button && (e.type !== 'wheel' || e.ctrlKey))
        .on('zoom', e => { if (!r.syncing) { camera = { zoom: e.transform.k, center: r.projection.invert(e.transform.invert([r.w / 2, r.h / 2])) }; paint(slot, r, e.transform); } });
      select(stage).call(r.zoom);
    }
    r.w = w; r.h = h;
    // Stable view also works with an empty dataset and with a single point.
    r.projection = geoMercator().center([23, 53.2]).scale(Math.min(w / .34, h / .31)).translate([w / 2, h / 2]);
    r.zoom.extent([[0, 0], [w, h]]).translateExtent([[-2 * w, -2 * h], [3 * w, 3 * h]]);
    const center = camera.center ? r.projection(camera.center) : [w / 2, h / 2], k = camera.zoom;
    const transform = zoomIdentity.translate(w / 2 - k * center[0], h / 2 - k * center[1]).scale(k);
    r.syncing = true; select(stage).call(r.zoom.transform, transform); r.syncing = false; paint(slot, r, transform);
  }
  for (const slot of slots) {
    slot.append(root.querySelector('template[data-template=map]').content.cloneNode(true));
    if (slot.dataset.mapSlot === 'expanded') slot.querySelector('[data-map-action=expand]').hidden = true;
    for (const button of slot.querySelectorAll('[data-map-action]')) button.addEventListener('click', () => {
      const action = button.dataset.mapAction;
      if (action === 'expand') return onExpand(button);
      if (action === 'reset') { camera = { zoom: 1, center: null }; slots.forEach(draw); return; }
      const r = runtime.get(slot); if (r) select(r.stage).call(r.zoom.scaleBy, action === 'in' ? 1.5 : 1 / 1.5);
    });
  }
  const observer = new ResizeObserver(() => slots.forEach(draw)); slots.forEach(s => observer.observe(s.querySelector('.r-map-stage')));
  return { draw: () => slots.forEach(draw) };
}
