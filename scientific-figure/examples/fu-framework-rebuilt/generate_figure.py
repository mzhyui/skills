#!/usr/bin/env python3
"""Rebuild fu_framework with GBHINDER's native-vector visual language."""
from pathlib import Path
from copy import deepcopy
import hashlib, json, xml.etree.ElementTree as E
OUT=Path(__file__).resolve().parent
SOURCE=OUT/'source/fu_framework.svg'
NS='http://www.w3.org/2000/svg'
E.register_namespace('', NS)
old=E.parse(SOURCE).getroot()
original={e.get('id'):e for e in old.iter() if e.tag==f'{{{NS}}}text'}
W,H=1280,460
root=E.Element(f'{{{NS}}}svg',width=str(W),height=str(H),viewBox=f'0 0 {W} {H}')
labels=[];nodes=[];edges=[];icons=[]
C={'ink':'#252c32','blue':'#7087be','cyan':'#dceff4','purple':'#cec3db','red':'#c84f45','green':'#729948','orange':'#d38753','muted':'#57616b'}
def el(tag,p=None,**attrs):
 return E.SubElement(root if p is None else p,f'{{{NS}}}{tag}',{k.replace('_','-'):str(v) for k,v in attrs.items() if v is not None})
def group(id,p=None):return el('g',p,id=id)
def rect(p,x,y,w,h,fill='white',stroke='none',sw=1,rx=0,**a):return el('rect',p,x=x,y=y,width=w,height=h,fill=fill,stroke=stroke,stroke_width=sw,rx=rx,**a)
def path(p,d,stroke=C['ink'],sw=1.4,fill='none',**a):return el('path',p,d=d,stroke=stroke,stroke_width=sw,fill=fill,stroke_linecap='round',stroke_linejoin='round',**a)
def text(p,id,x,y,size=15,bold=False,italic=False,anchor='middle',color=None):
 t=deepcopy(original[id]);t.attrib.clear();t.attrib.update({'id':id,'x':str(x),'y':str(y),'font-family':'Tinos','font-size':str(size),'font-weight':'bold' if bold else 'normal','font-style':'italic' if italic else 'normal','text-anchor':anchor,'fill':color or C['ink']})
 for s in list(t):
  s.attrib.pop('id',None);s.set('font-family','Tinos')
  s.set('font-size',str(max(11,size*.72) if s.get('baseline-shift') in ('sub','super') else size))
 p.append(t);labels.append({'id':id,'source_anchor':id,'parent':p.get('id'),'text':''.join(t.itertext()),'position':[x,y],'font_size':size,'alignment':anchor,'math_runs':[{'text':s.text,'shift':s.get('baseline-shift','baseline')} for s in t]})
 return t
def arrow(p,id,points,color='blue',dash=None):
 path(p,'M '+' L '.join(f'{x},{y}' for x,y in points),C[color],2.3,marker_end=f'url(#arrow-{color})',id=id,stroke_dasharray=dash)
 edges.append({'id':id,'spec_id':id,'source_anchor':id,'points':points,'color':color,'type':'control' if id.startswith(('withdrawal','request','diagnostic')) else 'data'})
def node(p,id,box,kind='operation',fill='#f4f4f3',stroke=None,dash=None):
 x,y,w,h=box;g=group(id,p);rect(g,x,y,w,h,fill,stroke or 'none',1.2,6,stroke_dasharray=dash)
 nodes.append({'id':id,'spec_id':id,'panel':p.get('id'),'kind':kind,'box':box});return g

def database(p,id,x,y,scale=1,color='blue'):
 g=group(id,p);g.set('transform',f'translate({x},{y}) scale({scale})');c=C[color]
 path(g,'M 0,6 V 28 C 0,36 28,36 28,28 V 6',c,1.6,fill='#f8fbfd')
 for yy in [14,21,28]:path(g,f'M 0,{yy} C 0,{yy+8} 28,{yy+8} 28,{yy}',c,1.2)
 el('ellipse',g,cx=14,cy=6,rx=14,ry=6,fill='white',stroke=c,stroke_width=1.6)
 icons.append({'id':id,'parent':p.get('id'),'role':'stored data','primitive':'vector database','box':[x,y,28*scale,36*scale]})

