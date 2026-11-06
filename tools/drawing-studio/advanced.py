"""Construction-based painting plans and reproducible digital stock-color recipes."""
from collections import Counter, defaultdict
import colorsys
import itertools
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

MODEL = 'Optical-density digital stock mixture: channel = exp(sum(weight * log(base channel))).'
NOTE = 'Digital estimates in 100 equal stock parts; physical pigments and paint brands require calibration.'


def rgb(color):
    if color.startswith('#'):
        return tuple(int(color[i:i+2],16) for i in (1,3,5))
    return tuple(map(int,color[4:-1].split(',')))


def density(color):
    return tuple(-math.log(max(1,c)/255) for c in color)


def mixed_color(bases, weights):
    return tuple(round(255*math.exp(-sum(w*density(b)[c] for b,w in zip(bases,weights)))) for c in range(3))


def solve(matrix, vector):
    """Small pivoted linear solve; singular stock subsets are skipped."""
    rows=[list(row)+[value] for row,value in zip(matrix,vector)]
    n=len(vector)
    for column in range(n):
        pivot=max(range(column,n),key=lambda j:abs(rows[j][column]))
        if abs(rows[pivot][column])<1e-10:
            return None
        rows[column],rows[pivot]=rows[pivot],rows[column]
        divisor=rows[column][column]
        rows[column]=[v/divisor for v in rows[column]]
        for j in range(n):
            if j!=column:
                factor=rows[j][column]
                rows[j]=[a-factor*b for a,b in zip(rows[j],rows[column])]
    return [row[-1] for row in rows]


def fit_recipe(target, bases):
    """Nearest nonnegative convex mixture, using at most four of six stocks."""
    target_d=density(target);vectors=[density(b) for b in bases]
    best=None
    for size in range(1,min(4,len(bases))+1):
        for selected in itertools.combinations(range(len(bases)),size):
            origin=vectors[selected[0]]
            differences=[tuple(vectors[j][c]-origin[c] for c in range(3)) for j in selected[1:]]
            if differences:
                matrix=[[sum(a*b for a,b in zip(u,v)) for v in differences] for u in differences]
                values=[sum(v[c]*(target_d[c]-origin[c]) for c in range(3)) for v in differences]
                solution=solve(matrix,values)
                if solution is None:
                    continue
                weights=[1-sum(solution)]+solution
            else:
                weights=[1.0]
            if min(weights)<-1e-8:
                continue
            predicted=[sum(w*vectors[j][c] for j,w in zip(selected,weights)) for c in range(3)]
            error=sum((a-b)**2 for a,b in zip(predicted,target_d))
            # Prefer a simpler recipe when the density fit differs imperceptibly.
            score=error+.000015*sum(w>.004 for w in weights)
            if best is None or score<best[0]:
                full=[0.0]*len(bases)
                for j,w in zip(selected,weights):
                    full[j]=max(0,w)
                best=(score,full)
    weights=best[1]
    total=sum(weights);percent=[w/total*100 for w in weights]
    parts=[int(p) for p in percent]
    for i in sorted(range(len(parts)),key=lambda i:percent[i]-parts[i],reverse=True)[:100-sum(parts)]:
        parts[i]+=1
    mixture=mixed_color(bases,[p/100 for p in parts])
    return {'target_rgb':list(target),'parts':parts,'mixed_rgb':list(mixture),'rgb_rmse':round(math.sqrt(sum((a-b)**2 for a,b in zip(target,mixture))/3),2)}


