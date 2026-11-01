#!/bin/sh
# Minimal key-pose route test: assemble -> qa_idle must run on assembled output.
set -e; cd "$(dirname "$0")"; rm -rf /tmp/kp_out
python3 ../../eight-dir-idle-sprites/scripts/assemble_idle.py --plan plan.json --output-dir /tmp/kp_out
python3 ../../eight-dir-idle-sprites/scripts/qa_idle.py /tmp/kp_out/qa_spec.json
