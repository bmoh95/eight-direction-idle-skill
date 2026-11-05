# Rossark idle motion handoff

This handoff is required for idle work, including one-direction and multi-direction requests. Load
the installed `rossark-motion-skill/SKILL.md`; upstream is
<https://github.com/rossark0/rossark-motion-skill>. If unavailable, install that existing skill in
the active agent's skill directory and load it. If installation or reading fails, report that the
handoff could not run; do not claim Rossark was used.

## Inputs and motion design

1. Give the motion designer the approved still for each requested direction, the structure and
   visible anatomy, contact or body anchor, wing/prop masks, requested output size, frame rate,
   duration, and the user's constraints. Reuse the same motion clock across directions.
2. Choose subtle motion suited to the character: grounded breathing with feet fixed; wing folding
   and body bob for a flyer; bob for a floater. Do not add limbs, facial layers, eye blinks, head
   turns, or hidden geometry unless the existing artwork and renderer support them.
3. Apply Rossark's continuous cycles, pivots, small amplitudes and loop-seam review. Translate the
   chosen channels into `idle_rig.py` spec fields (`breathe`, `flap`, `bob`, `amp_px`, `fold`,
   `cycles`, `phase`). `cycles` must be an integer and frame 0 must match the approved still.
   Adjust periods to the user's loop duration; do not silently override requested fps or duration.
4. `idle_rig.py` uses a cosine wave and supports per-channel cycles, but its phase-zero rest-frame
   rule means it does not implement every Rossark follow-through or articulated-joint recipe. Record
   unsupported motion instead of pretending it is present. Use the existing documented key-pose
   route if a requested movement needs new poses and the user has authorized that work.

## Render and verify

Render the representative direction using the existing mask, validation and `idle_rig.py` workflow;
then render the remaining requested directions. Run `qa_idle.py` and `pack_idle.py`, and inspect
motion at true speed, loop boundaries, masks and zoomed edges as required by the main skill. Check
contact, rigid props, identity, direction alignment and phase consistency. Record which Rossark
guidance was applied and which channels and settings actually rendered. A GIF is only a preview;
do not claim an engine run unless one was performed.

Rossark's bundled runtime templates target SwiftUI and React Native. They are not a Godot renderer
or an automated sprite segmentation / frame generation service. The local rig renders this workflow;
loading Rossark does not by itself generate or export images.
