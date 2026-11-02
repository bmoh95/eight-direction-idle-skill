#!/usr/bin/env python3
"""Regenerate ../index.html from index_template.html + options.json (single source). Run after editing options.json."""
import os
H = os.path.dirname(os.path.abspath(__file__))
def build():
    t = open(os.path.join(H, "index_template.html"), encoding="utf-8").read()
    j = open(os.path.join(H, "options.json"), encoding="utf-8").read().strip()
    return t.replace("/*OPTIONS_JSON*/", j)
if __name__ == "__main__":
    open(os.path.join(H, "..", "index.html"), "w", encoding="utf-8").write(build()); print("wrote index.html")
