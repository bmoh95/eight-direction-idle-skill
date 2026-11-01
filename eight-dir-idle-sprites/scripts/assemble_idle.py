#!/usr/bin/env python3
"""Assemble existing idle PNG states; never generate motion or validate identity."""

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_image(path, png=False):
    with Image.open(path) as raw:
        if getattr(raw, "n_frames", 1) != 1:
            raise ValueError(f"Use a declared still frame: {path}")
        if png and (raw.format != "PNG" or raw.getexif().get(274, 1) != 1):
            raise ValueError(f"State must be an explicitly normalized PNG: {path}")
        return ImageOps.exif_transpose(raw).convert("RGBA")


def premultiplied(image):
    r, g, b, a = image.split()
    return Image.merge("RGBA", (ImageChops.multiply(r, a),
                                ImageChops.multiply(g, a),
                                ImageChops.multiply(b, a), a))


def metrics(path, image):
    alpha = image.getchannel("A")
    limits = alpha.getextrema()
    box = alpha.point(lambda p: 255 if p > 16 else 0).getbbox()
    return {"input_path": str(path), "file_sha256": sha(path.read_bytes()),
            "visible_pixel_sha256": sha(premultiplied(image).tobytes()),
            "size_pixels": list(image.size), "alpha_range": list(limits),
            "alpha_framing_available": limits[0] <= 16 < limits[1],
            "visible_bounds_pixels": list(box) if box else None}


def pixel_delta(first, second):
    parts = ImageChops.difference(premultiplied(first), premultiplied(second)).split()
    delta = ImageChops.lighter(ImageChops.lighter(parts[0], parts[1]),
                               ImageChops.lighter(parts[2], parts[3]))
    hist = delta.histogram()
    return {"changed_pixel_fraction": round(1 - hist[0] / (first.width * first.height), 6),
            "mean_max_channel_delta_0_to_1": round(ImageStat.Stat(delta).mean[0] / 255, 6)}


