# New-art gates (text → front → 8 stills, front image → 8 stills)

Each gate is pass / fail / needs_review, written into the work manifest (`review.gates`) before the next step.
Do not start a step while an earlier gate is fail. Any image tool that accepts reference images works.

| Gate | When | Pass only if |
|---|---|---|
| G0 route | before any call | route chosen (Step 0), manifest copied and filled; unknowns marked `unknown` |
| G1 identity lock | after the front exists | `templates/front_qa.checklist.md` all pass; front file hashed (`original_bytes_sha256`); `design_spec` filled from the image, not from the prompt |
| G2 true front | before any rotation | camera faces the character head-on: eyes/face centred on the body axis, both shoulders/feet visible and near-symmetric, no 3/4 yaw. A 3/4 "front" fails: rotations anchored on it come out shifted by one step |
| G3 weapon hand | before W/E | anatomical hand recorded; `per_direction_screen_side` filled for all 8 from the SKILL.md table |
| G4 per-direction still | each of W,E,N then diagonals | `templates/stills_8dir_review.template.json` row filled: identity, proportion, palette, hand side, camera/scale/ground line (measure_sprite_framing.py), rear = minimal guess listed in `occluded_or_guessed`. Only a passed still may be an anchor |
| G5 set | all 8 done | same-scale contact sheet reviewed side by side; rotation preview named `*_rotation_preview.*` (never `idle`) |
| G6 stills-first | before idle | all 8 stills pass G4/G5 and are frozen (hash recorded). Idle work starts only now |

Rear rule (N, NW, NE): back details are unknown. Continue visible shapes plainly; add no ornaments, text,
patterns or props not seen in the front. List every guess.

Rotation preview vs idle: a rotation preview cycles the 8 stills to check consistency; it is not an animation
and must not be delivered as idle. Idle = loop within one direction, made from that direction's frozen still.

Text-only route extra: write the description into `design_spec` first, generate 2–4 front candidates,
pick one at G1, then treat it exactly like the front-image route. Never regenerate the front after G1;
fix a front defect by an edit pass against the same front and re-run G1/G2.