def model(p,id,x,y,scale=1,outline=False):
 g=group(id,p)
 for dx,dy,w,h,d,colors in [(0,0,12,48,11,('#dcecf7','#afd0e9','#edf5fc')),(24,5,11,39,10,('#eacbb3','#d9af92','#f3e2d8')),(46,10,10,30,8,('#b8d9ad','#95c18c','#d7e9d1')),(66,15,9,22,7,('#c8d0d5','#adb9c2','#e1e6ea'))]:
  xx,yy=x+dx*scale,y+dy*scale;w*=scale;h*=scale;d*=scale
  stroke=C['orange'] if outline else 'none'
  path(g,f'M {xx},{yy} l {d},{-d} h {w} l {-d},{d} Z',stroke,.65,colors[2]);rect(g,xx,yy,w,h,colors[0],stroke,.65)
  path(g,f'M {xx+w},{yy} l {d},{-d} v {h} l {-d},{d} Z',stroke,.65,colors[1])
 icons.append({'id':id,'parent':p.get('id'),'role':'schematic model; layer count is decorative','primitive':'perspective slabs','box':[x,y-11*scale,82*scale,59*scale]})

def papers(p,id,x,y,color):
 g=group(id,p)
 for k in range(3):
  xx=x+k*8;yy=y+k*5
  path(g,f'M {xx},{yy} h 17 l 6,6 v 23 h -23 Z',C[color],1,fill='white')
  path(g,f'M {xx+17},{yy} v 6 h 6 M {xx+4},{yy+12} h 14 M {xx+4},{yy+17} h 14 M {xx+4},{yy+22} h 11',C[color],.9)
 icons.append({'id':id,'parent':p.get('id'),'role':'sample collection','primitive':'vector document stack','box':[x,y,39,39]})

def title(p,prefix,x):
 rect(p,x+9,21,390,33,C['cyan'],rx=2)
 text(p,prefix+'-number',x+26,46,23,True,True)
 text(p,prefix+'-title',x+47,46,23,True,True,anchor='start')
 text(p,prefix+'-subtitle',x+18,74,13.5,anchor='start',color=C['muted'])

el('title').text='Federated training, client unlearning, and removal verification'
el('desc').text='GBHINDER-style reconstruction. Content preserved from source/fu_framework.svg; native vector illustrations and editable labels.'
d=el('defs')
for c in ('blue','red','green','orange'):
 m=el('marker',d,id='arrow-'+c,viewBox='0 0 10 8',refX=9,refY=4,markerWidth=4,markerHeight=3.2,orient='auto-start-reverse');path(m,'M 0,0 L 10,4 L 0,8 Z','none',0,C[c])
rect(root,0,0,W,H)
for id,x in [('training',16),('unlearning',436),('verification',856)]:
 p=group(id);rect(p,x,12,408,436,'white',C['ink'],1.25,12,stroke_dasharray='8 5',id=id+'-panel');title(p,id,x)
p=root.find(f".//{{{NS}}}g[@id='training']")
text(p,'clients-heading',96,105,15,True)
text(p,'randomize-heading',295,105,15,True)
noise=node(p,'noise-card',[197,118,89,192],fill='#eae4f0')
text(noise,'noise-heading',241.5,140,18,True)
text(noise,'noise-subtitle',241.5,157,13.5)
shuffle=node(p,'shuffler-card',[322,131,83,171],fill='#edf3f9',stroke=C['blue'],dash='5 4')
# Permutation is an abstract wiring illustration, with no extra scientific arrows.
g=group('shuffler-icon',shuffle)
for a,b in [(0,2),(1,0),(2,3),(3,1)]:path(g,f'M 341,{155+a*12} L 385,{155+b*12}',C['blue'],1.2)
for xx in [338,388]:
 for yy in [155,167,179,191]:el('circle',g,cx=xx,cy=yy,r=3.2,fill='white',stroke=C['blue'],stroke_width=1.3)
