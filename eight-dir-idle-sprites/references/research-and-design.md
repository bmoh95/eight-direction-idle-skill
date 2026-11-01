# 조사 및 설계 보고서 (Research & design)

표기: **[확인]** = 링크한 출처에서 직접 확인한 내용 · **[판단]** = 이 스킬의 설계 판단(검증된 표준 아님) · **[테스트]** = 동봉 테스트에서 측정한 값.

## 1. 출처 목록

| # | 출처 | 링크 | 핵심(확인한 범위) |
|---|---|---|---|
| S1 | GIF89a 사양 (W3C 사본) | https://www.w3.org/Graphics/GIF/spec-gif89a.txt | Graphic Control Extension의 Delay Time은 1/100초 단위 정수 |
| S2 | Godot AnimatedSprite2D | https://docs.godotengine.org/en/stable/classes/class_animatedsprite2d.html | `frame` 설정 시 `frame_progress` 초기화, `set_frame_and_progress()`로 유지 가능 |
| S3 | Unity Animator.Play | https://docs.unity3d.com/ScriptReference/Animator.Play.html | `normalizedTime`(0~1)으로 상태 내 시작 지점 지정 |
| S4 | Unity Sprite Editor | https://docs.unity3d.com/Manual/sprite/sprite-editor/use-editor.html | 스프라이트별 pivot 지정 |
| S5 | Aseprite Tags / Frame duration | https://www.aseprite.org/docs/tags/ , https://www.aseprite.org/docs/frame-duration/ | 태그 방향 Forward/Reverse/Ping-pong, 프레임별 지속시간 |
| S6 | TexturePacker texture settings | https://www.codeandweb.com/texturepacker/documentation/texture-settings | Reduce border artifacts(alpha bleeding), Extrude, Premultiply |
| S7 | Spine 메시 / 구매 | https://esotericsoftware.com/spine-meshes , https://esotericsoftware.com/spine-purchase | 메시는 Essential에 없음, 가중치 기반 변형 권장. 유료(Essential/Pro/Enterprise) |
| S8 | Live2D Cubism | https://www.live2d.com/en/cubism/about/ | 레이어 분리된 원화를 메시 변형하는 2D 리깅 도구(상용) |
| S9 | RIFE (Huang et al.) | https://arxiv.org/abs/2011.06294 | 실시간 중간 흐름 추정 기반 프레임 보간 |
| S10 | FILM (Reda et al.) | https://arxiv.org/abs/2202.04901 | 큰 움직임용 프레임 보간 |
| S11 | AnimeInterp (Siyao et al., CVPR 2021) | https://arxiv.org/abs/2104.02495 | 애니메이션은 평탄 색 영역·큰 비선형 움직임 때문에 일반 보간이 어렵다고 보고 |
| S12 | ToonCrafter (Xing et al.) | https://arxiv.org/abs/2405.17933 | 생성형 카툰 보간, 가림·비선형 움직임 대응 시도 |
| S13 | Thomas & Johnston, *The Illusion of Life* (1981); R. Williams, *The Animator's Survival Kit* (2001) | (도서) | 키포즈·인비트윈·타이밍·이징(slow in/out)·2s/1s 촬영 등 전통 원리 — 도서이므로 링크 없음, 일반 개념만 인용 |
| S14 | Agent Skills 사양 | https://agentskills.io/specification (github.com/agentskills/agentskills) | SKILL.md frontmatter(name≤64, description≤1024), scripts/references/assets, 500줄 이하 권장, 점진적 공개 |
| S15 | anthropics/skills skill-creator | https://github.com/anthropics/skills | 설명문은 "무엇+언제"를 적극적으로, 테스트 프롬프트로 반복 개선, package_skill/quick_validate |
| S16 | VoltAgent/awesome-agent-skills | https://github.com/VoltAgent/awesome-agent-skills | 품질 기준: 3인칭 설명, 500줄 이하, 절대경로 금지, 도구 최소화 |
| S17 | obra/superpowers | https://github.com/obra/superpowers | verification-before-completion(증거 없이 완료 주장 금지), writing-skills(기준선 실패→최소 스킬→허점 보완) |

## 2. 기본 원리 → 스킬 반영

- **표시 프레임 vs 고유 포즈** [확인 S5, S13 일반 개념]: 24fps 재생은 초당 24번 화면을 바꾼다는 뜻일 뿐, 고유 그림 24장이 필요하다는 뜻이 아니다. 전통 애니메이션은 같은 그림을 2프레임씩 보여주는 방식(on twos)을 흔히 쓴다. → 매니페스트에 `unique_poses_per_dir`와 `display_frames_per_dir`를 분리 기록.
- **루프와 이음매** [판단]: 끝에 첫 프레임 복제를 붙이면 같은 그림이 2프레임 연속 → 멈칫. → frame n-1→0을 이음매로 정의하고 `seam_ratio` 검사.
- **이징·위상** [판단, S13 개념 기반]: 채널마다 0~1 코사인 파형(정지점에서 느려짐)과 정수 cycles. 같은 함수를 8방향에 사용 → 위상 일치.
- **독립 채널** [판단]: breathe / flap / bob / (blink) 각각 독립 파라미터. 주기가 달라도 cycles가 정수면 루프가 닫힌다.
- **지상/부유/비행 기준점** [판단]: 지상형은 접점(발) 고정, 부유·비행형은 몸 중심 기준 + bob. 지상형에 bob 지정 시 스크립트가 거부.

