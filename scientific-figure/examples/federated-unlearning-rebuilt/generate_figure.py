#!/usr/bin/env python3
"""Faithful vector reconstruction; equations remain editable through these LaTeX strings."""
from pathlib import Path
import hashlib, json, io, re, html, random
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties
matplotlib.rcParams['mathtext.fontset']='stix'
OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'图片2.png'
W,H=2043,783
INK='#282c2d'; BLUE='#6ab6d5'; RED='#ff7878'; GOLD='#dcaf57'; GRAY='#5b686b'
parts=[]; objects=[]; equations=[]; edges=[]

def add(s): parts.append(s)
def attrs(d): return ' '.join(f'{k.replace("_","-")}="{html.escape(str(v),quote=True)}"' for k,v in d.items() if v is not None)
def el(tag,**kw): add(f'<{tag} {attrs(kw)}/>')
def rect(x,y,w,h,stroke=INK,sw=2,fill='white',rx=0,**kw): el('rect',x=x,y=y,width=w,height=h,rx=rx,stroke=stroke,stroke_width=sw,fill=fill,**kw)
def line(x1,y1,x2,y2,stroke=INK,sw=2,**kw): el('line',x1=x1,y1=y1,x2=x2,y2=y2,stroke=stroke,stroke_width=sw,**kw)
def path(d,stroke=INK,sw=2,fill='none',**kw): el('path',d=d,stroke=stroke,stroke_width=sw,fill=fill,**kw)
def circle(x,y,r,fill='white',stroke=INK,sw=2): el('circle',cx=x,cy=y,r=r,fill=fill,stroke=stroke,stroke_width=sw)
def text(id,x,y,s,size=26,bold=False,anchor='middle',fill='#080808'):
    add(f'<text {attrs(dict(id=id,x=x,y=y,font_family="Tinos, Times New Roman, serif",font_size=size,font_weight="bold" if bold else "normal",text_anchor=anchor,fill=fill))}>{html.escape(s)}</text>')
    objects.append(dict(id=id,kind='label',text=s,position=[x,y],font_size=size,alignment=anchor,source_anchor='reference pixels'))
def math(id,x,y,tex,size=29,color='#101416',anchor='middle'):
    buf=io.BytesIO(); math_to_image('$'+tex+'$',buf,prop=FontProperties(size=size),format='svg',color=color)
    root=ET.fromstring(buf.getvalue())
    for parent in root.iter():
        for child in list(parent):
            if child.tag.endswith('style') or child.attrib.get('id') == 'patch_1':
                parent.remove(child)
    vb=list(map(float,root.attrib['viewBox'].split())); ww,hh=vb[2:]
    inner=''.join(ET.tostring(c,encoding='unicode') for c in root if not c.tag.endswith('metadata'))
    inner=re.sub(r'id="([^"]+)"',lambda m:f'id="{id}-{m[1]}"',inner)
    inner=re.sub(r'(href=")#([^"]+)',lambda m:m[1]+'#'+id+'-'+m[2],inner)
    inner=re.sub(r'url\(#([^\)]+)\)',lambda m:'url(#'+id+'-'+m[1]+')',inner)
    xx=x-ww/2 if anchor=='middle' else x
    add(f'<g id="{id}" transform="translate({xx:.3f} {y-hh/2:.3f})"><title>{html.escape(tex)}</title>{inner}</g>')
    equations.append(dict(id=id,latex=tex,box=[xx,y-hh/2,ww,hh],rendering='STIX mathtext vector paths; editable LaTeX in generator',source_anchor='reference pixels'))
def arrow(id,pts,color=INK,sw=2,dash=None,meaning='',source=None,target=None):
    el('polyline',id=id,points=' '.join(f'{x},{y}' for x,y in pts),fill='none',stroke=color,stroke_width=sw,stroke_dasharray=dash,marker_end='url(#arrow-'+color[1:]+')')
    edges.append(dict(id=id,points=pts,color=color,meaning=meaning,source=source,target=target,source_anchor='reference pixels'))
def group(id,box,kind='illustration'):
    add(f'<g id="{id}">'); objects.append(dict(id=id,kind=kind,box=box,source_anchor='reference pixels'))
