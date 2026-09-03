# Stripe Payment Link activation

Fitsek uses a public Stripe Payment Link for its first digital-product checkout.

## Create the link

In Stripe Dashboard:

1. Create the **Fitsek 12-Week Recomp System** product with final price, currency, inclusions, and digital-product refund terms.
2. Create a Payment Link for that product.
3. Set the post-purchase redirect to `https://fitsek.com/product.html?checkout=success`.
4. Send the public `https://buy.stripe.com/...` link to the operator. Do not send a Stripe secret key.

## Activate

Set `site/checkout.json` to the public URL in a focused release. The browser only accepts `https://buy.stripe.com/` links; anything else keeps the free-reset fallback visible.

The product CTA records `checkout_start`. A completed-sale event must only be recorded after a Stripe webhook or verified Stripe dashboard sale read; this static site does not infer payment completion from a redirect.
