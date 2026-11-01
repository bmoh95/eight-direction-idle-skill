#!/usr/bin/env python3
"""Background cutout + white-matte cleanup for generated stills.

Why: generators return stills on a flat (usually white) background. A border
flood-fill only removes the *outer* background; background trapped inside
closed shapes (bow+string, arm loops, staff rings, cape gaps) stays opaque and
shows as a white patch, and the anti-aliased rim keeps a 1-2px white halo.

Usage:
  cutout.py RAW OUT.png [--tol 12] [--min-hole 40]   # make RGBA still
  cutout.py RAW OUT.png --prop-mask masks/bow.png   # also clear pockets touching a prop
  cutout.py --check STILL.png [--prop-mask M]   # fails on trapped matte OR white outline fringe (>1% of 2px edge band light)
  #                        # report leftover matte (exit 1 if found)
"""
import argparse, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd


def bg_color(rgb):
    b = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    return np.median(b, axis=0)


def holes_and_halo(rgba, bg, tol=6, min_hole=40, hole_std=4.0, hole_dist=8.0, reach=24, prop=None):
    rgb = rgba[..., :3].astype(float)
    alpha = rgba[..., 3]
    dist = np.abs(rgb - bg).max(-1)
    # pockets are JPEG-noisy: detect them with a wider tolerance than the border key, then judge flatness
    near = (dist <= max(tol, 20)) & (alpha > 0)
    outside = alpha == 0
    lab, k = nd.label(near)
    remove = np.zeros(near.shape, bool)
    report = []
    ring = nd.binary_dilation(outside, iterations=3) if outside.any() else np.zeros_like(near)
    # enclosed background is only ever walled off by a thin prop (string, staff, arm);
    # flat white deep inside the body (beard, eye shine) is art and must stay.
    near_out = nd.distance_transform_edt(~outside) <= reach if outside.any() else np.zeros_like(near)
    # Topology rule: background trapped between a prop and the body (bow limb + string + cuff + cape)
    # can sit far (>reach px) from the outside, so the distance heuristic misses it. Any flat
    # near-matte pocket that touches a prop/weapon mask is background, whatever its distance.
    near_small = nd.distance_transform_edt(~outside) <= 16 if outside.any() else np.zeros_like(near)
    lum = rgb.mean(-1)
    prop_d = nd.binary_dilation(prop, iterations=4) if prop is not None and prop.any() else None
    for i in range(1, k + 1):
        m = lab == i
        n = int(m.sum())
        d = dist[m]
        if ring[m].any() and n and (m & ~ring).sum() < 0.1 * n:
            remove |= m; report.append(("halo", n)); continue          # thin rim on silhouette
        flat = d.mean() <= hole_dist and rgb[m].std(0).max() <= hole_std
        loose = d.mean() <= 14 and rgb[m].std(0).max() <= 6
        if n >= min_hole and prop_d is not None and (m & prop_d).any() and (flat or (loose and n < 200)):
            ys, xs = np.nonzero(m)
            remove |= m; report.append(("prop_pocket", n, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))); continue
        # small gaps between hair strands / gun parts / trigger guards: tiny flat matte specks walled by
        # the dark outline and close to the silhouette. Eye shine sits deep in the face, so it is kept.
        # notch: small light gap between hair strands open to the outside (touches the silhouette edge)
        if 4 <= n < 200 and loose and ring[m].any():
            rim = nd.binary_dilation(m, iterations=2) & ~m & ~outside
            if rim.any() and (lum[rim] < 110).mean() >= 0.5:
                ys, xs = np.nonzero(m)
                remove |= m; report.append(("small_pocket", n, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))); continue
        if 4 <= n < min_hole and loose and near_small[m].any():
            rim = nd.binary_dilation(m, iterations=2) & ~m
            if rim.any() and (lum[rim] < 110).mean() >= 0.6:
                ys, xs = np.nonzero(m)
                remove |= m; report.append(("small_pocket", n, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))); continue
        if n >= min_hole and near_out[m].any() and d.mean() <= hole_dist and rgb[m].std(0).max() <= hole_std:
            ys, xs = np.nonzero(m)
            remove |= m; report.append(("enclosed_bg", n, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    return remove, report


def defringe(rgba, bg, tol):
    """Unmix bg colour from the 2px edge band so no light rim remains."""
    a = rgba[..., 3].astype(float) / 255
    out = a == 0
    band = nd.binary_dilation(out, iterations=2) & ~out
    rgb = rgba[..., :3].astype(float)
    d = np.abs(rgb - bg).max(-1)
    # pixels close to bg in the band: fade alpha proportionally to similarity
    f = np.clip(d / (tol * 4), 0, 1)
    a2 = np.where(band, np.minimum(a, f), a)
    # unmix: C = (P - (1-f) * bg) / f
    with np.errstate(divide="ignore", invalid="ignore"):
        un = (rgb - (1 - f[..., None]) * bg) / np.maximum(f[..., None], 1e-3)
    rgb2 = np.where(band[..., None] & (f[..., None] > 0), np.clip(un, 0, 255), rgb)
    res = np.dstack([rgb2, a2 * 255]).round().astype(np.uint8)
    res[res[..., 3] < 8] = 0
    return res


def load_props(paths, shape):
    if not paths: return None
    m = np.zeros(shape, bool)
    for p in paths: m |= np.array(Image.open(p).convert("L")) > 0
    return m


def decontaminate(rgba, depth=3):
    """Outline despill: pixels within `depth` px of the outside take the colour of the nearest
    pixel at >= depth (the dark crayon outline), keeping their alpha. Removes the white fringe a
    white-background generation leaves on the contour; interior art (eye shine, beard) is untouched."""
    a = rgba[..., 3]
    out = a < 8
    if not out.any(): return rgba
    d = nd.distance_transform_edt(~out)
    core = d > depth
    _, (iy, ix) = nd.distance_transform_edt(~core, return_indices=True)
    band = (~out) & (~core)
    res = rgba.copy()
    res[band, :3] = rgba[iy[band], ix[band], :3]
    return res


def fringe(rgba, band_px=2, light=170):
    """Count light, unsaturated pixels in the outer `band_px` of the silhouette (white halo)."""
    a = rgba[..., 3]; out = a < 8
    band = nd.binary_dilation(out, iterations=band_px) & ~out
    rgb = rgba[..., :3].astype(float)
    lt = band & (rgb.mean(-1) > light) & ((rgb.max(-1) - rgb.min(-1)) < 60)
    return int(lt.sum()), int(band.sum())


def cutout(raw, tol=6, min_hole=40, prop=None):
    rgb = np.array(raw.convert("RGB")).astype(float)
    bg = bg_color(rgb)
    near = np.abs(rgb - bg).max(-1) <= tol
    lab, _ = nd.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    outside = np.isin(lab, list(border))
    rgba = np.dstack([rgb, np.where(outside, 0, 255)]).astype(np.uint8)
    rep = []
    for _ in range(4):  # removing one trapped pocket can expose the next (pocket chains)
        rem, r = holes_and_halo(rgba, bg, tol, min_hole, prop=prop)
        if not rem.any(): break
        rgba[rem] = 0; rep += r
    rgba = defringe(rgba, bg, tol)
    rgba = decontaminate(rgba)
    return rgba, bg, rep


def check(path, tol=6, min_hole=40, prop=None):
    rgba = np.array(Image.open(path).convert("RGBA"))
    if prop is None: print("WARN: --check without --prop-mask cannot see pockets far from the outline (bow-string interiors); pass every weapon/prop mask", file=sys.stderr)
    vis = rgba[..., 3] > 0
    bg = np.array([255.0, 255.0, 255.0])  # matte colour to hunt for
    rem, rep = holes_and_halo(rgba, bg, tol, min_hole, prop=prop)
    rep = [r for r in rep if r[0] in ('enclosed_bg', 'prop_pocket', 'small_pocket') or r[1] >= 20]
    return sum(r[1] for r in rep), rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tol", type=float, default=6); ap.add_argument("--min-hole", type=int, default=40)
    ap.add_argument("--prop-mask", action="append", default=[], help="weapon/prop mask PNG (repeatable); pockets touching it are removed/flagged")
    A = ap.parse_args()
    if A.check:
        shp = Image.open(A.inp).size[::-1]
        n, rep = check(A.inp, A.tol, A.min_hole, load_props(A.prop_mask, shp))
        fl, fb = fringe(np.array(Image.open(A.inp).convert("RGBA")))
        bad_f = fl > 0.01 * max(fb, 1)
        print({"matte_px": int(n), "regions": rep[:20], "outline_fringe_px": fl, "outline_band_px": fb, "fringe_fail": bool(bad_f)})
        sys.exit(1 if (n or bad_f) else 0)
    raw = Image.open(A.inp)
    rgba, bg, rep = cutout(raw, A.tol, A.min_hole, load_props(A.prop_mask, raw.size[::-1]))
    Image.fromarray(rgba).save(A.out)
    print({"bg": bg.tolist(), "removed": rep})
