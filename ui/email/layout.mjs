// Email adapter of the Design System's light palette and 4px spacing scale.
// Inline frame styles remain readable when an email client removes the stylesheet.
// This frame is shared by daily reports and subscription confirmations.
export const emailLogoPath = '/assets/rta-mark-v1.png';
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const color = { paper:'#ffffff', canvas:'#f6f6f6', ink:'#171717', muted:'#626262', border:'#dedede' };

export function emailFrame({ title, eyebrow, headline, dateline = '', content, footer, siteUrl }) {
  const logo = new URL(emailLogoPath, siteUrl).href;
  return `<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHTML(title)}</title><style>
    body,table,td{font-family:Arial,Helvetica,sans-serif}table{border-collapse:collapse}a{color:${color.ink};text-decoration:underline;text-underline-offset:3px}p{margin:0 0 16px}h2{font-size:24px;line-height:1.3;margin:40px 0 20px;padding-top:28px;border-top:1px solid ${color.border};font-weight:700}h3{font-size:18px;line-height:1.4;margin:28px 0 12px}h4{font-size:17px;line-height:1.5;margin:24px 0 8px}ul{padding-left:20px;margin:0 0 24px}li{margin:0 0 8px}.r-email-meta{font-size:13px;line-height:1.6;color:${color.muted}}.r-email-group{background:${color.canvas};padding:12px 16px}.r-email-summary h2{border:0;padding:0;margin:0 0 20px;font-size:22px}.r-email-summary h3{font-size:14px;margin:20px 0 8px}.r-email-summary p:last-child{margin-bottom:0}a:focus-visible{outline:2px solid currentColor;outline-offset:4px}
    @media(max-width:480px){.r-email-shell{padding:12px 8px!important}.r-email-pad{padding:24px 20px!important}.r-email-headline{font-size:28px!important}.r-email-brand{font-size:22px!important}.r-email-inset{padding:20px!important}.r-email-score{font-size:48px!important}}
  </style></head><body style="margin:0;padding:0;background:${color.canvas};color:${color.ink};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="${color.canvas}"><tr><td class="r-email-shell" align="center" style="padding:32px 12px">
  <!--[if mso]><table role="presentation" width="680" cellpadding="0" cellspacing="0"><tr><td><![endif]-->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="${color.paper}" style="max-width:680px;table-layout:fixed;background:${color.paper}"><tr><td class="r-email-pad" bgcolor="${color.ink}" style="padding:32px;background:${color.ink};color:#ffffff">
    <table role="presentation" cellpadding="0" cellspacing="0"><tr><td width="44" style="width:44px;padding-right:8px;vertical-align:middle"><img src="${escapeHTML(logo)}" width="44" height="44" alt="" style="display:block;border:0;width:44px;height:44px"></td><td class="r-email-brand" style="font-size:24px;line-height:1.25;font-weight:700;color:#ffffff">RedThreatAlert</td></tr></table>
    <p style="margin:32px 0 8px;font-size:12px;line-height:18px;letter-spacing:1.5px;color:#dedede">${escapeHTML(eyebrow)}</p>
    <h1 class="r-email-headline" style="margin:0;font-size:36px;line-height:1.2;font-weight:700;color:#ffffff">${escapeHTML(headline)}</h1>
    ${dateline ? `<p style="margin:16px 0 0;font-size:13px;line-height:20px;color:#dedede">${escapeHTML(dateline)}</p>` : ''}
  </td></tr><tr><td class="r-email-pad" style="padding:32px;font-size:16px;line-height:1.65;color:${color.ink};overflow-wrap:anywhere;word-wrap:break-word">${content}</td></tr><tr><td class="r-email-pad" bgcolor="${color.canvas}" style="padding:32px;border-top:1px solid ${color.border};font-size:13px;line-height:1.6;color:${color.muted}">${footer}</td></tr></table>
  <!--[if mso]></td></tr></table><![endif]-->
  </td></tr></table></body></html>`;
}

export function emailInset(content) {
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0;background:${color.canvas}"><tr><td class="r-email-inset r-email-summary" bgcolor="${color.canvas}" style="padding:24px;font-size:16px;line-height:1.65;color:${color.ink}">${content}</td></tr></table>`;
}
