# 품질 검사와 최소 보정

먼저 [공통 잔여물 검사](artifact-review.md)로 의도하지 않은 점·짧은 선·외곽 돌출물을 확인한다. 알파 크기·여백 검사와 별도인 의미 검사이며, 정상 눈 반짝임·시위·의도된 효과를 지우지 않는다.

## 원본별로 기준을 계산하기

종족, 그림체, 캔버스 크기, 대상의 배율과 기준점은 매 입력에서 새로 관찰한다. 이 문서의 골렘 수치는 한 번의 진단 예시이며 다른 캐릭터의 목표 크기나 품질 기준으로 사용하지 않는다.

- 사람·동물·다족·무족·부유·수중·날개형 구조를 구분한다. 원본의 실제 팔다리와 식별 특징을 따른다.
- 발이 없는 대상에는 발 접지선을 강제하지 않는다. 확인한 몸 중심이나 사용자 정의 기준점을 사용한다.
- 기본 알파 경계 검사는 투명 배경에만 적용한다. 알파가 없거나 배경 전체가 불투명하면 `framing_available=false`와 이유를 남기고 시각적 기준점 검사를 사용한다.
- 입력의 화풍과 큰 구조를 유지한다. 눈의 수, 사람형 머리 비율, 이끼, 돌, 특정 색상이나 무기를 공통 기본값으로 넣지 않는다.

## 측정 명령

`SKILL_ROOT`는 현재 스킬 루트, `SOURCE`와 `OUTPUT_DIR`은 현재 작업의 실제 경로로 해석한다. 이 스크립트는 이미지를 수정하지 않으며 JSON만 기록한다.

```bash
python3 "$SKILL_ROOT/scripts/measure_sprite_framing.py" \
  --source "$SOURCE" --input-dir "$OUTPUT_DIR" \
  --output "$OUTPUT_DIR/framing-report.json"
```

일부 방향만 준비되어 있어도 검사할 수 있다. 최종 파일 개수까지 확인할 때는 `--require-all`을 추가한다. 단일 결과나 보정 전후 비교는 다음처럼 검사한다.

```bash
python3 "$SKILL_ROOT/scripts/measure_sprite_framing.py" \
  --source "$SOURCE" --candidate "$CANDIDATE" --direction W
```

경고가 있어도 명령은 진단 결과를 출력하며 정상 종료할 수 있다. `--require-all`에서 파일 누락, 이미지 읽기 오류, 잘못된 입력이 있으면 비정상 종료한다. 종료 코드 0은 시각적 품질 통과를 뜻하지 않는다.

## 경계와 실제 접점 구분

- 알파 상자는 무기·꼬리·뿔·날개까지 포함한다. 수평 폭은 방향에 따라 크게 달라지므로 폭 비율을 고정하지 않는다.
- 정면에 보이는 무릎과 측면의 굽힘, 발의 앞뒤 깊이, 고정된 카메라의 높이는 투영된 높이와 최하단 위치를 바꿀 수 있다. 작은 경고가 곧 잘못된 확대라는 뜻은 아니다.
- 실제 배율 판단에는 몸통·머리 같은 대응 부위의 시각적 크기도 함께 본다. 실제 발 접점과 몸 기준 피벗은 사용자가 지정한 기준점 또는 별도로 확인한 점으로 기록한다.
- 불투명 배경, 빈 투명 이미지, 알파를 분리할 수 없는 입력에서는 자동 경계 측정을 사용할 수 없다고 기록한다. 배경 전체를 캐릭터로 측정한 값을 신뢰하지 않는다.
- 기본 경고 기준 3% 높이 차이와 1.5% 위·아래 이동은 검토를 촉발하는 작업 설정이다. 결과를 통과시키려고 사후 변경하지 않는다. 사용자가 다른 기준을 지정하면 근거와 함께 설정을 기록한다.

## 특징 고정 절차

핵심 특징에 안정된 ID를 부여하고 원본 관찰값을 수정하지 않는다. 예: `jaw_notch_left`, `forehead_moss_pair`, `weapon_left_hand`.

각 특징에 다음을 기록한다.

1. 몸의 어느 부위·면과 해부학적 좌우에 붙는가?
2. 개수, 실루엣과 주변 특징과의 관계는 무엇인가?
3. 원본의 관찰 가능한 2D 영역은 어디인가? 알 수 없는 3D 위치는 추정이라고 표시한다.
4. 목표 방향에서 `visible`, `partial`, `hidden`, `unknown` 중 어떤 상태여야 하는가?
5. 누락·개수 변경·반대편 이동이 중요한 오류인가, 미세한 경계 차이인가?

