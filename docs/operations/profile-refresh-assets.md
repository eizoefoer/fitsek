# Fitsek profile + visual-content refresh assets

Created for the reopened social-profile deliverable after a live Instagram audit found a default avatar and a text-only feed.

## Assets

- `site/assets/brand/fitsek-instagram-avatar.png` — square Fitsek `F` avatar for Instagram/Facebook profile use.
- `site/assets/social/profile-reels/desk-walking-pad.png` — faceless desk-worker walking-pad photograph.
- `site/assets/social/profile-reels/meal-prep.png` — faceless meal-prep photograph.
- `site/assets/social/profile-reels/gym-progression.png` — faceless gym-progression photograph.
- Matching `*-reel.mp4` files — eight-second 1080×1920 H.264 motion reels derived from the matching approved photographs.
- `with-audio/*-reel-vo.mp4` — matching reels with short original FitSek voice-over audio. They use no third-party track and are ready for Graph API publishing. Instagram-native audio may also be selected when creating future reels in Meta Business Suite.
- `site/assets/social/fitsek-facebook-cover.png` — branded 1640×624 Facebook cover artwork with FitSek logo, clear tagline, and a faceless desk-worker wellness scene.

## Publishing guard

These assets are synthetic, faceless brand imagery. They must not be represented as customer content, testimonials, medical evidence, transformations, or guaranteed outcomes. Run the copy-polish gate and Meta preflight before scheduling. Use the uploaded avatar through Meta/Instagram profile management; the Graph publishing flow does not substitute a profile-image update.

## Suggested first sequence

1. Update the Instagram and Facebook profile/avatar using `fitsek-instagram-avatar.png`.
2. Publish one photographic feed post for each visual pillar before scheduling the three reels.
3. Verify profile presentation, media type, media IDs, captions, and feed/reel visibility after publishing.

## 2026-07-22 live verification

- Instagram profile avatar updated via the already-authenticated `https://www.instagram.com/fitsek.wellness/` browser tab by uploading `site/assets/brand/fitsek-instagram-avatar.png` through Instagram's hidden profile-photo file input.
- Graph API verification for `@fitsek.wellness` (`17841443568404793`) now returns `profile_picture_url` on `scontent.fsyd15-2.fna.fbcdn.net` with CDN leaf `753320135_18072593642452281_4462474257250171609_n.jpg`.
- Downloaded profile image proof: `/tmp/fitsek_ig_profile_picture_after.jpg`, SHA256 `261a9af3bf6b9d719ab9ab46f2e5294f75451280622b8a690d3477ecaa9ac197`; source avatar SHA256 `55875c4b486daf555fd0f8d564bb1dccc718b8f551ccc2ea0f329e80243d18e0`; resized 150×150 mean RGB difference `0.61`, consistent with Instagram JPEG processing.
- Recent Instagram verification window includes voice-over/current reel media ID `17961703493964896`, previous reel `17886647832607574`, and previous photo `18088193189136622`; `automation/verify_posts.py --window-hours 120 --json` reported no `missing_due` and no errors.
- Meta preflight remained ready: `meta_autopilot.py check` and `permissions` returned no missing Facebook or Instagram permissions.
