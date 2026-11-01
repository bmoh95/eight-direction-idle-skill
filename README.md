# eight-direction-idle-skill

2D 게임 캐릭터/몬스터를 **8방향 스틸**(S, SW, W, NW, N, NE, E, SE)로 만들고, 방향마다 **흔들리지 않는 idle 루프**
(기본 1초 · 24fps · 방향당 24프레임 · 총 192프레임)를 만드는 Agent Skill입니다.
기존 `create-round-pastel-characters` 스킬의 회전/스타일 규칙은 유지하고, idle 제작 방식을 새로 바꿨습니다.

핵심: idle 프레임을 이미지 생성기로 매번 다시 그리지 않고, **승인된 스틸 한 장을 부위별로 변형**(호흡 늘이기, 날개 접기, 부유 상하 이동)합니다.
그래서 얼굴·질감·소품·크기가 프레임마다 바뀌지 않고, 모든 변형은 로그로 남습니다.

## 설치
```bash
git clone https://github.com/bmoh95/eight-direction-idle-skill.git
cd eight-direction-idle-skill
# 1) 스킬 폴더만 사용하는 에이전트의 skills 디렉터리에 복사 (폴더 이름 유지)
cp -r eight-dir-idle-sprites ~/.claude/skills/        # Claude Code 예시
#    다른 에이전트: 프로젝트의 .cursor/skills/, ~/.agents/skills/ 등 해당 도구의 skills 경로
# 2) 파이썬 의존성 (시스템 pip가 막혀 있으면 가상환경 사용)
python3 -m venv .venv && . .venv/bin/activate
pip install -r eight-dir-idle-sprites/scripts/requirements.txt
# 3) 설치 확인: 동봉 테스트(지상형 왕)를 다시 생성 (약 1~2분)
cd tests/ground_king && python3 ../../eight-dir-idle-sprites/scripts/idle_rig.py spec_8dir.json
```
필요: Python 3.10+, Pillow, numpy, scipy, opencv-python-headless. 새 그림(텍스트→정면, 정면→방향)에는 **참조 이미지를 입력받는 이미지 생성/편집 도구**(어느 제공자든 무관)가 필요하고, idle 생성에는 필요 없습니다.
아래 `SKILL_DIR`은 복사한 `eight-dir-idle-sprites` 폴더 경로입니다(예: `~/.claude/skills/eight-dir-idle-sprites`).

## 사용법 (에이전트에게 이렇게 요청)
| 상황 | 요청 예시 |
|---|---|
| 텍스트만 | "주황 망토를 입은 고양이 기사, 오른손에 검. 8방향 + idle 만들어줘" |
| 정면 이미지 1장 | "이 정면 이미지로 8방향 만들고 방향별 idle 24프레임" |
| 8방향 스틸 보유 | "이 8방향 스틸로 idle만 만들어줘. 날개 달린 비행형이야" |
| idle만 다시 | "SE 방향 idle 호흡이 안 보여. 진폭 올려서 다시" |

지상형은 발을 고정하고 몸통만 호흡하며, 날개 비행형은 날개 접기 + 상하 부유, 부유형은 부유만 합니다. 없는 날개나 다리를 만들지 않습니다.

## 경로별 진행
1. **텍스트만** → 에이전트가 정면 전신 1장 생성·검토·고정 → 8방향 스틸 → idle.
2. **정면 이미지 1장** → 그 이미지를 원본 그대로 정체성 기준으로 사용(재스타일 금지) → 8방향 스틸(W, E, N 먼저, 대각선은 이웃 기준) → 방향별 검토 → idle.
3. **8방향 스틸 보유 / idle만** → 그림 생성 없이 마스크·spec 작성 → idle 생성 → QA.
각 작업 폴더에 `SKILL_DIR/templates/work_manifest.template.json`을 복사해 입력·무기 손·접점 등을 먼저 채웁니다.

