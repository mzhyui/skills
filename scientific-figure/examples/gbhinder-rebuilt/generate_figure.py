#!/usr/bin/env python3
"""Reconstruct the supplied GBHINDER raster as editable vector geometry."""
from pathlib import Path
import hashlib, json, xml.etree.ElementTree as E
OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'图片4.png'
W,H=2065,855
WIDTH=14
NS='http://www.w3.org/2000/svg'
E.register_namespace('',NS)
root=E.Element('{'+NS+'}svg',viewBox=f'0 0 {W} {H}',width=f'{WIDTH}in',height=f'{WIDTH*H/W}in')
def el(tag,p=None,**a):
    return E.SubElement(root if p is None else p,'{'+NS+'}'+tag,{k.replace('_','-'):str(v) for k,v in a.items() if v is not None})
def group(id): return el('g',id=id)
def path(p,d,fill='none',stroke='#222',sw=2,**kw): return el('path',p,d=d,fill=fill,stroke=stroke,stroke_width=sw,stroke_linejoin='round',stroke_linecap='round',**kw)
def rect(p,x,y,w,h,fill='none',stroke='none',sw=1,rx=0,**kw): return el('rect',p,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=sw,rx=rx,**kw)
def line(p,x,y,X,Y,c='#222',sw=2,**kw): return el('line',p,x1=x,y1=y,x2=X,y2=Y,stroke=c,stroke_width=sw,stroke_linecap='round',**kw)
def circ(p,x,y,r,fill='white',stroke='#255d6e',sw=4): return el('circle',p,cx=x,cy=y,r=r,fill=fill,stroke=stroke,stroke_width=sw)
labels=[]; edges=[]; nodes=[]
def txt(p,id,x,y,s,size=30,italic=False,bold=False,anchor='start',**kw):
    t=el('text',p,id=id,x=x,y=y,font_family='Tinos',font_size=size,font_style='italic' if italic else 'normal',font_weight='bold' if bold else 'normal',text_anchor=anchor,fill='#080808',**kw);t.text=s
    labels.append(dict(id=id,parent=p.get('id'),text=s,position=[x,y],font_size=size,alignment=anchor))
    return t
def math(p,id,x,y,runs,size=32):
    t=txt(p,id,x,y,'',size,True)
    previous=None
    for s,shift in runs:
        sp=el('tspan',t,baseline_shift=shift or 'baseline',font_size=size*.65 if shift else size)
        if shift=='super' and previous and previous[1]=='sub':sp.set('dx',str(-size*.65*.50*len(previous[0])))
        if 'ℱ' in s or 'ℋ' in s:sp.set('font-family','STIXGeneral')
        sp.text=s
        previous=(s,shift)
    labels[-1]['text']=''.join(s for s,_ in runs);labels[-1]['math_runs']=runs
    return t
BLUE='#7087be'; CYAN='#8bcede'; RED='#c84f45'; GREEN='#99bb5b'
def arrow(p,id,points,color='blue',sw=6,dash=None,source=None,target=None):
    d='M '+' L '.join(f'{x} {y}' for x,y in points)
    colors={'blue':BLUE,'cyan':CYAN,'red':RED,'green':GREEN,'gray':'#aaa','orange':'#ef7800'}
    if sw>=10:
        (x,y),(X,Y)=points
        if y==Y:
            d=f'M {x} {y-9} H {X-23} V {y-23} L {X} {Y} L {X-23} {y+23} V {y+9} H {x} Z'
        else:
            d=f'M {x-9} {y} V {Y+20} H {x-23} L {X} {Y} L {x+23} {Y+20} H {x+9} V {y} Z'
        path(p,d,fill=colors[color],stroke='none',sw=0,id=id)
    else:
        path(p,d,stroke=colors[color],sw=sw,marker_end=f'url(#arrow-{color})',stroke_dasharray=dash,id=id)
    edges.append(dict(id=id,spec_id=id,source=source,target=target,points=points,type='reference connector',color=color))
