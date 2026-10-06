import config from '../config/newsletter.json' with { type: 'json' };

const el = (tag, cls, text) => { const n=document.createElement(tag); if(cls)n.className=cls; if(text)n.textContent=text; return n; };
const paragraph = text => el('p','',text);
const link = (label,url) => { const a=el('a','r-link',label); a.href=url; return a; };
function newsletterPreview() {
  const figure=el('figure','r-newsletter-visual');
  const paper=el('div','r-newsletter-paper'); paper.setAttribute('aria-hidden','true');
  const cover=el('div','r-newsletter-paper-cover');
  const brand=el('div','r-newsletter-paper-brand'), mark=el('i'); mark.dataset.lucide='radar';
  brand.append(mark,el('span','','RedThreatAlert'));
  cover.append(brand,el('p','r-newsletter-paper-eyebrow','RAPORT DZIENNY'),el('div','r-newsletter-paper-title','Polska i wschodnia flanka NATO'));
  const content=el('div','r-newsletter-paper-content');
  const rows=[['Obraz sytuacji','Najważniejsze wydarzenia i ich kontekst.'],['Indeks i pewność danych','Wynik wraz z ograniczeniami oceny.'],['Źródła raportu','Linki do materiałów wykorzystanych w raporcie.']];
  for(const [title,text] of rows){
    const row=el('div','r-newsletter-paper-section');
    row.append(el('strong','',title),el('p','',text));content.append(row);
  }
  const end=el('div','r-newsletter-paper-footer');end.append(el('span','','redthreatalert.pl'),el('span','','Pixels4Users'));
  paper.append(cover,content,end);figure.append(paper,el('figcaption','','Przykładowy układ newslettera'));
  return figure;
}
export function initializeNewsletter(root, analytics = { enabled: false, track() {}, syncView() {} }) {
  const section=el('section','r-newsletter'); section.id='newsletter';section.tabIndex=-1;section.setAttribute('aria-labelledby','newsletter-title');
  const copy=el('div','r-newsletter-copy'), intro=el('div','r-newsletter-intro'), title=el('h2','','Obraz sytuacji. Prosto na Twój e-mail.'); title.id='newsletter-title';
  intro.append(el('p','r-newsletter-eyebrow','NEWSLETTER REDTHREATALERT'),title,paragraph('Najważniejsze ustalenia, indeks i pewność danych w wiadomości. Szczegóły wydarzeń — w pełnym raporcie na stronie.'));
  const cadence=el('p','r-newsletter-cadence'), clock=el('i');clock.dataset.lucide='clock-3';clock.setAttribute('aria-hidden','true');
  cadence.append(clock,document.createTextNode('Po publikacji raportu dziennego'));
  intro.append(cadence);
  const form=el('form','r-newsletter-form');
  const label=el('label','','Adres e-mail'); label.htmlFor='newsletter-email';
  const email=el('input'); email.type='email'; email.id='newsletter-email'; email.name='email'; email.required=true; email.maxLength=254; email.autocomplete='email'; email.placeholder='twoj@adres.pl';
  const row=el('div','r-newsletter-entry'), submit=el('button','r-button r-newsletter-submit','Zapisuję się na raport'); submit.type='submit'; submit.disabled=true;
  row.append(email,submit);
  const consentLabel=el('label','r-newsletter-consent'), consent=el('input'); consent.type='checkbox'; consent.required=true; consent.name='consent';
  consentLabel.append(consent,el('span','','Chcę otrzymywać newsletter RedThreatAlert od Pixels4Users, zawierający raporty i link do wsparcia projektu. Mogę zrezygnować w każdej wiadomości.'));
  const trap=el('input','r-newsletter-trap'); trap.name='website'; trap.type='text'; trap.tabIndex=-1; trap.autocomplete='off'; trap.setAttribute('aria-hidden','true');
  const info=el('p','r-small'); info.append(document.createTextNode('Zapis wymaga potwierdzenia adresu. '),link('Informacja o prywatności','#newsletter/prywatnosc'));
  const status=el('p','r-small'); status.setAttribute('role','status'); status.setAttribute('aria-live','polite');
  form.append(label,row,consentLabel,trap,info,status); copy.append(intro,form);section.append(newsletterPreview(),copy);
  root.querySelector('.r-bottom-line').before(section);
  const footer=root.querySelector('.r-footer-info'); footer.append(link('Prywatność newslettera','#newsletter/prywatnosc'));
  const signupLinks=[...root.querySelectorAll('.r-nav .r-coffee-link,.r-footer-actions .r-coffee-link')].map(coffee=>{
    const signup=el('a','r-support-link r-newsletter-link','Newsletter'); signup.href='#newsletter';
    coffee.before(signup); return signup;
  });

  async function api(action,body) {
    const response=await fetch(`/api/newsletter/${action}`,{method:body?'POST':'GET',credentials:'same-origin',cache:'no-store',
      headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(30_000)});
    const result=await response.json();
    if (!response.ok) { const error=new Error(result.status ?? result.error ?? 'unavailable'); error.status=response.status; throw error; }
    return result;
  }
  api('status').then(result=>{
    if(result.status==='enabled')submit.disabled=false;
    else { section.hidden=true; signupLinks.forEach(link=>{link.hidden=true;}); }
  }).catch(()=>{status.textContent='Zapisy są chwilowo niedostępne. Spróbuj ponownie później.';});
  let busy=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault(); if(busy || !form.reportValidity())return;
    const measure = analytics.enabled;
    busy=true;submit.disabled=true;status.textContent='Wysyłamy wiadomość z potwierdzeniem…';
    try {
      const result = await api('subscribe',{email:email.value,consent:consent.checked,consent_version:config.consent_version,website:trap.value});
      if (measure && result.status === 'accepted') analytics.track('newsletter_submit');
      status.textContent='Sprawdź pocztę i potwierdź adres. Jeśli wiadomość jeszcze nie dotarła, zajrzyj do folderu Spam. Po niedawnej próbie poczekaj 15 minut przed kolejnym zapisem.';
    } catch(error) { status.textContent=error.status===429?'Zbyt wiele prób. Odczekaj i spróbuj ponownie później.':error.status===400?'Sprawdź adres e-mail i zaznacz zgodę na newsletter.':'Nie udało się wysłać potwierdzenia. Spróbuj ponownie za 15 minut.'; }
    finally { busy=false;submit.disabled=false; }
  });

  const dialog=el('dialog','r-dialog r-newsletter-dialog'); dialog.setAttribute('aria-labelledby','newsletter-dialog-title');
  const close=el('button','r-newsletter-close'), closeIcon=el('i'), dialogTitle=el('h2');
  close.type='button';close.setAttribute('aria-label','Zamknij okno');close.title='Zamknij okno';
  closeIcon.dataset.lucide='x';closeIcon.setAttribute('aria-hidden','true');close.append(closeIcon);
  dialogTitle.id='newsletter-dialog-title';
  const header=el('div','r-newsletter-dialog-header'), headingGroup=el('div','r-newsletter-dialog-heading'), content=el('div','r-newsletter-dialog-content');
  headingGroup.append(el('p','r-newsletter-dialog-eyebrow','NEWSLETTER'),dialogTitle);
  header.append(headingGroup,close);dialog.append(header,content);root.append(dialog);
  let opener=null, returnHash='', confirmationBusy=false;
  close.addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{
    history.replaceState(null,'',location.pathname+location.search+returnHash);
    analytics.syncView();
    (opener?.isConnected && opener!==document.body ? opener : section).focus();
  });
  function heading(text){ content.append(el('h3','',text)); }
  function privacyContent() {
    dialogTitle.textContent='Prywatność newslettera';
    heading('Kto prowadzi newsletter');
    content.append(paragraph(`${config.operator.name}, ${config.operator.address}, NIP ${config.operator.nip}, jest administratorem danych osobowych związanych z newsletterem.`));
    const contact=paragraph('Kontakt w sprawach danych: '); contact.append(link(config.reply_to,`mailto:${config.reply_to}`));content.append(contact);
    heading('Dane i cel');
    content.append(paragraph('Podajesz dobrowolnie adres e-mail, aby otrzymywać dzienne raporty oraz informacje o wsparciu RedThreatAlert. Przechowujemy też czas zgłoszenia i potwierdzenia zapisu, wersję zgody oraz techniczny status dostarczenia i rezygnacji. Bez podania adresu nie możemy wysyłać newslettera.'));
    content.append(paragraph('Wysyłka opiera się na Twojej zgodzie (art. 6 ust. 1 lit. a RODO). Możesz ją wycofać w dowolnym momencie, korzystając z linku „Wypisz się” w wiadomości lub pisząc do nas. Wycofanie nie wpływa na zgodność wcześniejszego przetwarzania z prawem.'));
    content.append(paragraph('Ochrona formularza przed nadużyciami i zachowanie dowodu zgody służą naszemu prawnie uzasadnionemu interesowi (art. 6 ust. 1 lit. f RODO). W tym celu używamy skrótów kryptograficznych adresu e-mail i adresu IP; samego IP nie zapisujemy w bazie newslettera.'));
    heading('Dostawcy usług');
    content.append(paragraph('Korzystamy z Resend do wysyłki wiadomości, obsługi listy i rezygnacji, Supabase do obsługi formularza i dowodów zgody oraz hostingu Sites i Cloudflare do udostępniania strony. Dostawcy przetwarzają dane potrzebne do świadczenia tych usług.'));
    const transfers=paragraph('Usługi mogą wiązać się z przekazaniem danych poza EOG, w tym do USA. Informacje o zabezpieczeniach, w tym standardowych klauzulach umownych, opisują ');
    transfers.append(link('warunki przetwarzania Resend','https://resend.com/legal/dpa'),document.createTextNode(' i '),link('warunki przetwarzania Supabase','https://supabase.com/legal/dpa'),document.createTextNode('. Kopię informacji o stosowanych zabezpieczeniach możesz uzyskać, kontaktując się z nami.'));content.append(transfers);
    heading('Jak długo przechowujemy dane');
    content.append(paragraph('Adres na aktywnej liście służy wysyłce do rezygnacji. Po wypisie zachowujemy informację o rezygnacji, aby nie wznowić wysyłki bez nowej zgody. Dowód zgody zachowujemy w ograniczonym zakresie przez okres niezbędny do wykazania prawidłowości wysyłki i obrony przed roszczeniami, do ich przedawnienia.'));
    content.append(paragraph('Link do potwierdzenia wygasa po 24 godzinach. Zgłoszenia starsze niż 7 dni oraz dane ograniczania liczby prób starsze niż 2 dni usuwamy podczas automatycznego porządkowania przy obsłudze newslettera. Po potwierdzeniu usuwamy adres e-mail z tabeli zgłoszeń; pozostaje na liście w Resend. Techniczne logi dostawców podlegają ich zasadom retencji.'));
    heading('Twoje prawa');
    content.append(paragraph('Możesz żądać dostępu do danych, ich sprostowania, usunięcia, ograniczenia przetwarzania i — w przypadkach określonych w RODO — przeniesienia. Możesz wnieść sprzeciw wobec przetwarzania opartego na uzasadnionym interesie oraz złożyć skargę do Prezesa Urzędu Ochrony Danych Osobowych.'));
    content.append(paragraph('Nie podejmujemy na podstawie danych newslettera zautomatyzowanych decyzji wywołujących wobec Ciebie skutki prawne lub podobnie istotnych.'));
    content.append(el('p','r-small',`Wersja informacji: ${config.consent_version}.`));
  }
  function route() {
    const hash=location.hash;
    if (!hash.startsWith('#newsletter/'))return;
    if(!dialog.open)opener=document.activeElement;
    content.replaceChildren();
    dialog.dataset.view=hash==='#newsletter/prywatnosc'?'privacy':hash==='#newsletter/potwierdzono'?'success':'confirm';
    if(hash==='#newsletter/prywatnosc')privacyContent();
    else if(hash==='#newsletter/potwierdzono'){
      dialogTitle.textContent='Zapis potwierdzony';
      content.append(paragraph('Kolejny opublikowany raport dzienny otrzymasz na e-mail.'),el('p','r-newsletter-dialog-note','Zrezygnujesz linkiem w dowolnej wiadomości.'));
    } else {
      dialogTitle.textContent='Potwierdź zapis';
      const token=/^#newsletter\/potwierdz\/([a-f0-9]{64})$/.exec(hash)?.[1];
      if(!token)content.append(paragraph('Ten link jest nieprawidłowy. Zapisz się ponownie w formularzu.'));
      else {
        content.append(paragraph('Potwierdzam, że chcę otrzymywać newsletter RedThreatAlert od Pixels4Users.'));
        const actions=el('div','r-newsletter-dialog-actions'), confirm=el('button','r-button r-newsletter-confirm','Potwierdzam zapis'), message=el('p');
        confirm.type='button';message.setAttribute('role','status');actions.append(confirm,message);content.append(actions);
        confirm.addEventListener('click',async()=>{
          if(confirmationBusy)return;const measure = analytics.enabled;confirmationBusy=true;confirm.disabled=true;message.textContent='Potwierdzamy zapis…';
          try {
            const result = await api('confirm',{token});
            history.replaceState(null,'',location.pathname+location.search+'#newsletter/potwierdzono');route();
            if (measure && result.status === 'confirmed' && result.newly_confirmed === true) analytics.track('newsletter_confirmed');
          }
          catch(error){message.textContent=error.status===410?'Link wygasł. Zapisz się ponownie w formularzu.':error.status===409?'Trwa potwierdzanie zapisu. Spróbuj ponownie za chwilę.':'Nie udało się potwierdzić adresu. Spróbuj ponownie za chwilę.';confirm.disabled=false;}
          finally{confirmationBusy=false;}
        });
      }
    }
    analytics.syncView();
    if(!dialog.open)dialog.showModal();close.focus();
  }
  window.addEventListener('hashchange',event=>{
    if(!dialog.open && location.hash.startsWith('#newsletter/'))returnHash=new URL(event.oldURL).hash;
    route();
  }); route();
}
