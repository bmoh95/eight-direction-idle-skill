#!/usr/bin/env python3
"""Deterministic part-layer idle generator (no generative redraw, no optical flow).
Every display frame is computed from the SAME locked still, so texture, face, props and outline
cannot drift. Channels (all optional, independent, periodic over the loop):
  breathe : vertical stretch weighted by height above the contact line (feet rows stay fixed)
  flap    : each wing component scaled toward its own hinge on the body (wings stay behind the body)
  bob     : whole-sprite INTEGER vertical translation (flyers/floaters only; never for grounded)
  rigid   : masks (weapon, crown, ...) that move rigidly with the deformation at their anchor, never stretch
Phase is global time t = i/fps; every direction uses the same functions, so a direction switch at the
same t lands on the same motion phase. Usage: idle_rig.py spec.json  (see templates/idle_spec.ground.example.json / idle_spec.fly.example.json).
       idle_rig.py spec.json --check   validates the spec only (no frames written)"""
import json, math, sys, os, cv2, numpy as np
from scipy import ndimage as nd

def wave(t, ch):
    """0..1 eased cycle; 0 at phase 0. cycles must be an integer so the loop closes."""
    c = ch.get("cycles", 1); assert float(c).is_integer() and c >= 1, "cycles per loop must be an integer"
    return 0.5 - 0.5 * math.cos(2 * math.pi * (c * t + ch.get("phase", 0.0)))

def remap(img, my):
    h, w = my.shape; mx = np.tile(np.arange(w, dtype=np.float32), (h, 1))
    return cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def premul(img):
    o = img.astype(np.float32); o[..., :3] *= o[..., 3:4] / 255; return o

