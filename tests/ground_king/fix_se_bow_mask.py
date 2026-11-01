# test-specific: SE bow mask originally covered only the upper limb above the hand.
# Add the lower limb (brown component below the hand) and the string so the whole bow moves rigidly.
import cv2,numpy as np,sys
from scipy import ndimage as nd
sys.path.insert(0,'../../eight-dir-idle-sprites/scripts'); import make_masks as M
im=M.load('input/SE.png'); a=im[...,3]>16
m0=cv2.imread('masks/SE_bow.png',0)>127
hsv=cv2.cvtColor(np.ascontiguousarray(im[...,:3]),cv2.COLOR_BGR2HSV)
brown=(hsv[...,0]>=3)&(hsv[...,0]<=22)&(hsv[...,1]>90)&(hsv[...,2]<200)&a
brown[:600]=False; brown[:, :676]=False
lab,n=nd.label(nd.binary_closing(brown,iterations=2)); sl=nd.find_objects(lab)
cands=[i for i in range(n) if sl[i][1].stop>740 and (lab[sl[i]]==i+1).sum()>500]
low=lab==max(cands,key=lambda i:sl[i][0].stop-sl[i][0].start)+1
# string: light thin pixels near the line from upper tip to lower tip
yy,xx=np.mgrid[:a.shape[0],:a.shape[1]]
ys,xs=np.where(m0); t=(int(xs[ys.argmin()]),int(ys.min()))
ly,lx=np.where(low); b=(int(lx[ly.argmax()]),int(ly.max()))
d=np.abs((b[1]-t[1])*(xx-t[0])-(b[0]-t[0])*(yy-t[1]))/np.hypot(b[0]-t[0],b[1]-t[1])
string=(d<6)&a&(yy>=t[1])&(yy<=b[1])&(hsv[...,1]<80)&(hsv[...,2]>150)
m=nd.binary_closing(m0|low|string,iterations=2)
cv2.imwrite('masks/SE_bow.png',(m*255).astype(np.uint8)); M.overlay(im,m,'masks/SE_bow_overlay.png')
print(int(m0.sum()),int(m.sum()),t,b)
