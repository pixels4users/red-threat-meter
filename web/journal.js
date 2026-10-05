import { dateKey, parts, statuses } from './data.js';
import { signalTime } from './signal-time.js';

const dayFormat = new Intl.DateTimeFormat('pl-PL', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' });

export function journalDays(records) {
  const groups = new Map();
  for (const event of records) {
    const t = signalTime(event), day = t.day ?? (t.value ? dateKey(t.value) : '');
    if (!groups.has(day)) groups.set(day, []);
    groups.get(day).push(event);
  }
  return [...groups].sort(([a], [b]) => b.localeCompare(a)).map(([day, events]) => ({
    day, label: day ? dayFormat.format(new Date(`${day}T12:00:00Z`)) : 'Bez ustalonej daty', events,
  }));
}

export function journalClock(event) {
  const t = signalTime(event);
  if (t.precision === 'day') return 'Pomiar';
  if (!t.value) return '—';
  const p = parts(t.value); return `${p.hour}:${p.minute}`;
}

export function journalCaution(event) {
  const notes = [];
  if (!['confirmed_primary', 'corroborated'].includes(event.status)) notes.push(statuses[event.status] ?? 'Status nieustalony');
  if (event.review_current === false) notes.push('Dostępna nowsza wersja materiału');
  return notes.join(' · ');
}
