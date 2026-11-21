extends SpotLight3D
## Shadow-free, diffuse-only capture fill, restricted to opted-in character meshes.
var original_layers := {}
func configure(targets: Array, layer := 20) -> void:
    light_cull_mask=1<<(layer-1)
    shadow_enabled=false
    light_specular=0.0
    light_color=Color("fff7ef")
    light_energy=0.0
    spot_range=20.0
    spot_angle=65.0
    spot_attenuation=1.0
    for target in targets:
        var meshes: Array=target.find_children("*","GeometryInstance3D",true,false)
        if target is GeometryInstance3D:meshes.append(target)
        for mesh in meshes:
            original_layers[mesh]=mesh.layers
            mesh.layers|=light_cull_mask
func _process(_delta: float) -> void:
    var camera := get_viewport().get_camera_3d()
    if camera:
        global_transform=camera.global_transform
        translate_object_local(Vector3(-.4,.5,0))
## Call while the scene is alive if removing the fill without unloading the scene.
## Never mutate mesh layers from _exit_tree: renderer teardown is already in progress.
func release_targets() -> void:
    light_energy=0.0
    light_cull_mask=0
    for mesh in original_layers:
        if is_instance_valid(mesh) and mesh.is_inside_tree():mesh.layers=original_layers[mesh]
    original_layers.clear()
