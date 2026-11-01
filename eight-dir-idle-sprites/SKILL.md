---
name: eight-dir-idle-sprites
description: Builds consistent 8-direction 2D game sprites (S,SW,W,NW,N,NE,E,SE) from a text description, one front image, or existing direction stills, and per-direction idle loops (default 1 s, 24 fps, 24 display frames per direction) that do not drift in scale, position, props, texture or loop phase. Use whenever the user wants a character or monster turned into 8 directions, a turnaround, a rotation sheet, or an idle / breathing / hover / wing-flap / bob animation for sprites, including idle-only for stills they already have, grounded vs flying monsters, or fixing jittery, sliding, morphing or popping sprite idles.
license: MIT
compatibility: Python 3.10+ with Pillow, numpy, scipy, opencv-python-headless (scripts/requirements.txt). New art (fronts, directions) needs an image-generation/edit tool that accepts reference images; idle frames need no generator.
metadata:
  version: "1.0.0"
  supersedes: create-round-pastel-characters (rotation + style parts kept in references/legacy)
---

# Eight-direction sprites + stable idle

Two jobs, kept separate:
1. **Stills**: identity-locked front, then 8 direction stills (generative edit, reviewed one by one).
2. **Idle**: per-direction loops computed from each approved still by **part-layer deformation**
   (`scripts/idle_rig.py`), not by redrawing every frame with a generator.

Why the idle path changed: when every idle frame is regenerated, the model re-decides scale, face,
props and crayon texture each time. Prompt wording cannot remove that variance (see
`references/research-and-design.md` §4). Deforming the one approved still keeps every pixel's source
fixed, so body texture, face and props cannot drift; motion becomes an explicit, logged transform.

## Style lock (highest priority — read before any new art)

Matching the bundled sample art style and character proportions is the most important requirement of this skill.
- Default `style_ref` = `assets/styles/style-king.png` (landmarks and style words in `assets/styles/style_samples.json`;
  `style-original-king.png`, `style-party.png` show the same family). Pass the sample as a real reference image on
  every front / direction call.
- Lock to the sample: soft crayon/felt grain texture, thick dark continuous outline, flat pastel palette with light
  shading, big dark oval eyes with one shine, blush, short stubby limbs, **2-head chibi** (`proportion_class: chibi_2head`,
  head ≈ 55% of skull-top→feet height, head ≥ body).
- An input image supplies **identity only** (species, markings, character colours, props, face details). Do **not** copy
  its rendering style (painterly, storybook, meadow, realistic, anime, vector) or its proportions. A different style or
  proportion is used only when the user explicitly says so; record that in `design_spec.style_override` with the quote.
- Fail closed: if `scripts/style_check.py` fails or the side-by-side vs the sample does not read as the same family,
  the front fails G1 and nothing downstream (8-dir, idle) may start.
  `python3 scripts/style_check.py --sample assets/styles/style-king.png --candidate front.png --head-top-y Y1 --head-bottom-y Y2 --feet-y Y3`
  (head top excludes ears/hats/crowns; Y values by eye on the candidate).

## Step 0 — decide the route (write it into the work manifest)

| Input | Do |
|---|---|
| Text only | Generate a front full-body reference (legacy `style-workflow.md` + `generation-template.md`), review it, lock it. Then the stills route. |
| One front image | If it already matches the style sample (style_check pass + visual): keep it byte-exact. Otherwise extract identity only and redraw a true front in the sample style/proportions (Style lock), then stills route. |
| 8 direction stills | Skip generation. Check them against the front (legacy `artifact-review.md`). Idle route. |
| Idle only for existing dirs | Idle route only. Do not regenerate characters or directions. |

Copy `templates/work_manifest.template.json` into the job folder and fill it **before** making
frames: references, canvas, target display size, structure, locomotion, pivot/contact, landmarks,
weapon hand (anatomical, not screen side), rigid vs moving parts, what is occluded or guessed per
direction. Unverified values stay `"unknown"` or `"estimated"`.

