# ModelForge blender_run: bake solidify/bevel into every morph pose consistently.
# params: entries [{source, output}]. Preserve all source Blender files.
from pathlib import Path
import hashlib,json
reports=[]
for entry in params['entries']:
    source=Path(entry['source']);before=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    originals=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys]
    baked=[]
    for obj in originals:
        keys=obj.data.shape_keys
        for track in keys.animation_data.nla_tracks:track.mute=True
        keys.animation_data.action=None
        for key in keys.key_blocks:key.value=0
        bpy.context.view_layer.update()
        deps=bpy.context.evaluated_depsgraph_get()
        mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
        new=bpy.data.objects.new(obj.name+'_volume',mesh);bpy.context.collection.objects.link(new)
        new.matrix_world=obj.matrix_world.copy();new.shape_key_add(name='Basis')
        waves=[[0,.65,0,-.65],[0,-.35,1,.12],[0,.65,1,.25],[0,1,.4,0]]
        for key in list(keys.key_blocks)[1:]:
            name,slot=key.name.rsplit('_',1);clip=['idle','cast','guard','hit'].index(name);wave=waves[clip][int(slot)]
            newkey=new.shape_key_add(name=key.name)
            for vertex,src in zip(newkey.data,mesh.vertices):
                original=src.co
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
        new.data.shape_keys.animation_data_create()
        for old_track in keys.animation_data.nla_tracks:
            track=new.data.shape_keys.animation_data.nla_tracks.new();track.name=old_track.name
            for old_strip in old_track.strips:
                strip=track.strips.new(old_strip.name,int(old_strip.frame_start),old_strip.action)
                if hasattr(old_strip,'action_slot') and old_strip.action_slot:strip.action_slot=old_strip.action_slot
            track.mute=True
        baked.append(new)
        bpy.data.objects.remove(obj,do_unlink=True)
    out=Path(entry['output'])
    target=out/'editable-volume.blend'
    if target.exists():raise FileExistsError(target)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in baked:
        obj.select_set(True)
        for track in obj.data.shape_keys.animation_data.nla_tracks:track.mute=False
    bpy.context.view_layer.objects.active=baked[0]
    glb=out/'animated-volume.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_animations=True,export_nla_strips=True,export_morph=True,export_apply=False,export_cameras=False,export_lights=False)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    reports.append({'source_sha256':before,'glb':str(glb),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'vertices':sum(len(o.data.vertices) for o in baked)})
result['exports']=reports
