#!/usr/bin/env python3
"""Background cutout + white-matte cleanup for generated stills.

Why: generators return stills on a flat (usually white) background. A border
flood-fill only removes the *outer* background; background trapped inside
closed shapes (bow+string, arm loops, staff rings, cape gaps) stays opaque and
shows as a white patch, and the anti-aliased rim keeps a 1-2px white halo.

Usage:
  cutout.py RAW OUT.png [--tol 12] [--min-hole 40]   # make RGBA still (default engine rembg/birefnet-general, falls back to flood)
  cutout.py RAW OUT.png --prop-mask masks/bow.png   # also clear pockets touching a prop
  cutout.py RAW OUT.png [--engine rembg|flood] [--model birefnet-general] [--no-decontaminate] [--matting]
  #   ML matte first (optional extra: pip install "rembg[cpu]"), then the SAME pocket/halo cleanup
  #   and the --check gate run on the result; falls back to the flood engine if rembg is missing.
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


def holes_and_halo(rgba, bg, tol=6, min_hole=40, hole_std=4.0, hole_dist=8.0, reach=24, prop=None, pure_dist=3.5):
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
        # S7e matte-purity rule: the generator's background keeps the exact matte value (JPEG noise only,
        # mean distance <= ~3), while drawn white (beard, hair, cape trim, eye shine) is always slightly
        # off-matte (mean distance ~4-6). So an enclosed flat region at matte purity is background wherever it
        # sits (deep bow-string / staff / arm pockets far from the outline), and off-matte white is art even
        # when it touches the outline (the old distance-only rule ate white hair/beard at tight framing).
        if n >= min_hole and d.mean() <= pure_dist and rgb[m].std(0).max() <= hole_std:
            ys, xs = np.nonzero(m)
            remove |= m; report.append(("enclosed_bg", n, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    return remove, report


# S7g prop-cavity rule: background walled off between a thin prop (bow limb + string, staff, kunai, gun)
# and the body is off-matte after JPEG/glow blending, so the purity rule misses it. Topology decides instead:
# drop every light flat region, open the remaining silhouette with a disk (removes thin props, keeps the body),
# fill holes -> body. A light region outside that body whose thin neighbours are mid-tone prop pixels (not the
# dark outline) is a cavity -> background. Regions bordering skin (beard, collar under the chin) stay.
def _disk(r):
    y,x=np.ogrid[-r:r+1,-r:r+1];return x*x+y*y<=r*r
def prop_cavities(rgba, bg, maxd=16, maxsd=10, min_n=15, r=5, dark=80, max_skin=0.12, core_d=3, core_n=60, max_med=5.5):
    rgb = rgba[..., :3].astype(float); a = rgba[..., 3] > 0
    d = np.abs(rgb - bg).max(-1); lum = rgb.mean(-1)
    comps = []
    lab, _ = nd.label((d <= maxd) & a)
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = lab[sl] == i
        if m.sum() >= min_n and rgb[sl][m].std(0).max() <= maxsd:
            full = np.zeros(a.shape, bool); full[sl] = m; comps.append(full)
    # matte-pure cores: a pocket glued to a glow/sparkle halo fails the flatness test as a whole,
    # but its matte-pure core (d <= core_d) is still a clean, large region.
    cand = np.zeros(a.shape, bool)
    for m in comps: cand |= m
    labc, _ = nd.label((d <= core_d) & a & ~cand)
    for i, sl in enumerate(nd.find_objects(labc), 1):
        m = labc[sl] == i
        if m.sum() >= core_n:
            full = np.zeros(a.shape, bool); full[sl] = m; comps.append(full); cand |= full
    # soft skill glow (cream/yellow halo) is FX, not body: it must not wall a cavity in
    R_, G_, B_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    glow = (R_ > 225) & (G_ > 210) & (B_ < G_ - 12) & (lum > 200)
    M = a & ~cand & ~glow; O = nd.binary_opening(M, structure=_disk(r)); body = nd.binary_fill_holes(O)
    thin = M & ~O; rem = np.zeros(a.shape, bool); rep = []
    for m in comps:
        if body[m].mean() >= 0.5: continue
        if np.median(d[m]) > max_med: continue  # drawn white (hair, beard, fur) is shaded off-matte
        t = thin & nd.binary_dilation(m, iterations=3)
        if t.sum() < 5: continue
        ring = nd.binary_dilation(m, iterations=2) & ~m & a
        rr = rgb[ring]
        skin = ((rr[:, 0] > 190) & (rr[:, 0] - rr[:, 2] > 30) & (rr[:, 0] - rr[:, 2] < 120) & (rr[:, 1] > 130)).mean() if len(rr) else 0
        if skin > max_skin and np.median(d[m]) > 2: continue  # matte-pure pockets may touch a hand
        ml = float(np.median(lum[t]))
        if ml >= dark:
            rem |= m; ys, xs = np.nonzero(m)
            rep.append(("prop_cavity", int(m.sum()), int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), round(ml)))
    return rem, rep


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


ENGINES = ("flood", "rembg")
DEFAULT_ENGINE = "rembg"  # ML matte + mandatory cleanup/gate; falls back to flood if rembg is missing
DEFAULT_MODEL = "birefnet-general"  # benchmark winner; birefnet-dis erased white beard art - see references/cutout-engines.md
_SESSIONS = {}


def rembg_alpha(raw, model=DEFAULT_MODEL, decont=True, matting=False):
    """ML matte via rembg. Returns (alpha uint8 HxW, rgb uint8 HxWx3) or None if rembg is unavailable.
    Only the alpha is trusted: the cleanup below still hunts trapped matte, because a segmentation net
    can keep a bow-string pocket opaque or leave it half-transparent white."""
    try:
        from rembg import new_session, remove
    except Exception as e:  # not installed / onnxruntime missing
        print(f"WARN: rembg is not installed ({e.__class__.__name__}: {e}). FALLING BACK to --engine flood "
              f"(weaker on JPEG halos and small ring/strand gaps). Install: python3 -m pip install -r scripts/requirements-ml.txt",
              file=sys.stderr)
        return None
    if model not in _SESSIONS:
        try:  # BiRefNet at 1024px peaks ~9 GB with the default CPU arena; without it it fits in ~4 GB
            import onnxruntime as ort
            so = ort.SessionOptions(); so.enable_cpu_mem_arena = False; so.enable_mem_pattern = False
            _SESSIONS[model] = new_session(model, sess_opts=so)
        except TypeError:
            _SESSIONS[model] = new_session(model)
    kw = dict(session=_SESSIONS[model], post_process_mask=False)
    if matting: kw["alpha_matting"] = True  # rembg ignores decontaminate when matting is on
    else: kw["decontaminate"] = bool(decont)
    out = np.array(remove(raw.convert("RGB"), **kw).convert("RGBA"))
    return out[..., 3], out[..., :3]


def cutout(raw, tol=6, min_hole=40, prop=None, cavities=True, engine=DEFAULT_ENGINE, model=DEFAULT_MODEL,
           decont=True, matting=False, min_alpha=8, art_guard=True, guard_d=40):
    rgb = np.array(raw.convert("RGB")).astype(float)
    bg = bg_color(rgb)
    ml = rembg_alpha(raw, model, decont, matting) if engine == "rembg" else None
    if ml is not None:
        alpha, mrgb = ml
        alpha = alpha.astype(np.int32)
        d = np.abs(rgb - bg).max(-1)
        if art_guard:
            # Art guard: a segmentation net can erase white/off-white art that touches the background
            # (birefnet-dis ate ~2k px of a white beard in the benchmark). Anything the flood fill keeps
            # inside the silhouette whose colour is clearly NOT the matte is art -> force opaque.
            near = d <= tol
            lab, _ = nd.label(near)
            border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
            inside = ~np.isin(lab, list(border))
            alpha = np.where(inside & (d > guard_d), 255, alpha)
        # soft matte residue: half-transparent pixels that still carry the matte colour (ring holes,
        # bow-string pockets) are background, not edge -> clear them instead of shipping a grey veil.
        alpha = np.where((alpha < 250) & (d <= 20), 0, alpha)
        alpha = np.where(alpha < min_alpha, 0, alpha).astype(np.uint8)
        # keep the original pixels for opaque art (the pocket rules key on matte purity of the raw);
        # use the decontaminated colour only on the soft edge.
        col = np.where((alpha < 250)[..., None], mrgb.astype(float), rgb)
        rgba = np.dstack([col, alpha]).astype(np.uint8)
        rgba[alpha == 0] = 0
    else:
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
    if cavities:
        rem, r = prop_cavities(rgba, bg)
        rgba[rem] = 0; rep += r
    rgba = defringe(rgba, bg, tol)
    rgba = decontaminate(rgba)
    return rgba, bg, rep


def atlas_check(path, cell=128, min_px=3, light=232, sat=24, rects=None):
    """Final-atlas gate (S7f): after LANCZOS downscale a matte pocket survives as a tiny light, unsaturated
    patch walled by the dark outline/prop, and a matte rim survives as light pixels with partial alpha.
    Stills-only gates never see these. Count per cell: light partial-alpha edge pixels (halo) and enclosed
    light flat specks of >= min_px whose rim is mostly dark outline (pocket)."""
    im = np.array(Image.open(path).convert("RGBA")); H, W = im.shape[:2]; tot = {"halo": 0, "pocket": 0, "cells": [], "gutter_px": 0, "edge_contact": []}
    if rects is None:
        rects = [(x, y, min(cell, W - x), min(cell, H - y)) for y in range(0, H, cell) for x in range(0, W, cell)]
    if not rects: raise ValueError("atlas manifest contains no frame rectangles")
    occupied = np.zeros((H, W), dtype=bool)
    for index, (x, y, w, h) in enumerate(rects):
        if any(type(v) is not int for v in (x, y, w, h)) or x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > W or y + h > H:
            raise ValueError(f"invalid atlas rectangle: {(x, y, w, h)}")
        if occupied[y:y+h, x:x+w].any(): raise ValueError("overlapping atlas rectangles")
        occupied[y:y+h, x:x+w] = True
        c = im[y:y + h, x:x + w]; a = c[..., 3]
        if a.max() < 8: continue
        if (a[0, :] > 0).any() or (a[-1, :] > 0).any() or (a[:, 0] > 0).any() or (a[:, -1] > 0).any():
            tot["edge_contact"].append(index)
        rgb = c[..., :3].astype(float); lum = rgb.mean(-1); s = rgb.max(-1) - rgb.min(-1)
        out = a < 8; lt = (a >= 8) & (lum >= light) & (s <= sat)
        halo = lt & (a < 200) & nd.binary_dilation(out, iterations=1)
        lab, k = nd.label(lt); pk = 0
        for i in range(1, k + 1):
            m = lab == i; n = int(m.sum())
            if n < min_px: continue
            rim = nd.binary_dilation(m, iterations=1) & ~m & ~out
            if rim.any() and (lum[rim] < 110).mean() >= 0.6 and rgb[m].min(-1).mean() >= 246: pk += n
        if halo.sum() or pk: tot["cells"].append((x // cell, y // cell, int(halo.sum()), pk))
        tot["halo"] += int(halo.sum()); tot["pocket"] += pk
    tot["gutter_px"] = int(((im[..., 3] > 0) & ~occupied).sum())
    return tot


def atlas_manifest_rects(path, manifest_path):
    """Read source rectangles from the manifest for this exact atlas."""
    import json
    from pathlib import Path
    manifest_path = Path(manifest_path).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    atlas_path = Path(path).resolve()
    if "frame_rects" in data:
        if (manifest_path.parent / data["atlas"]).resolve() != atlas_path:
            raise ValueError("manifest atlas path does not match input")
        return [rect for direction in data["rows_directions"] for rect in data["frame_rects"][direction]]
    matches = [d for d in data.get("directions", []) if (manifest_path.parent / d["atlas"]).resolve() == atlas_path]
    if len(matches) != 1: raise ValueError("manifest must identify this atlas exactly once")
    return [frame["atlas_rect"] for frame in matches[0]["frames"]]


def check(path, tol=6, min_hole=40, prop=None):
    rgba = np.array(Image.open(path).convert("RGBA")) if isinstance(path, str) else path
    if prop is None: print("WARN: --check without --prop-mask cannot see pockets far from the outline (bow-string interiors); pass every weapon/prop mask", file=sys.stderr)
    vis = rgba[..., 3] > 0
    bg = np.array([255.0, 255.0, 255.0])  # matte colour to hunt for
    rem, rep = holes_and_halo(rgba, bg, tol, min_hole, prop=prop)
    rep = [r for r in rep if r[0] in ('enclosed_bg', 'prop_pocket', 'small_pocket') or r[1] >= 20]
    return sum(r[1] for r in rep), rep


def gate(rgba, tol=6, min_hole=40, prop=None):
    """The --check gate on an in-memory RGBA. Returns (ok, report dict)."""
    n, rep = check(rgba, tol, min_hole, prop)
    fl, fb = fringe(rgba)
    bad_f = fl > 0.01 * max(fb, 1)
    return not (n or bad_f), {"matte_px": int(n), "regions": rep[:20], "outline_fringe_px": fl,
                              "outline_band_px": fb, "fringe_fail": bool(bad_f)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--atlas-check", action="store_true", help="check atlas for halo, pockets and gutter contamination; legacy fallback uses 128px cells")
    ap.add_argument("--atlas-manifest", help="manifest with frame rectangles; required for padded atlases")
    ap.add_argument("--tol", type=float, default=6); ap.add_argument("--min-hole", type=int, default=40)
    ap.add_argument("--prop-mask", action="append", default=[], help="weapon/prop mask PNG (repeatable); pockets touching it are removed/flagged")
    ap.add_argument("--engine", choices=ENGINES, default=DEFAULT_ENGINE, help="rembg (default) = ML matte, then the same cleanup; flood = border flood-fill (no extra deps, automatic fallback)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="rembg model (birefnet-dis | birefnet-general | birefnet-massive ...)")
    ap.add_argument("--no-decontaminate", action="store_true", help="rembg: keep raw edge colours (decontaminate is on by default)")
    ap.add_argument("--matting", action="store_true", help="rembg: classic alpha matting (slow; disables decontaminate)")
    ap.add_argument("--no-art-guard", action="store_true", help="rembg: trust the ML matte even where it erases clearly non-matte art")
    A = ap.parse_args()
    if A.atlas_check:
        try:
            rects = atlas_manifest_rects(A.inp, A.atlas_manifest) if A.atlas_manifest else None
            r = atlas_check(A.inp, rects=rects)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"atlas check error: {error}", file=sys.stderr); sys.exit(2)
        print({k: v for k, v in r.items() if k != "cells"}, r["cells"][:20])
        if r["edge_contact"]: print("WARN: frames touch the canvas edge; inspect for clipping or neighboring content", file=sys.stderr)
        sys.exit(1 if (r["halo"] or r["pocket"] or r["gutter_px"]) else 0)
    if A.check:
        shp = Image.open(A.inp).size[::-1]
        ok, r = gate(np.array(Image.open(A.inp).convert("RGBA")), A.tol, A.min_hole, load_props(A.prop_mask, shp))
        print(r)
        sys.exit(0 if ok else 1)
    raw = Image.open(A.inp)
    prop = load_props(A.prop_mask, raw.size[::-1])
    rgba, bg, rep = cutout(raw, A.tol, A.min_hole, prop, engine=A.engine, model=A.model,
                           decont=not A.no_decontaminate, matting=A.matting, art_guard=not A.no_art_guard)
    Image.fromarray(rgba).save(A.out)
    # always gate the written still: an ML matte is not a PASS by itself
    ok, r = gate(rgba, A.tol, A.min_hole, prop)
    print({"engine": A.engine, "bg": bg.tolist(), "removed": rep, "gate": "PASS" if ok else "FAIL", **r})
    sys.exit(0 if ok else 1)
