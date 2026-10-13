#!/usr/bin/env python3
"""Faithful, partly raster reconstruction of ../图片.png. Run from any cwd."""
from pathlib import Path
import base64, hashlib, json, xml.etree.ElementTree as E
from PIL import Image
OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'图片.png'
OUT.mkdir(exist_ok=True)
(OUT/'assets').mkdir(exist_ok=True)
W,H=2011,1021
WIDTH=14
BG='#f4f8ff'; CREAM='#fffdf6'; BLUE='#9bbbd8'; OUTLINE='#6396c6'; PURPLE='#b691bc'
SERIF='Liberation Serif'; HAND='Comic Neue'; MATH='TeX Gyre Termes'
E.register_namespace('', 'http://www.w3.org/2000/svg')
E.register_namespace('xlink','http://www.w3.org/1999/xlink')
NS='{http://www.w3.org/2000/svg}'
root=E.Element(NS+'svg',{'viewBox':f'0 0 {W} {H}','width':f'{WIDTH}in','height':f'{WIDTH*H/W}in','version':'1.1'})
E.SubElement(root,NS+'title').text='Batman: alignment in malicious null space — reconstructed reference figure'
E.SubElement(root,NS+'desc').text='Editable labels, diagrams, equations, networks, and connectors. Detailed illustrations and data photographs are cropped raster assets from the supplied reference.'
def el(tag,parent=None,**attrs):
    return E.SubElement(root if parent is None else parent,NS+tag,{k.replace('_','-'):str(v) for k,v in attrs.items() if v is not None})
def group(id): return el('g',id=id)
def rect(p,x,y,w,h,fill='none',stroke='none',sw=1,rx=0,id=None,**kw):
    return el('rect',p,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=sw,rx=rx,id=id,**kw)
def path(p,d,fill='none',stroke='black',sw=2,**kw): return el('path',p,d=d,fill=fill,stroke=stroke,stroke_width=sw,**kw)
def line(p,x1,y1,x2,y2,color='black',sw=2,**kw): return el('line',p,x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,stroke_width=sw,**kw)
def ellipse(p,x,y,rx,ry,fill,stroke='none',sw=1,**kw): return el('ellipse',p,cx=x,cy=y,rx=rx,ry=ry,fill=fill,stroke=stroke,stroke_width=sw,**kw)
labels=[]; assets=[]; edges=[]
def text(p,id,x,y,s,size=30,font=HAND,fill='black',weight='normal',anchor='start',italic=False,**kw):
    t=el('text',p,id=id,x=x,y=y,font_family=font,font_size=size,font_weight=weight,text_anchor=anchor,fill=fill,font_style='italic' if italic else 'normal',**kw)
    t.text=s
    labels.append({'id':id,'parent':p.get('id'),'text':s,'position':[x,y],'font_size':size,'font_family':font,'alignment':anchor,'fill':fill})
    return t
def math(p,id,x,y,parts,size=34,anchor='start'):
    t=text(p,id,x,y,'',size,MATH,anchor=anchor)
    previous=None
    for s,shift,scale,italic in parts:
        sp=E.SubElement(t,NS+'tspan',{'baseline-shift':shift,'font-size':str(size*scale),'font-style':'italic' if italic else 'normal'})
        if shift == 'super' and previous and previous[1] == 'sub':
            sp.set('dx', str(-size*previous[2]*.5*len(previous[0])))
        sp.text=s
        previous=(s,shift,scale,italic)
    if id == 'null-projector':
        sp.set('font-weight','bold')
    labels[-1]['text']=''.join(a[0] for a in parts)
    labels[-1]['math_runs']=parts
    return t
D=el('defs')
for name,col in [('black','black'),('purple','#6a486e'),('gray','#cfcecd'),('brown','#b37a47'),('teal','#a3c3c4'),('gold','#ecb03d')]:
    m=el('marker',D,id='arrow-'+name,viewBox='0 0 10 10',refX=8,refY=5,markerWidth=3 if name=='gray' else 5,markerHeight=3 if name=='gray' else 5,orient='auto-start-reverse')
    path(m,'M 0 0 L 10 5 L 0 10 Z',col,'none')