D=el('defs')
for name,col in [('blue',BLUE),('cyan',CYAN),('red',RED),('green',GREEN),('gray','#aaa'),('orange','#ef7800'),('block',BLUE)]:
    m=el('marker',D,id='arrow-'+name,viewBox='0 0 12 10',refX=11,refY=5,markerWidth=3 if name=='block' else 6,markerHeight=3 if name=='block' else 5,orient='auto-start-reverse')
    path(m,'M 0 0 L 11 5 L 0 10 Z','white' if name=='cyan' else col,col,1 if name=='cyan' else 0)
el('title').text='Overview of the proposed GBHINDER framework'
el('desc').text='Reconstruction of 图片4.png. Editable text, model stacks, graphs, features, arrows and vector illustrations. Font and devil icon approximate the raster source.'
p=group('background');rect(p,0,0,W,H,'white')
for id,x,y,w,h in [('local-data-panel',57,44,242,694),('aggregation-panel',314,44,1711,204),('method-panel',314,261,1711,477)]:
    rect(p,x,y,w,h,stroke='#222',sw=2,rx=16,id=id,stroke_dasharray='15 10')

def graph(p,id,pts,links,r=12,colors=None):
    g=el('g',p,id=id)
    for a,b in links: line(g,*pts[a],*pts[b],'#c1c3c2',2)
    for i,(x,y) in enumerate(pts): circ(g,x,y,r,colors[i] if colors else 'white','#253748' if colors else '#255d6e',2 if colors else 4)
    return g

def slab(p,x,y,w,h,dep,front,side,top,outline=False):
    st='#ff873a' if outline else 'none';sw=1.5
    path(p,f'M {x} {y} l {dep} {-dep} h {w} l {-dep} {dep} Z',top,st,sw)
    rect(p,x,y,w,h,front,st,sw)
    path(p,f'M {x+w} {y} l {dep} {-dep} v {h} l {-dep} {dep} Z',side,st,sw)

def model(p,id,x,y,outline=False,scale=1):
    g=el('g',p,id=id)
    for dx,dy,w,h,d,c in [(0,27,18,114,28,('#dcecf7','#afd0e9','#edf5fc')),(49,34,17,102,23,('#eacbb3','#d9af92','#f3e2d8')),(93,36,15,80,15,('#b8d9ad','#95c18c','#d7e9d1')),(125,48,15,56,14,('#c8d0d5','#adb9c2','#e1e6ea'))]:
        slab(g,x+dx*scale,y+dy*scale,w*scale,h*scale,d*scale,*c,outline)
    nodes.append(dict(id=id,spec_id=id,kind='model',box=[x,y,155*scale,144*scale],outlined=outline))
    return g

def devil(p,id,x,y,s=1):
    g=el('g',p,id=id,transform=f'translate({x},{y}) scale({s})')
    path(g,'M 27 28 Q 48 21 58 43 L 48 40 L 46 52 L 35 44 Z','#8e171c','#202020',1.5)
    path(g,'M 22 34 L 17 48 L 20 60 L 26 58 L 26 47 L 32 56 L 38 55 L 34 40 Z','#cc3533','#222',1.5)
    circ(g,24,24,12,'#efbd9e','#222',1.5)
    path(g,'M 12 21 Q 10 6 29 10 L 39 22 L 35 31 L 33 17 L 23 13 L 18 22 Z','#d53837','#222',1.4)
    path(g,'M 15 12 L 13 3 L 22 10 M 29 10 L 35 4 L 36 16','#eee','#222',1)
    circ(g,24,23,1.4,'black','none',0)
    path(g,'M 27 29 Q 23 32 20 28',stroke='#333',sw=1)
    line(g,5,10,12,58,'#222',1.6)
    path(g,'M 1 0 Q -3 20 7 19 Q 17 16 12 -1 M 6 -4 L 7 19',stroke='#222',sw=1.3)
    path(g,'M 36 49 Q 52 60 54 45 L 58 47',stroke='#bb2525',sw=2)
    return g

