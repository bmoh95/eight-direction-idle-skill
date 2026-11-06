---
name: eight-dir-idle-sprites
description: Generate and review consistent eight-direction character and monster still images with background removal.
---

# Eight-direction character stills

This Rakazo edition provides instructions only. Image generation and background removal require suitable tools in the execution environment. Follow the full skill in `eight-dir-idle-sprites/SKILL.md` when its files are available.

1. Establish the subject, reference, requested directions, style, camera, prop hand and output format. Preserve the user's requested identity and visual style.
2. Lock an approved front image. Generate the requested views using the original front and accepted directional anchors as references. The canonical order is S, SW, W, NW, N, NE, E, SE; SW faces screen left toward the viewer.
3. Inspect each image for facing, gaze, anatomy, identity, proportions, props, occlusion, scale, framing and alpha. Document unseen rear details as assumptions. Do not mirror asymmetric characters without permission.
4. Prefer native transparency. Where needed, use the full skill's `cutout.py` with rembg and birefnet-general, then inspect edges and enclosed prop gaps. The plugin alone does not install or run that script.
5. Deliver separate directional PNGs and identify any failed or unverified checks. Report completion only after all requested images have been reviewed.