## Step 1 — 8 direction stills (generative edit; keep what already worked)

**Gates (mandatory for new art): `references/new-art-gates.md` G0–G6.** Front must pass
`templates/front_qa.checklist.md` (identity lock + style/proportion lock + true front) before any rotation; record each direction in
`templates/stills_8dir_review.template.json`; all 8 stills frozen before any idle work.


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
- A rotation preview (stills cycled) is **not** an idle animation; name files accordingly.

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

## Step 2 — idle plan (per character, shared by all 8 directions)

Pick channels by structure; never invent anatomy:

| Structure | Channels | Pivot | Must not |
|---|---|---|---|
| Ground (legs) | `breathe` (torso stretch above the feet), optional blink | contact line (feet) | bob, slide, lift feet |
| Winged flyer | `flap` (wings about their roots) + `bob` (integer vertical) | body centre, no ground contact | plant feet, stand pose |
| Floater (ghost, slime-in-air) | `bob`, optional slow `breathe` with `contact_y` = body base | body centre | add wings, feet |
| Mech / rock / legless ground | small `bob` only if it hovers; otherwise subtle `breathe` of a soft part or none | contact/base | human chest breathing by default |

Defaults: 1.0 s, 24 fps, 24 display frames per direction, 192 total. The procedural route gives 24
unique poses per direction; if you instead generate key poses and reuse them (holds, ping-pong),
record `unique_poses_per_dir` vs `display_frames_per_dir` and the display map (e.g. `[0,0,1,1,2,...]`
or ping-pong `0..k..1`); key pose 0 must be the approved still itself, every key is generated from the
still (never from the previous key), and keys get the same QA as procedural frames. Never append a copy of frame 0 at the end
(it stalls the loop); frame n-1 → frame 0 is the seam. Duration and fps are free parameters, but
`cycles` of every channel must be an integer number per loop so the loop closes.

Amplitude: choose by **target display size**. The motion must move ≥1 display pixel or it is invisible
(tested: 4 px head lift on a 1024 px canvas ≈ 0.4 px at 96 px display; raised to 8 px). Working guide,
not a standard.

Phase: all directions use the same functions of t = frame / n and the same channel parameters (only
per-direction masks, `contact_y` and `flap_fold` differ). Keep `phase` = 0 so frame 0 is the still. In the engine keep one idle clock and
switch rows without resetting it (`references/engine-integration.md`).

## Step 2b — cutout (background removal) — never key by border flood-fill alone
Generated stills come on a flat (usually white) background. A border flood-fill leaves background **trapped inside closed shapes** (bow + string, arm/cape gaps, staff loops) as opaque white patches, plus a 1–2 px light rim. Always cut with:
```bash
python3 scripts/cutout.py raw.jpg job/DIR.png          # outer key + enclosed-pocket removal (iterated) + edge defringe
python3 scripts/cutout.py --check job/DIR.png          # exit 1 if any background-white pocket/halo is left
```
Enclosed pockets are removed only when they are flat background colour and lie close to the silhouette edge, so beard, fur, eye shine and other white art deep inside the body stay. Re-run `--check` on frame 0 and a mid-cycle frame after `idle_rig` (front_qa S7). Rigid prop masks must cover only prop pixels (wood, string, gripping hand) — never background pockets.

## Step 3 — masks (the only manual-judgement input)

Mask file = 8-bit grayscale PNG, same canvas size as its still, white (>127) = selected. Spec keys per direction:
| Part | Spec key | Effect |
|---|---|---|
| Wing | `"wing_mask": "masks/DIR_wing.png"` | rotates/folds about root (required for `flap`) |
| Weapon / crown / rigid prop | `"rigid": [{"name": "bow", "mask": "masks/DIR_bow.png"}]` | translated whole, never stretched |
| Body | no mask: body = still alpha minus wing mask | breathes/bobs |
| Ground contact | `"contact_y": <int row>` | rows at/below are locked |
All paths relative to the spec file's folder. Validate with `python3 scripts/idle_rig.py spec.json --check`.