p=group('local-data')
graph(p,'local-graph-1',[(91,239),(136,205),(154,251),(190,211),(189,153),(191,96),(252,119),(253,208),(234,261)],[(0,1),(1,2),(1,4),(2,3),(3,4),(4,5),(5,6),(6,7),(3,7),(3,8)])
graph(p,'local-graph-2',[(116,439),(133,406),(103,376),(114,342),(161,329),(207,347),(252,329),(182,383)],[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(5,7),(7,1)])
txt(p,'data-ellipsis',176,476,'⋯',49,anchor='middle')
graph(p,'local-graph-3',[(86,640),(122,582),(180,497),(181,565),(205,611),(240,522),(266,596),(245,656)],[(0,1),(1,2),(2,3),(2,5),(3,4),(4,0),(4,5),(4,7),(5,6),(6,7)])
txt(p,'local-data-label',179,708,'Local Data',28,anchor='middle')

p=group('aggregation')
txt(p,'global-label-1',332,140,'Global',28);txt(p,'global-label-2',332,173,'Model',28)
model(p,'global-model',422,73,True)
math(p,'global-weights',503,225,[('w',''),('t','super')],34)
arrow(p,'aggregate-to-global',[(774,168),(599,168)],sw=7,source='aggregation-sum',target='global-model')
txt(p,'aggregation-label',697,138,'Aggregation',32,anchor='middle')
path(p,'M 858 70 Q 823 79 823 99 V 192 Q 823 211 858 220',stroke=BLUE,sw=5)
for i,x in enumerate([870,1106,1470]):model(p,f'aggregation-model-{i+1}',x,75)
for i,x in enumerate([1060,1301,1429]):
    line(p,x-10,146,x+10,146,'#858585',8);line(p,x,136,x,156,'#858585',8)
txt(p,'sum-ellipsis',1370,161,'⋯',51,anchor='middle')
path(p,'M 1620 70 Q 1655 79 1655 99 V 192 Q 1655 211 1620 220',stroke=BLUE,sw=5)
devil(p,'malicious-client-icon',1165,147,1.15)
rect(p,1673,63,338,165,'white','#d6d6d6',4)
txt(p,'legend-malicious',1692,116,'Malicious Updates',32)
devil(p,'legend-devil',1935,74,.96)
txt(p,'legend-download',1692,165,'Download',32)
arrow(p,'legend-download-arrow',[(1993,155),(1856,155)],'red',7)
txt(p,'legend-upload',1692,212,'Upload',32)
arrow(p,'legend-upload-arrow',[(1857,202),(1993,202)],'green',7)
arrow(p,'global-download',[(468,209),(468,269)],'red',7,source='global-model',target='current-weights')
arrow(p,'client-upload',[(1540,268),(1540,212)],'green',6,source='local-model',target='aggregation-model-3')

p=group('historical-channel-attention')
arrow(p,'data-to-training',[(270,381),(320,381)],sw=15,source='local-data',target='current-weights')
for x in [268,274,280]:line(p,x,371,x,391,BLUE,3)
math(p,'current-weights',364,300,[('w',''),('k','sub'),('t','super'),(' ← w',''),('t','super')],34)
for id,x,y,w,h,d,c in [('current-first',325,334,18,114,28,('#dcecf7','#afd0e9','#edf5fc')),('current-middle',406,341,16,94,24,('#eacbb3','#d9af92','#f3e2d8')),('current-last',508,354,15,57,14,('#c8d0d5','#adb9c2','#e1e6ea'))]:
    g=el('g',p,id=id);slab(g,x,y,w,h,d,*c,True)