## 직접 실행 (idle)
spec 안의 상대 경로(`still`, `wing_mask`, `rigid[].mask`, `out_dir`)는 **spec 파일 위치 기준**입니다.
마스크 = 스틸과 같은 크기 흑백 PNG, 흰색(>127)=선택. 방향별 키: 날개 `"wing_mask"`, 무기·왕관 등 `"rigid": [{"name":"bow","mask":"masks/S_bow.png"}]`(늘어나지 않고 통째 이동), 몸통은 마스크 없음(알파 − 날개), 지상형 `"contact_y"`(발 맨 아래 행). 생성 전 `idle_rig.py spec.json --check`로 검증.
`measure_sprite_framing.py`: `--source 정면.png` + (`--input-dir 폴더`(8방향 DIR.png) 또는 `--candidate SE.png --direction SE`), 옵션 `--output`, `--require-all`, `--alpha-threshold`, `--height-review-pct`, `--edge-review-frac`.
```bash
mkdir my_job && cd my_job && mkdir input masks     # input/S.png, SW.png ... SE.png (같은 캔버스·같은 지면선)
```
**지상형 예시(다리 있음, 무기 든 왕)** — 발 고정, 몸통 호흡, 무기는 rigid:
```bash
cp SKILL_DIR/templates/idle_spec.ground.example.json spec.json   # 방향별 still, contact_y(발 맨 아래 행) 수정
python3 SKILL_DIR/scripts/measure_sprite_framing.py --source input/S.png --input-dir input   # 8방향 몸 높이·지면선 비교(읽기 전용)
python3 SKILL_DIR/scripts/make_masks.py color input/S.png masks/S_bow.png --lo H S V --hi H S V --box x0 y0 x1 y1
```
**비행형 예시(날개 토끼)** — 날개 접기 + 정수 상하 부유, 발 고정 없음:
```bash
cp SKILL_DIR/templates/idle_spec.fly.example.json spec.json
python3 SKILL_DIR/scripts/make_masks.py wing input/SE.png masks/SE_wing.png   # → masks/SE_wing_overlay.png 꼭 눈으로 확인
```
공통 생성·검사·패킹 (대표 방향 1개 먼저, 확인 후 8방향):
```bash
python3 SKILL_DIR/scripts/idle_rig.py  spec.json   # out_dir/DIR/DIR_000..023.png + transforms.json
python3 SKILL_DIR/scripts/qa_idle.py   spec.json   # qa_report.md / .json (자동 지표)
python3 SKILL_DIR/scripts/pack_idle.py spec.json   # atlas_256.png, atlas_manifest.json, GIF, same_phase_sheet.png, game_size_strip.png
```
`fps`, `duration_s`, 채널별 `amp_px`·`cycles`(정수)·`phase`는 spec에서 바꿉니다. 진폭은 **게임 표시 크기에서 1px 이상** 움직이게 고르세요. 실제 동작 예시는 `tests/ground_king/spec_8dir.json`, `tests/fly_bunny/spec_8dir.json`.

## 게임 엔진에서 사용
- 정확한 프레임: `out_dir/DIR/DIR_000..023.png` (PNG 시퀀스). 한 번에 쓰려면 `atlas_256.png`(행 = 방향, 열 = 프레임; 행 순서는 `atlas_manifest.json`의 `rows_directions`).
- `atlas_manifest.json`: `cell`(칸 크기), `fps`, loop, pivot/접점(`contact_y_source_px` × `scale_from_source`), 고유/표시 프레임 수.
- 피벗: 지상형 = 발 접점(8방향 동일), 비행형 = 몸 중심(부유는 프레임에 포함되어 있으니 엔진에서 추가 bob 금지).
- 방향 전환 시 idle 시계를 리셋하지 말고 프레임 번호·진행도 유지: Godot 4 `AnimatedSprite2D.set_frame_and_progress(f, p)`, Unity `Animator.Play(state, 0, normalizedTime)`, 직접 구현 시 `index = int(t * fps) % n`.
- 아틀라스 트리밍 시 오프셋 보존(안 하면 프레임마다 피벗이 흔들림). 자세한 내용: `eight-dir-idle-sprites/references/engine-integration.md`.