for id,stops,x2,y2 in [('attack-gradient',[(0,'#b693be'),(1,'#fff0bd')],0,1),('align-gradient',[(0,'#eeeaea'),(1,'#ab87b5')],1,0),('gap-gradient',[(0,'#f4f8ff'),(.5,'#cbd7ed'),(1,'#f4f8ff')],1,0)]:
    gr=el('linearGradient',D,id=id,x1='0%',y1='0%',x2=f'{x2*100}%',y2=f'{y2*100}%')
    for off,col in stops: el('stop',gr,offset=f'{off*100}%',stop_color=col)
pat=el('pattern',D,id='diagonal-hatch',width=11,height=11,patternUnits='userSpaceOnUse')
rect(pat,0,0,11,11,'#ffffff')
path(pat,'M -3 3 L 3 -3 M 0 11 L 11 0 M 8 14 L 14 8','none','#cbdce5',4)
pat=el('pattern',D,id='cross-hatch',width=7,height=7,patternUnits='userSpaceOnUse')
rect(pat,0,0,7,7,'#d9e8cf')
path(pat,'M 0 0 L 7 7 M 7 0 L 0 7','none','#f5f8ef',1.5)
source=Image.open(SRC).convert('RGBA')
# Raster details only: no panel labels, arrows, matrices, or equations.
crops={
'batman':(55,41,182,148), 'poisoned-photos':(111,235,287,394), 'clean-photos':(111,511,286,665),
'malicious-book':(522,57,606,151), 'benign-book':(543,477,627,560),
'sleeping':(1101,219,1163,280), 'working':(1101,383,1163,445),
'distribute':(87,905,173,996), 'aggregate':(235,870,308,946)}
for name,box in crops.items():
    crop=source.crop(box)
    if name not in ('poisoned-photos','clean-photos'):
        # Remove near-uniform pale backdrop; preserve original antialiasing/illustration.
        px=crop.load()
        bg=(244,248,255) if name not in ('distribute','aggregate') else (250,253,253)
        for yy in range(crop.height):
            for xx in range(crop.width):
                r,g,b,a=px[xx,yy]
                if max(abs(r-bg[0]),abs(g-bg[1]),abs(b-bg[2]))<23:
                    px[xx,yy]=(r,g,b,0)
    if name in ('malicious-book','benign-book'):
        for yy in range(min(18,crop.height)):
            for xx in range(crop.width):
                r,g,b,a=px[xx,yy]
                if max(r,g,b)-min(r,g,b)<19 and min(r,g,b)>115:
                    px[xx,yy]=(r,g,b,0)
    crop.save(OUT/'assets'/f'{name}.png')
    assets.append({'id':name,'file':f'assets/{name}.png','source_crop':box,'pixel_size':crop.size,'treatment':'original raster crop; near-background transparency for icons'})
def pic(p,name,x,y,w,h,id=None):
    b64=base64.b64encode((OUT/'assets'/f'{name}.png').read_bytes()).decode()
    node=el('image',p,id=id or name+'-image',x=x,y=y,width=w,height=h,preserveAspectRatio='xMidYMid meet')
    node.set('{http://www.w3.org/1999/xlink}href','data:image/png;base64,'+b64)
    return node
def blockarrow(p,id,x,y,length=90,height=40,color='#7e91ba',stroke='none'):
    d=f'M {x} {y-height*.23} H {x+length*.60} V {y-height*.5} L {x+length} {y} L {x+length*.60} {y+height*.5} V {y+height*.23} H {x} Z'
    return path(p,d,color,stroke,3,id=id)
def network(p,id,x,y,s,color):
    g=el('g',p,id=id)
    pts=[(0,.23),(0,.72),(.5,0),(.5,.48),(.5,.96),(1,.23),(1,.72)]
    for a,b in [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4),(2,5),(2,6),(3,5),(3,6),(4,5),(4,6)]:
        line(g,x+pts[a][0]*s,y+pts[a][1]*s,x+pts[b][0]*s,y+pts[b][1]*s,'#111111',4)
    for xx,yy in pts: ellipse(g,x+xx*s,y+yy*s,12,12,color,'#101010',4.5)
    return g

