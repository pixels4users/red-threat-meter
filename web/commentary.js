import { filterSignals } from './signals.js';

// Optional conclusions stay absent. A missing recommendation is not a request
// for the UI to invent one from a score or an unconfirmed signal.
export function commentaryRows(report, area, records = report?.incidents ?? []) {
  if (!report) return [];
  const sections = report.commentary.sections ?? (report.commentary.text ? { situation: report.commentary.text } : {});
  const rows = [];
  if (sections.situation) rows.push(['Sytuacja', sections.situation]);
  if (area === 'macro') {
    if (sections.impact) rows.push(['Wpływ na Polskę', sections.impact]);
    if (sections.recommendation) rows.push(['Co zrobić', sections.recommendation]);
  } else {
    const local = filterSignals(records, { asOf: report.as_of, area, period: 'current7', includeNational: false })
      .find(e => e.review_current && ['confirmed_primary', 'corroborated'].includes(e.status));
    if (local) rows.push(['Twój region', local.title]);
  }
  return rows;
}