큰 식별 무늬는 추적하되 파스텔 입자나 모든 미세 균열을 정확히 보존했다고 주장하지 않는다. 한 방향에서 새로 추정한 뒷면은 가정 기록에 고정하고 이후 방향에 일관되게 사용한다.

## 보정 분기

| 관찰된 문제 | 처리 |
| --- | --- |
| 방향이 틀리거나 손·핵심 장비가 바뀜 | 목표 방향과 고정 특징을 재명시해 해당 방향을 수정하고 기준 채택을 보류 |
| 전반적으로 확대되거나 위치만 어긋남 | 대상 + 정면을 참조해 재프레이밍만 수행; 아래 템플릿 사용 |
| 큰 무늬가 누락·복제·반대편으로 이동 | 특징 ID, 몸의 면과 가림을 명시해 해당 부위만 수정 |
| 고립 점·짧은 선·기능 없는 외곽 돌출물 | 위치와 의미를 확인하고 해당 부위만 보정; 기준 채택을 보류하고 관련 방향·프레임 재검사 |
| 작은 입자·경계 변화만 남음 | 남은 차이를 기록하고 허용 가능한지 판단; 자동으로 완전 동일이라고 처리하지 않음 |
| 원근 때문에 알파 경계가 달라짐 | 대응 몸 부위를 확인하고 `explained_by_projection`으로 근거 기록; 강제 변형하지 않음 |

처음 수치 경고를 받았을 때 전체 7방향을 다시 만들지 않는다. 문제 방향만 수정하고 이를 참조했던 대각선을 다시 점검한다. 같은 문제를 반복 수정해도 해결되지 않으면 원본과 최선의 결과, 남은 문제를 보존하고 사용자에게 명확히 알린다.

## 재프레이밍 전용 프롬프트

원본에서 실제 계산한 숫자를 대입한다. 첫 참조는 수정할 방향, 둘째 참조는 정면 원본이다. 보이는 높이 비율을 조정량으로 사용할 때는 원근·포즈 변화가 아닌 실제 배율 오류인지 먼저 확인한다.

```text
Reframe ONLY the first supplied image. Keep its exact target direction, pose,
anatomical sides, equipment, major markings, surface details, palette and texture.
The second supplied image is the immutable front framing reference.
The confirmed issue is {framing_error}, not a character design error.
On the same canvas, adjust the entire character uniformly by approximately
{confirmed_scale_adjustment}, without stretching individual body parts.
Place the visible head/body top near {source_top_percent}% and the verified
body/foot reference near {source_reference_y_percent}% down the canvas.
Preserve {source_bottom_margin_percent}% bottom margin where applicable.
Keep the same body pivot reference; do not center by an asymmetric weapon's
bounding box. Do not auto-zoom the narrower profile to fill the frame.
Do not change the angle, marking topology, number of features or limb connections.
Return one full-body sprite with the same requested background/transparency.
```

보정 후에는 실제 이미지와 수치를 다시 확인한다. 같은 특징을 유지하라고 지시한 것만으로 실제 세부가 불변이라고 판단하지 않는다.

## 관찰 사례: 골렘의 확대 문제와 잔여 차이

실제 정면 1장과 7방향 생성 테스트의 측정 기록이다. 원본·출력 모두 1254×1254였고, 알파 값 16 초과 영역의 경계를 비교했다.

| 항목 | 보이는 높이 | 알파 최하단 y | 정면 대비 |
| --- | ---: | ---: | --- |
| 정면 원본 | 963 px | 1082 px | 기준 |
| 최초 왼쪽 측면 | 1066 px | 1159 px | 높이 +10.70%, 아래끝 +77 px |
| 재프레이밍 후 측면 | 971 px | 1099 px | 높이 +0.83%, 아래끝 +17 px |

- 생성 도구에 전체 캐릭터를 약 10% 줄이고 원본의 상대 위·아래 위치로 옮기도록 지시한 추가 호출 1회로 큰 확대 문제를 줄였다. 보정 결과의 원본 대비 차이는 0이 아니었다.
- 최종 8장에서는 정면 대비 보이는 높이 차이가 최대 4.47%, 알파 최하단 범위가 1077~1113으로 36 px였다. 이 값은 실제 발 접점이나 게임 피벗을 계측한 결과가 아니다.
- 전체 화풍과 종족은 유지됐지만 이끼 경계와 작은 균열·마디는 달라졌다. 반복 참조만으로 세부 무늬가 자동 고정되지 않았다.
- 후면은 관찰 정보가 없어 최소한으로 이어 그린 설계 가정이다. 실제 원형의 복원이라고 설명하지 않는다.
- 당시에는 모든 세부 차이를 해결하지 않았다. 이 예제를 완벽한 동일성이나 개선된 생성 성능의 증거로 사용하지 않는다.