- Wings: `python3 scripts/make_masks.py wing still.png masks/DIR_wing.png` (outline-bounded regions
  classified pale-body vs saturated-wing, thin rims → wing, small body-hugged patches → body).
- Rigid props (weapon): `make_masks.py color still.png out.png --lo H S V --hi H S V --box x0 y0 x1 y1`,
  then keep the right component (see `examples/make_prop_masks_example.py`).
- **Open every `*_overlay.png`.** Masks are proposals. Typical misses: cheek blush on the silhouette
  edge, feet behind wings, far wing behind an ear. Fix by editing the mask PNG, not by tuning output.
- Wings that sit behind the body in a fold-mode flap can detach from the body or expose an unlined body edge.
  Per direction set `"root_backstop_px": 20-40` (keeps a static band of the wing root under the folding wing) and
  `"body_seam_outline": {"px": 4-6}` (draws the style outline on the body edge that met the wing). Rest frame stays byte-exact.
- If `make_masks.py wing` keeps 0 px (pale wings, cream body), build the mask by colour saturation and include the wing's
  outer outline + alpha halo; check `fill_holes(body) - body` is ~0, otherwise the body hull "hidden torso" inpaint paints dark smears.
- Back views where wings cover the torso: set `"flap_fold": -0.10` (spread mode) for that direction;
  folding would reveal torso that does not exist in the still. Record it.

## Step 4 — generate, check, pack

```bash
python3 scripts/idle_rig.py job/spec.json --check   # spec validation only: locomotion/channel rules, integer cycles,
                                               # numeric contact_y, masks exist, same canvas, 8 canonical keys
python3 scripts/idle_rig.py job/spec.json      # frames: out_dir/DIR/DIR_000..023.png + transforms.json
python3 scripts/qa_idle.py  job/spec.json      # qa_report.json/.md (auto metrics)
python3 scripts/pack_idle.py job/spec.json     # atlas, atlas_manifest.json, GIF previews, same-phase sheet, game-size strip
```
Spec format: `templates/idle_spec.ground.example.json`, `templates/idle_spec.fly.example.json`
(worked 8-direction specs: repo `tests/ground_king/spec_8dir.json`, `tests/fly_bunny/spec_8dir.json`).
Relative paths inside a spec (`still`, masks, `out_dir`) resolve against the spec file's folder.
`scripts/` here means this skill folder's `scripts/`; run with any cwd.
Do one representative direction first, review it, then run all 8.
The example specs in `templates/` point at placeholder `input/*.png` stills, so `--check` fails on
them until you replace the paths with your own stills; that is expected.
Already have idle frames from another source (generated key poses, hand-drawn)? Use
`scripts/assemble_idle.py --plan plan.json --output-dir new_dir/` (plan format:
`templates/assemble_plan.template.json`; first state must be `neutral` = the approved still). It only
assembles timing/atlas/previews; it does not make motion or check identity, and `qa_idle.py` does not
read its output (no `transforms.json`), so the visual review and the `qa-checklist.md` items are the
only gate for that route.
Key-pose route rules: timeline step 0 must be state `neutral` = the approved still (pixel-checked);
every key is generated from the still, never from the previous key; holds/ping-pong are written as
repeated states in `timeline` (e.g. neutral,k1,k2,k2,k1,neutral) and recorded in `transforms.json`
(`display_map`, `unique_poses_per_dir`). Set `locomotion` and `anchor.contact_y` in the plan. Then run
`python3 scripts/qa_idle.py new_dir/qa_spec.json`: intended holds are reported as held steps — confirm
them, do not hide them. Fixture: `tests/keypose_fixture/run_test.sh`.

What the generator guarantees (by construction, verified by `qa_idle.py`): no global scale, no
horizontal shift; ground contact rows unchanged; rest phase byte-identical to the still; rigid props
translate without stretching; every applied transform logged per frame.

