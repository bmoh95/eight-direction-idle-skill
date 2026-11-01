# Front QA (gates G1 + G2) — fill one per front

- [ ] Full body in frame, nothing cut at canvas edge; transparent or flat removable background
- [ ] True front: face centred on body axis, no visible yaw; both eyes equal size; both feet visible
- [ ] Proportions match the request / design (e.g. head:body); written into `design_spec.proportion`
- [ ] Face features complete and as intended (eyes, eye shine count, nose or none, mouth)
- [ ] Weapon/prop present, in the intended anatomical hand, whole (both ends, string, grip)
- [ ] Palette, outline and texture recorded (`palette_hex`, `outline`, `texture`)
- [ ] No extra limbs, fused fingers, stray specks, text or watermark
- [ ] File hashed and frozen (`original_bytes_sha256`); later steps use these bytes
Result: pass / fail (reason) / needs_review (what) — reviewer: ____
