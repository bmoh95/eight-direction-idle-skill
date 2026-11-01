# Engine use and phase-preserving direction switches

Files: `DIR/DIR_000..NNN.png` (exact frames), `atlas_<cell>.png` (rows = directions in
`atlas_manifest.json.rows_directions`, columns = frames), `atlas_manifest.json` (fps, loop, pivot, contact).

## One idle clock for all directions
Keep a single idle time `t` per character. Frame = floor(t * fps) mod n. When the facing changes,
switch the row/animation but keep the same frame index and progress. Every direction was generated
with the same phase functions, so the same index is the same motion state.

- **Godot 4**: `AnimatedSprite2D` — store `var f = sprite.frame; var p = sprite.frame_progress`,
  then `sprite.play("idle_" + dir)` and `sprite.set_frame_and_progress(f, p)`. Setting `frame` alone
  resets progress (Godot docs, AnimatedSprite2D).
- **Unity**: `animator.Play(stateName, layer, normalizedTime)` with the current
  `GetCurrentAnimatorStateInfo(0).normalizedTime % 1` (Unity docs, Animator.Play).
- Custom engines: index = (int)(globalIdleTime * fps) % n.

## Pivot
Ground: pivot at the contact line (`contact_y_source_px`, scaled by `scale_from_source`), x = feet centre.
Flyer: body centre; the bob is baked into frames (integer px), so do not add an engine bob on top.
Use the same pivot for all 8 rows; do not re-derive pivots from alpha bounds per frame.

## Atlas notes
Keep transparent padding; if your packer trims, preserve original offsets (trim + offset) or the
pivot shifts per frame. Use alpha bleeding / extrude to avoid dark edge halos with filtering
(TexturePacker docs, "Reduce border artifacts", "Extrude").

## Timing
24 fps = 41.67 ms per frame. GIF delays are in 1/100 s (GIF89a spec), so GIF previews alternate
40/40/50 ms. Use PNG sequence + manifest fps for true timing.