for x,y,w,h,d,c in [(325,554,18,114,28,('#dcecf7','#afd0e9','#edf5fc')),(406,561,16,94,24,('#eacbb3','#d9af92','#f3e2d8')),(508,576,15,55,14,('#c8d0d5','#adb9c2','#e1e6ea'))]:slab(p,x,y,w,h,d,*c)
txt(p,'layer-dots-current',450,381,'⋯',39);txt(p,'layer-dots-history',450,599,'⋯',39)
path(p,'M 374 594 H 381 Q 390 594 390 584 V 386 Q 390 376 400 376 H 405',stroke=BLUE,sw=3)
path(p,'M 482 594 H 488 Q 496 594 496 584 V 386 Q 496 376 506 376',stroke=BLUE,sw=3)
rect(p,360,449,175,70,'#cec3db',rx=11)
txt(p,'channel-label-1',447,478,'Channel',32,True,anchor='middle');txt(p,'channel-label-2',447,507,'Attention',32,True,anchor='middle')
math(p,'history-weights',357,689,[('h',''),('k','sub'),('t','super'),(' ← w',''),('k','sub'),('t−1','super')],33)
arrow(p,'loss-input',[(540,377),(572,377)],sw=5)
arrow(p,'channel-input',[(540,594),(572,594)],sw=5)
arrow(p,'history-update',[(602,288),(512,288),(498,298),(498,342)],'cyan',4,'5 7')
txt(p,'history-update-label',511,317,'Update',29,bold=True)
# CE loss panel
rect(p,600,270,180,202,'#f1f1f1');rect(p,600,270,180,37,'#dceff4')
txt(p,'ce-title',690,298,'CE Loss',33,True,True,anchor='middle')
rect(p,607,319,50,147,'none','#7b9d43',3,5,stroke_dasharray='8 6')
rect(p,725,319,51,147,'none','#7b9d43',3,5,stroke_dasharray='8 6')
for i,(c,s) in enumerate([('#478ca4','1'),('#d3e4be','0'),('#eebac1','1')]):
    y=348+i*44;circ(p,631,y,18,c,'#7b9d43',4)
    arrow(p,f'ce-link-{i}',[(664,y),(691,y)],'gray',2)
    arrow(p,f'ce-link-reverse-{i}',[(717,y),(691,y)],'gray',2)
    rect(p,732,y-19,36,38,'#e9e7eb','#d8d6db',2)
    txt(p,f'ce-value-{i}',750,y+12,s,39,bold=True,anchor='middle')
# Topological consistency panel
rect(p,790,270,379,202,'#f1f1f1');rect(p,790,270,379,37,'#dceff4')
txt(p,'topology-title',979,298,'Topological Consistency',32,True,True,anchor='middle')
txt(p,'pre-pooling-label',812,448,'pre-pooling',27,transform='rotate(-90 812 448)')
slab(p,824,343,15,99,24,'#bedcb0','#8cbf6a','#d8eacb',True)
arrow(p,'pre-pooling-to-graph',[(866,380),(901,380)],sw=5)
pts=[(963,345),(1013,330),(1063,350),(1110,330),(1036,390),(984,415),(951,386),(966,451)]
g=el('g',p,id='topology-graph')
for a,b in [(0,1),(0,6),(1,2),(1,3),(2,3),(2,4),(4,5),(5,6),(5,7)]:line(g,*pts[a],*pts[b],'#c1c3c2',2)
for (x,y),c in zip(pts,['#605078','#008ac1','#285a68','#4aabc7','#87ccda','#286275','#8769a6','#286275']):circ(g,x,y,13,'#f1f1f1',c,4)
for i,pts2 in enumerate([[(1029,322),(1052,333)],[(1085,321),(1071,333)]]):arrow(p,f'topology-small-{i}',pts2,'gray',1.8)

def feature(p,id,x,y,cols,w=28,h=96,stroke='#87729e'):
    g=el('g',p,id=id);rect(g,x-5,y-5,w+10,h+10,'none',stroke,2,4,stroke_dasharray='6 5')
    for i,c in enumerate(cols):rect(g,x,y+i*h/len(cols),w,h/len(cols)-2,c)
    return g
