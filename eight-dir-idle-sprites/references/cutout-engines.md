# Cutout engines: flood vs rembg (BiRefNet)

`scripts/cutout.py --engine {rembg,flood}`. **The default is `rembg` + `birefnet-general`**, and it falls back to flood with a warning if rembg is missing. Both engines end with the same cleanup and gate:
pocket and halo removal, prop cavities, defringe, outline despill, then the `--check` gate on the written still.

## Verified rembg facts (rembg 2.0.86, checked against the installed package)
| Claim | Verified |
|---|---|
| `pip install rembg` | Installs the library only. The CLI and runtime need extras: `pip install "rembg[cpu,cli]"` (or `[gpu,cli]`). Plain `rembg` gives no `rembg` command or onnxruntime. |
| Models `birefnet-general`, `birefnet-dis`, `birefnet-massive` | All three exist. Also `birefnet-general-lite`, `-fp16`, `-portrait`, `-hrsod`, `-cod`, `isnet-anime`, `bria-rmbg` and others. **The default model is `bria-rmbg`, not BiRefNet**, so always pass `-m`. |
| `rembg i -m <model> in out` | Correct. |
| `-dc` decontaminate | Exists: `-dc/--decontaminate`. Python: `remove(..., decontaminate=True)`. **It is ignored when alpha matting is on.** |
| `-a` alpha matting | Exists: `-a`, with `-af/-ab/-ae` thresholds. Python: `alpha_matting=True`. It is slow. |
| (not mentioned) | `-ppm/post_process_mask`, `-vm/--vitmatte` (edge refine), `-om` (mask only) and `-bgc` also exist. |
| Python API | `new_session(model, sess_opts=...)` and `remove(img, session=, alpha_matting=, post_process_mask=, decontaminate=, vitmatte=, only_mask=, bgcolor=)`. |
| Memory | BiRefNet at 1024 px peaks around 9 GB with the default ONNX CPU arena, and got OOM-killed on a 15 GB box. `cutout.py` turns off `enable_cpu_mem_arena` and `enable_mem_pattern`, which brings it to about 4 GB. Run one still per process if RAM is tight. |

## Benchmark (4 real 1024px white-background stills: bow+string x2, staff+hair, kunai ring)
Gate = `cutout.py --check` (trapped matte px, outline fringe > 1% of the 2px band).

| Still | flood (current) | birefnet-general (+cleanup) | birefnet-dis (+cleanup) |
|---|---|---|---|
| bow + string, white beard | PASS | PASS | **FAIL**: erased about 2.3k px of white beard. The art guard restored the core, but the eroded edge failed the fringe gate. |
| bow + string (2) | PASS | PASS | PASS |
| kunai ring | **FAIL** (324 matte px in small pockets, 456 light fringe px) | PASS | PASS |
| staff + hair strands | PASS (visual OK) | PASS. The raw net output kept an 85 px white sliver between strands, and the cleanup removed it. | PASS |

Decontaminate on or off made no gate difference after the cleanup. The cleanup's own despill dominates. The raw `-dc` output from birefnet-dis did *raise* the fringe on the beard still (193 light px, FAIL).

**birefnet-massive** was run on the kunai ring still only, the hardest case. It got PASS with 0 trapped px and 0 fringe px, and its raw output also scored 0/0. It differs from general by only 15 px and looks the same in a zoom. Inference took 13 s, but peak RAM was about 8.3 GB against about 4 GB, roughly 2x. **Not chosen.**

**Default: `--engine rembg --model birefnet-general`.** `birefnet-dis` is sharper in thin gaps, but it removes white art (beards, white hair, cuffs) that touches the background, and the gate can't put lost art back. Try it per still for props on non-white characters, and check it with a zoom. Without the cleanup, raw net output is not shippable. It leaves white slivers and half-transparent veils in ring holes.

Speed: about 12–16 s per 1024 px still on 8 CPU cores for either model. flood takes under 2 s.
