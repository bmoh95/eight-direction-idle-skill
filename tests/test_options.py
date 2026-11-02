"""Tests for scripts/options.py, options.json and index.html sync. Run: python3 tests/test_options.py"""
import json, os, subprocess, sys, tempfile
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eight-dir-idle-sprites")
sys.path.insert(0, os.path.join(R, "scripts"))
import options as O, build_index as B
PY = [sys.executable, os.path.join(R, "scripts", "options.py")]


def run(*a):
    p = subprocess.run(PY + list(a), capture_output=True, text=True); return p.returncode, p.stdout


def req(d, ext=".json"):
    f = tempfile.NamedTemporaryFile("w", suffix=ext, delete=False, encoding="utf-8")
    f.write(json.dumps(d) if ext == ".json" else "\n".join(f"{k}: {v}" for k, v in d.items())); f.close(); return f.name


def test_menu_lists_every_option_with_current_and_alternatives():
    c, out = run()
    assert c == 0
    for k in O.OPTIONS: assert f"({k}):" in out, k
    assert "view): SE+SW   | other: front / SE / SW / 8dir" in out
    assert "cutout_engine): rembg   | other: flood" in out
    assert "(required - please tell me)" in out and "이렇게 할까요?" in out


def test_defaults():
    assert O.OPTIONS["cutout_model"][2] == "birefnet-general" and O.OPTIONS["camera"][2] == "side"
    assert O.OPTIONS["eye_palette"][2] == "blue,red,black"


def test_valid_request_ok_and_merged():
    c, out = run(req({"task": "idle_animation", "subject": "slime", "view": "8dir"}))
    assert c == 0 and "OK: request is complete" in out and "view): 8dir   | other: front / SE / SW / SE+SW" in out


def test_yaml_request():
    c, out = run(req({"task": "front_face_icon", "subject": "bear"}, ".yaml")); assert c == 0, out


def test_missing_and_invalid():
    c, out = run(req({"task": "fly", "camera": "fisheye", "bogus": 1}))
    assert c == 1 and "unknown option: bogus" in out and "camera: 'fisheye'" in out and "MISSING: subject" in out
    c, out = run(req({"task": "new_character", "subject": "x", "style_lock": "user_reference", "weapon": "bow"}))
    assert c == 1 and "style_ref" in out and "hand" in out


def test_face_presets_marked_as_preset():
    _, out = run(req({"task": "front_face_icon", "subject": "p", "face_preset": "line_nose"}))
    assert "preset, not universal" in out and "[x] Beardless humans" in out
    _, out = run(); assert "[ ] Beardless humans" in out and "[x] Eye shine always pure white" in out


def test_index_html_in_sync_with_options_json():
    html = open(os.path.join(R, "index.html"), encoding="utf-8").read()
    a = html.index('type="application/json">') + len('type="application/json">'); b = html.index("</script>", a)
    assert json.loads(html[a:b]) == json.load(open(os.path.join(R, "scripts", "options.json"), encoding="utf-8"))
    assert html == B.build(), "run python3 scripts/build_index.py"
    assert "http://" not in html and "https://" not in html, "index.html must be offline (no CDN)"


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try: f(); print("PASS", k)
            except AssertionError as e: fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