for id,x,y,cols in [('topo-feature-1',925,313,['#8067a0','#b78586','#d1c2d9','#dddae9']),('topo-feature-2',913,388,['#87659d','#be8495','#b9dde3','#d5cde2']),('topo-feature-3',1040,413,['#8ed2de','#cad8a7','#d59b9b','#b3a2c8']),('topo-feature-4',1084,356,['#275f70','#82a653','#dfb5b6','#d4c9e0']),('topo-feature-5',1133,317,['#77c7d5','#cbd6b4','#e1b9b8','#d9d5e9'])]:feature(p,id,x,y,cols,12,48)
# Layer channels and channel-attention graph
rect(p,600,477,570,219,'#f1f1f1')
for j,(x,c) in enumerate([(616,'#e0edc6'),(668,'#bfe5ef'),(720,'#e7dff0'),(808,'#fff3e2')]):
    path(p,f'M {x} 479 l 76 45 v 171 l -76 -46 Z',c,'none')
    ps=[(x+12,541),(x+7,572),(x+20,608),(x+13,633),(x+40,598),(x+50,570),(x+31,542),(x+68,565)]
    for a,b in [(0,1),(0,6),(1,2),(2,3),(2,4),(4,5),(5,6),(5,7)]:line(p,*ps[a],*ps[b],'#30364a',1.4)
    for k,(xx,yy) in enumerate(ps):el('ellipse',p,cx=xx,cy=yy,rx=4.7,ry=11,fill=['#ffff65','#5555a0','#609eb2','#63489a'][((k+j)%4)],stroke='#40536a',stroke_width=1.3)
    txt(p,f'channel-index-{j}',x+44,671,str(j+1) if j<3 else 'Dₗ',30,italic=j==3)
txt(p,'channel-dots-top',765,510,'⋯',37);txt(p,'channel-dots-bottom',801,687,'⋯',37)
rect(p,985,477,185,219,'#d6cce1');rect(p,885,477,285,40,'#dceff4')
txt(p,'channel-attention-title',1026,507,'Channel Attention',32,True,True,anchor='middle')
math(p,'channel-operator',884,586,[('ℋ',''),('CH','sub'),('(ℱ',''),('l','super'),(')','')],28)
arrow(p,'channel-representation',[(888,605),(977,605)],sw=5)
graph(p,'channel-attention-graph',[(1025,576),(1014,610),(1043,638),(1028,671),(1089,616),(1114,580),(1070,562),(1155,562)],[(0,1),(0,6),(1,2),(2,3),(2,4),(4,5),(5,6),(5,7)],12,['#7ed151','#2c7795','#ffff08','#7151aa','#2c7795','#ffff08','#2c7795','#57428b'])
math(p,'channel-vector-space',1102,643,[('ℝ',''),('N','super')],30)
txt(p,'history-panel-title',791,727,'Historical Channel Attention Regularization',33,True,True,anchor='middle',text_decoration='underline')

p=group('adaptive-momentum')
def graphstack(id,x,y,adv=False):
    g=el('g',p,id=id)
    for off in [-42,-21,0]:rect(g,x+off,y+off*.5,151,148,'white','#222',2,17,stroke_dasharray='14 9')
    ps=[(x+15,y+116),(x+39,y+77),(x+78,y+65),(x+78,y+20),(x+119,y+36),(x+95,y+95),(x+135,y+86),(x+121,y+127)]
    graph(g,id+'-graph',ps,[(0,1),(0,7),(1,2),(1,3),(2,3),(3,4),(4,5),(5,7),(6,7)],8)
    math(g,id+'-label',x+9,y+39,[('G',''),('i','sub')]+([('adv','super')] if adv else []),32)
    if adv:
        for j,(xx,yy) in enumerate([(x+65,y+103),(x+128,y+57)]):
            line(g,xx-6,yy-6,xx+6,yy+6,'#eb210e',3);line(g,xx-6,yy+6,xx+6,yy-6,'#eb210e',3)
        line(g,x+19,y+112,x+82,y+100,'#bbc3c8',2,stroke_dasharray='5 5')
    nodes.append(dict(id=id,spec_id=id,kind='graph-stack',box=[x-42,y-21,193,169],adversarial=adv))
graphstack('perturbed-graphs',1243,292,True)
graphstack('original-graphs',1243,539)
arrow(p,'perturb-graphs',[(1247,503),(1247,462)],sw=12,source='original-graphs',target='perturbed-graphs')
for y in [495,501,507]:line(p,1238,y,1256,y,BLUE,3)
math(p,'perturb-label',1275,488,[('Perturb(','') ,('G',''),(')','')],27)
for id,y in [('perturbed-to-local',354),('original-to-history',606)]:
    arrow(p,id,[(1416,y),(1450,y)],sw=15)
    for x in [1408,1413]:line(p,x,y-10,x,y+10,BLUE,3)
