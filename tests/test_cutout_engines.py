"""Cutout engine tests on tiny synthetic stills (no model download). Run: python3 tests/test_cutout_engines.py"""
import builtins, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eight-dir-idle-sprites", "scripts"))
import cutout as C


def still():
    """96px white still: dark outlined body with a white beard patch + a ring prop with a white hole."""
    im = np.full((96, 96, 3), 255, np.uint8)
    y, x = np.mgrid[:96, :96]
    body = (abs(x - 40) < 22) & (abs(y - 50) < 30)
    im[body] = (40, 30, 30); im[(abs(x - 40) < 19) & (abs(y - 50) < 27)] = (60, 90, 200)
    im[(abs(x - 40) < 12) & (y > 56) & (y < 75)] = (214, 208, 200)   # off-white (shaded) beard art
    r = np.hypot(x - 76, y - 30)
    im[(r < 12)] = (40, 30, 30); im[(r < 6)] = 255                    # ring with trapped white hole
    im[(abs(x - 66) < 3) & (y > 30) & (y < 50)] = (40, 30, 30)        # ring handle into body
    return Image.fromarray(im), body, r


def test_flood_gate_passes_on_clean_cutout():
    raw, _, r = still()
    rgba, _, _ = C.cutout(raw, engine="flood")
    assert rgba[30, 76, 3] == 0, "ring hole must be cleared"
    ok, rep = C.gate(rgba); assert ok, rep


def test_gate_catches_trapped_white():
    raw, _, r = still()
    a = np.dstack([np.array(raw), np.full((96, 96), 255, np.uint8)])
    a[(np.array(raw).min(-1) == 255) & (r > 14)] = 0          # outer bg cleared, hole left opaque white
    ok, rep = C.gate(a); assert not ok, rep


def test_rembg_missing_falls_back_to_flood():
    real = builtins.__import__
    def fake(name, *a, **k):
        if name == "rembg": raise ImportError("no rembg")
        return real(name, *a, **k)
    builtins.__import__ = fake
    try:
        raw, _, _ = still()
        rgba, _, _ = C.cutout(raw, engine="rembg")
    finally:
        builtins.__import__ = real
    ok, rep = C.gate(rgba); assert ok, rep


def _with_ml(alpha_fn):
    raw, body, r = still()
    rgb = np.array(raw)
    old = C.rembg_alpha
    C.rembg_alpha = lambda *a, **k: (alpha_fn(rgb, body, r).astype(np.uint8), rgb)
    try:
        return C.cutout(raw, engine="rembg")[0]
    finally:
        C.rembg_alpha = old


def test_art_guard_restores_erased_white_art():
    def ml(rgb, body, r):
        a = np.where(body | (r < 12), 255, 0)
        a[(rgb[..., 0] == 214)] = 0              # net erased the off-white beard
        return a
    out = _with_ml(ml)
    assert out[65, 40, 3] == 255, "beard must be restored by the art guard"


def test_soft_matte_residue_and_opaque_pocket_are_cleared():
    def ml(rgb, body, r):
        a = np.where(body | (r < 12), 255, 0)
        a[r < 6] = 120                            # half-transparent white veil in the ring hole
        return a
    out = _with_ml(ml)
    assert out[30, 76, 3] == 0
    ok, rep = C.gate(out); assert ok, rep
    out2 = _with_ml(lambda rgb, body, r: np.where(body | (r < 12), 255, 0))  # net kept the hole opaque
    assert out2[30, 76, 3] == 0, "cleanup must still remove an opaque trapped pocket"


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try: f(); print("PASS", k)
            except AssertionError as e: fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
