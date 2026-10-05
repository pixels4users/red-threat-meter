// Display geography only. Never writes coordinates or changes a frozen report.
import capitals from './assets/capitals.json' with { type: 'json' };
import boundaries from './assets/admin1.json' with { type: 'json' };
import { presentation } from './signals.js';

const fold = s => (s ?? '').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/ł/g, 'l').replace(/\s+/g, ' ').trim();
const byId = new Map(boundaries.features.map(f => [f.properties.id, f]));
const includesName = (text, name) => new RegExp(`(^|[\\s,;:()—–-])${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?=$|[\\s,;:()—–-])`, 'u').test(text);

export function eventAreas(event) {
  const p = presentation(event), location = event.location;
  // A reviewed city or an actual point is more precise than the filter region.
  if (location.geometry || p.map_anchor || p.scope === 'national') return [];
  const label = fold(location.label), ids = new Set();
  if (event.country === 'PL') for (const id of p.region_ids) if (byId.has(id) && id.startsWith('PL-')) ids.add(id);
  if (!['unknown', 'country'].includes(location.precision)) {
    for (const f of boundaries.features) {
      const { id, country, label: name } = f.properties;
      if (country === event.country && includesName(label, fold(name))) ids.add(id);
    }
  }
  return [...ids].map(id => {
    const feature = byId.get(id), name = fold(feature.properties.label);
    const exact = location.precision === 'region' && (label === name || (event.country === 'PL' && /^wojewodztwa? /.test(label) && includesName(label, name.replace(/^wojewodztwo /, ''))));
    return { feature, context: !exact };
  });
}

export function mapPoints(report) {
  if (!report) return [];
  const points = [];
  for (const event of report.incidents) {
    const p = presentation(event), geometry = event.location.geometry, anchor = p.map_anchor;
    if (geometry?.type === 'Point') points.push({ id: event.id, coordinates: geometry.coordinates, event, national: false });
    else if (anchor?.type === 'Point') points.push({ id: event.id, coordinates: anchor.coordinates, event, national: false, city: anchor.label });
    else if (p.scope === 'national') {
      const capital = capitals.find(c => c.country_code === event.country);
      if (capital) points.push({ id: event.id, coordinates: capital.coordinates, event, national: true, capital: capital.name });
    }
  }
  return points;
}

export function mapAreas(report) {
  const areas = new Map();
  for (const event of report?.incidents ?? []) for (const { feature, context } of eventAreas(event)) {
    const id = feature.properties.id;
    if (!areas.has(id)) areas.set(id, { feature, events: [] });
    areas.get(id).events.push({ event, context });
  }
  return [...areas.values()];
}

export function mappedSignalIds(report) {
  return new Set([...mapPoints(report).map(p => p.id), ...mapAreas(report).flatMap(a => a.events.map(e => e.event.id))]);
}

export function areaLocationNote(event) {
  const areas = eventAreas(event);
  if (!areas.length) return '';
  return areas.some(a => a.context)
    ? `Orientacja na mapie: ${areas.map(a => a.feature.properties.label).join(', ')}. Obrys pomaga odnaleźć opisany rejon; nie oznacza zasięgu zdarzenia ani zagrożenia.`
    : 'Obrys pokazuje region wskazany w raporcie, nie dokładne miejsce ani zasięg zagrożenia.';
}
