#!/usr/bin/env python3
"""Regression checks for padded atlases, frame rectangles, and gutter validation."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "eight-dir-idle-sprites" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import cutout


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], check=True, capture_output=True, text=True)


def frame(arrow=False):
    im = Image.new("RGBA", (16, 12))
    for x in range(5, 10):
        for y in range(3, 10): im.putpixel((x, y), (20, 40, 60, 255))
    if arrow: im.putpixel((0, 6), (240, 30, 20, 255))
    return im


def check_gutters(image, rects):
    covered = Image.new("1", image.size)
    for x, y, w, h in rects:
        covered.paste(1, (x, y, x + w, y + h))
    for y in range(image.height):
        for x in range(image.width):
            if not covered.getpixel((x, y)): assert image.getpixel((x, y))[3] == 0


def check_pack(base):
    out = base / "rig"; (out / "SW").mkdir(parents=True)
    for i in range(6): frame(i == 5).save(out / "SW" / f"SW_{i:03d}.png")
    (out / "transforms.json").write_text(json.dumps({"fps": 6, "display_frames_per_dir": 6,
        "directions": {"SW": {"pivot": [8, 11], "contact_y": 11}}}))
    spec = base / "spec.json"
    spec.write_text(json.dumps({"out_dir": "rig", "fps": 6, "directions": {"SW": {}}}))
    run(SCRIPTS / "pack_idle.py", spec, "--cell", "16", "--game", "16")
    m = json.loads((out / "atlas_manifest.json").read_text()); im = Image.open(out / m["atlas"]).convert("RGBA")
    rects = m["frame_rects"]["SW"]
    assert m["cell"] == [16, 12] and m["atlas_cell"] == [32, 28] and m["padding_px"] == 8
    assert rects[4] == [136, 8, 16, 12] and rects[5] == [168, 8, 16, 12]
    for i, (x, y, w, h) in enumerate(rects): assert im.crop((x, y, x+w, y+h)).tobytes() == frame(i == 5).tobytes()
    check_gutters(im, rects)
    report = cutout.atlas_check(out / m["atlas"], rects=cutout.atlas_manifest_rects(out / m["atlas"], out / "atlas_manifest.json"))
    assert report["gutter_px"] == 0 and report["edge_contact"] == [5]
    im.putpixel((0, 0), (255, 0, 0, 255)); im.save(out / m["atlas"])
    assert cutout.atlas_check(out / m["atlas"], rects=rects)["gutter_px"] == 1


def check_assemble(base):
    source = base / "neutral.png"; shot = base / "shot.png"
    frame().save(source); frame(True).save(shot)
    plan = {"timeline": [{"state": "neutral", "duration_ms": 100}] * 5 + [{"state": "shot", "duration_ms": 100}],
        "export": {"atlas_columns": 3}, "directions": [{"key": "SW", "source": "neutral.png",
        "states": {"neutral": "neutral.png", "shot": "shot.png"}}]}
    path = base / "plan.json"; path.write_text(json.dumps(plan)); out = base / "assembled"
    run(SCRIPTS / "assemble_idle.py", "--plan", path, "--output-dir", out)
    m = json.loads((out / "idle-manifest.json").read_text()); direction = m["directions"][0]
    rects = [f["atlas_rect"] for f in direction["frames"]]
    assert direction["atlas_padding_px"] == 8 and direction["atlas_cell"] == [32, 28]
    assert rects[4] == [40, 36, 16, 12] and rects[5] == [72, 36, 16, 12]
    im = Image.open(out / direction["atlas"]).convert("RGBA")
    for i, (x, y, w, h) in enumerate(rects): assert im.crop((x, y, x+w, y+h)).tobytes() == frame(i == 5).tobytes()
    check_gutters(im, rects)
    assert cutout.atlas_manifest_rects(out / direction["atlas"], out / "idle-manifest.json") == rects
    diagnostics = json.loads((out / "idle-diagnostics.json").read_text())
    assert "frame_5_touches_canvas_edge_review_for_clipping_or_neighbor_art" in diagnostics["directions"][0]["warnings"]


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        check_pack(Path(tmp)); print("PASS padded procedural atlas")
        check_assemble(Path(tmp)); print("PASS padded key-pose atlas")