g=group('background')
rect(g,0,0,W,H,'white')
rect(g,47,33,1927,798,BG,'#a2afb9',3.5,9)
rect(g,47,845,1927,161,'#fcfefe','#858585',3,9,stroke_dasharray='14 10')
line(g,1172,846,1172,1005,'#858585',3,stroke_dasharray='14 10')

p=group('attacker-client')
pic(p,'batman',55,41,127,107)
text(p,'batman-title',160,108,'Batman',55,SERIF,'#636c68','bold',italic=True)
line(p,160,115,344,115,'#636c68',3)
rect(p,78,199,237,540,'white','#858585',3.4,24,stroke_dasharray='14 10')
line(p,78,469,315,469,'#858585',3,stroke_dasharray='13 5')
pic(p,'poisoned-photos',111,235,176,159)
pic(p,'clean-photos',111,511,175,154)
text(p,'poisoned-data',199,430,'Poisoned Data',32,HAND,'#c00000','bold',anchor='middle')
text(p,'clean-data',198,709,'Clean Data',32,HAND,weight='bold',anchor='middle')
text(p,'attacker-label',211,797,'Attacker Client',38,SERIF,'#888888','bold',anchor='middle')

p=group('malicious-knowledge')
rect(p,388,65,781,394,'none','#a6a6a6',3.5,18)
pic(p,'malicious-book',522,57,84,94)
text(p,'malicious-title',628,119,'Malicious Knowledge',42,SERIF,weight='bold')
text(p,'malicious-parameter',448,187,'Malicious Parameter',28,HAND,'#a7a7a7')
rect(p,433,204,469,209,'none','#aaa',2)
# SVD blocks are separate editable shapes.
clip=el('clipPath',D,id='clip-svd-left');rect(clip,452,217,115,150,rx=21)
rect(p,452,217,115,150,BLUE,OUTLINE,3.5,21)
rect(p,511,217,56,150,'url(#diagonal-hatch)',clip_path='url(#clip-svd-left)')
rect(p,452,217,115,150,'none',OUTLINE,3.5,21)
clip=el('clipPath',D,id='clip-svd-mid');rect(clip,588,231,119,118,rx=10)
rect(p,588,231,119,118,BG,OUTLINE,3,10)
rect(p,589,232,59,58,BLUE,clip_path='url(#clip-svd-mid)')
rect(p,648,290,59,59,'url(#diagonal-hatch)',clip_path='url(#clip-svd-mid)')
rect(p,588,231,119,118,'none',OUTLINE,3,10)
clip=el('clipPath',D,id='clip-svd-right');rect(clip,725,229,157,121,rx=10)
rect(p,725,229,157,121,BLUE,OUTLINE,3.5,10)
rect(p,725,290,157,60,'url(#diagonal-hatch)',clip_path='url(#clip-svd-right)')
rect(p,725,229,157,121,'none',OUTLINE,3.5,10)
text(p,'svd-label',672,403,'Singular Value Decomposition',32,HAND,weight='bold',anchor='middle')
text(p,'decomposition-equals',929,315,'=',64,SERIF,anchor='middle')
rect(p,952,153,200,118,'url(#diagonal-hatch)','#b0d3dc',3.5,14)
text(p,'redundant-title',962,183,'Redundant',31,HAND,BLUE,'bold')
rect(p,954,190,108,21,'url(#cross-hatch)')
rect(p,954,213,73,21,'#baa0c0')
text(p,'redundant-no-svd',1070,208,'No SVD',21,HAND,BLUE,italic=True)
text(p,'redundant-svd',1042,236,'SVD',21,HAND,BLUE,italic=True)
line(p,1023,223,969,223,'#ffd28e',2,marker_end='url(#arrow-gold)')
text(p,'tac-decrease-prefix',962,264,'TAC',23,HAND,weight='bold')
text(p,'tac-decrease',1009,264,'Decrease',21,HAND,'#609126','bold')
pic(p,'sleeping',1101,219,62,61)
text(p,'decomposition-plus',1046,310,'+',56,SERIF,weight='bold',anchor='middle')
rect(p,951,311,202,117,BLUE,OUTLINE,3.5,13)
text(p,'important-title',964,342,'Important',31,HAND,'white','bold')
rect(p,954,350,85,18,'url(#cross-hatch)')
rect(p,954,372,116,18,'#ad88b6')
text(p,'important-no-svd',1047,365,'No SVD',20,HAND,'white',italic=True)
text(p,'important-svd',1076,387,'SVD',20,HAND,'white',italic=True)
line(p,980,380,1066,380,'#ffcd85',2.5,marker_end='url(#arrow-gold)')
text(p,'tac-increase-prefix',963,421,'TAC',23,HAND,weight='bold')
text(p,'tac-increase',1010,421,'Increase',21,HAND,'#bd6513','bold')
pic(p,'working',1101,383,62,62)

