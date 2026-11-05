"""Copy light test artifacts into tests/<case>/results/<run>/ (256 px frames cut from the atlas)."""
import json, shutil, sys, os
from PIL import Image
case, run, dst = sys.argv[1], sys.argv[2], sys.argv[3]
src = os.path.join(case, run); out = os.path.join(case, 'results', dst)
os.makedirs(out, exist_ok=True)
for f in ['atlas_256.png','atlas_manifest.json','qa_report.md','qa_report.json','transforms.json','same_phase_sheet.png','game_size_strip.png']:
    if os.path.exists(os.path.join(src,f)): shutil.copy(os.path.join(src,f), out)
m = json.load(open(os.path.join(src,'atlas_manifest.json')))
atlas = Image.open(os.path.join(src,'atlas_256.png'))
dirs = m['rows_directions']; n = m['frames_per_row']
for r, d in enumerate(dirs):
    os.makedirs(os.path.join(out,'frames_256',d), exist_ok=True)
    if 'frame_rects' in m:
        rects = m['frame_rects'][d]
    else:
        cell = m.get('cell', [m.get('cell_px', 256)] * 2)
        rects = [[c * cell[0], r * cell[1], *cell] for c in range(n)]
    fr = [atlas.crop((x, y, x + w, y + h)) for x, y, w, h in rects]
    for c, im in enumerate(fr): im.save(os.path.join(out,'frames_256',d,f'{d}_{c:03d}.png'))
    bg = [Image.alpha_composite(Image.new('RGBA', im.size, (64,64,96,255)), im).convert('P', palette=Image.ADAPTIVE) for im in fr]
    dur = [[40,40,50][i%3] for i in range(n)]
    bg[0].save(os.path.join(out,f'preview_{d}.gif'), save_all=True, append_images=bg[1:], duration=dur, loop=0, disposal=2)
print(out, n, dirs)
