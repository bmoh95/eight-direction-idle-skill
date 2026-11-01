# Idle QA checklist

Status per direction: `pass` (auto ok + visual ok) · `needs_review` (anything unresolved, with reason) · `fail`.
A failed or unmeasurable landmark is never a pass.

## A. Automatic (`scripts/qa_idle.py`): guides, not standards
| Check | Metric | Working guide | Meaning |
|---|---|---|---|
| Locked region | mean abs diff of pixels promised static (flyer body after undoing logged bob; ground feet band) | ≤ 1.5 | scale/face/texture drift |
| Rest frame | frame 0 vs still (premultiplied, after logged shift) | ≤ 2 | frame 0 must be the approved still |
| Foot contact (ground) | lowest opaque row range, bottom-band x drift | ≤ 1 px | sliding / lifting |
| Loop seam | step(n-1→0) / median step | ≤ 1.6 | pop at loop |
| Jumps | max step / median step | ≤ 2.5 | sudden frame |
| Holds | zero-change steps | only if intended | stall / duplicate end frame |
| Specks | new alpha islands < 30 px vs still | 0 (or intended particles) | stray dots |
| Clipping | opaque pixel on canvas edge | none | cut off |
| Phase sync | identical (t, bob, flap, breathe) logs across directions | true | direction switch pops |
| Alpha bbox | width/height range | info only | never used to centre or scale |

Guides were set from the two bundled tests (procedural output scores 0 on locked/frame0; old generated
idles scored 8–70 locked MAD). They are not validated on other styles.

## B. Visual (human or independent reviewer)
- [ ] Normal speed from PNG sequence/engine at true fps; slow (200 ms) GIF; game display size strip; 2–4× zoom.
- [ ] Face: eye count/shape, highlights, nose, mouth unchanged; blink only on eyelid-capable eyes.
- [ ] Props: length, grip point, hand side constant; not bent by breathing.
- [ ] Wings: count, attachment, behind/in-front layering per direction; no ghost rims or static fragments.
- [ ] Ground: feet planted; Flyer/floater: no ground contact implied.
- [ ] Motion reads at game size (≥1 display px) but is not larger than a calm idle.
- [ ] Seam: watch 3+ loops; no hitch.
- [ ] `same_phase_sheet.png`: all 8 directions at same phase have matching size, height, motion state.
- [ ] Transparent edges: no halos / dark fringes on the target background.

## C. Failure loop
1. Name the defect + frame(s) + direction. 2. Find the cause (mask, amplitude, rigid region, fold sign,
contact_y). 3. Change only that input. 4. Regenerate that direction, re-run A and B.
5. After 2 failed fixes: `needs_review`, keep the best candidate and the evidence.

## D. Procedure gates (any agent/tool)
- [ ] Manifest filled before frames; unknowns stay `unknown`/`estimated`.
- [ ] Handedness table per direction (anatomical hand → screen side); no E↔W mirror unless allowed.
- [ ] Rear/occluded assumptions listed in `occluded_or_guessed`.
- [ ] `idle_rig.py spec.json --check` passes (no SPEC ERRORS; warnings explained).
- [ ] Frame 0 = approved still; unique poses vs display frames and hold/ping-pong map recorded.
- [ ] Winged flyer flaps; legless/floater has no invented feet; mech/rock has no human chest breath.
- [ ] Engine playback claimed only if actually run; otherwise "preview only".


## Style / proportion lock (applies to fronts, every direction still, and idle frame 0)
- Run `scripts/style_check.py` against `style_ref`; `fail` = reject, `needs_review` = visual reviewer decides and writes why.
- Visual: same crayon grain, outline weight, palette softness and chibi head:body as the sample, side by side at the same height.
- A still that drifts toward the input image's original style (painterly, storybook, realistic) is a fail even if identity is right.

## S7 — background matte on props
- `scripts/cutout.py --check` = 0 on still, frame 0, mid frame. Bow-string gap and arm/cape gaps must show the backdrop on black/magenta zooms.
