# 테스트 결과 보고서

날짜: 2026-11-01 (KST). 모든 수치는 `scripts/qa_idle.py` 자동 측정값이며, 시각 검토는 별도 표기.

## 테스트 케이스
| 케이스 | 구조 | 입력 | 채널 | 산출 |
|---|---|---|---|---|
| `tests/fly_bunny` | 날개 있는 비행형(나비날개 토끼) | 기존 승인 8방향 스틸 | flap(fold 0.30, 뒷모습 N/NW/NE spread −0.10) + bob 10px | 8방향 × 24 = **192 프레임 실제 생성** |
| `tests/ground_king` | 지상형(활 든 왕) | 기존 8방향 스틸(1024px) | breathe 8px, 활 = rigid | 8방향 × 24 = **192 프레임 실제 생성** |

진행 순서: bunny SE 한 방향 먼저(`spec_SE.json`) → 검토 → 8방향. 왕은 r1(4px) → 게임 크기에서 안 보여 8px로 r2.
고유 포즈/표시 프레임: 절차적 방식은 방향당 고유 24 / 표시 24 (홀드·핑퐁 없음), 캐릭터당 192 고유.

## 기존 방식 vs 새 방식 (bunny, 같은 QA)
| 지표 | 기존(생성형 5포즈 홀드) | 새(부위 변형) |
|---|---|---|
| 잠금 영역(몸) MAD 최대, 8방향 | 8.2 ~ 70.7 | 0.0 (전 방향) |
| frame0 = 승인 스틸 | 아니오(별도 생성 스틸 사용, diff 255) | 예 (diff 0) |
| 정지/중복 스텝 | 24개 중 16개, 이음매 스텝 0(끝 프레임 중복) | 0 |
| 이음매 비율 / 점프 비율 | 0.0 / 1.1~2.2 | 0.19~0.31 / 1.31~1.55 |
| 미세 잔여 픽셀 / 가장자리 잘림 | 0 / 없음 | 0 / 없음 |
| 방향 간 위상 | 측정 불가(변환 로그 없음 — 표의 "True"는 로그 부재로 인한 무의미 값) | 일치(t, bob, flap, breathe 로그 동일) |
| 소요 | 방향당 생성 호출 다수 + 수리 | 방향당 수 초(CPU) + 마스크 검토 |

지상형 왕: 잠금 MAD 0, frame0 diff 0, 접점(발) 이동 0px, 이음매 0.18~0.20, 점프 1.37~1.38, 위상 일치 — 8방향 auto_ok.

## 시각 검토 (역할 C)
- r1(커밋 f2c450f): 구현 패스와 같은 흐름의 자체 검토만 했고 needs_review 4건을 남김.
- r2(이번): 마스크 4건 수정 후 8방향 전체 재생성·재측정, 별도 검토 패스에서 확대 오버레이·극값 위상(0/6/12/18)·same_phase_sheet 확인.
  사람/외부 리뷰어 검토는 아님.

### needs_review 4건 처리 (r2)
| 항목 | 원인 | 수정 | 결과 |
|---|---|---|---|
| bunny NW 가장자리 정지 날개 조각 | 자동 마스크의 얇은 돌출부 | `tests/fly_bunny/fix_wing_masks.py`: opening(3×3, 7회) + 8000px 미만 조각 제거 | 해결: 날개 외곽이 함께 움직임 |
| bunny NW/NE 발이 날개 마스크에 포함 | 하단 몸통 띠의 크림색 털이 마스크에 섞임 | 하단 28%·중앙 띠의 털색(S<90, V>170) 픽셀 제외 | 해결: 발은 잠금 영역(MAD 0) |
| bunny SE 귀 뒤 먼 날개 조각 | 별개 성분이 마스크에 포함 | 가장 큰(가까운) 날개 성분만 유지, 몸 쪽(오른쪽 42%, x≥58%) 하단 털 제외 | 해결: 먼 날개는 몸과 함께 고정. 중간 시도(opening 포함)는 날개 뿌리에 정지 조각·알파 섬 11~12개 → 제거 후 섬 0 |
| king SE 활 마스크 부분적 | 손 위 윗 활대만 잡힘(6134px) | `tests/ground_king/fix_se_bow_mask.py`: 손 아래 갈색 활대 성분 + 시위(끝점 연결선 6px 내 밝은 픽셀) 추가 → 12720px | 해결: 활 전체가 rigid로 이동, 늘어남 없음(잠금 MAD 1.06은 활 경계 안티앨리어싱) |

