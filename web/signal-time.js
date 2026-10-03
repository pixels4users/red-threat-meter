// A daily measurement has a date, never an invented publication time.
// UTC midnight is only its deterministic ordering/binning key. The UI renders
// the whole observed day, including a separate daily row in the hourly timeline.
export function signalTime(event) {
  const measurement = event.presentation?.kind === 'measurement' || event.sources?.some(s => s.source_id === 'gpsjam_reviewed');
  if (measurement && /^\d{4}-\d{2}-\d{2}$/.test(event.occurred_on ?? '')) {
    const value = `${event.occurred_on}T00:00:00Z`;
    if (Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === event.occurred_on)
      return { value, day: event.occurred_on, precision: 'day', basis: 'measurement' };
  }
  if (event.published_at && Number.isFinite(Date.parse(event.published_at)))
    return { value: event.published_at, day: null, precision: 'instant', basis: 'publication' };
  return { value: null, day: null, precision: 'unknown', basis: null };
}