## Step 5 — review and failure handling

Use `references/qa-checklist.md`. Auto metrics (locked-region diff, contact drift, seam ratio, jump
ratio, new alpha islands, canvas-edge contact, phase sync) only flag problems; they never prove quality.
Visual review is required at: normal speed (PNG sequence or engine at true fps), slow GIF, game display
size (`game_size_strip.png`), zoom, and the 8-direction `same_phase_sheet.png`. Prefer a second,
independent reviewer (another agent/model) for the visual pass.

On a failure: fix only the cause (mask, amplitude, rigid region, per-direction fold), regenerate,
re-run QA. If it still fails, mark that direction `needs_review` with the reason. Never hide drift with
per-frame auto-scaling, alpha-bbox centring or cropping. Do not "clean" intentional details flagged by
the speck check (eye shine, sparkles, particles present in the still): compare against the still first.
After a partial fix, re-run QA and the visual pass on **every** direction you touched and on the
same-phase sheet, not only the frame you edited.

## Delivery checklist

PNG sequences per direction, `transforms.json`, `atlas_manifest.json` (dirs, order, fps, loop, pivot,
unique vs display frames), atlas, previews, `qa_report.md`, written visual review, original stills
untouched. Say "8-direction idle complete" only if all 8 × n frames exist and passed review. Report
engine playback only if you actually ran the engine; otherwise say "PNG/GIF preview only, engine not
run". Report which checks were automatic vs visual and who did the visual review. GIF timing
is centisecond-quantised: 24 fps cannot be uniform in GIF, so GIFs are previews only.

## Limits (state them to the user)

- Part deformation cannot invent unseen geometry: no head turns, no new wing poses beyond fold/spread,
  no limb repositioning. For large motions use generated key poses (legacy `idle-generation-template.md`)
  + this skill's QA; expect drift and budget repair time.
- Masks are heuristic for pale-body/saturated-wing designs; other palettes need manual masks.
- Rigid props crossing the breathing band move by their anchor's lift (≈ sub-pixel at small amplitudes).
- No optical-flow/video inbetweening by default (ghosting, wing-overlap tearing; see research doc).
- Built-in style samples (`assets/styles/`) are the round pastel set; other styles are kept from input.


## Walk / locomotion loops (key-pose route)
A walk or hop loop is not an idle breathe: legs must change pose, so `idle_rig.py` (deformation only) cannot make it.
Generate 3–6 gait keys from the approved direction still (style_ref passed again), check each against the style lock,
snap keys to one ground line (`contact_y`; an airborne key may lift by a logged px value), and assemble them with
`scripts/assemble_idle.py` (timeline = gait order, holds documented). Record `locomotion: walk` and `gait`
(e.g. quadruped hop, biped walk) in the manifest; quadrupeds keep all four paws in the cycle. In `qa_idle.py`
"locked region changed" / "foot contact moved" are expected for walk; review them visually instead.

## Eye shine
Every visible eye must keep a clear white highlight like the style sample; ask for it explicitly in the still prompt and verify on a zoom crop of the still and of a mid-cycle frame (front_qa S6). Flat eyes are a reject.

## Props: no white background (S7)
Look at every weapon/prop on black AND magenta at zoom: the gap between bow limb and string, between arm and body, inside rings must show the backdrop, not white. Any white pocket = run `cutout.py` again on the raw still; never ship it.

## Facing check (diagonals)
On a top-down 8-direction camera, SE/SW/NE/NW mean a true ~45° diagonal: the body axis (tail→nose) runs corner to corner on screen, the face sits in the matching lower/upper quadrant of the head, and the tail/rear sits in the opposite corner. A mild 20–35° head turn on an upright front-ish body reads as E/W (or S): reject it and regenerate the still before rigging. For flying or prone diagonal poses, style_check's head_frac is not meaningful (the body is horizontal), so check proportion on the front still and compare the diagonal visually against the sample.
