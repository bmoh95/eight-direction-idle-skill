#!/usr/bin/env python3
"""Read-only alpha-framing diagnostics; never validate pose, identity or pivots."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow is required for numeric inspection. No images were changed.")


def image_metrics(path, alpha_threshold=16):
    path = Path(path).expanduser().resolve()
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        result = {
            "path": str(path),
            "size_pixels": [width, height],
            "original_mode": image.mode,
            "frame_count": getattr(image, "n_frames", 1),
            "selected_frame_index": 0,
            "exif_orientation": image.getexif().get(274, 1),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "alpha_threshold": alpha_threshold,
            "framing_available": False,
            "bounds_role": "alpha silhouette diagnostic, not a body pivot or ground-contact measurement",
        }
        if not has_alpha:
            result["unavailable_reason"] = "no_alpha_channel_or_transparency"
            return result
        alpha = image.convert("RGBA").getchannel("A")
        low, high = alpha.getextrema()
        result["alpha_range"] = [low, high]
        if low > alpha_threshold:
            result["unavailable_reason"] = "no_separable_transparent_background"
            return result
        bounds = alpha.point(lambda value: 255 if value > alpha_threshold else 0).getbbox()
        if bounds is None:
            result["unavailable_reason"] = "empty_foreground_at_alpha_threshold"
            return result
        left, top, right, bottom = bounds
        result.update({
            "framing_available": True,
            "visible_bounds_pixels": list(bounds),
            "visible_bounds_normalized": [left / width, top / height, right / width, bottom / height],
            "visible_height_pixels": bottom - top,
            "visible_height_fraction": (bottom - top) / height,
            "top_fraction": top / height,
            "bottom_fraction": bottom / height,
            "bottom_margin_fraction": (height - bottom) / height,
            "silhouette_center_fraction": [(left + right) / (2 * width), (top + bottom) / (2 * height)],
        })
        return result


def compare_metrics(source, candidate, height_review_pct=3.0, edge_review_frac=0.015):
    flags = []
    result = {
        "review_flags": flags,
        "angle_verified_by_script": False,
        "identity_verified_by_script": False,
        "game_pivot_verified_by_script": False,
        "automatic_image_correction_applied": False,
    }
    if candidate["size_pixels"] != source["size_pixels"]:
        flags.append("canvas_size_differs")
    if source["frame_count"] > 1:
        flags.append("source_multiple_frames_first_frame_only")
    if candidate["frame_count"] > 1:
        flags.append("candidate_multiple_frames_first_frame_only")
    if source["exif_orientation"] != 1:
        flags.append("source_exif_orientation_needs_review")
    if candidate["exif_orientation"] != 1:
        flags.append("candidate_exif_orientation_needs_review")
    if not source["framing_available"]:
        flags.append("source_alpha_framing_unavailable")
    if not candidate["framing_available"]:
        flags.append("candidate_alpha_framing_unavailable")
    if source["framing_available"] and candidate["framing_available"]:
        height_delta = (candidate["visible_height_fraction"] / source["visible_height_fraction"] - 1) * 100
        top_delta = candidate["top_fraction"] - source["top_fraction"]
        bottom_delta = candidate["bottom_fraction"] - source["bottom_fraction"]
        result.update({
            "normalized_visible_height_change_pct": round(height_delta, 4),
            "top_boundary_shift_fraction": round(top_delta, 6),
            "bottom_boundary_shift_fraction": round(bottom_delta, 6),
            "top_boundary_shift_in_source_pixels": round(top_delta * source["size_pixels"][1], 3),
            "bottom_boundary_shift_in_source_pixels": round(bottom_delta * source["size_pixels"][1], 3),
            "interpretation": "Review visually: projection, appendages and occlusion can change these bounds without a scale error.",
        })
        if abs(height_delta) > height_review_pct + 1e-9:
            flags.append("visible_height_change_needs_review")
        if abs(top_delta) > edge_review_frac + 1e-12:
            flags.append("top_boundary_shift_needs_review")
        if abs(bottom_delta) > edge_review_frac + 1e-12:
            flags.append("bottom_boundary_shift_needs_review")
    result["review_state"] = "needs_visual_review" if flags else "no_numeric_flags_visual_review_still_required"
    return result


def nonnegative_float(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("Use a finite nonnegative number.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input-dir", type=Path)
    mode.add_argument("--candidate", type=Path)
    parser.add_argument("--direction", choices=["S", "SW", "W", "NW", "N", "NE", "E", "SE"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--alpha-threshold", type=int, default=16)
    parser.add_argument("--height-review-pct", type=nonnegative_float, default=3.0)
    parser.add_argument("--edge-review-frac", type=nonnegative_float, default=0.015)
    args = parser.parse_args(argv)
    if not 0 <= args.alpha_threshold <= 254:
        parser.error("--alpha-threshold must be between 0 and 254")
    if args.edge_review_frac > 1:
        parser.error("--edge-review-frac must be at most 1")
    if args.candidate and args.require_all:
        parser.error("--require-all applies to --input-dir, not a single candidate")
    if args.direction and not args.candidate:
        parser.error("--direction applies to a single --candidate")
    if args.input_dir and not args.input_dir.is_dir():
        parser.error("--input-dir must be an existing directory")
    if args.output and args.output.suffix.lower() != ".json":
        parser.error("--output must be a .json report, never an image file")
    try:
        source = image_metrics(args.source, args.alpha_threshold)
        if args.candidate:
            entries = [{"key": args.direction or "candidate", "filename": str(args.candidate)}]
        else:
            map_path = Path(__file__).resolve().parent.parent / "references" / "legacy" / "directions.json"
            entries = json.loads(map_path.read_text(encoding="utf-8"))["directions"]
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": str(error), "images_modified": False}, ensure_ascii=False))
        return 2
    records = []
    for entry in entries:
        path = args.candidate if args.candidate else args.input_dir / entry["filename"]
        if not args.candidate and not path.is_file():
            alt = args.input_dir / f"{entry['key']}.png"  # skill-standard naming S.png ... SE.png
            if alt.is_file():
                path = alt
        record = {"direction": entry["key"], "path": str(path.resolve())}
        if not path.is_file():
            record["file_state"] = "missing"
        else:
            try:
                candidate = image_metrics(path, args.alpha_threshold)
                record.update({
                    "file_state": "measured",
                    "metrics": candidate,
                    "same_bytes_as_source": candidate["sha256"] == source["sha256"],
                    "comparison": compare_metrics(source, candidate, args.height_review_pct, args.edge_review_frac),
                })
            except (OSError, ValueError) as error:
                record.update({"file_state": "error", "error": str(error)})
        records.append(record)
    missing = [r["direction"] for r in records if r["file_state"] == "missing"]
    errors = [r["direction"] for r in records if r["file_state"] == "error"]
    measured = [r for r in records if r["file_state"] == "measured"]
    report = {
        "schema_version": 2,
        "scope": "read-only alpha-framing diagnostics; thresholds are configurable review heuristics",
        "source": source,
        "review_configuration": {"alpha_threshold": args.alpha_threshold, "height_review_pct": args.height_review_pct, "edge_review_fraction": args.edge_review_frac},
        "directions": records,
        "summary": {
            "measured_count": len(measured),
            "missing_directions": missing,
            "error_directions": errors,
            "numeric_review_directions": [r["direction"] for r in measured if r["comparison"]["review_flags"]],
            "visual_review_required": True,
            "game_ready_alignment_verified": False,
            "images_modified": False,
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output_path = args.output.expanduser().resolve()
        input_paths = [Path(source["path"]), *[Path(record["path"]) for record in records]]
        for input_path in input_paths:
            if output_path == input_path or (output_path.exists() and input_path.exists() and output_path.samefile(input_path)):
                parser.error("--output must not overwrite or alias an input image")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 2 if errors or not measured or (args.require_all and missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
