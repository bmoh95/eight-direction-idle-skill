# eight-direction-idle-skill

2D 게임 캐릭터/몬스터를 **8방향 스틸**(S, SW, W, NW, N, NE, E, SE)로 만들고, 방향마다 **흔들리지 않는 idle 루프**
(기본 1초 · 24fps · 방향당 24프레임 · 총 192프레임)를 만드는 Agent Skill입니다.
기존 `create-round-pastel-characters` 스킬의 회전/스타일 규칙은 유지하고, idle 제작 방식을 새로 바꿨습니다.

핵심: idle 프레임을 이미지 생성기로 매번 다시 그리지 않고, **승인된 스틸 한 장을 부위별로 변형**(호흡 늘이기, 날개 접기, 부유 상하 이동)합니다.
그래서 얼굴·질감·소품·크기가 프레임마다 바뀌지 않고, 모든 변형은 로그로 남습니다.

## 설치
```bash
git clone https://github.com/bmoh95/eight-direction-idle-skill.git
# 스킬 폴더만 에이전트의 skills 디렉터리에 복사
cp -r eight-direction-idle-skill/eight-dir-idle-sprites ~/.claude/skills/      # Claude Code 예시
# 또는 사용하는 에이전트의 skills 경로(예: .cursor/skills/, ~/.agents/skills/)
pip install -r eight-direction-idle-skill/eight-dir-idle-sprites/scripts/requirements.txt
```
필요: Python 3.10+, Pillow, numpy, scipy, opencv-python-headless. 새 그림(정면/방향 생성)에는 참조 이미지를 받는 이미지 생성 도구가 필요하고, idle 생성에는 필요 없습니다.

## 사용법 (에이전트에게 이렇게 요청)
| 상황 | 요청 예시 |
|---|---|
| 텍스트만 | "주황 망토를 입은 고양이 기사, 오른손에 검. 8방향 + idle 만들어줘" |
| 정면 이미지 1장 | "이 정면 이미지로 8방향 만들고 방향별 idle 24프레임" |
| 8방향 스틸 보유 | "이 8방향 스틸로 idle만 만들어줘. 날개 달린 비행형이야" |
| idle만 다시 | "SE 방향 idle 호흡이 안 보여. 진폭 올려서 다시" |

지상형은 발을 고정하고 몸통만 호흡하며, 날개 비행형은 날개 접기 + 상하 부유, 부유형은 부유만 합니다. 없는 날개나 다리를 만들지 않습니다.

## 직접 실행
```bash
cd my_job
python3 SKILL/scripts/make_masks.py wing input/SE.png masks/SE_wing.png     # 날개 마스크 제안 → *_overlay.png 꼭 눈으로 확인
cp SKILL/templates/idle_spec.fly.example.json spec.json                     # 또는 ground 예시; 경로·contact_y 수정
python3 SKILL/scripts/idle_rig.py spec.json    # out_dir/DIR/DIR_000..023.png + transforms.json
python3 SKILL/scripts/qa_idle.py  spec.json    # qa_report.md
python3 SKILL/scripts/pack_idle.py spec.json   # atlas_256.png, atlas_manifest.json, GIF, same_phase_sheet.png
```
`fps`, `duration_s`, 채널별 `amp_px`·`cycles`(정수)·`phase`는 spec에서 바꿉니다. 진폭은 **게임 표시 크기에서 1px 이상** 움직이게 고르세요.

## 엔진 사용
아틀라스 행 = 방향, 열 = 프레임. 방향을 바꿀 때 프레임 번호와 진행도를 유지하세요 (Godot `set_frame_and_progress`, Unity `Animator.Play(state, 0, normalizedTime)`).
자세한 내용: `eight-dir-idle-sprites/references/engine-integration.md`. GIF는 1/100초 단위라 24fps가 정확하지 않으므로 미리보기용입니다.

## 저장소 구성
- `eight-dir-idle-sprites/` — 설치용 스킬 (SKILL.md, scripts, templates, references, assets, examples)
- `docs/research-and-design.md` — 조사·설계 보고서 (출처 링크, 방식 비교, 확인 사실 vs 판단 구분)
- `docs/test-report.md` — 테스트 결과 (기존 vs 새 방식, 남은 문제)
- `tests/` — 지상형(왕)·비행형(토끼) 테스트 입력, 마스크, spec, 결과(256px 프레임·아틀라스·QA·미리보기)

## 한계
머리 돌리기·팔 위치 변경 같은 큰 동작은 변형으로 안 됩니다(키포즈 생성 경로 + QA 사용). 자동 마스크는 색 대비에 의존합니다. 자동 QA는 문제를 찾는 보조일 뿐이고 시각 검토가 필요합니다. 남은 문제는 `docs/test-report.md` 참고.

라이선스: 코드/문서 MIT. 캐릭터 그림은 예시용으로 포함되며 재사용 라이선스가 아닙니다.
