extends RefCounted
## GameCore world-life kit (workflow ambient-world-life): shared helpers for ambient life in a Godot 4
## game. Merged vertex-colour meshes (one draw call per creature part), cached materials and shaders
## (flutter cloth), shore and water placement, a world-life clock that follows game time (also under
## Movie Maker), a night amount, a song beat clock, synthesised sounds, simple birds, and the
## attention registry (ping/best_ping) that lets characters glance at whatever just leapt or flew by.
##
## World contract: the node passed as `world` provides height_at(x, z) -> float (terrain height; water
## below 0). For sea surfaces it may also provide wave_at(Vector2, seconds) -> float and a float
## property ocean_elapsed; otherwise the sea is flat at y = 0.
## The game advances KIT.time each frame (a root node's _process) and may set effects_volume to a
## Callable returning the effects volume (0..1, or a negative number while sounds are off).
## Vendored by tools/game_music_video.py vendor --module world-life; do not edit the vendored copy.
const VERSION := "0.1.0"

static var time := 0.0
static var night := 0.0
static var quality := 2
static var pings: Array[Dictionary]=[]
# Beat clock (v002): WorldLife sets these each frame from the playing song (game/data/song_beats.json),
# or from the recorder's video clock via song_clock(); with no music it ticks at 120 BPM.
static var beat_phase := 0.0
static var beat_index := 0
static var on_beat := false
static var bpm := 120.0
static var song_id := ""
static var song_time := -1.0
static var song_override_until := -1.0
static var effects_volume := Callable()
static var _materials := {}
static var _shaders := {}

static func reset() -> void:
    time=0.0;night=0.0;pings.clear();beat_phase=0.0;beat_index=0;on_beat=false;song_id="";song_time=-1.0;song_override_until=-1.0

## The recorder (or a cutscene) drives the beat from its own clock: call every frame with the song id
## and the song position in seconds.
static func song_clock(id: String, seconds: float) -> void:
    song_id=id;song_time=seconds;song_override_until=time+.5

# ------------------------------------------------------------------ attention

## Something worth a glance happened at `at`. Strength 1 is a dolphin leap; .4 a butterfly.
static func ping(at: Vector3, strength := 1.0, seconds := 2.0) -> void:
    pings.append({"at":at,"strength":strength,"until":time+seconds,"born":time})
    if pings.size()>24:pings.pop_front()

## The strongest recent ping in front of `from` (within 100° of `forward`) and `reach` metres.
static func best_ping(from: Vector3, forward: Vector3, reach := 40.0) -> Dictionary:
    var best := {};var score := 0.0
    forward.y=0
    for p in pings:
        if float(p.until)<time:continue
        var to: Vector3=p.at-from
        var d := to.length()
        if d>reach or d<.4:continue
        var flat := Vector3(to.x,0,to.z)
        if forward.length_squared()>.001 and flat.length_squared()>.001 and forward.normalized().dot(flat.normalized())<-.17:continue
        var s: float=float(p.strength)*(1.0-d/reach)*(1.0-.5*clampf((time-float(p.born))/2.0,0,1))
        if s>score:score=s;best=p
    return best

# ------------------------------------------------------------------ materials

static func mat(color: Color, rough := .6, emit := 0.0, unshaded := false) -> StandardMaterial3D:
    var key := "%s|%.2f|%.2f|%s"%[color.to_html(),rough,emit,unshaded]
    if _materials.has(key):return _materials[key]
    var m := StandardMaterial3D.new();m.albedo_color=color;m.roughness=rough
    if color.a<.999:m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.render_priority=2   # after the water surface
    if emit>0:m.emission_enabled=true;m.emission=Color(color.r,color.g,color.b);m.emission_energy_multiplier=emit
    if unshaded:m.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
    _materials[key]=m
    return m

## A vertex-colour material shared by every merged mesh.
static func vcol(rough := .55, alpha := false, emit := 0.0) -> StandardMaterial3D:
    var key := "vcol|%.2f|%s|%.2f"%[rough,alpha,emit]
    if _materials.has(key):return _materials[key]
    var m := StandardMaterial3D.new();m.vertex_color_use_as_albedo=true;m.roughness=rough
    if alpha:m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.render_priority=2
    if emit>0:m.emission_enabled=true;m.emission=Color.WHITE;m.emission_energy_multiplier=emit;m.emission_operator=BaseMaterial3D.EMISSION_OP_MULTIPLY
    _materials[key]=m
    return m

