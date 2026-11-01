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

## Step 0 — decide the route (write it into the work manifest)

| Input | Do |
|---|---|
| Text only | Generate a front full-body reference (legacy `style-workflow.md` + `generation-template.md`), review it, lock it. Then the stills route. |
| One front image | Keep it byte-exact as identity reference. Stills route. Never restyle it. |
| 8 direction stills | Skip generation. Check them against the front (legacy `artifact-review.md`). Idle route. |
| Idle only for existing dirs | Idle route only. Do not regenerate characters or directions. |

Copy `templates/work_manifest.template.json` into the job folder and fill it **before** making
frames: references, canvas, target display size, structure, locomotion, pivot/contact, landmarks,
weapon hand (anatomical, not screen side), rigid vs moving parts, what is occluded or guessed per
direction. Unverified values stay `"unknown"` or `"estimated"`.

## Step 1 — 8 direction stills (generative edit; keep what already worked)

Follow `references/legacy/rotation-workflow.md` exactly (direction convention in
`references/legacy/directions.json`: 0° faces viewer, yaw first turns to **screen left**; output order
S,SW,W,NW,N,NE,E,SE; generate W,E,N, then diagonals anchored on their neighbours). Key rules:
- Every call passes the approved front (and the anchors) as real reference images.
- Same camera, scale and ground line in all 8; silhouette width and alpha bbox may change with turning.
- Weapon stays in the same **anatomical** hand; record screen side per direction.
- Rear details not visible in the front are minimal guesses, recorded in `occluded_or_guessed`.
- Measure with `scripts/measure_sprite_framing.py` (body height, ground line), never fix by auto-scaling.
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

## Step 3 — masks (the only manual-judgement input)

- Wings: `python3 scripts/make_masks.py wing still.png masks/DIR_wing.png` (outline-bounded regions
  classified pale-body vs saturated-wing, thin rims → wing, small body-hugged patches → body).
- Rigid props (weapon): `make_masks.py color still.png out.png --lo H S V --hi H S V --box x0 y0 x1 y1`,
  then keep the right component (see `examples/make_prop_masks_example.py`).
- **Open every `*_overlay.png`.** Masks are proposals. Typical misses: cheek blush on the silhouette
  edge, feet behind wings, far wing behind an ear. Fix by editing the mask PNG, not by tuning output.
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
Spec format: `templates/idle_spec.ground.example.json`, `templates/idle_spec.fly.example.json`.
Do one representative direction first, review it, then run all 8.

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
