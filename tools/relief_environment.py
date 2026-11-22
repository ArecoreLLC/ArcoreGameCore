# ModelForge blender_run environment stage. params: output (new consumer directory).
from pathlib import Path
import math, random
out=Path(params['output']);out.mkdir(parents=True,exist_ok=True)
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.render.film_transparent=False;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard';scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(0.008,0.016,0.035,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
def material(name,rgb,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=(*rgb,1);b.inputs['Roughness'].default_value=.55;b.inputs['Metallic'].default_value=.15
 b.inputs['Emission Color'].default_value=(*rgb,1);b.inputs['Emission Strength'].default_value=emission
 if not emission:
  noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18;noise.inputs['Detail'].default_value=3
  bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.07
  m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],b.inputs['Normal'])
 return m
stone=material('Deep blue inkstone',(.025,.05,.075));edge=material('Cut slate',(.065,.105,.13));dark=material('Distant blueprint',(.008,.018,.035));glow=material('Cyan inscription',(.07,.7,.5),2)
def cube(name,loc,scale,mat,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:m=o.modifiers.new('Worn edges','BEVEL');m.width=bevel;m.segments=3
 return o
cube('Foundation',(0,1,-.35),(18,18,.6),stone)
for x in range(-5,6):
 for y in range(-4,7):
  cube('Blueprint tile',(x*1.15,y*1.15,0),(1.08,1.08,.12),edge,.025)
for x in [-4.2,4.2]:
 for y,h in [(1.5,3.3),(4.5,5.3)]:
  cube('Pillar plinth',(x,y,.3),(1.3,1.3,.6),edge)
  cube('Fractured pillar',(x,y,h/2+.5),(.65,.75,h),stone)
  cube('Pillar crown',(x,y,h+.45),(1.05,1.05,.28),edge)
  cube('Glowing seam',(x,y-.39,h*.55),(.035,.025,h*.55),glow,0)
# A broken portal frames the skyline; the central sightline stays clear.
for i in range(11):
 a=math.pi*i/10
 x=3.4*math.cos(a);z=3.5+3.4*math.sin(a)
 o=cube('Broken archivault arch',(x,5.2,z),(.83,.85,.65),edge,.06);o.rotation_euler.y=-a
random.seed(8417)
for i in range(18):
 x=random.choice([-1,1])*random.uniform(4.8,8);y=random.uniform(4,10);h=random.uniform(3,8)
 cube('Distant Static tower',(x,y,h/2),(.6,.8,h),dark,.03)
bpy.ops.mesh.primitive_torus_add(major_radius=2.1,minor_radius=.025,major_segments=96,minor_segments=6,location=(0,10,5.2),rotation=(math.pi/2,0,0))
bpy.context.object.name='Blueprint eclipse';bpy.context.object.data.materials.append(glow)
for i in range(14):
 x=random.choice([-1,1])*random.uniform(3.6,6.5);y=random.uniform(-3,4)
 o=cube('Loose stone',(x,y,.18),(.5,.45,.35),stone);o.rotation_euler.z=random.random()*3
bpy.ops.object.camera_add(location=(0,-10,7.8));cam=bpy.context.object;cam.rotation_euler=(Vector((0,2,2.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13;scene.camera=cam
for loc,power,color,size in [((-4,-4,10),700,(.58,.82,1),8),((4,2,7),500,(.3,1,.7),6),((0,6,9),700,(.6,.55,1),5)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.color=color;l.data.size=size;l.rotation_euler=(Vector((0,1,0))-l.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(out/'environment_raw.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'editable.blend'))
result['pipeline']={'type':'relief-environment-v1','output':str(out),'size':1024}
