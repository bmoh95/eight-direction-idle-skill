# test-specific cleanup of auto wing masks:
#  NW/NE: remove cream foot/fur pixels in the lower body band; open to drop thin edge slivers
#  SE: keep only the main (near) wing; far-wing piece behind the ear stays static with the body
import cv2,numpy as np,sys
from scipy import ndimage as nd
sys.path.insert(0,'../../eight-dir-idle-sprites/scripts'); import make_masks as M
for d in ['NW','NE','SE']:
    im=M.load(f'input/{d}.png'); m=cv2.imread(f'masks/{d}_wing.png',0)>127
    if d=='SE':
        lab,n=nd.label(m); sz=nd.sum(m,lab,range(1,n+1)); m=lab==int(np.argmax(sz))+1
        a=im[...,3]>16; ys=np.where(a.any(1))[0]; top,bot=ys[0],ys[-1]; H=bot-top
        hsv=cv2.cvtColor(np.ascontiguousarray(im[...,:3]),cv2.COLOR_BGR2HSV)
        fur=(hsv[...,1]<90)&(hsv[...,2]>170); band=np.zeros_like(m); xs=np.where(a.any(0))[0]; band[int(top+0.6*H):, int(xs[0]+0.58*(xs[-1]-xs[0])):]=True
        m=m&~nd.binary_dilation(fur&band,iterations=6)
        lab,n=nd.label(m); sz=nd.sum(m,lab,range(1,n+1)); m=lab==int(np.argmax(sz))+1
    else:
        a=im[...,3]>16; ys=np.where(a.any(1))[0]; xs=np.where(a.any(0))[0]
        top,bot=ys[0],ys[-1]; H=bot-top; cx=(xs[0]+xs[-1])//2; W=xs[-1]-xs[0]
        hsv=cv2.cvtColor(np.ascontiguousarray(im[...,:3]),cv2.COLOR_BGR2HSV)
        fur=(hsv[...,1]<90)&(hsv[...,2]>170)
        band=np.zeros_like(m); band[int(top+0.72*H):, int(cx-0.32*W):int(cx+0.32*W)]=True
        feet=nd.binary_dilation(fur&band,iterations=4)
        m=m&~feet
        m=nd.binary_opening(m,structure=np.ones((3,3)),iterations=7)
        lab,n=nd.label(m); sz=nd.sum(m,lab,range(1,n+1)); m=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>8000])
    cv2.imwrite(f'masks/{d}_wing.png',(m*255).astype(np.uint8)); M.overlay(im,m,f'masks/{d}_wing_overlay.png'); print(d,int(m.sum()))
