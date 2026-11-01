# Turnaround generation template

Fill the values from the actual front image and design-lock record. Use the front image and validated angle anchors as actual image inputs. For an edit, specify the exact target image and the limited correction.

## Prompt

Create ONE additional view of the EXACT SAME character or monster in the first supplied image. This is a fixed-pose turntable view, not a redesign, costume variation or animation frame. The first image is the immutable original front view. Other supplied views are validated geometry references of this same character.

TARGET VIEW:
{target_view_description_from_directions_json}
The entire observed structure, including any head, torso, limbs, appendages, held items and attached clothing, rotates together around a vertical axis. Keep the camera's elevation, tilt, projection feel and viewing distance fixed. Do not merely turn a head or rotate the image plane. Keep the source joint pose and physical equipment attachments where present.

IDENTITY LOCK:
{observed_identity_design_lock}
{stable_feature_ids_with_body_surface_anatomical_side_shape_count_and_angle_visibility}
Preserve the observed species, limb count, shape language and source rendering.
Do not impose human anatomy, two eyes, two arms, a generic chibi head ratio,
pastel texture, moss, rocks or the bundled example's design on another subject.

HIDDEN SURFACES:
{minimal_rear_surface_assumptions}
Treat these as conservative design continuations, not observed facts. Maintain them consistently across later angles. Do not add new emblems, hair ornaments, equipment, spikes or a face on the back. Do not duplicate front-only markings on the back unless the design explicitly wraps around.

VISIBLE AND OCCLUDED FEATURES:
{angle_specific_visibility_notes}
Use correct occlusion and foreshortening. The far eye or far limbs may be partly or completely hidden. Do not move a held weapon to the opposite anatomical hand to make it visible. Body-side markings and moss patches rotate with their actual body surfaces instead of staying on the same side of the picture.
Preserve the source eye treatment: if the source has small catchlights, retain their restrained size, color and sheen on visible eye surfaces with a natural response to the fixed lighting and view. Treat specular highlights as reflections, not fixed skin markings or stickers. Do not flatten shiny source eyes into featureless dark ovals. Do not invent catchlights on originally matte eyes without a request, or show highlights on closed, absent or occluded eyes or the back of the head. Preserve self-emitting eyes as their specified emission rather than converting them into ordinary glossy eyes.

STYLE AND SCALE LOCK:
Match the original's exact character proportions, shape language, outline softness, palette, detail density, surface texture and rendering technique. Do not impose a generic chibi, pixel-art, realistic or plush style if the original is different. Use the original screen-space lighting direction and allow shading to respond naturally to the newly visible surfaces.
Keep the character's body magnification and verified source body anchor consistent with the references. Keep a verified ground-contact reference only for a subject that has one. Do not auto-zoom each angle to fill the frame; a weapon, horn, wing or tail can change the silhouette without changing body size. Keep all expected elements inside the canvas with sufficient margin. Follow requested canvas dimensions and alpha only when the tool supports them, and inspect the actual result afterwards. If the source is rotationally symmetric, do not invent features to make all views look artificially different.

MEASURED SOURCE FRAMING:
{source_canvas_dimensions_and_measured_normalized_top_bottom_margins}
{verified_body_scale_landmarks_and_anchor_kind_with_confidence}
These values must come from this input, not from another example character.
Keep the source's body magnification and verified body anchor. A silhouette's
lowest alpha pixel is only a framing proxy, not a measured foot contact or game
pivot. For a floating, swimming, flying or footless subject, preserve its verified
body anchor without inventing a ground-contact point. Allow legitimate projection
and occlusion changes, and never stretch the body to force equal alpha bounds.
Do not move fixed markings to keep them visible when their body surface turns away.

DETAIL CLEANLINESS:
Keep small details intentional and structurally coherent. Do not add orphan
specks, unexplained short strokes, clipped fragments, tiny rectangular stubs
or extra protrusions at silhouette edges, hands, grips, equipment or overlaps.
Preserve legitimate eye catchlights, taut strings, costume details, soft edge
antialiasing and explicitly requested particles/effects in their proper places.
Known excluded artifacts: {confirmed_artifacts_to_omit_or_none}.
Do not copy a known artifact from a reference as an identity feature.

OUTPUT:
ONE complete full-body sprite in the target direction. Preserve the requested background or source transparency. Do not include labels, other angles, a contact sheet, a turntable platform, floor shadow or extra characters. Do not mirror an earlier image or swap the character's anatomical sides. Do not copy the source front-facing eyes or emblem onto surfaces that should be hidden in this view.

## Angle-specific reminders

- True profile W/E: nose or leading face surface points toward the specified screen side. Do not use a mild three-quarter view as a profile.
- True rear N: the back of the head, torso and limbs faces the viewer; front eyes, mouth, facial hair and front-only jewels are normally hidden.
- Rear three-quarter NW/NE: show mostly back surfaces with the appropriate side. Do not accidentally generate another front three-quarter image.
- Front three-quarter SW/SE: show front surfaces and the appropriate side; distinguish the near and far sides naturally.
- Keep the reference object physically asymmetric where it is asymmetric. A left-hand bow remains in the left hand at every yaw.

## After generation

Measure each actual file with the bundled read-only framing script, then review
direction and feature IDs visually. Numeric flags trigger review, not automatic
proof of a defect. Fix confirmed frame-scale issues with the reframe-only template
in quality-and-repair.md; fix identity issues by naming the exact feature and its
physical surface. Keep separate angle, identity and framing review states. Do not
promote an unreviewed or critically wrong image into a geometry reference.