def end(): add('</g>')
def database(x,y):
    path(f'M{x} {y+12} v45 c0 22 62 22 62 0 v-45',sw=4,fill='white')
    for dy in [27,41,55]: path(f'M{x} {y+dy} c0 20 62 20 62 0',sw=3)
    el('ellipse',cx=x+31,cy=y+12,rx=31,ry=12,fill='white',stroke=INK,stroke_width=4)
    for dy in [30,44,58]: circle(x+52,y+dy,1.4,INK,INK,0)
def neural(x,y,muted=False):
    layers=[[(x,y+35),(x,y+85)],[(x+46,y+10+i*33) for i in range(4)],[(x+90,y+10+i*33) for i in range(4)],[(x+137,y+60)]]
    for aa,bb in zip(layers,layers[1:]):
        for a in aa:
            for b in bb: line(*a,*b,GRAY if muted else GOLD,1.5)
    for j,layer in enumerate(layers):
        for px,py in layer: circle(px,py,11,['#cfe7f7','#cde4ce','#cde4ce','#d8d1e7'][j],['#5999ce','#70ba6e','#70ba6e','#8a77b4'][j],1.8)
def graph(id,x,y,scale=1,frame=False):
    group(id,[x,y,110*scale,110*scale]); add(f'<g transform="translate({x} {y}) scale({scale})">')
    if frame: rect(0,0,110,110,sw=2)
    pts=[(17,28),(66,8),(102,72),(55,100),(9,78)]
    for i in range(5):
        for j in range(i+1,5): line(*pts[i],*pts[j],sw=4)
    for px,py in pts: circle(px,py,6.5,sw=4)
    end();end()
def dots(id,x,y): text(id,x,y,'⋮',29)

# Specification is serialized before geometry generation.
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
(OUT/'diagram-spec.md').write_text(f'''# Figure reconstruction specification

Source: `../图片2.png`, SHA-256 `{source_hash}`, 2043 × 783 pixels. The image itself supplies all content; no manuscript or implementation was provided. This is a faithful graphical reconstruction, not validation of the depicted algorithm.

Canvas: original aspect ratio, white background; assumed print width 14 inches. Left column has Client 1, Client 2, Client C, databases and neural networks. Client C carries a departure icon. The central server exchanges learning (blue) and unlearning (red) messages. Green connector lines magnify Client 1 into the top privacy panel. The top-right annotation defines arrow colors.

Stages and source anchors:
- privacy (x690–1673, y22–194): update g_t^c → Receive Budget → privacy budget → Gaussion Noise → differential-private update tilde g_t^c. Preserve the source spelling “Gaussion”.
- learning (x689–1993, y208–476): client updates → Aggregate Update → global models → Select Models (lambda) → selected models → Select Updates (gamma) → selected updates.
- unlearning (x686–1993, y493–762): remaining-client updates → Compute Direction Consistency → direction-angle diagram → Calibrate updates → calibrated vector → Aggregate Update → unlearned model.

Notation: preserve tilde/bar/hat distinctions, t/T/T′, C/C′ and C_t^r. Client C update uses uppercase C; requested-client vector superscripts use lowercase c_r. Equations are transcribed in scene-graph.json and the generator. Norms, cosine, inner product and the ratio retain their source placement.

Every listed arrow follows the source direction. No convergence condition or interpretation of lambda/gamma is supplied; none is added. Network connectivity, shaded update cells and hatch strokes are illustrative geometry rather than measured values. Font identity and exact hand-drawn noise strokes are unrecoverable from this raster.
''')
add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="14in" height="{14*H/W}in" viewBox="0 0 {W} {H}">')
add('<defs>')
for color in [INK,BLUE,RED,'#89999d']:
    add(f'<marker id="arrow-{color[1:]}" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L12 6 L0 12 L3 6 Z" fill="{color}"/></marker>')
add('<radialGradient id="cell-shade"><stop offset="0" stop-color="#f6faf9"/><stop offset="1" stop-color="#9ea8a8"/></radialGradient></defs>')
rect(0,0,W,H,stroke='none')
# Magnified region and main panels.
path('M691 22 L408 25 L25 25 L25 270 L408 270 L691 194',stroke='#79bc78',sw=1.8)
line(408,25,408,270,'#79bc78',1.8)
for id,x,y,w,h,c in [('privacy',691,23,981,171,'#d5eadd'),('legend',1689,23,304,171,'#e4e7e7'),('learning',689,208,1304,268,'#c4e0ed'),('unlearning',686,494,1307,267,'#ffd6d1')]:
    group(id,[x,y,w,h],'panel');rect(x,y,w,h,stroke=c,sw=5);end()