## 3. 좌표·피벗·아틀라스

- 피벗은 엔진에서 스프라이트별로 지정 가능 [확인 S4]. 몸 중심·접점·무게중심은 서로 다르며, 알파 경계 상자는 날개·무기·망토 때문에 프레임/방향마다 바뀐다 [판단]. → 알파 bbox는 "정보용"으로만 기록, 정렬·배율에 사용 금지.
- 트림 패킹 시 오프셋을 보존하지 않으면 피벗이 프레임마다 이동 [판단, S6 trim 옵션]. 가장자리 후광은 alpha bleeding/extrude로 완화 [확인 S6].
- GIF는 1/100초 단위라 41.67ms 균일 불가 [확인 S1] → GIF는 미리보기, 정확한 타이밍은 PNG 시퀀스+매니페스트.
- 방향 전환 시 진행도 유지: Godot `set_frame_and_progress` [확인 S2], Unity `normalizedTime` [확인 S3].

## 4. 제작 방식 비교

| 방식 | 품질/일관성 | 난도 | 시간·비용 | 도구·제약 | 가려진 부위 |
|---|---|---|---|---|---|
| 1. 참조 기반 생성형 편집(프레임마다) | 포즈 자유도 높음, 그러나 매 호출 크기·얼굴·질감·소품이 재결정되어 흔들림 [테스트: 기존 bunny idle의 몸 영역 MAD 8~70] | 낮음 | 호출당 비용, 수리 반복 많음 | 이미지 생성 도구·사용량 한도(테스트 중 한도 도달) | 생성기가 그럴듯하게 "지어냄" — 사실이 아님 |
| 2. 키포즈 생성 + 인비트윈 | 키는 좋을 수 있으나 키 간 질감 차이 → 인비트윈에서 깜박임 | 중 | 키 3~7장 생성 + 검수 | 1과 같음 | 1과 같음 |
| 3. 레이어 분리 + 본/메시 리깅(Spine, Live2D) | 높은 일관성, 부드러운 변형 | 높음(레이어 분리·가중치) | 유료 라이선스 [확인 S7, S8], 작업 시간 큼 | 단일 이미지에서 레이어 자동 분리는 불완전 — 가려진 부분은 직접 그려야 함 | 수작업 필요 |
| 4. 부위 변형/절차적(본 스킬) | 원본 픽셀 재사용 → 얼굴·질감·소품 불변, 움직임 작음 | 중(마스크 검수) | 로컬 CPU, 무료, 방향당 수 초 | Python+OpenCV | 드러나는 영역이 없도록 설계(뒷모습은 spread 모드), 필요 시 추정·기록 |
| 5. 프레임 보간(RIFE/FILM, ToonCrafter) | 실사엔 강함, 셀 애니는 평탄 색·큰 움직임에서 왜곡 보고 [확인 S11, S12 동기] ; 날개 겹침 잔상 [테스트: 이전 flow 보간 결과 리뷰 반려] | 중 | GPU 권장 | 모델 가중치/라이선스 확인 필요 | 생성(지어냄) |
| 6. 3D 모델 → 렌더 | 방향·위상 완벽 일관 | 높음(모델링/리깅) | 큼 | Blender 등 | 3D로 재구성 필요 |

**선택 [판단]**: idle(작은 반복 동작)은 4번을 기본 경로로, 큰 동작이나 새로운 포즈가 필요하면 1/2번 + 본 스킬 QA를 보조 경로로, 리깅 도구가 있으면 3번을 권장. 모든 캐릭터에 한 방식을 강제하지 않고 SKILL.md Step 0/2 표로 경로 결정.

## 5. 기존 스킬 분석 (create-round-pastel-characters)

- 장점(유지): 방향 규약 JSON, W/E/N→대각선 생성 순서와 앵커 참조, 정면 정체성 고정, 후면 추정 기록, framing 측정 스크립트, 스타일 샘플.
- idle 문제의 원인: (a) idle 포즈를 생성기로 다시 그림 → 몸·질감 재결정, (b) 5포즈 왕복을 8표시 프레임 200ms로 사용, 24fps 표준 부재, (c) 검사 스크립트(`assemble_idle.py`)는 조립만 하고 동일성 검증 안 함(스스로 명시), (d) 비행형 전용 채널·layer 순서·뒷모습 가림 규칙 없음, (e) 방향 전환 위상 구현 문서 없음.
- 개선: idle을 생성에서 변형으로 이동, 잠금 영역 수치 검사, 접점·이음매·위상·잔여물 자동 검사, 비행/지상/부유 채널 분리, 뒷모습 spread 모드, 엔진 위상 문서.

## 6. 남은 어려운 문제
- 회전·고개 돌림·팔 위치 변경 등 큰 포즈 변화는 변형으로 불가.
- 마스크 자동화는 색 대비에 의존; 단색 캐릭터는 수작업 마스크 필요.
- 독립 시각 리뷰어(다른 모델)는 사용량 한도로 이번 테스트에서 일부만 사용(테스트 보고서 참조).
- 뒷모습 날개 spread와 앞모습 fold의 시각적 대응은 설계 판단이며, 사용자 취향 확인 필요.
