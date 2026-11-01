# Root cause: white below bow grip passed S7 (King SE plane v3)
Trace: generator returns a white-background JPG -> border flood removes outside only -> `holes_and_halo` removes an enclosed flat-white pocket only if some pixel is within `reach=24` px of the outside.
- Upper bow pocket (limb/string) touches the thin string near the outline -> removed.
- Lower pocket (2271 px, bbox 766,673-803,778) plus a 591 px pocket left of the string (733,684-755,734) are walled by the thick limb (~25 px), string, cuff and cape; nearest outside >24 px -> kept.
- Flatness could not be used alone: white hair under the crown is equally flat (std ~1.2), so the script had no topology signal for "this is background".
- `--check` used the same heuristic -> matte_px 0 (false PASS). The rigid bow mask included the pocket pixels, so idle_rig copied them every frame. qa_idle only measures motion. The checklist asked for a bow zoom but frames were checked at the upper bow.
Fix: prop-aware topology rule (`--prop-mask`): any flat matte pocket touching a weapon/prop mask is background. `--check` warns without masks. `idle_rig` gates on it using the spec rigid masks. SKILL S7 + checklists require lower-cavity zooms.