text('privacy-title',704,56,'Local Training with Adaptive Differential Privacy',28,True,'start')
text('learning-title',701,238,'Federated Learning',30,True,'start')
text('unlearning-title',699,523,'Federated Unlearning',30,True,'start')
# Client cards.
for idx,(y,name) in enumerate([(42,'Client 1'),(293,'Client 2'),(546,'Client C')]):
    c=GOLD if idx<2 else GRAY
    group(f'client-{idx+1}',[31,y,359,214],'client')
    rect(32,y,357,214,stroke=c,sw=3.4,rx=34)
    text(f'client-{idx+1}-name',216,y+28,name,27,True)
    rect(45,y+36,132,162,stroke=c,sw=3.1,rx=22,stroke_dasharray='3.5 3.5')
    rect(184,y+36,193,162,stroke=c,sw=3.1,rx=26,stroke_dasharray='3.5 3.5')
    text(f'data-{idx}-a',110,y+66,'Local',23,True);text(f'data-{idx}-b',110,y+94,'Data',23,True)
    database(79,y+113);neural(218,y+61,idx==2);end()
# Client departure.
group('client-departure',[308,520,100,100]);circle(358,570,49,'white',GRAY,3.4)
path('M380 555 V550 Q380 546 375 546 H339 Q335 546 335 551 V588 Q335 592 340 592 H375 Q380 592 380 586 V581',sw=3.5)
path('M362 569 H384 M376 560 L385 569 L376 578',sw=3.5,stroke_linecap='round');circle(355,569,1.7,INK,INK,0);end()
# Exchanges and server routes.
for id,pts,col in [('model-1',[(571,315),(571,96),(399,96)],BLUE),('update-1',[(398,126),(538,126),(538,309)],BLUE),('unlearn-model-1',[(570,311),(570,173),(402,173)],RED),('unlearn-update-1',[(398,203),(538,203),(538,309)],RED),('model-2',[(506,346),(392,346)],BLUE),('update-2',[(392,377),(500,377)],BLUE),('unlearn-model-2',[(508,423),(395,423)],RED),('unlearn-update-2',[(391,453),(504,453)],RED),('model-C',[(522,504),(522,617),(407,617)],BLUE),('update-C',[(403,648),(547,648),(547,510)],BLUE),('server-to-learning',[(637,379),(682,379)],BLUE),('server-to-unlearning',[(637,395),(637,627),(680,627)],RED)]:
    arrow(id,pts,col,3.5,meaning=id)
for id,x,y,tex in [('m1',486,82,r'M_t'),('g1',441,112,r'\tilde{g}_t^1'),('mh1',487,159,r'\hat{M}_t'),('gh1',442,190,r'\hat{g}_t^1'),('m2',475,331,r'M_t'),('g2',434,362,r'\tilde{g}_t^2'),('mh2',476,408,r'\hat{M}_t'),('gh2',434,439,r'\hat{g}_t^2'),('mc',487,602,r'M_t'),('gc',437,633,r'\tilde{g}_t^C')]: math(id,x,y,tex,27)
group('server',[516,315,110,130])
for y in [315,346,377]:
    rect(520,y,102,29,sw=5,rx=5);circle(545,y+15,3,INK,INK,0);line(570,y+15,600,y+15,sw=5,stroke_linecap='round')
line(571,419,571,435,sw=7,stroke_linecap='round');line(523,435,619,435,sw=7)
for x in [523,571,619]:circle(x,435,9,INK,INK,1)
end();text('server-label',573,478,'Server',29,True)
# Privacy details.
group('raw-update',[721,105,285,36])
for i in range(8):rect(721+i*35.6,105,35.6,36,fill='url(#cell-shade)',sw=2)
end();math('raw-g',889,79,r'g_t^c',34);text('raw-update-label',864,177,'Update',26)
arrow('receive-budget',[(1010,125),(1116,125)],meaning='receive budget')
text('receive',1063,115,'Receive',25);text('budget',1063,145,'Budget',25)
group('privacy-budget',[1129,94,58,59]);path('M1157 95 Q1171 105 1184 105 Q1182 135 1157 149 Q1132 137 1130 105 Q1143 104 1157 95',sw=1.5)
path('M1157 102 Q1169 110 1177 110 Q1175 133 1157 141 Q1139 133 1137 110 Q1148 107 1157 102',sw=1,stroke_dasharray='1 2')
circle(1157,120,11,sw=1);text('budget-dollar',1157,127,'$',21);end()
text('privacy-budget-label',1159,177,'Privacy budget',25)
arrow('noise',[(1196,125),(1318,125)],meaning='Gaussion Noise')
text('gaussion',1251,115,'Gaussion',25);text('noise-label',1253,145,'Noise',25)
group('noisy-update',[1343,104,287,38])
rng=random.Random(12)
for i in range(8):
    x=1343+i*35.8;rect(x,104,35.8,37,sw=2,rx=2)
    for j in range(8):
        a=x+rng.uniform(1,34);b=max(x+1,min(x+34,a+rng.uniform(-17,17)))
        path(f'M{a:.1f} 106 L{b:.1f} 139',sw=.9)
