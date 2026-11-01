#!/usr/bin/env python3
"""Heuristic part-mask helper. Output masks are PROPOSALS: always open the overlay and fix by hand if wrong.
wing:  appendages = opaque pixels outside the low-saturation main body (works for pale body + saturated wings).
color: pixels in an HSV box, optionally limited to a bbox (e.g. a wooden weapon)."""
import argparse, cv2, numpy as np
from scipy import ndimage as nd

def load(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED); assert im is not None and im.shape[2] == 4, f"need RGBA PNG: {p}"
    return im

def wing_mask(im, sat_split=85, min_px=2000, line_v=120, min_region=500):
    """Split the sprite into regions bounded by its dark outline, classify each region by median saturation
    (pale body vs saturated wing), then give outline/small pixels to the nearest classified region."""
    a = im[..., 3] > 16
    hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)
    lab, n = nd.label(a & (hsv[..., 2] >= line_v)); assert n, "no regions"
    cnt = np.bincount(lab.ravel()); med = np.r_[0, nd.median(hsv[..., 1], lab, range(1, n + 1))]
    big = (cnt >= min_region); big[0] = False
    cls = np.zeros(lab.shape, np.int8)                       # 0 unknown, 1 body, 2 wing
    cls[big[lab] & (med[lab] < sat_split)] = 1; cls[big[lab] & (med[lab] >= sat_split)] = 2
    sm = cv2.medianBlur(hsv[..., 1], 21)                     # region-scale saturation, ignores crayon grain
    frac = np.r_[0, nd.mean(sm < sat_split, lab, range(1, n + 1))]
    mixed = big & (frac > 0.2) & (frac < 0.8)                # no outline between body and wing: classify per pixel
    m = mixed[lab]; cls[m] = np.where(sm[m] < sat_split, 1, 2)
    idx = nd.distance_transform_edt(cls == 0, return_distances=False, return_indices=True)
    cls = cls[idx[0], idx[1]]; cls[~a] = 0
    body = nd.binary_fill_holes(cls == 1)                    # blush, inner ears, eyes enclosed by body stay body
    blab, bn = nd.label(body); dt = nd.distance_transform_edt(body)
    thick = np.r_[0, nd.maximum(dt, blab, range(1, bn + 1))]
    body &= thick[blab] >= 30                                 # thin pale strips (wing rims) belong to the wing
    w = a & ~body
    lab, n = nd.label(w)
    cc = np.bincount(lab.ravel())[1:]; lim = max(min_px, 0.01 * cc.sum())   # edge blush/mouth slivers are tiny vs wings
    keep = []
    for i, c in enumerate(cc):
        if c < lim: continue
        comp = lab == i + 1; edge = nd.binary_dilation(comp, iterations=2) & ~comp
        touch = (edge & body).sum() / max(edge.sum(), 1)
        if c < 0.05 * cc.sum() and touch > 0.45:   # small saturated patch mostly hugged by body = blush/mouth/nose, not wing
            print(f"  reassigned to body: {int(c)} px, body-contact {touch:.2f}"); continue
        keep.append(i + 1)
    print("wing components kept:", [int(cc[k - 1]) for k in keep])
    return np.isin(lab, keep), body

def color_mask(im, lo, hi, box=None):
    hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, np.array(lo), np.array(hi)) > 0
    m &= im[..., 3] > 16
    if box:
        b = np.zeros_like(m); x0, y0, x1, y1 = box; b[y0:y1, x0:x1] = 1; m &= b
    return m

def overlay(im, m, path):
    o = im[..., :3].copy(); o[m] = (0.4 * o[m] + 0.6 * np.array([255, 0, 255])).astype(np.uint8)
    cv2.imwrite(path, o)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("kind", choices=["wing", "color"]); ap.add_argument("img"); ap.add_argument("out")
    ap.add_argument("--sat-split", type=int, default=85); ap.add_argument("--lo", type=int, nargs=3); ap.add_argument("--hi", type=int, nargs=3)
    ap.add_argument("--box", type=int, nargs=4); ap.add_argument("--min-px", type=int, default=2000)
    a = ap.parse_args(); im = load(a.img)
    m = wing_mask(im, a.sat_split, a.min_px)[0] if a.kind == "wing" else color_mask(im, a.lo, a.hi, a.box)
    cv2.imwrite(a.out, (m * 255).astype(np.uint8)); overlay(im, m, a.out.replace(".png", "_overlay.png"))
    print(a.out, int(m.sum()), "px")
