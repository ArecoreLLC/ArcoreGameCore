# Executed inside ModelForge blender_run, not as a host Python program.
# params: output (new consumer directory), palette (source JSON), preview_only.
import os, json, math
from pathlib import Path
out = Path(params['output'])
out.mkdir(parents=True, exist_ok=True)
palette = json.loads(Path(params['palette']).read_text())['materials']
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
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
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    bm.to_mesh(obj.data); bm.free()
    for v in obj.data.vertices:
        # A shared convex volume, preserving the authored front silhouette.
        dome=max(0.0,1-(v.co.x/2.1)**2)*max(0.0,1-(v.co.y/2.1)**2)
        v.co.z = v.co.z*1.8 + 0.42*dome
    solid=obj.modifiers.new('Raised ink depth','SOLIDIFY');solid.thickness=0.24;solid.offset=-1
    bevel=obj.modifiers.new('Soft enamel edge','BEVEL');bevel.width=0.025;bevel.segments=3
    for mat in obj.data.materials:
        key=mat.name.split('.')[0]
        rgba=palette.get(key,[0.12,0.3,0.35,1]);rgb=rgba[:3]
        mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=tuple(v**2.2 for v in rgb)+(1,)
        bs.inputs['Alpha'].default_value=rgba[3] if len(rgba)>3 else 1
        bs.inputs['Metallic'].default_value=0.18
        bs.inputs['Roughness'].default_value=0.43
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
# Morph-key clips remain editable and exportable, not just rendered vertex poses.
base={o.name:[v.co.copy() for v in o.data.vertices] for o in objects}
for obj in objects:obj.shape_key_add(name='Basis')
clip_names=['idle','cast','guard','hit']
# Anticipation, strike and recovery have distinct silhouettes.
waves=[[0,.65,0,-.65],[0,-.35,1,.12],[0,.65,1,.25],[0,1,.4,0]]
for frame in range(16):
    clip=frame//4;wave=waves[clip][frame%4]
    for obj in objects:
        key=obj.shape_key_add(name=clip_names[clip]+'_'+str(frame%4))
        for vertex,original in zip(key.data,base[obj.name]):
            v=original.copy();height=max(0,min(1,(v.y+1.8)/3.6))
            # Core rotation, springy extremities and changing depth catch the key light.
            edge=min(1,abs(v.x)/1.4)
            if clip==1:
                v.x+=height*.30*wave;v.y-=.07*wave
                v.z+=wave*(.18*height+.12*edge)
            elif clip==2:
                v.y=-1.8+(v.y+1.8)*(1-.085*wave);v.x*=1+.025*wave
                v.z+=.12*wave*height
            elif clip==3:
                v.x-=height*.26*wave;v.y-=.06*wave*edge;v.z-=.12*wave*height
            else:
                v.y+=height*.035*wave;v.x+=.018*wave*edge*(1 if v.x>0 else -1)
                v.z+=.055*wave*height
            vertex.co=v
        key.value=1
    scene.render.filepath=str(out/('frame_%02d.png'%frame))
    bpy.ops.render.render(write_still=True)
    for obj in objects:obj.data.shape_keys.key_blocks[-1].value=0
# Four independent NLA clips, with interpolation between authored 3D poses.
scene.render.fps=24
scene.frame_start=1;scene.frame_end=17
for obj in objects:
    keys=obj.data.shape_keys
    for clip,name in enumerate(clip_names):
        for slot in range(4):
            key=keys.key_blocks[1+clip*4+slot]
            for sample in range(5):
                active=sample if sample<4 else (0 if clip==0 else 3)
                key.value=1.0 if active==slot else 0.0
                key.keyframe_insert(data_path='value',frame=1+sample*4,group=name)
        action=keys.animation_data.action;action.name=name+'_'+obj.name
        track=keys.animation_data.nla_tracks.new();track.name=name
        track.strips.new(name,1,action)
        track.mute=True
        keys.animation_data.action=None
        for key in keys.key_blocks:key.value=0
scene.frame_set(1)
scene.render.filepath=''
bpy.ops.wm.save_as_mainfile(filepath=str(out/'editable.blend'))
# Export animated morph targets for the browser/PC review, with no scene lights/camera.
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
for obj in objects:
    for track in obj.data.shape_keys.animation_data.nla_tracks:track.mute=False
bpy.ops.export_scene.gltf(filepath=str(out/'animated.glb'),export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_morph=True,export_apply=False,export_cameras=False,export_lights=False)
result['pipeline']={'type':'svg-volume-v2','frames':16,'frame_size':384,'output':str(out),'clips':clip_names,'depth':.24,'dome':.42}
