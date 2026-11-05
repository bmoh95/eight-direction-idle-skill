#!/usr/bin/env python3
"""Pack idle frames: atlas + engine manifest + review previews.
Usage: pack_idle.py spec.json [--cell 256] [--game 96] [--padding 8]
Writes in <out_dir>/: atlas_<cell>.png, atlas_manifest.json, preview_<dir>.gif (approx timing),
preview_<dir>_slow.gif, same_phase_sheet.png (8 dirs x sampled phases), game_size_strip.png.
GIF delays are integer centiseconds, so 24 fps (41.67 ms) cannot be uniform: we alternate 40/40/50 ms
(avg 43.3) only for preview. True timing = PNG sequence + manifest fps."""
import json, os, sys, argparse
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--cell", type=int, default=256); ap.add_argument("--game", type=int, default=96); ap.add_argument("--padding", type=int, default=8, help="transparent pixels on each side of every frame")
A = ap.parse_args(); S = json.load(open(A.spec)); base = os.path.dirname(os.path.abspath(A.spec))
if A.padding < 0 or A.padding > 128: ap.error("--padding must be between 0 and 128 pixels")
out = os.path.join(base, S["out_dir"]); T = json.load(open(f"{out}/transforms.json")); n = T["display_frames_per_dir"]; fps = T.get("fps") or S.get("fps") or round(1000 / (sum(T.get("frame_ms", []) or [1000 / 24]) / max(1, len(T.get("frame_ms", []) or [1]))))
dirs = list(S["directions"]); F = {d: [Image.open(f"{out}/{d}/{d}_{i:03d}.png").convert("RGBA") for i in range(n)] for d in dirs}
W, H = F[dirs[0]][0].size; c = A.cell; ch = round(H * c / W); p = A.padding
if any(f.size != (W, H) for frames in F.values() for f in frames): ap.error("all frames must have the same canvas size")
stride_x, stride_y = c + 2 * p, ch + 2 * p
atlas = Image.new("RGBA", (stride_x * n, stride_y * len(dirs)))
rects = {}; edge_contact = []
for r, d in enumerate(dirs):
    rects[d] = []
    for i, f in enumerate(F[d]):
        resized = f.resize((c, ch), Image.Resampling.LANCZOS)
        x, y = i * stride_x + p, r * stride_y + p
        atlas.paste(resized, (x, y)); rects[d].append([x, y, c, ch])
        bounds = resized.getchannel("A").getbbox()
        if bounds and (bounds[0] == 0 or bounds[1] == 0 or bounds[2] == c or bounds[3] == ch):
            edge_contact.append({"direction": d, "frame": i, "alpha_bounds": list(bounds)})
atlas.save(f"{out}/atlas_{c}.png")
man = {"atlas": f"atlas_{c}.png", "cell": [c, ch], "source_canvas": [W, H], "scale_from_source": c / W,
       "padding_px": p, "atlas_cell": [stride_x, stride_y], "frame_rects": rects, "edge_contact_frames": edge_contact,
       "rows_directions": dirs, "frames_per_row": n, "fps": fps, "loop": True, "loop_duration_s": n / fps,
       "frame_order": "column i = frame i; no duplicated end frame (frame n-1 -> 0 is the seam)",
       "unique_poses_per_dir": T.get("unique_poses_per_dir"), "display_frames_per_dir": n, "display_frames_total": n * len(dirs),
       "pivot": {d: T["directions"][d].get("pivot") for d in dirs}, "contact_y_source_px": {d: T["directions"][d].get("contact_y") for d in dirs},
       "phase_rule": "all rows share t = (global_time*fps) % n; on direction change keep the same frame index",
       "png_sequences": {d: f"{d}/{d}_000.png .. {d}_{n-1:03d}.png" for d in dirs}, "transforms_log": "transforms.json"}
json.dump(man, open(f"{out}/atlas_manifest.json", "w"), indent=1)
bg = (64, 64, 96, 255); pat = [40, 40, 50]
def flat(f, s):
    g = Image.new("RGBA", f.size, bg); g.alpha_composite(f); return g.convert("RGB").resize(s, Image.LANCZOS)
for d in dirs:
    fr = [flat(f, (c * 2, ch * 2)) for f in F[d]]
    fr[0].save(f"{out}/preview_{d}.gif", save_all=True, append_images=fr[1:], duration=[pat[i % 3] for i in range(n)], loop=0)
    fr[0].save(f"{out}/preview_{d}_slow.gif", save_all=True, append_images=fr[1:], duration=200, loop=0)
ph = list(range(0, n, max(1, n // 6)))
sheet = Image.new("RGB", (len(dirs) * c, len(ph) * ch), bg[:3])
for x, d in enumerate(dirs):
    for y, i in enumerate(ph): sheet.paste(flat(F[d][i], (c, ch)), (x * c, y * ch))
sheet.save(f"{out}/same_phase_sheet.png")
g = A.game; gh = round(H * g / W); strip = Image.new("RGB", (g * n, gh * len(dirs)), bg[:3])
for r, d in enumerate(dirs):
    for i, f in enumerate(F[d]): strip.paste(flat(f, (g, gh)), (i * g, r * gh))
strip.save(f"{out}/game_size_strip.png"); print("packed", out, "rows", dirs, "same-phase rows at frames", ph)
