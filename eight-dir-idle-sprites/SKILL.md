---
name: eight-dir-idle-sprites
description: Generate and review consistent eight-direction 2D character or monster still images, preserving identity, style, anatomy, camera and transparent backgrounds.
license: MIT
compatibility: Python 3.10+ and an image generation or editing tool that accepts reference images.
metadata:
  version: "1.1.0"
---

# Eight-direction character stills

Generate and review separate static directional images. Preserve the approved reference and report unverified details.

## Step 0 — Option intake (always first, before any generation or edit)
The user should not have to remember options. On every invocation, before doing anything:
1. Show the **option menu** as a question card, with **every** option on its own line: its **current value** (request merged over the defaults) **and the other choices**. The source is `scripts/options.json`. `python3 scripts/options.py [req.yaml] [--lang ko]` prints exactly this list.
2. Fill in what the request already says, and ask **only about the missing items**. Required: `task` and `subject`. Also ask for `style_ref` when the style lock is a user reference, and for `hand` when there is a weapon.
3. Close with the plan and ask **"이렇게 할까요?"** (Shall I proceed like this?). Start only after the user confirms.

| Option | Default | Other choices |
|---|---|---|
| task | (required) | new_character / new_monster / partial_edit / directional_stills |
| subject | (required) | free text |
| style_lock / style_ref | repo_default (`assets/styles/style-king.png`) | user_reference (the user's image) |
| view | 8dir | front / SE / SW / SE+SW |
| camera | side (plane) | top_down, only when explicitly asked |
| weapon / hand | none / left | free text / right, both, none |
| background | transparent (cutout) | cream |
| cutout_engine / cutout_model | rembg / birefnet-general (falls back to flood with a warning) | flood / birefnet-dis, birefnet-massive |
| face_preset / eye_palette | standard / blue,red,black | line_nose, none / free text |
| output_dir | ./out | free text |
| qa_level | standard | quick / full |

Helpers:
- `index.html` is an offline, single-file form that generates the request text. Pick the options, switch between Korean and English, and copy the text.
- `references/option-guide.md` has copy-paste example requests in Korean and English.
- After editing `scripts/options.json`, run `python3 scripts/build_index.py` to refresh the copy inlined in `index.html`. A test checks that the two match.

## Face rules (preset, not universal; any rule can be overridden per request)
Use these with `face_preset`. `standard` turns on rules 1, 2 and 5. `line_nose` turns on all five. `none` turns them all off.
1. **eye_shine_white**: the eye shine (highlight) is always pure white, whatever the eye colour.
2. **eye_palette_limit**: human eye colours come only from `eye_palette` (default blue, red, black). Keep the eye shape, the outline and the shine; recolour only the iris.
3. **female_no_nose**: female humans get no nose.
4. **line_nose_beardless**: beardless humans get a thin vertical line nose with rounded ends, the same stroke thickness and colour as the mouth line. If there is no visible mouth, draw one in that stroke.
5. **animals_keep_nose**: animals keep their own species nose.

## Style lock (highest priority — read before any new art)

Matching the bundled sample art style and character proportions is the most important requirement of this skill.
- Default `style_ref` = `assets/styles/style-king.png` (landmarks and style words in `assets/styles/style_samples.json`;
  `style-original-king.png` shows the same family). Pass the sample as a real reference image on
  every front / direction call.
- Lock to the sample: soft crayon/felt grain texture, thick dark continuous outline, flat pastel palette with light
  shading, big dark oval eyes with one shine, blush, short stubby limbs, **2-head chibi** (`proportion_class: chibi_2head`,
  head ≈ 55% of skull-top→feet height, head ≥ body).
- When the user asks to preserve the input image style, use it as the style and identity reference. The bundled sample applies by default when no different style is requested. Record the chosen style and any explicit override.
- Fail closed: if the style check or side-by-side comparison against the chosen style reference fails,
  the front fails G1 and nothing downstream (8-dir) may start.
  `python3 scripts/style_check.py --sample assets/styles/style-king.png --candidate front.png --head-top-y Y1 --head-bottom-y Y2 --feet-y Y3`
  (head top excludes ears/hats/crowns; Y values by eye on the candidate).

## Step 0 — decide the route (write it into the work manifest)

| Input | Do |
|---|---|
| Text only | Generate a front full-body reference (legacy `style-workflow.md` + `generation-template.md`), review it, lock it. Then the stills route. |
| One front image | Preserve the original as identity reference. Preserve its style when requested; otherwise apply the chosen style. If a true front is needed, obtain and review it before generating other views. |
| 8 direction stills | Skip generation. Check them against the front (legacy `artifact-review.md`). Review the existing stills. |

Copy `templates/work_manifest.template.json` into the job folder and fill it **before** making
stills: references, canvas, target display size, structure, ground contact, landmarks,
weapon hand (anatomical, not screen side), what is occluded or guessed per
direction. Unverified values stay `"unknown"` or `"estimated"`.

## Step 1 — 8 direction stills (generative edit; keep what already worked)

**Gates (mandatory for new art): `references/new-art-gates.md` G0–G5.** Front must pass
`templates/front_qa.checklist.md` (identity lock + style/proportion lock + true front) before any rotation; record each direction in
`templates/stills_8dir_review.template.json`; all 8 stills frozen before final delivery.


Follow `references/legacy/rotation-workflow.md` exactly (direction convention in
`references/legacy/directions.json`: 0° faces viewer, yaw first turns to **screen left**; output order
S,SW,W,NW,N,NE,E,SE; generate W,E,N, then diagonals anchored on their neighbours). Key rules:
- Every call passes the approved front (and the anchors) as real reference images.
- Same camera, scale and ground line in all 8; silhouette width and alpha bbox may change with turning.
- Weapon stays in the same **anatomical** hand; record screen side per direction.
- Rear details not visible in the front are minimal guesses, recorded in `occluded_or_guessed`.
- Measure with `scripts/measure_sprite_framing.py` (body height, ground line), never fix by auto-scaling:
  `python3 scripts/measure_sprite_framing.py --source front.png --input-dir dirs/` (all 8 `DIR.png`) or
  `--source front.png --candidate dirs/SE.png --direction SE` (one). Options: `--output report.json`,
  `--require-all`, `--alpha-threshold`, `--height-review-pct`, `--edge-review-frac`. Read-only JSON diagnostics.
- Deliver each direction as a separate image.

Handedness, worked out once and written into the manifest (`anatomical_sides.per_direction_screen_side`):
the character's left hand is on **screen right** in S, SW, SE; on **screen left** in N, NW, NE; in W
(facing screen left) the left hand is the near side (toward the camera) and in E (facing screen right)
the far/occluded side; mirror for a right-handed weapon.
Never "keep the weapon on the same screen side", and never mirror E↔W unless the user allows it and the
design is symmetric (record it as a mirrored derivative).

Per-direction edit prompt skeleton (any image tool that takes reference images):
`Same character as reference 1 (identity, proportions, palette, texture, line weight, lighting). Rotate
the whole body to <target_view from directions.json>. Same camera height, same scale, same ground line,
same canvas <W×H>, transparent background. <weapon> stays in the character's <anatomical> hand (screen
<side> in this view). Visible: <list>. Hidden: <list>. Back of <part> is unknown: keep it plain, continue
visible shapes, add no new ornaments. No new props, no pose change, no mirroring.`
Then open the result, compare against the front at the same zoom, measure, and record pass /
`needs_review` per direction before using it as an anchor.


## Step 2 — cutout (background removal) — never key by border flood-fill alone
Generated stills come on a flat (usually white) background. A border flood-fill leaves background **trapped inside closed shapes** (bow + string, arm/cape gaps, staff loops) as opaque white patches, plus a 1–2 px light rim. Always cut with:
```bash
python3 -m pip install -r scripts/requirements-ml.txt   # once: rembg + onnxruntime (CPU) for the default engine
python3 scripts/cutout.py raw.jpg job/DIR.png --prop-mask masks/DIR_bow.png   # default: --engine rembg --model birefnet-general
python3 scripts/cutout.py --check job/DIR.png --prop-mask masks/DIR_bow.png   # exit 1 if any background-white pocket/halo is left
```
The default engine is `rembg` with `birefnet-general`, but rembg only supplies the alpha. The same trapped-pocket, prop-cavity, defringe and despill cleanup always runs after it. An **art guard** puts back clearly non-matte pixels the net erased, half-transparent matte-coloured pixels are cleared, and the written still is **always gated**: exit 1 on trapped matte or a white fringe. An ML cut is never a PASS by itself. If rembg is not installed, `cutout.py` prints a `FALLING BACK to --engine flood` warning and uses the border flood-fill. The cleanup and the gate still run, but install the extra for production art. Use `--engine flood` to force the old path.

Other options: decontaminate is on by default (`--no-decontaminate` turns it off). `--matting` turns on classic alpha matting, which is slow, rarely needed and turns decontaminate off.

Models are compared in `references/cutout-engines.md`:
- `birefnet-dis` erased white beard art on a bow still and failed the fringe gate. Use it only per still, after checking it.
- `birefnet-massive` gave the same result as general for about twice the memory, so it was not chosen.

A BiRefNet model downloads about 1 GB on first use and needs about 4 GB RAM per 1024 px still. Run one still per process when RAM is tight.
Enclosed pockets are removed only when they are flat background colour and lie close to the silhouette edge, so beard, fur, eye shine and other white art deep inside the body stay. Re-run `--check` on every delivered directional still (front_qa S7). Rigid prop masks must cover only prop pixels (wood, string, gripping hand) — never background pockets.


## Eye shine
Every visible eye must keep a clear white highlight like the style sample; ask for it explicitly in the still prompt and verify on a zoom crop of the still  (front_qa S6). Flat eyes are a reject.

## Still generation: transparent first, white background only as fallback
- **Preferred (alpha-capable generator):** request a transparent background / alpha PNG (or WebP) directly and keep the alpha. No matte means no trapped pockets and no white contour fringe. Still run `cutout.py --check` (it must find nothing).
- **Fallback (generator outputs only a flat/solid background, often JPEG):** ask for one flat, uniform background colour, no shadow, no gradient, then immediately run `cutout.py RAW OUT.png --prop-mask <weapon masks>`. A white/solid-background image is never final art.
- Not every generator can output alpha; check the tool's documented output formats (JPEG has no alpha). Record `source_alpha: native | keyed` in the manifest.
- Why the fallback leaves residue: the generator anti-aliases the dark crayon outline into the white background, so after keying the outer 1–2 px still carry white (a light ring visible on dark/magenta), and background walled in by props is not reachable from the border.

## Small specks (S7d)
JPEG output leaves noisy near-white specks (not exact white) in hair-strand gaps, gun parts and trigger guards. `cutout.py` detects pockets with a wider tolerance (20) and removes small flat pockets walled by the dark outline near the silhouette, and small pockets touching a prop mask. Eye shine (deep inside the face) and large textured whites (beard, cuffs) are kept. Zoom hair tips and weapon holes on black.

## Outline fringe (S7c)
`cutout.py` ends with an outline despill: pixels within 3 px of the outside take the colour of the nearest pixel deeper inside (the dark outline), keeping alpha. Interior art (eye shine, beard, cuffs) is untouched. `cutout.py --check` fails when more than 1% of the 2 px edge band is light/unsaturated. Visual: zoom the contour (crown, cape, boots, bow) on black AND magenta for each direction; any white ring = reject.

## Props: no white background (S7) — mandatory, not optional cleanup
Background trapped inside closed shapes (bow limb + string, string + cuff + cape, arm loops, staff rings) is a defect, never "minor cleanup".
1. Make the prop mask first, then cut out with it: `cutout.py RAW SE.png --prop-mask masks/SE_bow.png` (repeat `--prop-mask` per weapon). Any flat matte-coloured pocket touching a prop mask is removed regardless of its distance to the outline.
2. `cutout.py --check SE.png --prop-mask ...` must report `matte_px: 0`. Without `--prop-mask` the check only sees pockets within ~24 px of the outline and can falsely pass.
3. Visual: zoom every cavity of every weapon (upper AND lower bow half, under hand/cuff, between string and cape) on black AND magenta for every directional still. Any white wedge = reject.
Known failure (fixed): a pocket below the bow grip, walled by the thick limb, string, cuff and cape, sat >24 px from the outside, so the distance rule skipped it and the check passed while the GIF showed white.

## Camera: plane view by default (top-down only on request)
Default camera is the **plane / side view**: a flat 2D sprite-sheet look, eye-level or slight high angle (at most ~15°), character standing upright on one horizontal ground line, the whole figure readable like the front sample. The 8 compass keys are **body facings on that plane**, not an overhead camera.
- Use a **top-down / overhead / bird's-eye / isometric-from-above** camera **only when the user explicitly asks** for it ("top-down", "overhead", "bird's-eye", "isometric", "탑다운", "쿼터뷰", "위에서 내려다본"). Record it as `camera: "top_down"` in the manifest; otherwise record `camera: "plane"`.
- Never infer top-down from "8 directions", "diagonal", an earlier run, or a game genre. When unsure, use plane view.
- Still prompts must state the camera: plane = "flat 2D side-view game sprite, eye-level camera, upright on a flat ground line, no top-down / no bird's-eye perspective"; top-down only if requested.

## Facing check (diagonals)
**Plane view (default):** SE/SW = three-quarter view turned toward the viewer and to screen right/left (face and chest visible, near shoulder forward, head, eyes and body all turned the same way (see Gaze below), feet on the same horizontal ground line, head NOT foreshortened, no view of the top of the head/shoulders). NE/NW = the same three-quarter turn seen from behind. The body stays upright; it does not lie along a screen diagonal. A face turned only ~10–20° that still reads as S is a reject; so is any still that looks down on the character.
**Top-down (only if the user asked):** SE/SW/NE/NW mean a true ~45° diagonal on screen: the body axis (tail→nose) runs corner to corner, the face sits in the matching lower/upper quadrant of the head, rear in the opposite corner.
Reject an unrequested top-down still, and reject a plane still when the user asked for top-down. For flying or prone poses style_check's head_frac is not meaningful; check proportion on the front still and compare visually against the sample.


## Gaze follows the direction (S9)
The eyes look where the body faces. In every direction except S (front), head, eyes and body share one heading; the character never looks at the camera.
- **Plane SE/SW:** pupils sit toward the screen-right (SE) or screen-left (SW) side of each eye, and the face turns that way (nose and mouth off-centre toward that side, far eye narrower, far ear hidden). Eyes looking straight out at the viewer while the body is SE is a reject, even if the head is turned.
- **E/W:** profile, eye looking along the heading. **N/NE/NW:** face hidden or mostly hidden, no eyes looking back at the camera.
- **S (front):** the only direction where looking at the camera is correct.
- **Top-down (only if the user asked):** the gaze follows that camera's diagonal; these plane rules are not applied.
- **Does not change:** camera gate (plane by default), the diagonal 3/4 turn, eye shine (a highlight is not gaze, keep it on the visible eyes), left/right weapon hand, style lock, cutout gates.
- **Prompt:** name it explicitly, e.g. "head, eyes and body all facing southeast; she looks toward the lower right of the screen, not at the viewer; pupils toward the right side of the eyes".
- **QA:** zoom the eyes, nose and body axis of each non-front still . Visual check is mandatory; there is no automatic gaze gate.
