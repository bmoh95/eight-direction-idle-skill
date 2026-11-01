#!/usr/bin/env python3
"""Automatic idle QA (assists visual review, never replaces it).
Usage: qa_idle.py spec.json [--locked-from-wing] -> <out_dir>/qa_report.json + qa_report.md
Thresholds are WORKING GUIDES tuned on the bundled tests, not validated industry standards."""
import json, os, sys, cv2, numpy as np
from scipy import ndimage as nd

G = {"frame0_max_diff": 2, "locked_mad": 1.5, "contact_drift_px": 1.0, "seam_ratio": 1.6, "jump_ratio": 2.5,
     "stray_px": 30, "border_px": 1}

def load(p): return cv2.imread(p, cv2.IMREAD_UNCHANGED)

def shift(img, dy):
    o = np.zeros_like(img)
    if dy > 0: o[dy:] = img[:-dy]
    elif dy < 0: o[:dy] = img[-dy:]
    else: o = img.copy()
    return o

def comps_small(a, lim):
    lab, n = nd.label(a > 16); c = np.bincount(lab.ravel())[1:]
    return int((c < lim).sum()), lab, c

def run(spec_path):
    S = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path)); P = lambda p: os.path.join(base, p)
    out = P(S["out_dir"]); T = json.load(open(f"{out}/transforms.json")); n = T["display_frames_per_dir"]
    rep = {"guides_note": "thresholds are working guides, not standards", "guides": G, "directions": {}}
    sync = {}
    for d, D in S["directions"].items():
        still = load(P(D["still"])); fr = [load(f"{out}/{d}/{d}_{i:03d}.png") for i in range(n)]
        logs = T["directions"][d]["frames"]; R = {}; issues = []
        a0 = still[..., 3] > 16
        wing = load(P(D["wing_mask"]))[..., ] > 127 if D.get("wing_mask") else np.zeros(a0.shape, bool)
        # locked region = what the method promises never changes (body of a flyer / feet band of a grounded char)
        if S["locomotion"] != "ground":
            locked = a0 & ~nd.binary_dilation(wing, iterations=4)
            undo = [-l.get("bob_dy_px_int", 0) for l in logs]
        else:
            cy = D["contact_y"]; top = int(np.argwhere(a0.any(1))[0][0]); fb = cy - 0.15 * (cy - top) * 0.6
            locked = a0.copy(); locked[: int(fb)] = False; undo = [0] * n
        mad = []
        for f, u in zip(fr, undo):
            g = shift(f, u).astype(np.int16); s = still.astype(np.int16)
            mad.append(float(np.abs(g[locked] - s[locked]).mean()))
        R["locked_region_mad_max"] = round(max(mad), 3); R["locked_region_px"] = int(locked.sum())
        if max(mad) > G["locked_mad"]: issues.append("locked region changed")
        pm = lambda x: x[..., :3].astype(int) * x[..., 3:4].astype(int) // 255
        d0 = int(max(np.abs(pm(shift(fr[0], undo[0])) - pm(still)).max(), np.abs(shift(fr[0], undo[0])[..., 3].astype(int) - still[..., 3]).max())); R["frame0_vs_still_max_diff_after_logged_shift"] = d0
        if d0 > G["frame0_max_diff"]: issues.append("frame0 differs from still")
        # contact (ground): lowest opaque row & bottom-band x centroid per frame
        if S["locomotion"] == "ground":
            low = [int(np.argwhere((f[..., 3] > 16).any(1))[-1][0]) for f in fr]
            xs = [float(np.argwhere(f[l - 8:l + 1, :, 3] > 16)[:, 1].mean()) for f, l in zip(fr, low)]
            R["contact_lowest_row_range"] = [min(low), max(low)]; R["contact_x_drift_px"] = round(max(xs) - min(xs), 2)
            if max(low) - min(low) > G["contact_drift_px"] or max(xs) - min(xs) > G["contact_drift_px"]: issues.append("foot contact moved")
        # temporal smoothness incl. loop seam (last -> first)
        steps = []
        for i in range(n):
            a, b = fr[i].astype(np.int16), fr[(i + 1) % n].astype(np.int16); m = (a[..., 3] > 16) | (b[..., 3] > 16)
            steps.append(float(np.abs(a[m] - b[m]).mean()))
        nz = [x for x in steps if x > 0]; med = float(np.median(nz)) if nz else 1e-6  # holds excluded from the baseline
        R["step_mad_median"] = round(med, 3); R["seam_step_mad"] = round(steps[-1], 3)
        R["seam_ratio"] = round(steps[-1] / med, 2); R["jump_ratio"] = round(max(steps) / med, 2)
        dup = [i for i, s_ in enumerate(steps) if s_ == 0]; R["zero_change_steps"] = dup
        if R["seam_ratio"] > G["seam_ratio"]: issues.append("loop seam pop")
        if R["jump_ratio"] > G["jump_ratio"]: issues.append("frame jump")
        if dup and len(dup) < n: issues.append(f"held/duplicate steps {dup} (ok only if intended)")
        # artifacts: new tiny alpha islands vs still, canvas clipping
        s0, _, _ = comps_small(still[..., 3], G["stray_px"]); extra = []
        for i, f in enumerate(fr):
            k, _, _ = comps_small(f[..., 3], G["stray_px"]); extra.append(k - s0)
        R["new_tiny_islands_max"] = max(extra)
        if max(extra) > 0: issues.append("new tiny alpha islands (inspect: specks or intended particles?)")
        bd = any((f[0, :, 3] > 0).any() or (f[-1, :, 3] > 0).any() or (f[:, 0, 3] > 0).any() or (f[:, -1, 3] > 0).any() for f in fr)
        R["touches_canvas_edge"] = bool(bd)
        if bd: issues.append("sprite touches canvas edge (possible clipping)")
        bb = [cv2.boundingRect((f[..., 3] > 16).astype(np.uint8)) for f in fr]
        R["alpha_bbox_info_only"] = {"w_range": [min(b[2] for b in bb), max(b[2] for b in bb)], "h_range": [min(b[3] for b in bb), max(b[3] for b in bb)]}
        R["auto_status"] = "auto_ok" if not issues else "needs_review"; R["issues"] = issues
        R["visual_status"] = "pending: check normal speed, slow, game size, zoom, 8-dir same-phase sheet"
        rep["directions"][d] = R
        sync[d] = [(l.get("t"), l.get("bob_dy_px_int", 0), l.get("flap_wave"), l.get("breathe_wave")) for l in logs]
    ref = next(iter(sync.values())); rep["phase_sync_all_dirs"] = all(v == ref for v in sync.values())
    json.dump(rep, open(f"{out}/qa_report.json", "w"), indent=1)
    with open(f"{out}/qa_report.md", "w") as m:
        m.write(f"# Auto QA ({T['display_frames_per_dir']} frames/dir @ {T['fps']} fps)\n\nPhase sync across directions: {rep['phase_sync_all_dirs']}\n\n")
        m.write("| dir | locked MAD max | frame0 diff | seam ratio | jump ratio | contact | islands | edge | auto |\n|---|---|---|---|---|---|---|---|---|\n")
        for d, R in rep["directions"].items():
            c = R.get("contact_x_drift_px", "n/a (not grounded)")
            m.write(f"| {d} | {R['locked_region_mad_max']} | {R['frame0_vs_still_max_diff_after_logged_shift']} | {R['seam_ratio']} | {R['jump_ratio']} | {c} | {R['new_tiny_islands_max']} | {R['touches_canvas_edge']} | {R['auto_status']}: {'; '.join(R['issues'])} |\n")
        m.write("\nAuto checks do not judge appeal, anatomy or identity. Visual review is still required.\n")
    print(open(f"{out}/qa_report.md").read())

if __name__ == "__main__":
    run(sys.argv[1])
