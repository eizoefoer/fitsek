(() => {
  const link = document.querySelector('[data-checkout-link]');
  const fallback = document.querySelector('[data-checkout-fallback]');
  if (!link) return;

  const track = (type, extra = {}) => {
    if (typeof window.fitsekTrack === 'function') window.fitsekTrack(type, extra);
  };
  const showFallback = (reason) => {
    link.hidden = true;
    if (fallback) fallback.hidden = false;
    track('checkout_unavailable', { reason });
  };

  fetch('/checkout.json', { cache: 'no-store' })
    .then((response) => response.ok ? response.json() : Promise.reject(new Error(`config_${response.status}`)))
    .then((config) => {
      const url = String(config?.url || '').trim();
      if (!url.startsWith('https://buy.stripe.com/')) {
        showFallback('stripe_link_not_configured');
        return;
      }
      const destination = new URL(url);
      destination.searchParams.set('client_reference_id', 'fitsek_12_week');
      link.href = destination.toString();
      link.hidden = false;
      if (fallback) fallback.hidden = true;
      link.addEventListener('click', () => track('checkout_start', { href: link.href }));
    })
    .catch(() => showFallback('checkout_config_unavailable'));
})();
