# test-specific helper: bow = tallest brown component whose centroid is below the crown zone
import cv2,numpy as np,sys
from scipy import ndimage as nd
sys.path.insert(0,'../../eight-dir-idle-sprites/scripts'); import make_masks as M
for d in "S SW W NW N NE E SE".split():
    im=M.load(f'input/{d}.png'); a=im[...,3]>16
    ys=np.where(a.any(1))[0]; top,bot=int(ys[0]),int(ys[-1]); H=bot-top
    m=M.color_mask(im,(5,110,40),(18,255,215),(0,top,1024,int(bot-0.12*H)))
    m=nd.binary_closing(m,iterations=2); lab,n=nd.label(m); sl=nd.find_objects(lab)
    def score(i):
        c=lab[sl[i]]==i+1; cy=sl[i][0].start+np.argwhere(c)[:,0].mean()
        return (sl[i][0].stop-sl[i][0].start) if c.sum()>800 and cy>top+0.3*H else 0
    m=lab==max(range(n),key=score)+1
    cv2.imwrite(f'masks/{d}_bow.png',(m*255).astype(np.uint8)); M.overlay(im,m,f'masks/{d}_bow_overlay.png'); print(d,int(m.sum()))