def generate_bases(strokes):
    bins=defaultdict(list)
    for op in strokes:
        color=rgb(op['color']);bins[tuple(c//12 for c in color)].append(color)
    candidates=[tuple(round(sum(c[i] for c in colors)/len(colors)) for i in range(3)) for colors in bins.values() if len(colors)>=3]
    if not candidates:
        candidates=[(120,115,75)]
    dark=min(candidates,key=sum)
    if sum(dark)>600:dark=(18,22,18)
    bases=[(252,251,247),dark]
    # Chromatic diversity is weighted more than value, already covered by white/dark.
    def feature(color):
        mean=max(20,sum(color)/3)
        return tuple(c/mean for c in color)+(sum(color)/765*.35,)
    pool=[c for c in candidates if 120<sum(c)<690]+[(220,176,90),(113,82,50),(87,120,75),(55,125,126)]
    for _ in range(4):
        candidate=max((c for c in pool if c not in bases),key=lambda c:min(sum((a-b)**2 for a,b in zip(feature(c),feature(base))) for base in bases))
        bases.append(candidate)
    def name(color,i):
        if i==0:return 'Warm white'
        if i==1:return 'Deep shadow'
        h,l,s=colorsys.rgb_to_hls(*(c/255 for c in color))
        if s<.12:return 'Soft gray'
        if h<.08 or h>.95:return 'Earth red'
        if h<.18:return 'Earth ochre' if l>.45 else 'Warm umber'
        if h<.42:return 'Deep forest' if l<.30 else 'Moss green'
        if h<.60:return 'Cool teal'
        if h<.77:return 'Blue violet'
        return 'Muted rose'
    return [{'id':f'B{i+1}','name':name(c,i),'rgb':list(c),'hex':'#'+''.join(f'{v:02x}' for v in c)} for i,c in enumerate(bases)]


def construction_parts(data):
    ellipses=[(i,g) for i,g in enumerate(data['guides']) if g['type']=='ellipse' or (g['type']=='contour' and g.get('closed') and g.get('stage',2)<2)]
    if not ellipses:
        raise ValueError('Advanced painting needs at least one construction ellipse in the lesson.')
    if len(ellipses)>64:
        raise ValueError('Advanced mode supports at most 64 construction ellipses; simplify the lesson.')
    # Guide indices refer to the exact ellipses drawn during construction.
    if data.get('study')=='spider' and len(ellipses)==32:
        definitions=[('abdomen','Abdomen',[0]),('head','Head',[1]),
            ('left-eye','Large left eye',[2]),('right-eye','Large right eye',[3]),('small-eyes','Small eyes',list(range(4,10))),
            ('left-back','Left rear leg',[10,11]),('left-front','Left front leg',[12,13,14]),('left-inner','Left inner leg',[15,16]),
            ('left-palp','Left feeler',[17,18]),('right-palp','Right feeler',[19]),('right-front','Right front leg',[20,21,22]),
            ('right-middle','Right middle leg',[23,24,25]),('right-rear','Right rear leg',[26,27,28]),('right-back','Right far leg',[29,30,31])]
        order=['shadow','abdomen','left-back','right-back','left-inner','right-rear','head','left-front','right-middle','right-front','left-palp','right-palp','small-eyes','left-eye','right-eye']
    else:
        definitions=[(f'shape-{j+1}',g.get('proposed_role') or f'Construction shape {j+1}',[j]) for j,(_,g) in enumerate(ellipses)]
        order=['shadow']+[p[0] for p in definitions]
    parts=[{'id':'shadow','name':'Ground / uncovered areas','guide_indices':[]}]
    for identifier,name,indices in definitions:
        parts.append({'id':identifier,'name':name,'guide_indices':[ellipses[i][0] for i in indices]})
    parts.sort(key=lambda part:order.index(part['id']))
    return parts


def region_map(data,parts):
    """Exclusive ownership masks from the very same construction polygons."""
    size=(640,349);regions=Image.new('L',size,0);draw=ImageDraw.Draw(regions)
    indices={part['id']:i for i,part in enumerate(parts)}
    # Body masses first; smaller shapes overwrite them so eyes and joints stay reserved.
    mappings=[];geometry=[]
    for part in parts:
        for index in part['guide_indices']:
            guide=data['guides'][index]
            xs=[p[0] for p in guide['points']];ys=[p[1] for p in guide['points']]
            area=(max(xs)-min(xs))*(max(ys)-min(ys))
            mappings.append((area,indices[part['id']],guide['points']))
            points=guide['points']
            geometry.append((indices[part['id']],sum(p[0] for p in points[:-1])/max(1,len(points)-1)/2,sum(p[1] for p in points[:-1])/max(1,len(points)-1)/2,max(2,(max(xs)-min(xs))/4),max(2,(max(ys)-min(ys))/4)))
    for _,index,points in sorted(mappings,reverse=True):
        draw.polygon([(round(x/2),round(y/2)) for x,y in points],fill=index)
    # Fill silhouette slivers just outside a guide with the nearest construction mass.
    lookup=regions.load()
    for op in data['stages'][5]:
        x=min(639,max(0,int(op['x']/2)));y=min(348,max(0,int(op['y']/2)))
        if lookup[x,y]:continue
        best=(float('inf'),0)
        for index,cx,cy,rx,ry in geometry:
            distance=((x-cx)/rx)**2+((y-cy)/ry)**2
            if distance<best[0]:best=(distance,index)
        if best[0]<1.65:
            draw.ellipse((x-2,y-2,x+2,y+2),fill=best[1])
    return regions


def sketch_schedules(data,parts,regions):
    """Finish linework and shading on each form; retain contour stroke order."""
    pixel=regions.load(); groups={p['id']:[] for p in parts}
    for stage in (2,3):
        for op in data['stages'][stage]:
            if op.get('kind')=='pencil':
                x=(op['a'][0]+op['b'][0])/2; y=(op['a'][1]+op['b'][1])/2
            else:x,y=op['x'],op['y']
            owner=parts[pixel[min(639,max(0,int(x/2))),min(348,max(0,int(y/2)))]]['id']
            tagged={**op,'sketch_part_id':owner}
            if op.get('kind')!='pencil':tagged['part_id']=owner
            groups[owner].append(tagged)
    # Uncovered/background marks come last, after the identified forms.
    ordered=parts[1:]+parts[:1]
    schedules=[{'id':p['id'],'name':p['name'],'operations':groups[p['id']]} for p in ordered if groups[p['id']]]
    split=max(1,len(schedules)//2)
    data['sketch_schedules']=[schedules[:split],schedules[split:]]
    for stage,schedule in zip((2,3),data['sketch_schedules']):
        data['stages'][stage]=[op for part in schedule for op in part['operations']]
    data['instructions'][2]={'title':'Sketch the first forms','text':'Complete the contours and graphite shading of each form before moving on.'}
    data['instructions'][3]={'title':'Sketch the remaining forms','text':'Follow each remaining form with detailed lines, then shade it.'}


def build_advanced(data):
    bases=generate_bases(data['stages'][5]);parts=construction_parts(data);regions=region_map(data,parts)
    sketch_schedules(data,parts,regions)
    by_color=defaultdict(list)
    for op in data['stages'][5]:
        color=rgb(op['color']);by_color[tuple(min(255,round(c/16)*16) for c in color)].append(color)
    colors={key:tuple(round(sum(c[i] for c in values)/len(values)) for i in range(3)) for key,values in by_color.items()}
    recipes=[];color_recipe={};base_rgb=[b['rgb'] for b in bases]
    for key,target in colors.items():
        recipe=fit_recipe(target,base_rgb);recipe['id']=f'M{len(recipes)+1:03}';recipe['uses']=len(by_color[key]);recipes.append(recipe);color_recipe[key]=recipe
    grouped={p['id']:[[],[]] for p in parts};pixel=regions.load()
    usage={p['id']:Counter() for p in parts}
    for layer_index,stage in enumerate((4,5)):
        for op in data['stages'][stage]:
            part=parts[pixel[min(639,max(0,int(op['x']/2))),min(348,max(0,int(op['y']/2)))]]
            color=rgb(op['color']);key=tuple(min(255,round(c/16)*16) for c in color)
            recipe=color_recipe.get(key)
            if recipe is None:
                recipe=fit_recipe(color,base_rgb);recipe['id']=f'M{len(recipes)+1:03}';recipe['uses']=1;recipes.append(recipe);color_recipe[key]=recipe
            painted={**op,'part_id':part['id'],'recipe_id':recipe['id'],'color':'rgb('+','.join(map(str,recipe['mixed_rgb']))+')'}
            grouped[part['id']][layer_index].append(painted);usage[part['id']][recipe['id']]+=1
    schedules=[]
    for p in parts:
        broad,fine=grouped[p['id']]
        p['broad_strokes']=len(broad);p['fine_strokes']=len(fine);p['recipe_ids']=[r for r,_ in usage[p['id']].most_common()]
        if broad or fine:
            schedules.append({'id':p['id'],'name':p['name'],'broad_count':len(broad),'operations':broad+fine})
    split=max(1,len(schedules)//2)
    data['stages'][4]=[op for p in schedules[:split] for op in p['operations']]
    data['stages'][5]=[op for p in schedules[split:] for op in p['operations']]
    data['paint_schedules']=[schedules[:split],schedules[split:]]
    data['advanced']=True
    data['instructions'][4]={'title':'Paint the first forms','text':'Finish each construction region with its base coat and smaller paint strokes before moving to the next form.'}
    data['instructions'][5]={'title':'Complete the remaining forms','text':'Build the remaining detected forms region by region using the same six stock colors and their calculated mixtures.'}
    manifest={'version':1,'model':MODEL,'note':NOTE,'base_colors':bases,'recipes':recipes,'parts':parts,'paint_order':[p['id'] for p in schedules],'mean_rgb_rmse':round(sum(r['rgb_rmse']*r['uses'] for r in recipes)/sum(r['uses'] for r in recipes),2),'max_rgb_rmse':max(r['rgb_rmse'] for r in recipes)}
    return data,manifest,regions


def schedule_count(schedule,fraction):
    if not schedule:return 0,None,0
    position=max(0,min(1,fraction))*len(schedule)
    index=min(len(schedule)-1,int(position));local=min(1,position-index)
    count=sum(len(p['operations']) for p in schedule[:index])+int(local*len(schedule[index]['operations']))
    return count,schedule[index],local


def selected_recipes(manifest,limit=8):
    by_id={r['id']:r for r in manifest['recipes']}
    pool=[]
    # Include each form's dominant mixture, then choose a visually diverse lesson.
    for part in manifest['parts']:
        if part['recipe_ids']:
            candidate=by_id[part['recipe_ids'][0]]
            if candidate not in pool:pool.append(candidate)
    for candidate in sorted(manifest['recipes'],key=lambda r:r['uses'],reverse=True):
        if len(pool)>=60:break
        if candidate not in pool:pool.append(candidate)
    chosen=[max(pool,key=lambda r:r['uses'])]
    while len(chosen)<min(limit,len(pool)):
        candidate=max((r for r in pool if r not in chosen),key=lambda r:min(sum((a-b)**2 for a,b in zip(r['target_rgb'],s['target_rgb'])) for s in chosen))
        chosen.append(candidate)
    return chosen


def palette_sheet(manifest,path,font):
    recipes=selected_recipes(manifest,12)
    sheet=Image.new('RGB',(1500,500+len(recipes)*90),(250,248,241));d=ImageDraw.Draw(sheet)
    d.text((55,28),'DRAWING ATELIER / SIX STOCK COLORS',font=font(18),fill=(62,92,71))
    d.text((55,72),'A small palette. Many useful mixtures.',font=font(36,True),fill=(40,57,47))
    for i,base in enumerate(manifest['base_colors']):
        x=55+i*236;d.rounded_rectangle((x,150,x+205,240),radius=10,fill=tuple(base['rgb']))
        d.text((x,255),f'{base["id"]}  {base["name"]}',font=font(19),fill=(40,57,47));d.text((x,284),base['hex'],font=font(16),fill=(116,123,112))
    d.text((55,340),'Target  /  calculated mixture             Recipe in 100 equal stock parts',font=font(21),fill=(62,92,71))
    d.text((55,378),'Digital stock-color estimates; test real paints with a physical swatch.',font=font(18),fill=(116,123,112))
    for i,recipe in enumerate(recipes):
        y=430+i*90
        d.rounded_rectangle((55,y,125,y+58),radius=6,fill=tuple(recipe['target_rgb']))
        d.rounded_rectangle((135,y,205,y+58),radius=6,fill=tuple(recipe['mixed_rgb']))
        text=' + '.join(f'{parts} {base["id"]}' for parts,base in zip(recipe['parts'],manifest['base_colors']) if parts)
        d.text((235,y+4),f'{recipe["id"]}   {text}',font=font(22),fill=(40,57,47))
        d.text((235,y+36),f'RGB approximation error: {recipe["rgb_rmse"]:.1f} / 255',font=font(16),fill=(116,123,112))
    path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)


def mixing_frame(manifest,recipe,progress,width,font):
    """Deposit ratio-sized paint portions, fold them together, then show the mix."""
    s=width/960;image=Image.new('RGB',(width,round(650*s)),(250,248,241));d=ImageDraw.Draw(image)
    def text(x,y,value,size=18,color=(40,57,47),serif=False):
        d.text((round(x*s),round(y*s)),value,font=font(max(8,round(size*s)),serif),fill=color)
    text(38,25,'DRAWING ATELIER / COLOR MIXING',14,(62,92,71));text(38,62,f'{recipe["id"]}  Build the mixture',32,serif=True)
    for i,base in enumerate(manifest['base_colors']):
        x=40+i*151
        d.rounded_rectangle(tuple(round(v*s) for v in (x,127,x+124,178)),radius=round(7*s),fill=tuple(base['rgb']))
        text(x,188,f'{base["id"]} {base["name"]}',13);text(x,212,f'{recipe["parts"][i]} parts',16)
    text(40,260,'1  Measure' if progress<.35 else '2  Fold and blend' if progress<.8 else '3  Compare and use',21,serif=True)
    bounds=(40,303,625,534)
    d.rounded_rectangle(tuple(round(v*s) for v in bounds),radius=round(20*s),fill=(235,232,220),outline=(215,214,200))
    cx,cy=330,419
    blend=max(0,min(1,(progress-.35)/.45));target=tuple(recipe['mixed_rgb'])
    for i,(base,parts) in enumerate(zip(manifest['base_colors'],recipe['parts'])):
        if not parts:continue
        angle=i/6*math.tau
        deposit=min(1,progress/.35)
        x=cx+math.cos(angle)*165*(1-blend);y=cy+math.sin(angle)*64*(1-blend)
        # Equal aspect ratios make visible paint-portion area proportional to parts.
        radius=90*math.sqrt(parts/100)*deposit
        color=tuple(round(c*(1-blend)+t*blend) for c,t in zip(base['rgb'],target))
        d.ellipse(tuple(round(v*s) for v in (x-radius,y-radius*.7,x+radius,y+radius*.7)),fill=color)
        if blend<.95:
            text(x-radius,y+radius*.7+5,base['id'],12)
    if blend>0:
        for k in range(5):
            angle=progress*math.tau*3+k*1.2
            x=cx+math.cos(angle)*64*(1-blend);y=cy+math.sin(angle)*35*(1-blend)
            color=tuple(min(255,c+round((1-blend)*22)) for c in target)
            d.arc(tuple(round(v*s) for v in (x-90,y-42,x+90,y+42)),start=k*30,end=k*30+210,fill=color,width=max(1,round(5*s)))
    for j,(label,color) in enumerate((('REFERENCE TARGET',recipe['target_rgb']),('CALCULATED MIX',recipe['mixed_rgb']))):
        y=306+j*118;text(680,y,label,13,(116,123,112))
        d.rounded_rectangle(tuple(round(v*s) for v in (680,y+25,918,y+100)),radius=round(8*s),fill=tuple(color))
    ratio=' + '.join(f'{p} {b["id"]}' for p,b in zip(recipe['parts'],manifest['base_colors']) if p)
    text(40,558,ratio,20)
    uses=[p['name'] for p in manifest['parts'] if recipe['id'] in p['recipe_ids']]
    text(40,588,'Use on: '+', '.join(uses[:2]) if uses else 'Use on: detail and transitional tones',14)
    text(40,619,'100 total parts / digital estimate / test physical paints separately',13,(116,123,112))
    return image


def export_mixing(manifest,path,width,fps,font):
    recipes=selected_recipes(manifest,8);frames=[];durations=[]
    # A shared palette sampled from deposits, intermediate blends, and final mixtures.
    canvas=Image.new('RGB',(480,325*len(recipes)*3))
    for i,r in enumerate(recipes):
        for j,p in enumerate((.25,.60,1)):
            canvas.paste(mixing_frame(manifest,r,p,480,font),(0,(i*3+j)*325))
    palette=canvas.quantize(colors=256)
    for recipe in recipes:
        count=max(8,round(fps*3))
        for i in range(count):
            frame=mixing_frame(manifest,recipe,i/(count-1),width,font)
            frames.append(frame.quantize(palette=palette,dither=Image.Dither.NONE))
            durations.append(round((i+1)*300/count)*10-round(i*300/count)*10)
        durations[-1]+=700
    path.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(path,save_all=True,append_images=frames[1:],loop=0,duration=durations,disposal=1,optimize=False)
    with Image.open(path) as gif:
        duration=0
        for i in range(gif.n_frames):gif.seek(i);gif.load();duration+=gif.info.get('duration',0)
        return {'path':str(path.resolve()),'frames':gif.n_frames,'size':list(gif.size),'duration_ms':duration,'loop':gif.info.get('loop'),'recipes_shown':[r['id'] for r in recipes]}