p=group('benign-knowledge')
rect(p,388,488,785,320,'none','#a6a6a6',3.5,19)
pic(p,'benign-book',544,477,84,83)
text(p,'benign-title',651,540,'Benign Knowledge',42,SERIF,weight='bold')
text(p,'clean-model-label',480,589,'Clean model',31,HAND,anchor='middle')
network(p,'clean-network',459,611,81,'#aed490')
rect(p,577,585,148,48,'url(#gap-gradient)')
rect(p,593,586,31,95,BLUE,'#4e70a5',2.5)
rect(p,673,633,29,48,BLUE,'#4e70a5',2.5)
path(p,'M 573 568 V 682 H 720','none','black',4,marker_end='url(#arrow-black)')
line(p,573,680,573,567,'black',3,marker_end='url(#arrow-black)')
text(p,'clean-gap',640,619,'Gap',37,HAND,'#565e65','bold',italic=True)
text(p,'truth-label-1',609,715,'Truth',27,HAND,'#76af3e',anchor='middle')
text(p,'truth-label-2',609,745,'Label',27,HAND,'#76af3e',anchor='middle')
text(p,'attack-label-1',700,715,'Attack',27,HAND,'#ad68b4',anchor='middle')
text(p,'attack-label-2',700,745,'Label',27,HAND,'#ad68b4',anchor='middle')
line(p,728,565,777,801,'#8b8b8b',5,stroke_dasharray='20 13')
text(p,'clean-parameter-label',608,788,'Clean Parameter',35,HAND,weight='bold',anchor='middle')
rect(p,774,648,379,51,'url(#gap-gradient)')
path(p,'M 822 696 Q 850 628 841 584 M 822 696 Q 883 679 902 624 M 822 696 Q 885 745 977 725','none','#aaaaaa',1.5)
line(p,844,689,984,632,'black',1,marker_end='url(#arrow-black)')
ellipse(p,841,584,26,24,'#e9f2e0','black',2.5)
ellipse(p,902,623,26,24,'#e9f2e0','black',2.5)
ellipse(p,822,698,38,34,BG,'black',2.5)
ellipse(p,977,725,26,24,'#d1bdd6','black',2.5)
for id,x,y in [('w-benign-a',841,595),('w-benign-b',902,634),('w-attack',977,736)]: text(p,id,x,y,'W',34,MATH,anchor='middle')
math(p,'previous-global-weight',822,708,[('W','baseline',1,True),('g','sub',.7,False),('t−1','super',.7,False)],32,'middle')
text(p,'benign-clients-label',749,630,'Benign',30,HAND,'#70ad43')
text(p,'attack-clients-label',1018,734,'Attack',31,HAND,'#a16daf')
text(p,'global-gap',978,687,'Gap',37,HAND,'#565e65','bold',italic=True)
network(p,'updated-global-network',1002,566,81,'#ffda62')
math(p,'updated-global-weight',1107,586,[('W','baseline',1,False),('g','sub',.7,False),('t','super',.7,False)],34)
text(p,'global-parameter-label',971,788,'Global Parameter',35,HAND,weight='bold',anchor='middle')

