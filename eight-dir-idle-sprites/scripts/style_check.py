#!/usr/bin/env python3
"""Style/proportion lock check: compare a candidate sprite against a bundled style sample.

Read-only. Prints JSON with metrics and pass / needs_review / fail per check.
Metrics (silhouette = alpha>thr, or non-near-white pixels if no alpha):
  head_frac    : head height / body height. Head bottom = narrowest row ("neck") in the 35-80% band
                 of the silhouette, or --head-bottom-y given by the reviewer (preferred when known).
  outline_frac : share of the silhouette edge band (3..8 px inside) that is dark (luma < 110).
  texture_std  : median local luma std (5x5) inside the body; crayon/grain > flat vector.
Bands are relative to the sample: head_frac within +-0.05 (sample landmarks from assets/styles/style_samples.json), outline_frac >= 0.5x sample,
texture_std >= 0.4x sample. Outside band -> fail (proportion) / needs_review (outline, texture).
Usage: style_check.py --sample assets/styles/style-king.png --candidate front.png [--head-bottom-y N]
       [--sample-head-bottom-y N] [--output report.json]
"""
import argparse, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage

def load(path, thr=24):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im).astype(float)
    rgb, al = a[..., :3], a[..., 3]
    if (al < 250).mean() > 0.02:
        m = al > thr
    else:
        m = ~((rgb.min(-1) > 238))
        m = ndimage.binary_opening(m, iterations=2)
    lab, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    m = ndimage.binary_fill_holes(m)
    return rgb, m

def metrics(path, head_bottom_y=None, head_top_y=None, feet_y=None):
    rgb, m = load(path)
    ys = np.where(m.any(1))[0]; top, bot = int(ys[0]), int(ys[-1]); h = bot - top + 1
    widths = m.sum(1).astype(float)
    if head_bottom_y is None:
        lo, hi = top + int(0.35 * h), top + int(0.80 * h)
        w = ndimage.uniform_filter1d(widths, max(3, h // 40))
        head_bottom_y = lo + int(np.argmin(w[lo:hi])); how = "auto_neck"
    else:
        how = "given"
    luma = rgb @ [0.299, 0.587, 0.114]
    inner3 = ndimage.binary_erosion(m, iterations=max(2, h // 300))
    inner8 = ndimage.binary_erosion(m, iterations=max(6, h // 110))
    band = inner3 & ~inner8
    outline = float((luma[band] < 110).mean()) if band.any() else 0.0
    mean = ndimage.uniform_filter(luma, 5); sq = ndimage.uniform_filter(luma ** 2, 5)
    std = np.sqrt(np.clip(sq - mean ** 2, 0, None))
    core = ndimage.binary_erosion(m, iterations=max(10, h // 60))
    tex = float(np.median(std[core])) if core.any() else 0.0
    ht = top if head_top_y is None else head_top_y
    bot = bot if feet_y is None else feet_y
    return {"file": path, "body_h_px": bot - ht + 1, "head_top_y": int(ht), "head_bottom_y": int(head_bottom_y), "head_how": how,
            "head_frac": round((head_bottom_y - ht) / (bot - ht + 1), 3), "outline_frac": round(outline, 3),
            "texture_std": round(tex, 2)}

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sample", required=True); p.add_argument("--candidate", required=True)
    p.add_argument("--head-bottom-y", type=int); p.add_argument("--sample-head-bottom-y", type=int)
    p.add_argument("--feet-y", type=int, help="candidate ground contact row (exclude props hanging below feet)")
    p.add_argument("--head-top-y", type=int, help="candidate skull top (exclude ears/hats); strongly recommended")
    p.add_argument("--head-tol", type=float, default=0.05); p.add_argument("--output")
    a = p.parse_args()
    import os
    lm = {}
    meta = os.path.join(os.path.dirname(os.path.abspath(a.sample)), "style_samples.json")
    if os.path.exists(meta):
        for k, v in json.load(open(meta)).items():
            if isinstance(v, dict) and v.get("file") == os.path.basename(a.sample): lm = v
    s = metrics(a.sample, a.sample_head_bottom_y or lm.get("head_bottom_y"), lm.get("head_top_y"), lm.get("feet_y"))
    c = metrics(a.candidate, a.head_bottom_y, a.head_top_y, a.feet_y)
    checks = {
        "proportion_head_frac": "pass" if abs(c["head_frac"] - s["head_frac"]) <= a.head_tol else "fail",
        "outline": "pass" if c["outline_frac"] >= 0.5 * s["outline_frac"] else "needs_review",
        "texture": "pass" if c["texture_std"] >= 0.4 * s["texture_std"] else "needs_review",
    }
    overall = "fail" if "fail" in checks.values() else ("needs_review" if "needs_review" in checks.values() else "pass")
    out = {"sample": s, "candidate": c, "checks": checks, "auto_result": overall,
           "note": "Auto metrics are a floor. A visual side-by-side vs the sample is still required (front_qa S1-S5)."}
    js = json.dumps(out, indent=2); print(js)
    if a.output: open(a.output, "w").write(js)
    sys.exit(0 if overall != "fail" else 2)

if __name__ == "__main__":
    main()
