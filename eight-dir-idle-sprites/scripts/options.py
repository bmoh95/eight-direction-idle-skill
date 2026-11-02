#!/usr/bin/env python3
"""Option guide for this skill.

  python3 scripts/options.py                 # print every option: current value + other choices
  python3 scripts/options.py --lang ko       # Korean labels
  python3 scripts/options.py req.yaml|json   # validate a request; print the confirmation menu
                                             # (current values = request merged over defaults), list missing items
Exit 1 when the request has unknown keys / invalid values / missing required items.
"""
import json, sys

import os
FREE = None  # free-text option (no fixed choices)
SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "options.json")  # single source (index.html inlines a copy)
SPEC = json.load(open(SPEC_PATH, encoding="utf-8"))
# key: (label_en, label_ko, default, choices or FREE, required)
OPTIONS = {o["key"]: (o["en"], o["ko"], o["default"], o["choices"], o["required"]) for o in SPEC["options"]}
NOTES = {o["key"]: o["note"] for o in SPEC["options"] if o.get("note")}


def menu(req=None, lang="en"):
    req = req or {}
    out = []
    for k, (en, ko, d, ch, need) in OPTIONS.items():
        cur = req.get(k, d)
        cur_s = "(required - please tell me)" if cur is None and lang == "en" else ("(필수 - 알려주세요)" if cur is None else str(cur))
        if ch is FREE: alt = "free text" if lang == "en" else "자유 입력"
        else: alt = " / ".join(str(c) for c in ch if c != cur) or "-"
        lab = en if lang == "en" else ko
        note = f"  [{NOTES[k]}]" if k in NOTES and lang == "en" else ""
        out.append(f"- {lab} ({k}): {cur_s}   | {'other' if lang == 'en' else '다른 선택'}: {alt}{note}")
    preset = req.get("face_preset", OPTIONS["face_preset"][2])
    on = set(SPEC["presets"].get(preset, []))
    out.append(("Face rules (preset, not universal; preset '%s'):" if lang == "en" else "얼굴 규칙 (프리셋, 보편 규칙 아님; '%s'):") % preset)
    for r in SPEC["face_rules"]:
        out.append(f"  [{'x' if r['key'] in on else ' '}] {r[lang]} ({r['key']})")
    out.append(SPEC["confirm"][lang])
    return "\n".join(out)


def validate(req):
    errs = []
    if not isinstance(req, dict): return ["request must be a mapping"], []
    for k, v in req.items():
        if k not in OPTIONS: errs.append(f"unknown option: {k}"); continue
        ch = OPTIONS[k][3]
        if ch is not FREE and v not in ch and str(v) not in [str(c) for c in ch]:
            errs.append(f"{k}: '{v}' not in {ch}")
    missing = [k for k, o in OPTIONS.items() if o[4] and not req.get(k)]
    if req.get("style_lock") == "user_reference" and "style_ref" not in req: missing.append("style_ref")
    if req.get("weapon") not in (None, "none") and "hand" not in req: missing.append("hand")
    return errs, missing


def load(path):
    txt = open(path, encoding="utf-8").read()
    if path.endswith(".json"): return json.loads(txt)
    try:
        import yaml
        return yaml.safe_load(txt)
    except ImportError:  # tiny fallback: flat "key: value" lines
        d = {}
        for ln in txt.splitlines():
            ln = ln.split("#")[0].strip()
            if ":" in ln:
                k, v = ln.split(":", 1); v = v.strip().strip('"\'')
                d[k.strip()] = int(v) if v.isdigit() else v
        return d


def main(argv):
    lang = "ko" if "--lang" in argv and argv[argv.index("--lang") + 1] == "ko" else "en"
    files = [a for a in argv if not a.startswith("--") and a not in ("ko", "en")]
    if not files:
        print(menu(lang=lang)); return 0
    req = load(files[0]); errs, missing = validate(req)
    print(menu(req if isinstance(req, dict) else {}, lang))
    for e in errs: print("ERROR:", e)
    if missing: print("MISSING:", ", ".join(missing))
    if not errs and not missing: print("OK: request is complete")
    return 1 if errs or missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