p=group('alignment-panel')
rect(p,1254,61,684,753,CREAM,'#837d70',3.5,27)
text(p,'alignment-title',1596,117,'Alignment in Malicious Null Space',41,SERIF,weight='bold',anchor='middle')
# Performance before and after: axes and illustrative regions, no numeric data implied.
for id,x,after in [('before',1316,False),('after',1685,True)]:
    text(p,id+'-performance-label',x+79,174,'Attack Performance',29,HAND,anchor='middle')
    rect(p,x-34,201,16,177,'url(#attack-gradient)','#918b84',1.5)
    path(p,f'M {x} 200 V 381 H {x+231}','none','black',4.5,marker_end='url(#arrow-black)')
    line(p,x,381,x,200,'black',4,marker_end='url(#arrow-black)')
    line(p,x+2,231,x+163,231,'#b593c0',2,stroke_dasharray='9 7')
    # Small dagger indicator remains vector.
    path(p,f'M {x+14} 220 Q {x+3} 231 {x+14} 243 L {x+19} 243 Q {x+11} 232 {x+19} 220 Z M {x+11} 229 H {x+31} V 234 H {x+11} Z', '#d6bfd8','#312635',1.2)
    ellipse(p,x+32,231,2.5,5,'#d6bfd8','#312635',1)
    if not after:
        ellipse(p,x+70,325,58,47,'#fce9bc')
        ellipse(p,x+168,230,57,47,'#bc99c4')
        pic(p,'malicious-book',x+134,190,68,76,id+'-malicious-icon')
        pic(p,'benign-book',x+32,282,73,72,id+'-benign-icon')
        line(p,x+157,270,x+110,323,'#a87651',5,marker_end='url(#arrow-brown)')
        text(p,'initial-delta',x+111,287,'Δ',31,MATH)
    else:
        path(p,f'M {x+73} 200 C {x+145} 172 {x+163} 215 {x+143} 264 C {x+119} 300 {x+164} 321 {x+116} 342 C {x+47} 382 {x+2} 367 {x+10} 318 C {x+15} 270 {x+75} 259 {x+60} 230 Z','url(#attack-gradient)','none')
        pic(p,'malicious-book',x+69,189,68,76,id+'-malicious-icon')
        pic(p,'benign-book',x+23,276,73,72,id+'-benign-icon')
        # Dashed ghost book is native linework.
        path(p,f'M {x+188} 241 L {x+180} 254 L {x+202} 262 L {x+214} 258 L {x+227} 238 L {x+208} 242 L {x+201} 255 Z M {x+182} 228 Q {x+175} 213 {x+187} 202 Q {x+197} 183 {x+210} 200 Q {x+233} 197 {x+227} 223 Q {x+211} 232 {x+206} 241','none','#bb87cb',1.8,stroke_dasharray='6 5')
        line(p,x+173,230,x+139,230,'#6a486e',3,marker_end='url(#arrow-purple)')
        math(p,'projected-delta',x+135,220,[('Δ','baseline',1,False),('P','baseline',1,True)],34)
    text(p,id+'-parameter-label',x+119,415,'Parameter Space',29,HAND,anchor='middle')
    ellipse(p,x+49 if not after else x+41,358 if not after else 350,9,9,'#ffdf55')
    cx=x+49 if not after else x+41;cy=358 if not after else 350
    ellipse(p,cx-3,cy-2,1.1,1.7,'#805f21');ellipse(p,cx+3,cy-2,1.1,1.7,'#805f21')
    path(p,f'M {cx-4} {cy+2} Q {cx} {cy+7} {cx+4} {cy+2}','none','#805f21',1.5)
