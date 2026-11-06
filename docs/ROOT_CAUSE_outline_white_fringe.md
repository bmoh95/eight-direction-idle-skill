# Root cause: white residue on the outline (King SE v4)
Q: Is it because we generate on a background and then cut it out? **Yes, mainly.**
- The still generator used in these runs returned an opaque JPEG on white. The dark crayon outline is anti-aliased into the white, so its outer 1-2 px are light blends. cutout.py removed only near-exact background (tol 6) and its `defringe` only faded alpha on a 2 px band, so light-coloured pixels stayed. On black/magenta they read as a white ring. v4 still: 5298 of 11222 pixels in the 2 px edge band were light (47%).
- Same source causes trapped pockets between props and body (see ROOT_CAUSE_bow_white_lower.md).
- `--check` only looked for enclosed pockets, never the contour, so it passed.
Fix (skill): (1) generation prefers native transparent output when the tool supports it; white/solid-background + cutout is a documented fallback, never final art; manifest records `source_alpha`. (2) cutout.py adds outline despill (decontaminate: edge band takes the colour of the nearest deeper pixel, alpha kept; interior untouched). (3) `--check` fails when >1% of the 2 px edge band is light. (4) S7c checklist: contour zooms on black + magenta, each directional still.
Result on the same raw still: edge-band light px 5298 -> 41 (frame 0), 37 (6), 28 (12).
Can generation itself be transparent? Yes when the generator supports alpha output (some image APIs offer a transparent-background option / PNG-WebP output). Not all do: a generator that only returns JPEG cannot carry alpha, so it must use the keyed fallback with the gates above.
