# test-specific: NE auto wing mask leaked into the ear/head junction (cream fur + outline between right ear and head),
# which made that fur move with the wing and opened a visible seam. Remove fur-colored pixels (dilated) in the
# upper-center band; keep the large wing components.
import cv2,numpy as np,sys
from scipy import ndimage as nd
sys.path.insert(0,'../../eight-dir-idle-sprites/scripts'); import make_masks as M
d='NE'; im=M.load(f'input/{d}.png'); m=cv2.imread(f'masks/{d}_wing.png',0)>127
a=im[...,3]>16; ys=np.where(a.any(1))[0]; xs=np.where(a.any(0))[0]
top,bot=ys[0],ys[-1]; H=bot-top; cx=(xs[0]+xs[-1])//2; W=xs[-1]-xs[0]
hsv=cv2.cvtColor(np.ascontiguousarray(im[...,:3]),cv2.COLOR_BGR2HSV)
fur=(hsv[...,1]<90)&(hsv[...,2]>170)
band=np.zeros_like(m); band[top:int(top+0.45*H), int(cx-0.05*W):int(cx+0.17*W)]=True
before=int(m.sum()); m=m&~nd.binary_dilation(fur&band,iterations=5)
lab,n=nd.label(m); sz=nd.sum(m,lab,range(1,n+1)); m=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>8000])
cv2.imwrite(f'masks/{d}_wing.png',(m*255).astype(np.uint8)); M.overlay(im,m,f'masks/{d}_wing_overlay.png'); print(d,before,int(m.sum()))