static func shader(key: String, code: String) -> Shader:
    if _shaders.has(key):return _shaders[key]
    var s := Shader.new();s.code=code;_shaders[key]=s
    return s

## Cloth that flutters from a pinned edge (UV.x = 0). Flags, bunting, towels, sails, kite tails.
static func flutter_material(color: Color, amount := 1.0, stripes := Color(0,0,0,0)) -> ShaderMaterial:
    var m := ShaderMaterial.new()
    m.shader=shader("flutter","""shader_type spatial;
render_mode cull_disabled;
uniform vec4 tint:source_color=vec4(1.0);
uniform vec4 stripe:source_color=vec4(0.0);
uniform float amount=1.0;
uniform float phase=0.0;
void vertex(){
    float w=UV.x;
    float t=TIME*6.0+phase;
    VERTEX.z+=sin(t-UV.x*7.0+UV.y*2.0)*0.10*w*amount;
    VERTEX.y+=sin(t*0.7-UV.x*5.0)*0.04*w*amount;
}
void fragment(){
    vec3 c=tint.rgb;
    if(stripe.a>0.0 && fract((UV.x+UV.y)*3.0)>0.5) c=stripe.rgb;
    ALBEDO=c;ROUGHNESS=0.8;
}""")
    m.set_shader_parameter("tint",color);m.set_shader_parameter("stripe",stripes);m.set_shader_parameter("amount",amount)
    m.set_shader_parameter("phase",randf()*TAU)
    return m

# ------------------------------------------------------------------ meshes

static func sphere_mesh(segments := 12) -> SphereMesh:
    var m := SphereMesh.new();m.radius=.5;m.height=1.0;m.radial_segments=segments;m.rings=maxi(4,segments/2)
    return m

static func box_mesh() -> BoxMesh:
    var m := BoxMesh.new();m.size=Vector3.ONE
    return m

static func cyl_mesh(top := .5, bottom := .5, segments := 10) -> CylinderMesh:
    var m := CylinderMesh.new();m.top_radius=top;m.bottom_radius=bottom;m.height=1.0;m.radial_segments=segments;m.rings=1
    return m

## Merge primitive parts into one vertex-coloured ArrayMesh.
## Each part: [Mesh, Transform3D, Color].
static func merge(parts: Array) -> ArrayMesh:
    var st := SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for part in parts:
        var mesh: Mesh=part[0]
        var xf: Transform3D=part[1]
        var color: Color=part[2]
        var arrays := mesh.surface_get_arrays(0)
        var verts: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
        var normals: PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
        var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
        var basis := xf.basis.inverse().transposed()
        var order: PackedInt32Array=indices if indices.size()>0 else PackedInt32Array(range(verts.size()))
        for i in order:
            st.set_color(color);st.set_normal((basis*normals[i]).normalized());st.add_vertex(xf*verts[i])
    return st.commit()

static func xf(at: Vector3, size: Vector3, rot := Vector3.ZERO) -> Transform3D:
    return Transform3D(Basis.from_euler(rot).scaled(size),at)

static func instance(parent: Node, mesh: Mesh, material: Material, at := Vector3.ZERO, view := 90.0, shadows := false) -> MeshInstance3D:
    var mi := MeshInstance3D.new();mi.mesh=mesh;mi.material_override=material;mi.position=at
    mi.visibility_range_end=view
    mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    parent.add_child(mi)
    return mi

static func quiet(root: Node, view := 90.0) -> void:
    for g in root.find_children("*","GeometryInstance3D",true,false):
        g.visibility_range_end=view;g.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

# ------------------------------------------------------------------ placement

static func surface(world: Node, at: Vector3) -> float:
    if not world.has_method("wave_at"):return 0.0
    return world.wave_at(Vector2(at.x,at.z),float(world.get("ocean_elapsed")) if world.get("ocean_elapsed")!=null else time)

static func deep(world: Node, at: Vector3, depth := 1.5) -> bool:
    return world.height_at(at.x,at.z)<-depth

## Walk outward from an island centre along `angle` to the waterline. Positive `inland` steps back
## onto the sand; negative steps out into the water.
static func shore(world: Node, center: Vector2, angle: float, inland := 0.0) -> Vector3:
    var dir := Vector2(cos(angle),sin(angle))
    var r := 2.0
    while r<160.0 and world.height_at(center.x+dir.x*r,center.y+dir.y*r)>.05:r+=.5
    r-=inland
    var p := center+dir*r
    return Vector3(p.x,maxf(world.height_at(p.x,p.y),0.0),p.y)

static func camera(node: Node) -> Camera3D:
    return node.get_viewport().get_camera_3d()