def checked_int(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer from {low} to {high}")
    return value


def prepare(plan, base, output):
    if output.exists() or output.is_symlink():
        raise ValueError("Output directory already exists; choose a new directory")
    timeline = plan["timeline"]
    if not isinstance(timeline, list) or not 2 <= len(timeline) <= 120:
        raise ValueError("Timeline needs 2..120 actual display steps")
    if timeline[0]["state"] != "neutral":
        raise ValueError("First display frame must preserve neutral")
    for step in timeline:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", step["state"]):
            raise ValueError("Invalid state name")
        checked_int(step["duration_ms"], 10, 60000, "duration_ms")
    exports = plan.get("export", {})
    columns = checked_int(exports.get("atlas_columns", 4), 1, 16, "atlas_columns")
    preview = checked_int(exports.get("preview_max_side", 512), 32, 2048, "preview_max_side")
    directions = plan["directions"]
    if not isinstance(directions, list) or not 1 <= len(directions) <= 16:
        raise ValueError("Supply 1..16 explicit directions")
    prepared, keys = [], set()
    state_names = list(dict.fromkeys(step["state"] for step in timeline))

    def resolve(name):
        if not isinstance(name, str) or not name:
            raise ValueError("Input image path is missing")
        path = (base / name).resolve()
        if path.is_relative_to(output) or not path.is_file():
            raise ValueError(f"Missing input or input inside output directory: {path}")
        return path

    for direction in directions:
        key = direction["key"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,15}", key) or key in keys:
            raise ValueError("Direction keys must be unique safe folder names")
        keys.add(key)
        source_path = resolve(direction["source"])
        source = load_image(source_path)
        paths = {name: resolve(direction["states"][name]) for name in state_names}
        images = {name: load_image(path, png=True) for name, path in paths.items()}
        if any(im.size != source.size for im in images.values()):
            raise ValueError(f"Canvas size mismatch in direction {key}; no auto-resizing")
        if premultiplied(images["neutral"]).tobytes() != premultiplied(source).tobytes():
            raise ValueError(f"Neutral does not match the source pixels in {key}")
        source_alpha = source.getchannel("A").getextrema()
        if source_alpha[1] == 0:
            raise ValueError(f"Source is empty/fully transparent in {key}")
        if source_alpha[0] < 255 and any(im.getchannel("A").getextrema()[0] == 255 for im in images.values()):
            raise ValueError(f"Source transparency was lost in {key}")
        if source_alpha[0] == 255 and any(im.getchannel("A").getextrema()[0] < 255 for im in images.values()):
            raise ValueError(f"Opaque source background changed to transparency in {key}; prepare a declared new baseline first")
        records = {name: metrics(paths[name], im) for name, im in images.items()}
        unique = len({m["visible_pixel_sha256"] for m in records.values()})
        if unique == 1:
            raise ValueError(f"No visible change across states in {key}; cannot claim idle motion")
        warnings = []
        if unique < len(state_names):
            warnings.append("some_named_states_have_identical_visible_pixels")
        if records[timeline[-1]["state"]]["visible_pixel_sha256"] == records["neutral"]["visible_pixel_sha256"]:
            warnings.append("duplicate_endpoint_may_hold_at_loop_boundary")
        sheet_pixels = source.width * columns * source.height * math.ceil(len(timeline) / columns)
        if sheet_pixels > 64000000:
            raise ValueError("Atlas exceeds 64M pixels; split clips or explicitly export lower-resolution frames")
        steps = [images[s["state"]] for s in timeline]
        transitions = [dict(from_frame=i, to_frame=(i + 1) % len(steps),
                            **pixel_delta(im, steps[(i + 1) % len(steps)]))
                       for i, im in enumerate(steps)]
        prepared.append({"key": key, "source_path": source_path, "paths": paths,
                         "source_metrics": metrics(source_path, source),
                         "states": records, "size_pixels": list(source.size),
                         "unique_visible_states": unique, "warnings": warnings,
                         "transitions_including_loop": transitions,
                         "anchor_from_plan": direction.get("anchor", {"kind": "unknown"}),
                         "neutral_same_bytes_as_source": paths["neutral"].read_bytes() == source_path.read_bytes()})
    return prepared, timeline, columns, preview


def assemble(plan_path, output):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    prepared, timeline, columns, preview = prepare(plan, plan_path.parent, output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema_version": 1, "state": "assembled_visual_review_required",
                "motion_kind": plan.get("motion_kind", "unspecified"),
                "blink_enabled": plan.get("blink_enabled", False),
                "timeline": timeline, "directions": [],
                "visual_review_state_from_plan": plan.get("visual_review_state", "unknown"),
                "images_generated_or_interpolated_by_script": False,
                "identity_direction_motion_quality_or_pivot_verified_by_script": False,
                "preview_method": "whole canvases uniformly downscaled; fixed background and palette; no per-frame bbox normalization"}
    diagnostics = {"scope": "pixel/alpha/file diagnostics only, not semantic motion validation", "directions": []}
    diagnostics["direction_canvas_sizes_differ"] = len({tuple(r["size_pixels"]) for r in prepared}) > 1
    for record in prepared:
        key = record["key"]
        folder = output / key
        folder.mkdir()
        src_folder = folder / "source"
        src_folder.mkdir()
        archived = src_folder / ("original" + record["source_path"].suffix)
        shutil.copy2(record["source_path"], archived)
        width, height = record["size_pixels"]
        atlas = Image.new("RGBA", (width * columns, height * math.ceil(len(timeline) / columns)))
        frames, mappings = [], []
        ratio = min(1, preview / max(width, height))
        view_size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
        for i, step in enumerate(timeline):
            source_path = record["paths"][step["state"]]
            frame_path = folder / f"idle_{i:02d}.png"
            shutil.copy2(source_path, frame_path)
            image = load_image(source_path, png=True)
            atlas.paste(image, ((i % columns) * width, (i // columns) * height))
            thumb = image.resize(view_size, Image.Resampling.LANCZOS)
            background = Image.new("RGBA", view_size, "#f3eadb")
            background.alpha_composite(thumb)
            frames.append(background.convert("RGB"))
            mappings.append({"file": str(frame_path.relative_to(output)), "state": step["state"],
                             "duration_ms": step["duration_ms"],
                             "atlas_rect": [(i % columns) * width, (i // columns) * height, width, height],
                             "source_state_sha256": record["states"][step["state"]]["file_sha256"]})
        atlas.save(folder / "idle-atlas.png")
        palette = frames[0].quantize(colors=256)
        encoded = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
        gif_durations = [max(10, (step["duration_ms"] // 10) * 10) for step in timeline]
        gif_path = folder / "idle-preview.gif"
        encoded[0].save(gif_path, save_all=True, append_images=encoded[1:],
                        duration=gif_durations, loop=0, disposal=2, optimize=False)
        actual_durations = []
        with Image.open(gif_path) as gif:
            encoded_count = gif.n_frames
            for i in range(encoded_count):
                gif.seek(i)
                actual_durations.append(gif.info.get("duration", 0))
        if encoded_count == 1:
            record["warnings"].append("preview_downscale_or_quantization_lost_motion")
        manifest["directions"].append({"key": key, "source": str(archived.relative_to(output)),
                                       "size_pixels": [width, height], "display_frame_count": len(timeline),
                                       "unique_visible_states": record["unique_visible_states"], "frames": mappings,
                                       "atlas": str((folder / "idle-atlas.png").relative_to(output)),
                                       "preview": str(gif_path.relative_to(output)),
                                       "encoded_gif_frames": encoded_count,
                                       "encoded_gif_durations_ms": actual_durations,
                                       "requested_loop_duration_ms": sum(s["duration_ms"] for s in timeline),
                                       "neutral_same_bytes_as_source": record["neutral_same_bytes_as_source"]})
        diagnostics["directions"].append({k: v for k, v in record.items() if k not in ("source_path", "paths")})
    # qa_idle.py compatibility: <out>/<key>/<key>_NNN.png + transforms.json + qa_spec.json
    loco = plan.get("locomotion", "ground" if plan.get("motion_kind") in (None, "breathe", "unspecified") else "float")
    tr = {"fps": None, "display_frames_per_dir": len(timeline), "method": "key-pose assembly (assemble_idle.py)",
          "display_map": [s["state"] for s in timeline], "durations_ms": [s["duration_ms"] for s in timeline],
          "unique_poses_per_dir": {}, "directions": {}}
    ms = {s["duration_ms"] for s in timeline}
    if len(ms) == 1: tr["fps"] = round(1000 / ms.pop(), 3)
    qspec = {"locomotion": loco, "out_dir": ".", "directions": {}}
    for record in prepared:
        key = record["key"]; folder = output / key
        for i, step in enumerate(timeline):
            shutil.copy2(record["paths"][step["state"]], folder / f"{key}_{i:03d}.png")
        tr["unique_poses_per_dir"][key] = record["unique_visible_states"]
        tr["directions"][key] = {"frames": [{"frame": i, "t": round(sum(x["duration_ms"] for x in timeline[:i]) / max(1, sum(x["duration_ms"] for x in timeline)), 5),
                                              "state": st["state"], "global_scale": 1.0, "global_dx": 0} for i, st in enumerate(timeline)]}
        D = {"still": f"{key}/source/original{record['source_path'].suffix}"}
        anc = record["anchor_from_plan"]
        if isinstance(anc, dict) and isinstance(anc.get("contact_y"), (int, float)): D["contact_y"] = anc["contact_y"]
        elif loco == "ground": D["contact_y"] = record["source_metrics"]["visible_bounds_pixels"][3] - 1 if record["source_metrics"]["visible_bounds_pixels"] else 0; D["contact_y_note"] = "estimated from alpha bbox bottom; verify"
        qspec["directions"][key] = D
    (output / "transforms.json").write_text(json.dumps(tr, indent=1) + "\n", encoding="utf-8")
    (output / "qa_spec.json").write_text(json.dumps(qspec, indent=1) + "\n", encoding="utf-8")
    (output / "idle-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "idle-diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"output_dir": str(output), "directions": len(prepared),
            "display_frames_per_direction": len(timeline), "visual_review_required": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = assemble(args.plan.expanduser().resolve(), args.output_dir.expanduser().resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error), "images_generated": False}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
