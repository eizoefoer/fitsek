# Fitsek brand image provenance

Generated 2026-07-10 with Hermes image generation for Fitsek faceless brand use. These are synthetic, photorealistic lifestyle images and must not be represented as real customers, testimonials, before/after proof, or medical evidence.

## Primary photorealistic image set

The current website/social image set is documented in:

- `docs/assets/photoreal-faceless-image-set-2026-07-10.md` — human-readable provenance, compliance notes, dimensions, and reuse guidance.
- `docs/assets/photoreal-faceless-manifest.json` — machine-readable file manifest.
- `docs/assets/prompts/photoreal-faceless/` — saved prompt records before generation.

Primary generated files:

- `site/assets/photoreal/fitsek-hero-desk-reset.png` / `.jpg` — website hero and reusable desk-worker visual.
- `site/assets/photoreal/fitsek-og-desk-system.png` / `.jpg` — website sharing/Open Graph source.
- `site/assets/social/og-fitsek-photoreal.png` / `.jpg` — social/Open Graph alias.
- `site/assets/social/photoreal-desk-walking-pad.png` / `.jpg` — walking-pad/desk movement social image.
- `site/assets/social/photoreal-gym-progression.png` / `.jpg` — strength/progression social image.
- `site/assets/social/photoreal-meal-prep-protein.png` / `.jpg` — meal-prep/protein-anchor social image.
- `site/assets/social/photoreal-product-context.png` / `.jpg` — digital product/tracker context social image.

## Derivative brand files

`automation/render_brand_assets.py` keeps the logo, favicons, app icons, Open Graph image, and optional reusable brand-photo derivatives deterministic from the approved faceless source images. The current website hero and social/Open Graph references use the primary photorealistic files above; derivative files are retained as reusable crop/format variants rather than customer proof:

- `site/assets/brand/photo-hero-workspace.jpg` / `.webp` — reusable website crop.
- `site/assets/brand/photo-social-reset.jpg` / `.webp` — reusable square social crop.
- `site/assets/brand/photo-product-system.jpg` / `.webp` — reusable product-context crop.
- `site/assets/brand/og-fitsek-site.png` — branded Open Graph fallback.
- `site/assets/brand/hero-desk-worker-recomp.webp` and `site/assets/social/hero-desk-worker-recomp.jpg` — earlier faceless hero/social crops kept for fallback reuse.
- `site/assets/social/social-meal-prep-desk-worker.jpg` / `.webp` and `site/assets/social/social-desk-strength-band.jpg` / `.webp` — earlier faceless social crops kept for fallback reuse.

## Prompt constraints used

- photorealistic lifestyle image
- faceless / no identifiable person
- no text overlays or logos
- no before/after framing
- no testimonial/customer-proof framing
- no medical or guaranteed-results claims
- dark Fitsek brand palette with mint/lime accents
