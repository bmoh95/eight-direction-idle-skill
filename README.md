# 8방향 캐릭터 이미지 스킬

캐릭터나 몬스터의 기준 이미지를 바탕으로 정면부터 남서·서·북서·북·북동·동·남동까지 일관된 8방향 이미지를 생성하고 검수합니다. 기존 저장소 및 스킬 경로는 호환성을 위해 유지합니다.

## 설치

```bash
git clone https://github.com/bmoh95/eight-direction-idle-skill.git
cd eight-direction-idle-skill
cp -r eight-dir-idle-sprites ~/.claude/skills/
pip install -r eight-dir-idle-sprites/scripts/requirements.txt
```

Rakazo에서는 **Integrations → + → From GitHub**에서 저장소 URL을 입력합니다. 플러그인은 지침만 설치하며 이미지 생성 도구와 Python 스크립트를 포함하지 않습니다. 이미지 생성에는 참조 이미지를 받을 수 있는 생성·편집 도구가 필요합니다.

## 작업 흐름

1. 기준 이미지와 화풍, 카메라, 소품의 해부학적 좌우 손을 확인합니다. 텍스트만 있으면 정면 전신 기준 이미지를 먼저 만듭니다.
2. 기준 이미지를 고정하고 요청한 방향을 생성합니다. 기준 방향을 반복 참조하며 실루엣, 비율, 얼굴, 무기와 가려진 뒷면을 검수합니다.
3. 투명 배경이 필요한 경우 원본 알파를 우선 사용합니다. 단색 배경일 때는 아래 배경 제거 절차를 사용합니다.
4. 방향별 PNG와 검수 결과를 전달합니다. 완성된 8방향 세트는 S, SW, W, NW, N, NE, E, SE 순서입니다.

기본 그림체는 `eight-dir-idle-sprites/assets/styles/`의 샘플입니다. 사용자가 기준 이미지의 화풍을 유지하도록 요청하면 해당 이미지를 우선합니다. 전체 지침은 `eight-dir-idle-sprites/SKILL.md`를 참고하세요.

## 배경 제거

```bash
pip install -r eight-dir-idle-sprites/scripts/requirements-ml.txt
python3 eight-dir-idle-sprites/scripts/cutout.py raw.png result.png
python3 eight-dir-idle-sprites/scripts/cutout.py --check result.png
```

기본 엔진은 `rembg`의 `birefnet-general`입니다. 소품 내부의 배경을 확인할 때는 `--prop-mask`를 사용할 수 있습니다. 모델별 한계와 대체 엔진은 `eight-dir-idle-sprites/references/cutout-engines.md`를 참고하세요. 밝고 어두운 배경에서 윤곽과 소품 틈을 확대해 확인합니다.

## 요청 양식과 검수 도구

- 브라우저에서 `eight-dir-idle-sprites/index.html`을 열면 요청 문구를 만들 수 있습니다.
- `python3 eight-dir-idle-sprites/scripts/options.py --lang ko`로 옵션을 확인할 수 있습니다.
- `scripts/measure_sprite_framing.py`와 `scripts/style_check.py`는 크기·배치와 화풍 검수를 돕습니다. 자동 결과와 함께 방향별 이미지를 직접 비교해야 합니다.
