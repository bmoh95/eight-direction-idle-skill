---
name: eight-dir-idle-sprites
description: Plan and review consistent eight-direction character sprites and idle animation, including grounded breathing, flying, and wing flaps.
---

# Eight-direction sprites and idle animation

This is the instructions-only Rakazo edition of the existing
[eight-dir-idle-sprites skill](https://github.com/bmoh95/eight-direction-idle-skill/tree/main/eight-dir-idle-sprites).
Rakazo plugin installs do not install or run this repository's Python scripts, images, or binary
assets. Do not claim that installing this plugin creates sprites, runs `idle_rig.py`, removes a
background, or provides the bundled art. Use available image and execution tools only when they
actually support the requested work; otherwise say what is missing.

1. Establish the requested subject, reference, style, directions, animation, output format and
   timing. User requirements take priority. Examine the actual reference; preserve its identity,
   colors, costume, anatomical weapon hand, camera and drawing style unless changes are requested.
2. For a turnaround, preserve the front and create only the requested missing directions. The default
   order is S, SW, W, NW, N, NE, E, SE, where SW faces screen left toward the viewer. Review each
   direction for correct facing, anatomical hand, occlusion, framing and continuity. Mark unseen
   rear details as assumptions. A rotation preview is not an idle animation.
3. For idle, use each accepted directional still as the source. Keep one shared phase and the
   user's duration and frame rate. Plan grounded breathing with feet planted; a winged flyer may
   flap and bob; a floater may bob. Avoid inventing features or independently redrawing every idle
   frame. Review props and masks and make loop boundaries continuous.
4. Consult [rossark-motion-skill](https://github.com/rossark0/rossark-motion-skill) for small,
   continuous motion, pivots and follow-through. It is a separate skill and is not automatically
   installed by this plugin. It supplies motion guidance; its SwiftUI and React Native templates
   are not a Godot sprite-frame renderer.
5. If an appropriate execution environment is available and the user authorizes using the full
   source, follow the original skill's `SKILL.md` and `references/rossark-idle-handoff.md` for its
   mask, `idle_rig.py`, `qa_idle.py`, and `pack_idle.py` workflow. A Rakazo plugin installation
   alone does not provide these files or make them executable. Do not claim they ran without
   evidence. If the environment cannot run them, provide the supported portion and state the limit.
6. Review actual playback at normal and reduced size, loop seams, alpha edges on light and dark
   backgrounds, body proportions, props, hands and contact points. Report failed or untested checks.
   Only call an eight-direction pack complete when all requested frames exist and have been reviewed.

Walking and attacks require actual pose changes. The idle deformation rig cannot invent them;
use suitable authoring tools and inspect the result rather than presenting a breathing loop as a walk.
