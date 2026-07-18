(() => {
  const endpoint = 'https://leads.fitsek.com';
  const qs = new URLSearchParams(location.search);
  const utmKeys = ['utm_source','utm_medium','utm_campaign','utm_content','utm_term'];
  const utm = Object.fromEntries(utmKeys.map(k => [k, qs.get(k) || localStorage.getItem('fitsek_' + k) || '']).filter(([,v]) => v));
  for (const [k,v] of Object.entries(utm)) localStorage.setItem('fitsek_' + k, v);

  function payload(type, extra = {}) {
    return {
      type,
      path: location.pathname,
      title: document.title,
      referrer: document.referrer,
      utm,
      ts: new Date().toISOString(),
      ...extra
    };
  }

  function track(type, extra = {}) {
    const body = JSON.stringify(payload(type, extra));
    if (navigator.sendBeacon) {
      try { navigator.sendBeacon(endpoint + '/event', new Blob([body], {type:'application/json'})); return; } catch (_) {}
    }
    fetch(endpoint + '/event', {method:'POST', headers:{'content-type':'application/json'}, body, mode:'cors', keepalive:true}).catch(() => {});
  }

  window.fitsekTrack = track;
  track('page_view');

  const scrollDepths = [25, 50, 75, 90];
  const seenDepths = new Set();
  function maybeTrackScrollDepth() {
    const doc = document.documentElement;
    const scrollable = Math.max(1, doc.scrollHeight - innerHeight);
    const pct = Math.min(100, Math.round((scrollY / scrollable) * 100));
    for (const depth of scrollDepths) {
      if (pct >= depth && !seenDepths.has(depth)) {
        seenDepths.add(depth);
        track('scroll_depth', {depth});
      }
    }
  }
  addEventListener('scroll', maybeTrackScrollDepth, {passive:true});
  addEventListener('pagehide', maybeTrackScrollDepth);

  if ('IntersectionObserver' in window) {
    const seenSections = new Set();
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id || entry.target.getAttribute('aria-label') || entry.target.className || 'section';
        if (seenSections.has(id)) return;
        seenSections.add(id);
        track('section_view', {section:id});
      });
    }, {threshold:0.45});
    document.querySelectorAll('main section[id], main section[aria-label]').forEach((section) => observer.observe(section));
  }

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-track]');
    if (!el) return;
    const href = el.getAttribute('href') || '';
    track('click', {label: el.dataset.track, href});
    if (/^https?:\/\//.test(href) && !href.includes(location.hostname)) {
      track('outbound_intent', {label: el.dataset.track, href});
    }
  });

  const form = document.getElementById('lead-form');
  if (!form) return;
  const status = document.getElementById('form-status');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    status.textContent = 'Sending…';
    const data = new FormData(form);
    const email = String(data.get('email') || '').trim();
    const company = String(data.get('company') || '').trim();
    const consent = Boolean(data.get('consent'));
    try {
      const res = await fetch(form.dataset.endpoint || endpoint + '/signup', {
        method: 'POST',
        mode: 'cors',
        headers: {'content-type':'application/json'},
        body: JSON.stringify(payload('signup', {email, company, consent, lead_magnet:'7-day-desk-worker-recomp-reset'}))
      });
      if (!res.ok) throw new Error('Signup failed');
      status.textContent = 'You are in. Open the reset now — and check your inbox when delivery is connected.';
      form.reset();
      track('signup_success', {lead_magnet:'7-day-desk-worker-recomp-reset'});
      setTimeout(() => { location.href = '/lead-magnet.html?utm_source=signup&utm_medium=site&utm_campaign=free_reset'; }, 650);
    } catch (err) {
      status.innerHTML = 'The signup endpoint is not reachable yet. Email <a href="mailto:hello@fitsek.com?subject=Send%20me%20the%207-Day%20Desk%20Worker%20Recomp%20Reset">hello@fitsek.com</a> and ask for the free reset.';
      track('signup_error', {reason:'endpoint_unreachable'});
    }
  });
})();
