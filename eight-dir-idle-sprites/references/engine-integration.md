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
Each frame has 16 transparent pixels per side by default (32 px between adjacent frames). In
`atlas_manifest.json`, `cell` is the visible frame canvas, `atlas_cell` is the padded stride,
`padding_px` is the inset and `frame_rects[direction][frame]` is `[x, y, width, height]`. For the
key-pose route, use each frame's `atlas_rect` in `idle-manifest.json`. Set the engine's source
region to that rectangle and keep the original frame size and pivot; multiplying the frame width
by the index or using equally divided `hframes` without accounting for padding is incorrect.
Legacy unpadded atlases still use their own metadata.

For Godot use `AtlasTexture.region` or `draw_texture_rect_region` with the manifest rectangle;
keep the original content-space pivot. Use nearest filtering for pixel art, disable mipmaps unless
padding is designed for their footprint, and inspect filtered rendering for edge halos. Run
`cutout.py <atlas> --atlas-check --atlas-manifest <manifest>` to validate the actual rectangles
and transparent gutters. Inspect every edge-contact warning and neighboring frame at zoom: a
misplaced arrow already drawn inside a frame cannot be distinguished reliably by padding alone.
If a packer trims, preserve trim offsets or the pivot shifts per frame.

Padding increases texture dimensions and memory. The packers record `atlas_size_px` and
`atlas_over_4096`; exceeding 4096 px is a review warning, not a universal GPU limit. Check the
actual target device's maximum texture size and split clips manually if needed. The packers do not
automatically split sheets.

## Timing
24 fps = 41.67 ms per frame. GIF delays are in 1/100 s (GIF89a spec), so GIF previews alternate
40/40/50 ms. Use PNG sequence + manifest fps for true timing.
