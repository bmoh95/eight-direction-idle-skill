# Option guide (quick start)

You don't need to remember anything. Ask for the work in one line and the agent shows the full option menu: every option with its current value and the other choices. Then it asks only about what's missing and waits for your **"이렇게 할까요?" → yes**.

- Print the menu: `python3 scripts/options.py` (`--lang ko` for Korean).
- Check a request file: `python3 scripts/options.py req.yaml` (or `.json`). Exit 1 means an unknown key, a bad value or a missing required item.
- Fill it in a form: open `index.html` (offline, single file). Pick options, then copy the generated text.
- Single source of options: `scripts/options.json`. After editing it, run `python3 scripts/build_index.py`.

## Copy-paste requests (Korean)
- `스킬로 새 캐릭터 만들어줘: 활 든 엘프 궁수, 남동/남서, 왼손 활, 투명 배경`
- `몬스터 idle 만들어줘: 둥근 슬라임, 8방향, 24fps 24프레임`
- `정면 얼굴 아이콘만: 곰, 고양이, 왕자. 내 참고 이미지로 그림체 고정, 크림 배경, 얼굴 규칙 line_nose`
- `이 캐릭터 부분 수정: 눈 색만 파랑으로, 나머지 그대로`
- `남동 피격 모션 만들어줘: 기사, 오른손 검`

## Copy-paste requests (English)
- `New character with the skill: elf archer with a bow, SE and SW, bow in the left hand, transparent background`
- `Idle for a monster: round slime, 8 directions, 24 fps, 24 frames`
- `Front face icons only: bear, cat, prince; style locked to my reference image, cream background, face preset line_nose`
- `Partial edit: change only the eye colour to blue`

## Request file example (`req.yaml`)
```yaml
task: idle_animation
subject: round blue slime with a leaf on top
view: SE+SW
fps: 24
frames: 24
cutout_engine: rembg
```