## 저장소 구성
- `eight-dir-idle-sprites/` — 설치용 스킬 (SKILL.md, scripts, templates, references, assets, examples)
- `docs/research-and-design.md` — 조사·설계 보고서 (출처 링크, 방식 비교, 확인 사실 vs 판단 구분)
- `docs/test-report.md` — 테스트 결과 (기존 vs 새 방식, 남은 문제)
- `tests/` — 지상형(왕)·비행형(토끼) 테스트 입력, 마스크, spec, 결과(256px 프레임·아틀라스·QA·미리보기)

## 한계 (솔직하게)
- **GIF ≠ 정확한 24fps**: GIF 지연은 1/100초 단위라 40/40/50ms로 근사됩니다. GIF는 미리보기용이고, 정확한 타이밍은 PNG 시퀀스 + `atlas_manifest.json`의 `fps`.
- **원본 해상도 프레임은 저장소에 없음**: 용량 때문에 `.gitignore` 처리(`tests/*/out_*/`). 저장소엔 256px 프레임·아틀라스·QA만 있고, 원본은 위 설치 확인 명령처럼 spec으로 재생성합니다.
- **시각 검수 필수**: 자동 QA는 문제를 찾는 보조일 뿐 품질을 증명하지 않습니다. 정상 속도·느린 GIF·게임 표시 크기·같은 위상 시트를 눈으로 확인하고, 가능하면 다른 리뷰어(다른 에이전트/사람)가 한 번 더 봅니다.
- 머리 돌리기·팔 위치 변경 같은 큰 동작은 변형으로 안 됩니다(키포즈 생성 경로 + QA, 드리프트 수리 시간 필요).
- 자동 마스크는 색 대비(밝은 몸/채도 높은 날개)에 의존 — 다른 배색은 마스크를 직접 그려야 합니다. 오버레이 확인 필수.
- 동봉 테스트 결과의 시각 판정은 제작자 자체 검토이며 외부 독립 검수가 아닙니다. 엔진 실속도 재생은 테스트하지 않았습니다. 남은 문제는 `docs/test-report.md`.

라이선스: 코드/문서 MIT. 캐릭터 그림은 예시용으로 포함되며 재사용 라이선스가 아닙니다.


## Style lock (most important)
New fronts and direction stills must match the bundled sample (`assets/styles/style-king.png`): crayon/felt grain,
thick dark outline, pastel palette, 2-head chibi proportions. An input image gives identity only. Check with
`python3 eight-dir-idle-sprites/scripts/style_check.py --sample eight-dir-idle-sprites/assets/styles/style-king.png --candidate front.png --head-top-y Y1 --head-bottom-y Y2 --feet-y Y3`.

## 카메라(시점) 기본값
- 기본은 **평면(사이드/살짝 3/4) 뷰**입니다. 캐릭터가 수평 지면선 위에 똑바로 서 있는 2D 스프라이트 구도입니다.
- **탑다운/위에서 내려다본/쿼터뷰/isometric** 구도는 사용자가 명시적으로 요청했을 때만 사용합니다.
- 대각선(SE 등)은 평면 뷰에서 3/4로 돌아선 자세이며, 화면 대각선으로 눕는 몸 방향은 탑다운 요청 시에만 적용합니다.

## 배경/누끼 원칙
- 가능하면 **투명 배경(알파 PNG)으로 바로 생성**합니다. 알파를 지원하지 않는 생성기(흰/단색 배경, JPEG 출력)는 대체 경로로만 쓰며, 생성 직후 `cutout.py --prop-mask`로 누끼 + 윤곽선 흰 테두리 제거를 거치고 `--check`를 통과해야 합니다.
- 흰 배경 이미지는 최종 아트가 아닙니다. 윤곽선 흰 잔여물·활 사이 흰 공간은 이 대체 경로에서 생기는 결함이며, 검사와 idle_rig 게이트가 막습니다.