end();math('noisy-g',1485,78,r'\tilde{g}_t^c',33);text('noisy-label',1493,177,'Update with differential privacy',25)
text('annotation',1711,60,'Annotation',28,True,'start')
text('legend-learning',1711,118,'Learning:',26,False,'start');text('legend-unlearning',1711,158,'Unlearning:',26,False,'start')
arrow('legend-blue',[(1869,109),(1964,109)],BLUE,3.3,meaning='Learning');arrow('legend-red',[(1869,145),(1964,145)],RED,3.3,meaning='Unlearning')
# Learning.
for id,y,t in [('one',251,'1'),('two',309,'2'),('last',386,'T')]:
    rect(730,y,241,43,sw=1.8,rx=6)
    math('client-updates-'+id,850,y+22,rf'\tilde{{g}}_{{{t}}}^1,\tilde{{g}}_{{{t}}}^2,\cdots,\tilde{{g}}_{{{t}}}^C',28)
dots('update-dots',850,377);text('updates-from-clients',860,459,'Updates from clients',26)
arrow('aggregate-learning',[(969,375),(1110,375)],meaning='Aggregate Update',source='client-updates',target='global-models')
text('aggregate-learning-a',1035,365,'Aggregate',22);text('aggregate-learning-b',1037,394,'Update',22)
graph('global-model-back',1185,241,1,True);graph('global-model-middle',1152,269,1,True);graph('global-model-front',1125,303,1,True)
text('global-models-label',1202,459,'Global models',26)
arrow('select-models',[(1311,372),(1452,372)],meaning='Select Models, lambda',source='global-model-front',target='selected-models')
text('select-models-label',1375,360,'Select Models',22);math('lambda',1376,385,r'\lambda',23)
for id,y,t in [('one',256,'1'),('two',314,'2'),('last',391,"T'")]:
    rect(1461,y,112,43,sw=1.8,rx=6);math('selected-model-'+id,1517,y+21,rf'\bar{{M}}_{{{t}}}',28)
    arrow('select-updates-'+id,[(1585,y+24),(1726,y+24)],meaning='Select Updates, gamma',source='selected-model-'+id,target='selected-updates-'+id)
    text('select-updates-label-'+id,1654,y+14,'Select Updates',21);math('gamma-'+id,1655,y+39,r'\gamma',22)
    rect(1741,y+3,241,43,sw=1.8,rx=6)
    math('selected-updates-'+id,1862,y+24,rf'\bar{{g}}_{{{t}}}^1,\bar{{g}}_{{{t}}}^2,\cdots,\bar{{g}}_{{{t}}}^{{C\prime}}',28)
dots('model-dots',1516,381);dots('selected-update-dots',1858,385)
text('selected-models-label',1521,458,'Selected models',26);text('selected-updates-label',1863,458,'Selected updates',26)
# Unlearning.
for id,y,t in [('one',541,'1'),('two',594,'2'),('last',671,"T'")]:
    rect(730,y,241,43,sw=1.8,rx=6)
    math('remaining-'+id,850,y+22,rf'\hat{{g}}_{{{t}}}^1,\hat{{g}}_{{{t}}}^2,\cdots,\hat{{g}}_{{{t}}}^{{|C_t^r|}}',28)