## A point `distance` metres in front of the camera, swung by `angle`, at sea level.
static func ahead(cam: Camera3D, distance: float, angle := 0.0) -> Vector3:
    var f := -cam.global_basis.z;f.y=0
    if f.length_squared()<.001:f=Vector3.FORWARD
    var p := cam.global_position+f.normalized().rotated(Vector3.UP,angle)*distance
    return Vector3(p.x,0,p.z)

# ------------------------------------------------------------------ sound

## A short synthesised sound: summed sines (frequencies in Hz) with an exponential decay. Built once
## at load time, so the stones, drums, chimes and cannons need no audio files.
static func tone(freqs: Array, seconds := 1.2, decay := 3.0, gain := .4, noise := 0.0) -> AudioStreamWAV:
    var rate := 22050;var length := int(rate*seconds)
    var data := PackedByteArray();data.resize(length*2)
    var rng := RandomNumberGenerator.new();rng.seed=int(freqs[0]*7.0)
    for i in range(length):
        var t := float(i)/rate
        var env := exp(-t*decay)*minf(1.0,t*300.0)
        var v := 0.0
        for k in range(freqs.size()):v+=sin(TAU*float(freqs[k])*t)/(1.0+k*.6)
        v=v/maxf(1.0,freqs.size()*.7)+noise*rng.randf_range(-1,1)*exp(-t*decay*2.5)
        data.encode_s16(i*2,int(clampf(v*env*gain,-1,1)*32767))
    var w := AudioStreamWAV.new();w.format=AudioStreamWAV.FORMAT_16_BITS;w.mix_rate=rate;w.data=data
    return w

## The effects volume (0..1) from the game's effects_volume Callable; negative means sounds are off.
static func volume() -> float:
    return float(effects_volume.call()) if effects_volume.is_valid() else 1.0

## Play a positional one-shot at the effects volume (skipped while the game's sounds are off).
static func play_at(node: Node3D, stream: AudioStream, at: Vector3, db := -10.0, pitch := 1.0) -> void:
    var v := volume()
    if v<0:return
    var p := AudioStreamPlayer3D.new();p.stream=stream;p.unit_size=6;p.max_distance=60;node.add_child(p);p.global_position=at
    p.volume_db=linear_to_db(maxf(v,.00001))+db;p.pitch_scale=pitch;p.play()
    p.finished.connect(p.queue_free)

# ------------------------------------------------------------------ birds

## A bird with wings on pivots: children "WingL"/"WingR" rotate about Z. Returns the holder.
static func bird(body: Color, wing: Color, size := 1.0, beak := Color("f2a640")) -> Node3D:
    var holder := Node3D.new()
    var s := sphere_mesh(10)
    var torso := merge([[s,xf(Vector3.ZERO,Vector3(.32,.3,.7)*size),body],[s,xf(Vector3(0,.12,.36)*size,Vector3(.26,.25,.26)*size),body],
        [cyl_mesh(0,.5,6),xf(Vector3(0,.1,.55)*size,Vector3(.09,.18,.09)*size,Vector3(PI*.5,0,0)),beak],
        [box_mesh(),xf(Vector3(0,.02,-.42)*size,Vector3(.24,.04,.26)*size),wing]])
    instance(holder,torso,vcol(),Vector3.ZERO,140)
    for side in [-1,1]:
        var pivot := Node3D.new();pivot.name="WingL" if side<0 else "WingR";holder.add_child(pivot);pivot.position=Vector3(side*.13,.08,0)*size
        var wmesh := merge([[box_mesh(),xf(Vector3(side*.42,0,0)*size,Vector3(.8,.035,.36)*size),wing],[box_mesh(),xf(Vector3(side*.9,0,-.05)*size,Vector3(.3,.03,.26)*size),body.darkened(.15)]])
        instance(pivot,wmesh,vcol(),Vector3.ZERO,140)
    return holder

## Flap a bird (or a seagull/butterfly model with WingL/WingR parts) at phase `t`; amount 0 glides.
static func flap(holder: Node3D, t: float, amount := 1.0, speed := 9.0) -> void:
    var a := sin(t*speed)*.75*amount+(.08 if amount<.2 else 0.0)
    for side in ["L","R"]:
        var w := holder.find_child("Wing"+side,true,false) as Node3D
        if not w:continue
        if not w.has_meta("rest_z"):w.set_meta("rest_z",w.rotation.z)
        w.rotation.z=float(w.get_meta("rest_z"))+(a if side=="L" else -a)