def unpremul(o):
    a = np.clip(o[..., 3:4], 0, 255); rgb = np.where(a > 0, o[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    return np.clip(np.concatenate([rgb, a], 2) + 0.5, 0, 255).astype(np.uint8)

def over(top, bot):  # premultiplied float
    return top + bot * (1 - top[..., 3:4] / 255)

def shift_int(img, dy):
    o = np.zeros_like(img)
    if dy >= 0: o[dy:] = img[:img.shape[0] - dy]
    else: o[:dy] = img[-dy:]
    return o

CANON = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

def validate(S, P):
    """Fail fast on spec mistakes that silently produce low-quality idles. Returns warnings."""
    err, warn = [], []
    kind = S.get("locomotion"); ch = S.get("channels", {})
    if kind not in ("ground", "fly", "float"): err.append(f"locomotion must be ground|fly|float, got {kind!r}")
    if not ch: warn.append("no channels: every frame will equal the still (static idle)")
    for k, c in ch.items():
        if not isinstance(c, dict): continue
        cy = c.get("cycles", 1)
        if not (isinstance(cy, (int, float)) and float(cy).is_integer() and cy >= 1): err.append(f"{k}.cycles must be an integer >= 1 (loop must close)")
        if c.get("phase", 0.0) != 0.0: warn.append(f"{k}.phase != 0: frame 0 will NOT equal the approved still (QA frame0 check will flag it)")
    if kind == "ground" and "bob" in ch: err.append("ground: use breathe, not bob (feet must stay planted)")
    if kind == "fly" and "flap" not in ch and any(D.get("wing_mask") for D in S["directions"].values()):
        err.append("fly with wing masks but no flap channel: a winged flyer must flap, not only breathe/bob")
    if kind == "fly" and "breathe" in ch and "flap" not in ch: err.append("fly: breathe-only is not a flyer idle; add flap (+bob)")
    if kind in ("fly", "float") and "bob" not in ch: warn.append(f"{kind}: no bob channel; airborne body will look parked")
    keys = list(S["directions"])
    bad = [k for k in keys if k not in CANON]
    if bad: err.append(f"unknown direction keys {bad}; use {CANON}")
    missing = [k for k in CANON if k not in keys]
    if missing: warn.append(f"directions missing {missing}: do not call this an 8-direction idle")
    sizes = set()
    for d, D in S["directions"].items():
        if not os.path.exists(P(D.get("still", ""))): err.append(f"{d}: still not found {D.get('still')}"); continue
        im = cv2.imread(P(D["still"]), cv2.IMREAD_UNCHANGED)
        if im is None or im.ndim != 3 or im.shape[2] != 4: err.append(f"{d}: still must be RGBA PNG"); continue
        sizes.add(im.shape[:2])
        if "breathe" in ch and not isinstance(D.get("contact_y"), (int, float)):
            err.append(f"{d}: breathe needs numeric contact_y (measured base row); 'unknown' cannot pass")
        if "flap" in ch and not D.get("wing_mask"): err.append(f"{d}: flap requested but no wing_mask")
        for m in [D.get("wing_mask")] + [r.get("mask") for r in D.get("rigid", [])]:
            if m and not os.path.exists(P(m)): err.append(f"{d}: mask not found {m}")
            elif m:
                mk = cv2.imread(P(m), cv2.IMREAD_UNCHANGED)
                g = (mk[..., 3] if mk is not None and mk.ndim == 3 and mk.shape[2] == 4 and mk[..., :3].max() == 0 else cv2.imread(P(m), 0)) if mk is not None else None
                if g is None or (g > 127).sum() < 50:
                    err.append(f"{d}: mask {m} is empty (<50 px >127 after grayscale read); a blank rigid mask silently disables the prop lock")
    if len(sizes) > 1: err.append(f"stills have different canvas sizes {sizes}: same camera/scale/canvas required; re-frame stills, never auto-scale frames")
    return err, warn

def run(spec_path, check_only=False):
    S = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    fps, dur = S["fps"], S["duration_s"]; n = round(fps * dur); assert abs(n - fps * dur) < 1e-6, "fps*duration must be integral"
    kind = S["locomotion"]; ch = S.get("channels", {})
    err, warn = validate(S, P)
    for w_ in warn: print("WARN:", w_)
    if err: sys.exit("SPEC ERRORS:\n  " + "\n  ".join(err))
    if check_only: print("spec ok"); return
    out = P(S["out_dir"]); log = {"spec": spec_path, "fps": fps, "duration_s": dur, "display_frames_per_dir": n,
          "unique_poses_per_dir": n, "method": "part-layer deformation of locked still (idle_rig.py)", "directions": {}}
    for d, D in S["directions"].items():
        src = cv2.imread(P(D["still"]), cv2.IMREAD_UNCHANGED); assert src is not None and src.shape[2] == 4, d
        h, w = src.shape[:2]; os.makedirs(f"{out}/{d}", exist_ok=True)
        wing = cv2.imread(P(D["wing_mask"]), 0) > 127 if D.get("wing_mask") else np.zeros((h, w), bool)
        if "flap" in ch: assert wing.any(), f"{d}: flap requested but no wing mask (never add wings to a wingless design)"
        body_rgba = src.copy(); body_rgba[wing, 3] = 0
        wing_rgba = src.copy(); wing_rgba[~wing, 3] = 0
        body_mask = (src[..., 3] > 16) & ~wing
        so = D.get("body_seam_outline", ch.get("flap", {}).get("body_seam_outline"))
        if so and wing.any():  # body edge that was hidden under/against the wing gets the style outline, so folded wings never expose an unlined or haloed body edge
            px = int(so.get("px", 4)); seam = body_mask & ~nd.binary_erosion(body_mask, iterations=px) & nd.binary_dilation(wing, iterations=px + 2)
            col = so.get("rgb")
            if col is None:
                dark = body_mask & (src[..., :3].max(-1) < 90); col = src[..., :3][dark].reshape(-1, 3).mean(0) if dark.any() else (40, 30, 30)
            body_rgba[seam, :3] = np.array(col, dtype=src.dtype); body_rgba[seam, 3] = 255
        comps = []
        if wing.any():
            lab, k = nd.label(wing); ring = nd.binary_dilation(body_mask, iterations=10)
            for i in range(1, k + 1):
                c = lab == i; hy, hx = np.argwhere(c & ring).mean(0) if (c & ring).any() else np.argwhere(c).mean(0)
                cy, cx = np.argwhere(c).mean(0); v = np.array([cx - hx, cy - hy]); v /= np.linalg.norm(v) + 1e-6
                comps.append((c, (float(hx), float(hy)), v))
        # torso hidden under front-facing wings (back views) is NOT in the still: estimate its silhouette, fill by inpaint, log as guessed
        hull = nd.binary_fill_holes(nd.binary_closing(np.pad(body_mask, 60), iterations=D.get("torso_close_px", 45)))[60:-60, 60:-60]
        hidden = hull & wing
        rig = [(cv2.imread(P(r["mask"]), 0) > 127, r) for r in D.get("rigid", [])]
        ys = np.arange(h, dtype=np.float32)
        # breathe weight: 0 at/below foot_top, ramps to 1 at chest line, 1 above (head rides rigidly on top)
        cy_ = D.get("contact_y"); top = int(np.argwhere(body_mask.any(1))[0][0])
        if "breathe" in ch:
            assert cy_ is not None, f"{d}: breathe needs contact_y (or measured body base); unknown is not allowed to pass silently"
            hgt = cy_ - top; b = ch["breathe"]
            y0 = cy_ - b.get("foot_frac", 0.15) * hgt; y1 = cy_ - b.get("chest_frac", 0.55) * hgt
            wy = np.clip((y0 - ys) / max(y0 - y1, 1), 0, 1); wy = wy * wy * (3 - 2 * wy)
        dl = []
        for i in range(n):
            t = i / n; rec = {"frame": i, "t": round(t, 5), "global_scale": 1.0, "global_dx": 0}
            frame_b = body_rgba
            if "breathe" in ch:
                a = ch["breathe"]["amp_px"] * wave(t, ch["breathe"])
                my = np.tile((ys + a * wy)[:, None], (1, w)).astype(np.float32)  # inverse map: sample lower => content rises
                frame_b = remap(body_rgba, my); rec["breathe_head_lift_px"] = round(a, 3); rec["breathe_wave"] = round(wave(t, ch["breathe"]), 5)
                pb = premul(frame_b)
                for m, r in rig:  # rigid props: whole-mask translation by the lift at their anchor row
                    ay = r.get("anchor_y", float(np.argwhere(m)[:, 0].mean())); dy = a * float(np.interp(ay, ys, wy))
                    M = np.float32([[1, 0, 0], [0, 1, -dy]]); layer = src.copy(); layer[~m, 3] = 0
                    pb = over(premul(cv2.warpAffine(layer, M, (w, h), flags=cv2.INTER_CUBIC)), pb)
                    rec.setdefault("rigid", []).append({"name": r.get("name", "rigid"), "dy_px": round(-dy, 3), "scale": 1.0})
                frame_b = unpremul(pb)
            pw = np.zeros((h, w, 4), np.float32)
            if "flap" in ch and comps:
                fold = D.get("flap_fold", ch["flap"]["fold"]); f = wave(t, ch["flap"]); A = fold * f
                Ap = (ch["flap"].get("perp_fold", 0.08) if fold > 0 else 0.0) * f
                rec["flap_fold"] = round(A, 4); rec["flap_wave"] = round(f, 5)
                for c, (hx, hy), v in comps:
                    u = np.array([-v[1], v[0]]); R = np.stack([v, u]); Sc = np.diag([1 - A, 1 - Ap])
                    L = R.T @ Sc @ R; tvec = np.array([hx, hy]) - L @ np.array([hx, hy])
                    layer = src.copy(); layer[~c, 3] = 0
                    pw = over(premul(cv2.warpAffine(layer, np.hstack([L, tvec[:, None]]).astype(np.float32), (w, h), flags=cv2.INTER_CUBIC)), pw)
                rb = D.get("root_backstop_px", ch["flap"].get("root_backstop_px", 0))
                if fold > 0 and rb:  # fold mode: keep a thin static band of the original wing root under the folding wing, so the wing never detaches from the body
                    band = nd.binary_erosion(wing, iterations=6) & nd.binary_dilation(body_mask, iterations=int(rb)); bs = wing_rgba.copy(); bs[~band, 3] = 0
                    pw = over(pw, premul(bs)); rec["root_backstop_px"] = int(rb)
                if fold < 0:  # spread mode (back views): backstop ONLY the hinge band so the original wing outline never shows through (ghost/double edge)
                    bs = wing_rgba.copy(); bs[~(wing & ring), 3] = 0
                    pw = over(pw, premul(bs))
            fr = unpremul(over(premul(frame_b), pw))  # body over wings; in back views body has holes where wings cover it
            if comps and hidden.any():
                rev = hidden & (fr[..., 3] < 250)
                if rev.any():
                    fr[..., :3] = cv2.inpaint(fr[..., :3], rev.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA) * rev[..., None] + fr[..., :3] * ~rev[..., None]
                    fr[rev, 3] = 255; rec["guessed_hidden_body_px"] = int(rev.sum())
            if "bob" in ch:
                dy = -int(round(ch["bob"]["amp_px"] * wave(t, ch["bob"])))
                fr = shift_int(fr, dy); rec["bob_dy_px_int"] = dy
            fr[fr[..., 3] < 3] = 0  # drop resample dust below 3/255 alpha
            if comps:  # drop detached specks (<40px islands) left by warped wing edges
                lab_, k_ = nd.label(fr[..., 3] > 0)
                if k_ > 1:
                    sz = nd.sum(np.ones_like(lab_), lab_, range(1, k_ + 1)); small = np.isin(lab_, 1 + np.flatnonzero(sz < 40))
                    fr[small] = 0
            if not any(rec.get(k) for k in ("breathe_head_lift_px", "flap_fold", "bob_dy_px_int")):
                fr = src.copy(); rec["identical_to_still"] = True   # rest phase = the approved still, byte-exact pixels
            cv2.imwrite(f"{out}/{d}/{d}_{i:03d}.png", fr); dl.append(rec)
        log["directions"][d] = {"still": D["still"], "contact_y": cy_, "pivot": D.get("pivot", "unknown"),
            "wing_hinges": [h_ for _, h_, _ in comps], "hidden_body_estimate_px": int(hidden.sum()), "frames": dl}
    json.dump(log, open(f"{out}/transforms.json", "w"), indent=1); print("wrote", out, n, "frames x", len(S["directions"]))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Deterministic part-layer idle generator (frames from one locked still per direction).")
    ap.add_argument("spec", help="idle spec JSON (see templates/idle_spec.*.example.json)")
    ap.add_argument("--check", action="store_true", help="validate the spec only; write no frames")
    a = ap.parse_args(); run(a.spec, a.check)