icons.append({'id':'shuffler-icon','parent':'shuffler-card','role':'optional permutation','primitive':'node wiring','box':[334,151,58,44]})
text(shuffle,'shuffler-heading',363.5,229,17,True)
text(shuffle,'shuffler-line-1',363.5,251,14)
text(shuffle,'shuffler-line-2',363.5,270,14)
for k,idx in enumerate(['1','2','j','n']):
 y=181+k*38;c='red' if idx=='j' else 'blue'
 client=node(p,'client-'+idx+'-card',[34,y-22,119,36],kind='input',fill='#fcf0ed' if idx=='j' else '#f7f9fb')
 database(client,'client-'+idx+'-icon',41,y-16,.7,c)
 text(client,'client-'+idx+'-label',96,y-8,19,color=C[c]);text(client,'client-'+idx+'-role',96,y+11,13.5,color=C[c] if idx=='j' else C['muted'])
 arrow(p,'client-'+idx+'-to-noise',[(156,y-3),(193,y-3)],c)
 for i,col in enumerate(['#a996be','#d6cce1','#b5cddb']):rect(noise,204,y-12+i*7,10,6,col)
 text(noise,'message-'+idx+'-label',249,y+3,19,color=C[c])
 arrow(p,'message-'+idx+'-to-shuffler',[(289,y-3),(318,y-3)],c)
arrow(p,'shuffler-to-history',[(363.5,306),(363.5,327)])
history=node(p,'history-card',[34,332,372,62],kind='representation',fill='#f1f1ef')
database(history,'history-icon',46,347,.9)
text(history,'history-heading',84,352,18,True,anchor='start')
text(history,'history-description',84,369,13.5,anchor='start')
text(history,'history-equation',237,388,18,color=C['blue'])
text(p,'privacy-boundary-1',220,415,14,color=C['muted'])
text(p,'privacy-boundary-2',220,433,14,color=C['muted'])

p=root.find(f".//{{{NS}}}g[@id='unlearning']")
g=node(p,'withdrawal-card',[452,88,115,47],kind='input',fill='#fcf0ed')
database(g,'withdrawal-icon',460,99,.63,'red');text(g,'withdrawal-heading',522,107,16,color=C['red']);text(g,'withdrawal-description',522,125,13.5)
g=node(p,'request-card',[596,88,232,47],fill='#faf0e7');text(g,'request-heading',712,107,17,True);text(g,'request-description',712,125,13.5)
arrow(p,'withdrawal-to-request',[(571,111),(590,111)],'red')
arrow(p,'request-to-recomputation',[(712,137),(712,149)],'blue')
g=node(p,'recomputation-card',[452,154,376,93],fill='#f2f2f0')
rect(g,452,154,376,27,C['cyan'],rx=3)
text(g,'recomputation-heading',640,173,18,True,True)
text(g,'recomputation-description',640,197,14)
text(g,'recomputation-retained',640,217,16)
text(g,'recomputation-clip',640,237,14,color=C['muted'])
arrow(p,'recomputation-to-replay',[(640,250),(640,263)])
g=node(p,'replay-card',[452,267,376,44],fill='#f1edf5');model(g,'replay-model',467,279,.5)
text(g,'replay-heading',667,285,18,True,True);text(g,'replay-description',667,304,14)
arrow(p,'replay-to-recovery',[(640,314),(640,326)])
g=node(p,'recovery-card',[452,330,376,44],fill='#eef3e9')
text(g,'recovery-heading',640,348,18,True,True);text(g,'recovery-description',640,367,14)
arrow(p,'recovery-to-model',[(640,377),(640,395)],'green')
g=node(p,'model-card',[484,399,312,35],kind='output',fill='#eef3e9')
model(g,'unlearned-model-icon',498,408,.43,True);text(g,'model-heading',665,424,21,True)

p=root.find(f".//{{{NS}}}g[@id='verification']")
rect(p,873,88,374,25,C['cyan'],rx=2);text(p,'evaluation-heading',1060,106,17,True,True)
for kind,yy,col,prefix in [('withdrawn',126,'red','withdrawn'),('clean',221,'green','clean')]:
 g=node(p,kind+'-evaluation',[873,yy,374,82],fill='#f5f5f3')
 papers(g,kind+'-sample-icon',893,yy+10,col)
 text(g,kind+'-samples-heading',918,yy+61,15,True,color=C[col]);text(g,kind+'-samples-description',918,yy+77,13.5)
 model(g,kind+'-model-icon',988,yy+23,.78)
 arrow(g,kind+'-samples-to-model',[(953,yy+37),(980,yy+37)],col)
 arrow(g,kind+'-model-to-result',[(1056,yy+37),(1080,yy+37)],'green')
 rect(g,1087,yy+8,150,65,'#eaf1e5',rx=5)
 if kind=='withdrawn':
  text(g,'mia-heading',1162,yy+28,16,True);text(g,'mia-value',1162,yy+47,14.5,True);text(g,'mia-description',1162,yy+65,13.5)
 else:
  text(g,'utility-heading',1162,yy+28,16,True);text(g,'utility-value',1162,yy+47,15.5,True);text(g,'utility-description',1162,yy+65,13.5)
