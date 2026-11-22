# Executed inside ModelForge blender_run, not as a host Python program.
# params: output (new consumer directory), palette (source JSON), preview_only.
import os, json, math
from pathlib import Path
out = Path(params['output'])
out.mkdir(parents=True, exist_ok=True)
palette = json.loads(Path(params['palette']).read_text())['materials']
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 384
scene.render.resolution_y = 384
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'
scene.world.color = (0.16,0.16,0.16)
for obj in objects:
    obj.rotation_euler = (0,0,0)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for face in bm.faces:
        if face.normal.z < 0: face.normal_flip()
    bmesh.ops.dissolve_limit(bm, angle_limit=0.0001, verts=list(bm.verts), edges=list(bm.edges), delimit={'MATERIAL'})
    bm.to_mesh(obj.data); bm.free()
    solid=obj.modifiers.new('Raised ink depth','SOLIDIFY');solid.thickness=0.055;solid.offset=-1
    bevel=obj.modifiers.new('Soft enamel edge','BEVEL');bevel.width=0.012;bevel.segments=3
    for mat in obj.data.materials:
        key=mat.name.split('.')[0]
        rgba=palette.get(key,[0.12,0.3,0.35,1]);rgb=rgba[:3]
        mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=tuple(v**2.2 for v in rgb)+(1,)
        bs.inputs['Alpha'].default_value=rgba[3] if len(rgba)>3 else 1
        bs.inputs['Metallic'].default_value=0.18
        bs.inputs['Roughness'].default_value=0.32
        if max(rgb)>0.8 and min(rgb)>0.3:
            bs.inputs['Emission Color'].default_value=tuple(v**2.2 for v in rgb)+(1,)
            bs.inputs['Emission Strength'].default_value=0.15
bpy.ops.object.camera_add(location=(0,-0.20,8))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0.1))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=4.45;scene.camera=cam
for name, loc, power, color, size in [('Key',(-3,4,5),450,(0.82,0.94,1),4),('Rim',(3,1,3),300,(0.40,1,0.85),3),('Fill',(0,-3,4),140,(0.75,0.65,1),4)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object;light.name=name;light.data.energy=power;light.data.color=color;light.data.shape='DISK';light.data.size=size
    light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
# Store original positions: every subject follows the identical four-clip motion contract.
base={o.name:[v.co.copy() for v in o.data.vertices] for o in objects}
count=1 if params.get('preview_only',False) else 16
for frame in range(count):
    clip=frame//4;phase=(frame%4)/3;wave=math.sin(phase*math.pi)
    for obj in objects:
        for vertex, original in zip(obj.data.vertices,base[obj.name]):
            v=original.copy();height=max(0,min(1,(v.y+1.8)/3.6))
            if clip==1: v.x+=height*0.22*wave;v.y-=0.035*wave
            elif clip==2: v.y=-1.8+(v.y+1.8)*(1-0.06*wave);v.x-=height*0.06*wave
            elif clip==3: v.x-=height*0.20*wave
            else:v.y+=height*0.018*wave
            vertex.co=v
        obj.data.update()
    scene.render.filepath=str(out/('frame_%02d.png'%frame))
    bpy.ops.render.render(write_still=True)
for obj in objects:
    for vertex, original in zip(obj.data.vertices,base[obj.name]):vertex.co=original
scene.render.filepath=''
bpy.ops.wm.save_as_mainfile(filepath=str(out/'editable.blend'))
result['pipeline']={'type':'svg-relief-v1','frames':count,'frame_size':384,'output':str(out),'materials':[m.name for o in objects for m in o.data.materials]}
