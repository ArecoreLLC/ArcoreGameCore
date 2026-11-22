# Executed inside ModelForge blender_run, not as a host Python program.
# params: output (fresh consumer directory), palette (source JSON), rig (authored sidecar).
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
rig=json.loads(Path(params['rig']).read_text(encoding='utf-8'))
rounded_volume = params.get('rounded_volume', False)
def point(p):return Vector(((p[0]/512-.5)*4,(.5-p[1]/512)*4,0.25))
arm_data=bpy.data.armatures.new('Authored skeleton')
arm=bpy.data.objects.new('Skeleton',arm_data);bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for spec in rig['bones']:
    bone=arm_data.edit_bones.new(spec['name']);bone.head=point(spec['head']);bone.tail=point(spec['tail']);bone.align_roll(Vector((0,0,1)))
    if spec.get('parent'):bone.parent=arm_data.edit_bones[spec['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
for obj in objects:
    obj.rotation_euler = (0,0,0)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for face in bm.faces:
        if face.normal.z < 0: face.normal_flip()
    bmesh.ops.dissolve_limit(bm, angle_limit=0.0001, verts=list(bm.verts), edges=list(bm.edges), delimit={'MATERIAL'})
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3 if rounded_volume else 1, use_grid_fill=True)
    bm.to_mesh(obj.data); bm.free()
    groups={b['name']:obj.vertex_groups.new(name=b['name']) for b in rig['bones']}
    for v in obj.data.vertices:
        # SVG layers are spaced by .008; outlines have a .003 offset.
        layer=int(math.floor(v.co.z/.008+0.0002))
        x=(v.co.x/4+.5)*512;y=(.5-v.co.y/4)*512
        weights={'root':1.0}
        for rule in rig['rules']:
            if layer not in rule['layers'] or x<rule.get('x_min',-1e9) or x>=rule.get('x_max',1e9):continue
            names=rule['bones']
            if len(names)==1:weights={names[0]:1.0}
            else:
                coord=x if rule['axis']=='x' else y
                t=max(0,min(1,.5+(coord-rule['split'])*rule.get('direction',1)/rule.get('blend',28)))
                t=t*t*(3-2*t);weights={names[0]:1-t,names[1]:t}
            break
        for name,weight in weights.items():
            if weight>0:groups[name].add([v.index],weight,'REPLACE')
    thickness = obj.vertex_groups.new(name='Volume thickness') if rounded_volume else None
    for v in obj.data.vertices:
        # A shared convex volume, preserving the authored front silhouette.
        dome=max(0.0,1-(v.co.x/2.1)**2)*max(0.0,1-(v.co.y/2.1)**2)
        # For deep shells, extrude the planar layers first: normal-based extrusion
        # of an already curved sheet can push its back through neighboring faces.
        v.co.z = v.co.z*1.8 + (0 if rounded_volume else 0.42)*dome
        if thickness:thickness.add([v.index],dome,'REPLACE')
    solid=obj.modifiers.new('Raised ink depth','SOLIDIFY');solid.thickness=1.35 if rounded_volume else 0.24;solid.offset=-1
    if thickness:
        solid.vertex_group=thickness.name;solid.thickness_vertex_group=0.18
    bevel=obj.modifiers.new('Soft enamel edge','BEVEL');bevel.width=0.055 if rounded_volume else 0.025;bevel.segments=3
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
# Bake neutral thickness/bevel before skinning: fixed topology, compact skeletal GLB.
for obj in objects:
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    if rounded_volume:
        for v in obj.data.vertices:
            dome=max(0.0,1-(v.co.x/2.1)**2)*max(0.0,1-(v.co.y/2.1)**2)
            v.co.z += 0.90*dome
    # Thickness is a modeling mask, never a skin influence.
    if rounded_volume:obj.vertex_groups.remove(obj.vertex_groups['Volume thickness'])
    modifier=obj.modifiers.new('Articulated skin','ARMATURE');modifier.object=arm
    obj.parent=arm
    for v in obj.data.vertices:
        total=sum(g.weight for g in v.groups)
        if total<=1e-8:raise ValueError('Unbound skin vertex')
        for g in list(v.groups):obj.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
scene.render.fps=24;scene.frame_start=1;scene.frame_end=17
clips=['idle','cast','guard','hit']
for clip_index,name in enumerate(clips):
    for pose in arm.pose.bones:pose.rotation_mode='XYZ'
    for sample in range(5):
        slot=sample if sample<4 else 0
        frame=1+sample*4
        for pose in arm.pose.bones:
            pose.rotation_euler=(0,0,math.radians(rig['clips'][name].get(pose.name,[0,0,0,0])[slot]))
            pose.keyframe_insert(data_path='rotation_euler',frame=frame,group=pose.name)
        root=arm.pose.bones['root']
        # Keep foot contacts stable; only the small idle breath translates the root.
        root.location=(0,([0,.012,0,-.012][slot] if name=='idle' else 0),0)
        root.keyframe_insert(data_path='location',frame=frame,group='root')
    action=arm.animation_data.action;action.name=name
    for sample in range(4):
        scene.frame_set(1+sample*4)
        scene.render.filepath=str(out/('frame_%02d.png'%(clip_index*4+sample)))
        bpy.ops.render.render(write_still=True)
    track=arm.animation_data.nla_tracks.new();track.name=name
    track.strips.new(name,1,action);track.mute=True;arm.animation_data.action=None
    for pose in arm.pose.bones:pose.rotation_euler=(0,0,0);pose.location=(0,0,0)
scene.frame_set(1);scene.render.filepath=''
bpy.ops.wm.save_as_mainfile(filepath=str(out/'editable.blend'))
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=arm
for track in arm.animation_data.nla_tracks:track.mute=False
bpy.ops.export_scene.gltf(filepath=str(out/'animated.glb'),export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_skins=True,export_apply=False,export_cameras=False,export_lights=False)
result['pipeline']={'type':'svg-articulated-volume-v2' if rounded_volume else 'svg-articulated-v1','bones':len(rig['bones']),'clips':clips,'frames':16,'frame_size':384,'rig':params['rig']}