line(p,1548,233,1653,233,'#dc0000',2,stroke_dasharray='9 6 2 6')
text(p,'keep-label',1574,257,'Keep',29,HAND,'#d40000')
path(p,'M 1563 286 H 1620 V 274 L 1645 299 L 1620 324 V 311 H 1563 L 1575 299 Z','url(#align-gradient)','#aea5b3',2.5)
text(p,'eq6',1916,435,'Eq. (6)',20,SERIF,'#888888',anchor='end')
# Two gray arrows connect the performance drawings with the null-space inset.
path(p,'M 1417 445 Q 1460 433 1485 495','none','#d0cfcd',10,marker_end='url(#arrow-gray)')
path(p,'M 1706 504 Q 1759 522 1771 449','none','#d0cfcd',10,marker_end='url(#arrow-gray)')
text(p,'projection-delta-label',1613,496,'Projection Δ',28,HAND,anchor='middle')
rect(p,1284,519,631,264,'none','black',3.5,19,stroke_dasharray='14 10')
rect(p,1290,485,235,75,'#f5e7d0',rx=12)
text(p,'null-space-title',1407,538,'Null Space',42,SERIF,weight='bold',anchor='middle')
ellipse(p,1355,651,49,47,'#bc99c4')
pic(p,'malicious-book',1322,612,67,76,'null-malicious-icon')
text(p,'null-svd-label',1357,739,'SVD',32,HAND,anchor='middle')
text(p,'singular-value-label',1536,584,'Singular Value',32,HAND,weight='bold',anchor='middle')
# Braces and diagonal matrix marks are editable vector paths/text.
path(p,'M 1452 597 Q 1436 597 1436 611 V 653 Q 1436 668 1423 670 Q 1436 672 1436 687 V 728 Q 1436 743 1452 743','none','black',3)
path(p,'M 1599 598 Q 1615 598 1615 613 V 656 Q 1615 671 1629 673 Q 1615 675 1615 690 V 728 Q 1615 743 1599 743','none','black',3)
math(p,'singular-x1',1446,617,[('x','baseline',1,True),('1','sub',.72,False)],33)
text(p,'singular-ellipsis',1481,641,'⋱',32,MATH)
math(p,'singular-xn',1463,655,[('x','baseline',1,True),('n','sub',.72,False)],33)
rect(p,1529,665,72,76,'#f2e4f4','#b18cbe',3.5,stroke_dasharray='14 7 3 7')
text(p,'zero-top',1534,698,'0',33,MATH)
text(p,'zero-ellipsis',1547,718,'⋱',29,MATH)
text(p,'zero-bottom',1572,729,'0',33,MATH)
math(p,'null-projector',1661,607,[('Ũ','baseline',1,True),('0','sub',.65,False),('Ũ','baseline',1,True),('0','sub',.65,False),('T','super',.65,True),(' = ','baseline',1,False),('P','baseline',1.3,True)],40)
path(p,'M 1662 733 L 1725 681 L 1900 685 L 1838 738 Z','#bdacc2','none')
line(p,1747,699,1747,649,'#eab348',3,stroke_dasharray='12 7',marker_end='url(#arrow-gold)')
line(p,1854,701,1749,648,'#ae784c',4,marker_end='url(#arrow-brown)')
line(p,1854,702,1750,700,'#735378',4,marker_end='url(#arrow-purple)')
path(p,'M 1578 755 C 1619 773 1664 739 1646 738 C 1618 735 1665 770 1706 749','none','#9d889f',3,marker_end='url(#arrow-purple)')
text(p,'eq4',1878,713,'Eq. (4)',20,SERIF,'#888888',anchor='end')

p=group('inter-panel-flows')
for id,x,y,length,height,col,src,dst,kind in [
('poison-training',327,315,95,47,'#7d91bb','poisoned-data','malicious-parameter','training'),
('clean-training',328,644,109,47,'#7d91bb','clean-data','clean-model-label','training'),
('malicious-parameter-flow',1155,373,101,47,'#f2ce92','important-title','alignment-panel','parameter'),
('benign-parameter-flow',1183,637,72,47,'#f2ce92','global-parameter-label','alignment-panel','parameter')]:
    blockarrow(p,id,x,y,length,height,col)
    edges.append({'id':id,'from':src,'to':dst,'type':kind,'points':[[x,y],[x+length,y]],'source_anchor':f'reference pixels near ({x},{y})'})
text(p,'eq3',1203,284,'Eq. (3)',20,SERIF,'#888888')
text(p,'eq5',1203,614,'Eq. (5)',20,SERIF,'#888888')

p=group('federated-training')
text(p,'distribute-label',56,901,'Distribute',31,HAND,weight='bold')
pic(p,'distribute',87,905,86,91)
pic(p,'aggregate',235,870,73,76)
text(p,'aggregate-label',311,955,'Aggregate',33,HAND,weight='bold')
path(p,'M 906 979 H 203 V 807','none','#a3c3c4',3.5,marker_end='url(#arrow-teal)')
line(p,228,804,228,968,'#a3c3c4',3.5,marker_end='url(#arrow-teal)')
for id,x in [('one',491),('two',813)]:
    line(p,x,918,x,968,'#a3c3c4',3.5,marker_end='url(#arrow-teal)')
for id,x in [('one',513),('two',781)]:
    line(p,x,977,x,918,'#a3c3c4',3.5,marker_end='url(#arrow-teal)')