model(p,'local-model',1472,270,True)
model(p,'historical-model',1472,530)
txt(p,'local-model-label',1550,438,'Local Model',28,anchor='middle')
txt(p,'historical-model-label',1558,696,'Historical Model',27,anchor='middle')
arrow(p,'model-update',[(1492,450),(1492,520)],'cyan',4,'5 8',source='local-model',target='historical-model')
txt(p,'model-update-label',1507,487,'Update',28,bold=True)
arrow(p,'local-features',[(1651,335),(1688,335)],sw=6)
arrow(p,'history-features',[(1649,605),(1686,605)],sw=6)
rect(p,1618,440,379,80,'#dceff4')
math(p,'delta-equals',1618,492,[('δ =','')],38)
path(p,'M 1696 446 Q 1676 450 1676 461 V 497 Q 1676 512 1696 517 M 1958 446 Q 1976 450 1976 461 V 497 Q 1976 512 1958 517',stroke='#898989',sw=4)
for j,(x,idx) in enumerate([(1740,'1'),(1837,'2'),(1935,'i')]):
    feature(p,f'adversarial-features-{idx}',x,321,[['#35869c','#d9e6bd','#e7baba','#dfd9e8'],['#ffc300','#9db755','#e8c7cd','#ddd7e7'],['#bc514a','#d9e5bd','#54a9b7','#80649e']][j],27,92)
    feature(p,f'historical-features-{idx}',x,548,[['#92cddd','#c5d9a0','#93372f','#ab97c0'],['#ffda67','#78963f','#d69997','#d9d1e4'],['#d49791','#d8e5bc','#a5c8d1','#b09cc4']][j],27,92)
    # Explicit fixed coordinates avoid stacking two superscripts into a single run.
    math(p,f'adversarial-feature-label-{idx}',x-43,300,[('ℱ(G',''),(idx,'sub'),('adv','super'),(')','')],27)
    math(p,f'historical-feature-label-{idx}',x-43,677,[('ℱ(G',''),(idx,'sub'),(')','')],29)
    math(p,f'pi-{idx}',x-49,488,[('π',''),(idx,'sub')],39)
    line(p,x-2,431,x+28,431,'#ef7800',3)
    arrow(p,f'delta-down-{idx}',[(x+14,436),(x+14,482)],'orange',2.4,'3 6')
    arrow(p,f'delta-up-{idx}',[(x+14,530),(x+14,482)],'orange',2.4,'3 6')
for id,y in [('features-ellipsis-top',382),('features-ellipsis-bottom',620)]:txt(p,id,1881,y,'⋯',38)
txt(p,'momentum-panel-title',1618,727,'Adaptive Momentum Information Update',33,True,True,anchor='middle',text_decoration='underline')
p=group('caption')
txt(p,'figure-caption',1040,814,'Figure 2: Overview of the proposed GBHINDER framework.',39,anchor='middle')

# Assign all geometry stable IDs for renderer bounding-box inspection.
for i,e in enumerate(root.iter()):
    if e.tag.rsplit('}',1)[-1] in {'path','rect','circle','ellipse','line','text'} and not e.get('id'):e.set('id',f'shape-{i:04d}')
