# Front QA (gates G1 + G1s + G2) — fill one per front

## Style / proportion lock (G1s — fail closed; check first)
- [ ] S1 Side-by-side with `style_ref` (default `assets/styles/style-king.png`) reads as the same art family
- [ ] S2 Texture: soft crayon/felt grain like the sample (not painterly, airbrushed, storybook, vector-flat, realistic fur)
- [ ] S3 Outline: thick dark continuous outline around the silhouette like the sample
- [ ] S4 Proportion: `proportion_class` matches (default chibi_2head, head ≥ body, stubby limbs); `scripts/style_check.py` proportion = pass
- [ ] S5 Input image used for identity only; its style/proportions not copied unless user explicitly overrode (quote in `design_spec.style_override`)

## Identity + true front (G1, G2)

- [ ] Full body in frame, nothing cut at canvas edge; transparent or flat removable background
- [ ] True front: face centred on body axis, no visible yaw; both eyes equal size; both feet visible
- [ ] Proportions match the request / design (e.g. head:body); written into `design_spec.proportion`
- [ ] Face features complete and as intended (eyes, eye shine count, nose or none, mouth)
- [ ] Weapon/prop present, in the intended anatomical hand, whole (both ends, string, grip)
- [ ] Palette, outline and texture recorded (`palette_hex`, `outline`, `texture`)
- [ ] No extra limbs, fused fingers, stray specks, text or watermark
- [ ] File hashed and frozen (`original_bytes_sha256`); later steps use these bytes
Result: pass / fail (reason) / needs_review (what) — reviewer: ____

- [ ] S6 Eye shine: every eye that faces the camera has a clear white highlight (광) like style-king (glossy dark oval + small white dot). Flat/dead eyes = regenerate the still. Re-check on frame 0 and a mid-cycle frame of every idle.
- [ ] S7 No background matte: on black and magenta zooms, no white/near-white pocket or rim around weapons/props (bow-string gap, arm/cape gaps, staff loops) or silhouette. `scripts/cutout.py --check` must report 0 on the still, frame 0 and a mid-cycle frame.
- [ ] S8 Camera: plane/side view (eye-level, upright on a flat ground line) unless the user explicitly asked for top-down/overhead/탑다운. Unrequested top-down (looking down on head/shoulders, body along a screen diagonal) = reject; plane view when top-down was requested = reject.
- [ ] S7b Prop cavities: `cutout.py --check STILL --prop-mask <each weapon mask>` = matte_px 0, and zooms of upper + lower bow half / under hand on black and magenta (frames 0, 6, 12) show no white wedge.
- [ ] S7c Outline fringe: `cutout.py --check` fringe_fail false; contour zooms on black and magenta (frames 0, 6, 12) show no white ring. Note `source_alpha` (native alpha preferred; keyed = fallback).