text(p,'benign-client-one',411,897,'Benign Client',38,SERIF,'#888888','bold')
text(p,'benign-client-two',674,899,'Benign Client',38,SERIF,'#888888','bold')
text(p,'clients-ellipsis',648,954,'⋯',66,MATH,'#cfcecd',anchor='middle')
network(p,'global-model-network',984,871,81,'#ffda62')
text(p,'global-model-label',1034,992,'Global model',41,HAND,weight='bold',anchor='middle')

p=group('legend')
path(p,'M 1207 881 H 1265 V 869 L 1285 891 L 1265 912 V 901 H 1207 L 1218 891 Z','url(#align-gradient)','#aaa1b0',2.5)
blockarrow(p,'legend-projection-arrow',1207,948,84,40,'#cecdcc')
blockarrow(p,'legend-training-arrow',1557,890,83,39,'#7d91bb')
blockarrow(p,'legend-parameter-arrow',1561,952,83,39,'#f2ce92')
text(p,'legend-alignment',1320,902,'Alignment',37,SERIF,weight='bold')
text(p,'legend-projection',1322,960,'Projection',37,SERIF,weight='bold')
text(p,'legend-training',1689,901,'Training Flow',37,SERIF,weight='bold')
text(p,'legend-parameter',1670,963,'Parameter Flow',37,SERIF,weight='bold')

# Give all editable primitives stable IDs and save explicit geometry before the SVG.
used={e.get('id') for e in root.iter() if e.get('id')};counts={}
for parent in root.iter():
    for child in parent:
        if child.tag.rsplit('}',1)[-1] in ('rect','path','line','ellipse','image','text') and not child.get('id'):
            prefix=parent.get('id','primitive');counts[prefix]=counts.get(prefix,0)+1
            candidate=f'{prefix}-{counts[prefix]}'
            while candidate in used:
                counts[prefix]+=1;candidate=f'{prefix}-{counts[prefix]}'
            child.set('id',candidate);used.add(candidate)
