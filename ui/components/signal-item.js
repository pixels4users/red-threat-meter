// Shared disclosure for timeline, map list and journal. Content is text/DOM,
// never report-supplied HTML. The caller owns selection and panel placement.
const node = (tag, cls, text) => {
  const e = document.createElement(tag); e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};
// Decorative taxonomy icon stays attached to its visible category label.
export function createCategoryLabel({ icon, label, count }) {
  const labelNode = node('span', 'r-category-label');
  const glyph = node('i', ''); glyph.dataset.lucide = icon;
  glyph.setAttribute('aria-hidden', 'true');
  labelNode.append(glyph, node('span', '', count === undefined ? label : `${count}× ${label}`));
  return labelNode;
}

export function createSignalItem({ id, signalId, controls, title, icon, clock,
  before = [], after = [], compact = false, onToggle }) {
  const row = node('article', 'r-signal-disclosure' + (compact ? ' r-signal-disclosure--compact' : ''));
  const trigger = node('button', 'r-signal-toggle'); trigger.type = 'button';
  trigger.id = id; trigger.dataset.signalId = signalId;
  trigger.setAttribute('aria-expanded', 'false'); trigger.setAttribute('aria-controls', controls);
  trigger.addEventListener('click', () => onToggle(trigger));
  if (clock) { clock.classList.add('r-signal-clock'); trigger.append(clock); }
  if (icon) {
    const glyph = node('i', 'r-signal-icon'); glyph.dataset.lucide = icon;
    glyph.setAttribute('aria-hidden', 'true'); trigger.append(glyph);
  }
  const content = node('span', 'r-signal-content');
  content.append(...before, node('span', 'r-signal-title', title), ...after);
  const chevron = node('i', 'r-signal-chevron'); chevron.dataset.lucide = 'chevron-down';
  chevron.setAttribute('aria-hidden', 'true'); trigger.append(content, chevron);
  row.append(trigger); return { row, trigger };
}

export function prepareSignalDetail(panel, { compact = false } = {}) {
  panel.classList.add('r-signal-detail');
  if (compact) panel.classList.add('r-signal-detail--compact');
  panel.setAttribute('role', 'region');
  panel.querySelector('[data-detail-title]').hidden = true;
  panel.querySelector('[data-detail-tag]').hidden = true;
  panel.querySelector('[data-close-detail]').remove();
  const copy = node('div', 'r-signal-detail-copy'), facts = node('div', 'r-signal-detail-facts');
  copy.append(panel.querySelector('[data-detail-summary]'));
  facts.append(panel.querySelector('dl'));
  panel.querySelector('.r-detail').append(copy, facts);
}