dots('remaining-dots',855,663);text('remaining-label',866,744,'Updates from remaining clients',26)
arrow('compute-direction',[(988,589),(1100,589)],meaning='Compute Direction Consistency')
for j,s in enumerate(['Compute','Direction','Consistency']):text('compute-'+str(j),1047,585+j*26,s,22)
arrow('direction-old',[(1200,655),(1149,552)],meaning='original update direction')
arrow('direction-new',[(1200,655),(1286,570)],meaning='remaining-client update direction')
path('M1187 630 Q1198 601 1225 630',sw=2)
math('direction-old-label',1180,546,r'\bar{g}_t^{c_r}',28);math('direction-new-label',1278,602,r'\hat{g}_t^{c_r}',28)
math('cosine-equation',1220,692,r'\cos(\theta_t^{c_r})=\dfrac{\langle\bar{g}_t^{c_r},\hat{g}_t^{c_r}\rangle}{\Vert\bar{g}_t^{c_r}\Vert_2\Vert\hat{g}_t^{c_r}\Vert_2}',27)
arrow('calibrate',[(1328,593),(1440,593)],meaning='Calibrate updates')
text('calibrate-label',1384,585,'Calibrate',22);text('calibrate-updates',1384,612,'updates',22)
arrow('calibration-old',[(1521,655),(1470,552)],'#89999d',1.7,'5 5',meaning='original update direction')
arrow('calibration-new',[(1521,655),(1607,570)],'#89999d',1.7,'5 5',meaning='remaining-client update direction')
arrow('calibration-result',[(1521,655),(1574,602)],sw=2,meaning='calibrated update')
math('calibration-old-label',1497,546,r'\bar{g}_t^{c_r}',27,'#89999d');math('calibration-new-label',1603,546,r'\hat{g}_t^{c_r}',27,'#89999d')
math('calibration-result-label',1597,615,r'U_t^{c_r}',28)
math('calibration-equation',1571,692,r'U_t^{c_r}=\cos(\theta_t^{c_r})\cdot\dfrac{\Vert\bar{g}_t^{c_r}\Vert_2}{\Vert\hat{g}_t^{c_r}\Vert_2}\cdot\hat{g}_t^{c_r}',27)
arrow('aggregate-unlearning',[(1663,595),(1803,595)],meaning='Aggregate Update',target='unlearned-model')
text('aggregate-unlearning-a',1728,585,'Aggregate',22);text('aggregate-unlearning-b',1728,612,'Update',22)
graph('unlearned-model',1823,540,1.0)
text('unlearned-label',1876,680,'Unlearned',27);text('unlearned-model-label',1876,713,'model',27)
add('</svg>')
scene=dict(schema_version=1,canvas=dict(view_box=[0,0,W,H],width_in=14,background='white'),source=dict(path='../图片2.png',sha256=source_hash),style_profile='style-profile.md',nodes=objects,edges=edges,equations=equations,notes=['All geometry is vector. Labels are editable text; mathematics is outlined with exact editable source in this generator.', 'Icon boxes refer to outer schematic extents. Low-level drawing primitives are preserved in the SVG.'])
(OUT/'scene-graph.json').write_text(json.dumps(scene,indent=2,ensure_ascii=False)+'\n')
(OUT/'figure.svg').write_text('\n'.join(parts))
(OUT/'style-profile.md').write_text(f'''# Reference style profile

Reference `../图片2.png`, SHA-256 `{source_hash}`; full 2043 × 783 pixel canvas (extracted).

| Dimension | Observation and confidence | Reconstruction |
|---|---|---|
| Layout | Three left client cards, center server, three right horizontal panels; top-right legend (measured/estimated from pixels) | Same canvas and relative positions |
| Design | White field; pale green, blue and coral borders; gold client outlines; dark gray departing client (estimated) | Native vector outlines and rounded cards |
| Fonts | Times-like serif; bold titles; italic mathematics (estimated; exact family unknown) | Tinos substitute; STIX mathematics |
| Lines | Dotted inner client borders, blue learning arrows, red unlearning arrows, black operation arrows; dashed calibration vectors (estimated) | Editable strokes and reusable arrow markers |
| Icons | Databases, multilayer networks, three server trays, shield/budget, stacked graphs and exit badge (visually inventoried) | Reconstructed entirely as vectors; noise hatch pattern approximated deterministically |

Print width is assumed to be 14 inches to retain the dense original layout. At 7 inches, small labels and equation scripts would need redesign for publication readability. Original misspelling “Gaussion Noise” is retained. Mathematical outlines can be regenerated from source strings; ordinary labels remain editable text. Exact source pixels, font identity, and sketch strokes are not claimed.
''')
print(OUT/'figure.svg')
