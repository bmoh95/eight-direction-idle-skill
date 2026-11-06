# Facing + gaze fix: cause and conflict map
## Cause (Ruby SE v1)
- The plane diagonal rule described the head and body (face off-centre, near shoulder forward, ear hidden) but said nothing about the eyes. The prompt likewise asked for the body turned 45 degrees and the face shifted, not the gaze.
- The generator's default for a cute chibi is pupils centred and looking at the viewer, so it produced an SE body with a front gaze. No check covered eye direction: style_check measures proportion and texture, S6 checks shine only, so the still’s gaze must be reviewed directly.
## Rules the gaze fix must obey (and how it avoids collision)
| existing rule | interaction |
|---|---|
| Camera gate: plane by default, top-down only on request | S9 is written for plane; under top-down it defers to the top-down diagonal rule, no override |
| Plane diagonal = 3/4 turn toward viewer | unchanged; S9 only adds that the eyes share that heading. Face is still visible (3/4), it just does not look at the camera |
| Eye shine (S6) | a highlight is not gaze; shine stays on every visible eye |
| Weapon hand (left = screen right in SE) | unchanged |
| Style lock / proportions | unchanged |
| Cutout / fringe / pocket gates (S7, S7b-d) | independent |
| Front (S) | the only direction where looking at the camera is correct |
## Gate
Visual, mandatory: S9 in front_qa and directional review. No automatic gaze gate (no reliable landmark detector for crayon chibi eyes; a heuristic would false-reject valid 3/4 stills).