arrow(p,'evaluations-to-diagnostic',[(1060,306),(1060,315)],'green')
g=group('diagnostic-card',p);path(g,'M 1060,319 L 1205,348 L 1060,377 L 915,348 Z',C['green'],1.5,'#eaf1e5')
nodes.append({'id':'diagnostic-card','spec_id':'diagnostic-card','panel':'verification','kind':'decision','box':[915,319,290,58]})
text(g,'diagnostic-heading',1060,349,16,True);text(g,'diagnostic-description',1060,364,14)
arrow(p,'diagnostic-yes',[(990,363),(972,391)],'green');arrow(p,'diagnostic-no',[(1130,363),(1148,391)],'red')
text(p,'diagnostic-yes-label',958,382,14,True,color=C['green']);text(p,'diagnostic-no-label',1164,382,14,True,color=C['red'])
g=node(p,'passed-card',[873,396,180,45],kind='output',fill='#eaf1e5');text(g,'passed-heading',963,411,16,True,color=C['green']);text(g,'passed-description-1',963,425,12);text(g,'passed-description-2',963,437,12)
g=node(p,'failed-card',[1067,396,180,45],kind='output',fill='#faece9');text(g,'failed-heading',1157,411,16,True,color=C['red']);text(g,'failed-description-1',1157,425,12);text(g,'failed-description-2',1157,437,12)
# Explicit endpoint reconciliation to source arrows.
for e in edges:
 id=e['id']
 if '-to-noise' in id:e.update(source=id.replace('-to-noise','-card'),target='noise-card')
 elif '-to-shuffler' in id:e.update(source='noise-card',target='shuffler-card')
 elif '-samples-to-model' in id:
  kind=id.split('-')[0];e.update(source=kind+'-sample-icon',target=kind+'-model-icon')
 elif '-model-to-result' in id:
  kind=id.split('-')[0];e.update(source=kind+'-model-icon',target='mia-heading' if kind=='withdrawn' else 'utility-heading')
 else:
  pairs={'shuffler-to-history':('shuffler-card','history-card'),'withdrawal-to-request':('withdrawal-card','request-card'),'request-to-recomputation':('request-card','recomputation-card'),'recomputation-to-replay':('recomputation-card','replay-card'),'replay-to-recovery':('replay-card','recovery-card'),'recovery-to-model':('recovery-card','model-card'),'evaluations-to-diagnostic':('evaluation-heading','diagnostic-card'),'diagnostic-yes':('diagnostic-card','passed-card'),'diagnostic-no':('diagnostic-card','failed-card')}
  e.update(zip(('source','target'),pairs[id]))
scene={'schema_version':1,'canvas':{'view_box':[0,0,W,H],'width_in':W/96,'background':'white'},'style_profile':'style-profile.md','source':'source/fu_framework.svg','typography':{'family':'Tinos','min_font_pt':8.25},'panels':[{'id':id,'box':[x,12,408,436]} for id,x in [('training',16),('unlearning',436),('verification',856)]] ,'nodes':nodes,'edges':edges,'labels':labels,'icons':icons}
(OUT/'scene-graph.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2)+'\n')
# All source labels and directed connectors are retained one-to-one.
new={e.get('id'):''.join(e.itertext()) for e in root.iter() if e.tag==f'{{{NS}}}text'}
assert new=={id:''.join(e.itertext()) for id,e in original.items()}
assert {e['id'] for e in edges}=={e.get('id') for e in old.iter() if e.get('marker-end')}
assert len([e.get('id') for e in root.iter() if e.get('id')])==len({e.get('id') for e in root.iter() if e.get('id')})
E.ElementTree(root).write(OUT/'figure.svg',encoding='utf-8',xml_declaration=True)
print(f'Generated figure.svg: {len(labels)} exact source labels; {len(edges)} retained arrows; native vectors only.')