### r2 자동 QA
- bunny 8방향: 잠금 MAD 0.0, frame0 diff 0, 섬 0, 잘림 없음, 이음매 0.17~0.31, 점프 1.31~1.57 — 전부 auto_ok.
- king 8방향: 접점 이동 0px, 섬 0, 이음매 0.18~0.20, 점프 1.37~1.38 — 전부 auto_ok.

### r2 시각 판정
- bunny: PASS(테스트 범위). 8방향 위상·크기 일치, 얼굴·몸 변화 없음, 날개 정지 조각 없음.
  남은 관찰: SE 아래 날개 뿌리의 몸 쪽 작은 끝부분은 몸과 함께 고정(눈에 띄지 않는 수준).
- king: PASS(테스트 범위). 발 고정, 활 형태 유지, 왕관·수염·망토 변화 없음.
- 정상 속도 확인은 GIF(근사 타이밍)로만 함. 엔진 실속도 재생은 하지 않음.

## 결론
- 자동 QA: 두 캐릭터 8방향 모두 auto_ok. 시각: 두 캐릭터 PASS(테스트 범위, 외부 리뷰어 아님).
- GIF는 40/40/50ms 근사. 정확한 24fps 타이밍은 PNG 시퀀스 + `atlas_manifest.json`.
- 저장소에는 용량 문제로 256px 프레임(`results/*/frames_256`)만 포함. 원본 해상도 프레임은 스펙으로 재생성 가능:
  `cd tests/fly_bunny && python3 ../../eight-dir-idle-sprites/scripts/idle_rig.py spec_8dir.json`.
- 교훈(스킬 일반): 자동 마스크는 항상 오버레이로 확인하고, 발·털처럼 잠가야 할 부위가 섞이면 색+위치 띠로 제외, 얇은 조각은 opening/면적 필터로 정리. 단 날개 뿌리처럼 경계가 몸과 닿는 곳에 opening을 쓰면 정지 조각·알파 섬이 생기므로 섬 수(QA)를 반드시 다시 확인.

## r3 독립 결과물 시각 QA (Part B)
- 방법: 256px 프레임 직접 측정(바닥/상단/무게중심/면적/섬/프레임 간 변화) + 확대 크롭·어니언 오버레이·24프레임 시트. 이전 PASS를 전제하지 않음.
- 발견: **bunny NE 귀-머리 경계 이음매**. 자동 날개 마스크가 오른쪽 귀 아래 털·윤곽선을 포함해 그 부분이 날개와 함께 움직이며 목/귀 뿌리에 갈색 선이 열렸다 닫힘. 자동 QA는 잠금 MAD 0으로 통과시켰음(누출 부위가 마스크 안이라 측정 대상 밖) → 자동 QA로 잡을 수 없는 유형.
- 수정: `tests/fly_bunny/fix_ne_ear_junction.py` — 상단 45%·중심 -5%~+17% 띠의 털색 픽셀(팽창 5) 제외, 8000px 이상 성분 유지. NE만 재생성(다른 방향 프레임 바이트 동일).
- 재검: NE 이음매 해소, 자동 QA 8방향 auto_ok 유지(섬 0, 잠금 MAD 0).
- king: 8방향 발 바닥 이동 0px, 발 무게중심 이동 0px, 섬 0, SE 활 형태·시위 24프레임 유지 → PASS.
- 남은 관찰(needs_review 아님, 원본 스틸 성질): 방향별 캐릭터 화면 크기 차이(king N/S 대비 측면), bunny SE는 3/4 시점이라 먼 날개는 귀 뒤 끝만 보임.

## Team 2 (Part I / Part E) — bunny back-view ghost outlines
- Found (independent visual, 2x zoom): NE frame 12 showed doubled wing/ear/back outlines. Cause: spread mode (`flap_fold<0`, back views) composited the whole original wing as a backstop under the enlarged wing, so the overlapping near/far wing edges showed twice.
- Fix (`idle_rig.py`, generic): backstop only the hinge band (wing ∩ body ring); drop detached alpha islands <40px. Regenerated all 8 bunny dirs; qa_idle auto_ok x8, islands 0.
- Visual re-check NE/N/NW f0 vs f12: doubled outlines gone. needs_review: slightly ragged wing tip edge near NE ear and NW lower-left fringe at max spread.
- `measure_sprite_framing.py --input-dir`: falls back to `<DIR>.png` (S.png…SE.png); king input measures 8/8.