sha=hashlib.sha256(SRC.read_bytes()).hexdigest()
spec=f'''# Reconstruction specification

Source S1: `../图片.png`, SHA-256 `{sha}`; 2011 × 1021 pixels, no physical-size metadata. User request: “rebuild [Image #1]”. The image was located and opened despite the attachment error. No manuscript or experimental data was supplied.

Brief: faithful reconstruction of S1, same aspect ratio and white background; editable SVG plus PDF/PNG. Assumed delivery width 14 in (height {WIDTH*H/W:.4f} in); this is a presentation master, not a claim of journal-size readability.

## Source-grounded stages and entities
- `attacker-client`: source x47–344, y33–831. Batman identity, poisoned rabbit/dog image stack, clean rabbit/dog stack. Photographs and logo remain raster.
- `malicious-knowledge`: source x388–1169, y57–459. Malicious Parameter; three-block Singular Value Decomposition; equality with Redundant + Important; No SVD / SVD bars; TAC Decrease / TAC Increase. These bars are schematic with no numeric scale in S1.
- `benign-knowledge`: source x388–1173, y477–808. Clean model; Truth Label / Attack Label bars and Gap; Clean Parameter; client weights W and previous W_g^(t−1); benign/attack branches; global W_g^t and Gap; Global Parameter.
- `alignment-panel`: source x1254–1938, y61–814. Before/after Attack Performance versus Parameter Space; malicious/benign knowledge; initial Δ and projected ΔP; Keep at the same attack-performance height; gray projection connections; Null Space with singular values x_1 … x_n and zero block; projector Ũ_0 Ũ_0^T = P; projection-plane illustration. Preserve equation references (3), (4), (5), (6) as printed. Their definitions are unavailable.
- `federated-training`: source x47–1172, y845–1006. Distribute / Aggregate, two representative Benign Client labels and ellipsis, Global model, teal up/down arrows.
- `legend`: source x1172–1974, y845–1006. Alignment (purple gradient), Projection (gray), Training Flow (blue), Parameter Flow (gold).

## Edges and notation
Blue arrows: poisoned data → malicious parameter; clean data → clean model. Gold arrows: important malicious component → alignment; global parameter → alignment. Gray curves connect left performance plot to the null-space inset and inset to right performance plot. Purple horizontal arrow illustrates alignment; brown Δ points from malicious region toward benign region; ΔP points left at preserved attack performance. Small parameter graph and communication connections retain their pictured endpoints. Paths and positions are enumerated in scene-graph.json.

Symbols are transcribed from S1 without inferring dimensions or proving claims. W_g^(t−1), W_g^t, x_1, x_n, Δ, ΔP, Ũ_0 Ũ_0^T = P are retained with editable text/tspan math. No loop stopping rule or additional algorithm is supplied or invented.

## Reconstruction limits
Coordinates, typefaces, linework, ghost-book outline, and color gradients are estimated from pixels. Fine-grained illustrated details use nine original raster crops, placed 14 times. Background transparency is applied to icon crops. All surrounding labels, matrices, axes, arrows, graphs, and panel outlines are native SVG. Tiny icon lettering remains raster. The original is unchanged. Font identity and original vector topology cannot be recovered from PNG. Scientific accuracy beyond visual transcription is not assessed.
'''
(OUT/'diagram-spec.md').write_text(spec)
profile=f'''# Reference style profile

Reference: S1 `../图片.png`; SHA-256 `{sha}`; PNG 2011 × 1021 (dimensions extracted), aspect {W/H:.6f}. Entire reference used.

| Dimension | Observation and evidence | Confidence / implementation |
|---|---|---|
| Layout | Left data column, stacked middle knowledge panels, tall right alignment panel, bottom communication/legend strip | Estimated pixel coordinates; same 2011 × 1021 viewBox |
| Design | Pale blue outer field, warm ivory alignment panel, rounded gray outlines, purple/gold knowledge, schematic matrices | Estimated fills and gradients; no additional stages |
| Fonts | Bold Times-like section headings; casual handwritten annotations; serif math | Original families unknown; Liberation Serif, Comic Neue, TeX Gyre Termes substituted, all installed |
| Lines | 3–4 px rounded panel borders, dashed data/null/legend boxes, broad blue/gold flow arrows, curved gray projection arrows | Estimated native SVG geometry |
| Icons | Batman portrait, data photos, magic books, sleeping/working and server/cloud illustrations; black network edges with colored nodes | Nine cropped PNG assets preserve detailed drawings. Networks, ghost-book outline and projection plane reconstructed as vectors |

Print width is assumed 14 in because S1 has no DPI metadata. Smallest native label: 20 user units = {20*72*WIDTH/W:.2f} pt at this width (subscripts are smaller). Original raster details are about {W/WIDTH:.1f} effective ppi when placed at their original canvas size; high-DPI export does not add detail. Reducing the complete figure to 7 in would make the small labels about 5 pt, unsuitable without a separate layout revision.
'''
(OUT/'style-profile.md').write_text(profile)
scene={'schema_version':1,'source':{'path':'../图片.png','sha256':sha},'style_profile':'style-profile.md','canvas':{'view_box':[0,0,W,H],'width_in':WIDTH,'background':'white'},'typography':{'heading':SERIF,'annotation':HAND,'math':MATH},'panels':[{'id':x.get('id'),'spec_id':x.get('id')} for x in root if x.tag==NS+'g'],'labels':labels,'edges':edges,'assets':assets,'equations':[l for l in labels if 'math_runs' in l],'objects':[]}
def collect(parent,ancestry):
    for c in parent:
        name=c.tag.rsplit('}',1)[-1]
        if name in ('rect','line','path','ellipse','image','text'):
            attrs={k:v for k,v in c.attrib.items() if not k.endswith('href')}
            scene['objects'].append({'id':c.get('id'),'parent':parent.get('id'),'primitive':name,'spec_id':next((v for v in ancestry if v in [a['id'] for a in scene['panels']]),None),'geometry_and_style':attrs,'role':'reference-reconstruction'})
        collect(c,ancestry+[c.get('id')])
collect(root,[])
(OUT/'scene-graph.json').write_text(json.dumps(scene,indent=2,ensure_ascii=False)+'\n')
E.ElementTree(root).write(OUT/'figure.svg',encoding='utf-8',xml_declaration=True)
print(f'Wrote {OUT}/figure.svg; {len(labels)} editable labels; {len(assets)} raster assets.')
