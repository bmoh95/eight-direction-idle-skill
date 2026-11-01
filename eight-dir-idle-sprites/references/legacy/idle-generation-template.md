# Idle frame editing prompt

실제 원본을 열고 확인한 디자인과 현재 방향, 작은 동작량을 대입한다. 첫 입력은 변경하지 않은 해당 방향의 neutral, 나머지는 검수한 같은 방향 포즈다. 한 번에 상태 하나를 만든다. 깜박임은 별도 국소 편집으로 처리한다.

```text
Edit IMAGE 1 into ONE {state_name} pose for a subtle looping IDLE animation.
Image 1 is the immutable neutral of THIS SAME CHARACTER IN THIS SAME DIRECTION.
Other supplied images are approved motion anchors, not redesign references.

TARGET MOTION: {species_appropriate_motion_channel} at relative amplitude
{normalized_amplitude}, where 1 is the already specified SMALL peak motion,
not a scale multiplier. The intended peak displacement is approximately
{measured_or_visually_chosen_displacement} on this source canvas. Preserve
the same yaw, camera, body magnification and screen placement. This is not a
turnaround, stepping animation, whole-image bounce or new gesture.

IDENTITY LOCK: {actually_observed_face_body_clothing_markings_and_palette}.
Keep eye count, shape, color, nose, mouth, beard, horns, head silhouette and
texture intensity stable. Preserve the observed catchlights on visible open
eyes. No new eye features or face on occluded/rear surfaces. No identity drift,
duplicated nose/limbs, random grain changes or new costume details.

RIGID ATTACHMENTS: {equipment_shapes_dimensions_anatomical_hands_and_grips}.
Do not shorten, lengthen, stretch, duplicate or switch weapons. Keep fingers
and grip connected. Preserve cape/wing/ornament attachment points. Only the
small explicitly permitted secondary motion may change these overlaps.

ANCHORS: {verified_contacts_or_body_anchor_with_confidence}.
For grounded subjects keep the verified foot contacts still. For floating or
footless subjects use the agreed body anchor without inventing feet or a
ground point. Keep unrequested horizontal drift and camera motion at zero.
Do not globally stretch the head/body to simulate breathing.

DETAIL CLEANLINESS:
Keep small details intentional and structurally coherent. Do not add orphan
specks, unexplained short strokes, clipped fragments, tiny rectangular stubs
or extra protrusions at silhouette edges, hands, grips, equipment or overlaps.
Preserve legitimate eye catchlights, taut strings, costume details, soft edge
antialiasing and explicitly requested particles/effects in their proper places.
Known excluded artifacts: {confirmed_artifacts_to_omit_or_none}.
Do not copy a known artifact from a reference as an identity feature.

ALLOWED CHANGES: {specific_local_motion_and_corresponding_occlusion}.
FORBIDDEN CHANGES: everything outside those motion channels, including the
direction, pose intent, background, colors, silhouette identity and equipment.
Preserve source transparency/background and canvas dimensions where supported.
Return ONE complete frame, no labels, sheet, other angles, floor or extra objects.
```

깜박임 편집에서는 몸 포즈가 이미 맞는 해당 상태를 첫 입력으로 사용하고, 눈꺼풀 영역만 닫힘·반닫힘·다시 뜸 상태로 수정한다. 닫힌 눈에 반사광을 유지하지 않는다. 표정·머리·코·몸·무기를 다시 그리거나 발광 눈을 눈꺼풀로 덮지 않는다.

생성 후 원본 및 이웃 상태와 실제 결과를 비교한다. 숫자와 금지 조건을 프롬프트에 넣었다는 이유만으로 보존됐다고 판단하지 않는다.
