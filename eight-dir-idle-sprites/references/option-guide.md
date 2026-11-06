# 8-direction request options

Use `python3 scripts/options.py --lang ko` to display the available options, or open `index.html` for the offline request form. `scripts/options.json` is the source of both. Regenerate the form with `python3 scripts/build_index.py` after changing the options.

Examples:

- 이 정면 캐릭터를 원래 그림체와 무기 든 손을 유지하며 8방향으로 만들어줘.
- 둥근 슬라임의 정면을 만든 다음 8방향 투명 PNG로 만들어줘.
- Generate the missing directional stills from this reference, preserving the design.

```yaml
task: directional_stills
subject: round blue slime with a leaf
view: 8dir
cutout_engine: rembg
```