sha=hashlib.sha256(SRC.read_bytes()).hexdigest()
# Save specification/scene before the final SVG, including literal geometry.
(OUT/'diagram-spec.md').write_text(f'''# GBHINDER reference reconstruction

Source S1: `../图片4.png`, SHA-256 `{sha}`, 2065 × 855 pixels. The figure itself supplies all content. No paper or algorithm code was supplied.

Brief: faithful reconstruction with editable SVG/PDF and PNG, white background, original aspect ratio. Assumed delivery width 14 inches preserves dense labels; this is not a venue-specific print-size claim.

Stages and source anchors:
- local-data: left dashed panel, three illustrative graph instances.
- aggregation: upper dashed panel, client models combined toward global model; red download and green upload arrows; malicious-update legend and icon.
- historical-channel-attention: lower left, current weights w_k^t ← w^t, historical weights h_k^t ← w_k^{{t−1}}, channel attention, CE Loss and 1/0/1 labels, pre-pooling and Topological Consistency. Layer channels 1, 2, 3, …, D_l feed ℋ_CH(ℱ^l) and an ℝ^N graph representation.
- adaptive-momentum: lower right, G_i and perturbed G_i^adv, local and historical models, feature columns ℱ(G_1), ℱ(G_2), …, ℱ(G_i) and adversarial counterparts. δ = [π_1 π_2 π_i] follows the source's displayed terms; the reference shows feature-column ellipses but no explicit ellipsis in the delta row.

Node/edge/notation inventory: `scene-graph.json` records labels, math runs, model and graph groups, arrow routes and complete editable geometry. Arrow direction follows S1; colored update arrows are transcribed without adding causal or algorithmic claims. Two-way CE connectors are retained. No convergence rule or tensor dimensions can be recovered and none are invented.

Abstraction: vector devil icons approximate the raster artwork; model faces, graphs, channel planes and feature bars are schematic redraws. Fine icon contours, model shadows, and exact raster antialiasing are not recovered. Font identity is estimated from pixels. The illustration is not measured evidence or verification of the method.
''')
scene=dict(schema_version=1,source=dict(path='../图片4.png',sha256=sha),style_profile='style-profile.md',canvas=dict(view_box=[0,0,W,H],width_in=WIDTH,background='white'),typography=dict(family='Tinos'),nodes=nodes,edges=edges,labels=labels,geometry=[dict(tag=e.tag.rsplit('}',1)[-1],attributes=e.attrib,text=e.text) for e in root.iter()])
(OUT/'scene-graph.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2)+'\n')
E.ElementTree(root).write(OUT/'figure.svg',encoding='utf-8',xml_declaration=True)
(OUT/'style-profile.md').write_text(f'''# Reference style profile

Reference `../图片4.png`, SHA-256 `{sha}`. Dimensions extracted: 2065 × 855; full image including caption retained.

| Dimension | Observation / confidence | Implementation |
|---|---|---|
| Layout | Estimated from pixels: left data column x≈.028–.145; aggregation y≈.05–.29; lower method region y≈.31–.86; caption at .95H | Original aspect ratio, dashed rounded enclosures, same section arrangement |
| Design | Estimated pastel blue/peach/green/gray model slabs; pale cyan headers, purple attention panel, white background | Native polygons, consistent pastel fills; tiny raster shadows omitted |
| Fonts | Serif body and italic bold section headings; exact identity unknown | Locally installed Tinos; editable text and tspan scripts; physical width assumed 14 in |
| Line styles | Estimated 2-unit dashed enclosures, blue solid flow arrows, red download, green upload, cyan dashed update, orange dotted comparison | Separate native paths and arrow markers |
| Icons | Model slabs, node-link graphs, layer planes, feature bars and devil cartoons | All reconstructed as vectors; devil contours adapted |

This is an estimated visual reconstruction, not recovery of the original source objects or exact fonts. At 7 inches wide the dense original layout makes many labels smaller than 8 pt; use the supplied 14-inch width for inspection or redesign for a specific manuscript size.
''')
(OUT/'README.md').write_text('''# GBHINDER reconstruction

Editable reconstruction of `../图片4.png`. Run:

```bash
python3 figures/gbhinder-rebuilt/generate_figure.py
python3 skills/scientific-figure/scripts/render_check.py figures/gbhinder-rebuilt/figure.svg --out-dir figures/gbhinder-rebuilt/exports --width-in 14 --dpi 300
```

Use `--overwrite` for a deliberate repeat export. Tinos and Inkscape are required. All figure elements are native vectors; text remains editable. See validation.md for review and reconstruction limits.
''')
print(OUT/'figure.svg')
