extends SceneTree
## GameCore gameplay music-video recorder (Godot 4.x). Engine runtime of the
## game-music-video workflow: workflows/game-music-video/README.md.
##
## A game extends this script with a small adapter (hero, camera, terrain,
## captions, HUD) and one shot list per song. The base supplies the video clock,
## caption timing, simulated keys, camera-relative steering, a camera guard that
## swings around scenery, cut planning on caption starts and a library of
## generic shots. Output markers are parsed by tools/game_music_video.py.
##
## Contract: run with --fixed-fps <FPS> (and --write-movie to record). Never let
## a recording write the player's save; disable saving in _load_world().
## Vendored copy: do not edit in the game; change it in ArcoreGameCore and
## re-run `python tools/game_music_video.py vendor`.
const VERSION := "0.7.1"
const FPS := 30
var MIN_SHOT := 8.5          # seconds; cuts land on caption starts at least this far apart
var MAX_SHOT := 16.0         # songs without captions get a cut roughly this often
var KEY_FORWARD := KEY_W
var KEY_BACK := KEY_S
var KEY_LEFT := KEY_A
var KEY_RIGHT := KEY_D
var KEY_RUN := KEY_SHIFT
var KEY_UP := KEY_SPACE
var KEY_DOWN := KEY_CTRL
var KEY_BOOST := KEY_Q
var KEY_FLY := KEY_E

var song_id := ""
var song_frame := -1
var song_length := 0.0
var cam_theta := 0.0         # camera yaw relative to the direction of travel (0 behind, PI in front)
var cam_pitch := -.2
var cam_distance := 6.5
var guard_enabled := true
var measure_unguarded := true    # 0.5.0: shots with the guard off still count blocked frames (a shot may opt out, e.g. a helm view through rigging)
var hide_world_labels := true    # Label3D quest/debug markers are UI too; hidden with the HUD
var prop_radius := 25.0          # meshes this close are checked by bounding box (props often lack collision)
var held: Dictionary={}
var hidden_layers: Array[CanvasLayer]=[]
var props: Array[GeometryInstance3D]=[]
var labels: Array[Label3D]=[]
var hud_hidden := false
var blocked_time := 0.0
var blocked_samples := 0
var shot_samples := 0
var swing_dir := 1.0
# Ambient staging (0.3.0): still shots and caption beats ask the game to put life in frame.
var stage_still := true          # closeup/gaze/hold shots call _stage_ambient("still") once
var stage_beats := 0             # every Nth caption start calls _stage_ambient("beat"); 0 = off
var beat_index := 0
var beat_count := 0
var staged_this_shot := false
# Lyric-cued staging (0.4.0): a caption whose text contains a keyword stages that kind of life.
var lyric_stage: Dictionary={}   # lowercase keyword -> stage kind; calls _stage_ambient("lyric:"+kind)
var lyric_spacing := 3.0         # seconds between lyric-cued stagings
var lyric_index := 0
var last_lyric_stage := -1000.0
var lyric_shots: Array=[]       # [keyword, Callable(until)] pairs: a cut whose lines name the keyword plays that shot once
var lyric_shot_lead := 1.5      # a line must start this long before the cut ends to claim the shot
var frame_guard := true         # 0.6.0: keep the subject unblocked and fully in frame by orbiting the camera
var frame_guard_shot := true    # a shot may switch the guard off after its cut (reset at every cut)
var orbit_speed := .55          # radians per second while the camera swings to a clear view
var frame_targets: Array[Callable]=[]   # extra subjects that must stay unblocked (watch shots add theirs)
var view_offset := 0.0          # guard offsets added to the shot's own view
var pitch_offset := 0.0
var distance_scale := 1.0
var view_goal := Vector3(0,0,1)
var seeking := false
var pending_solve := false
var give_up_until := -1.0
var last_view := Vector3(0,-.2,6.5)   # the shot's own yaw, pitch and distance, before guard offsets
var occluders: Array[GeometryInstance3D]=[]
var tri_cache: Dictionary={}
var frame_debug := false        # --frame-debug or MUSIC_VIDEO_FRAME_DEBUG=1: print what blocks the subject, once per shot
var block_reason := ""
var reported_block := false
var clear_foreground := true      # 0.7.0: hide props that sit in front of the subject and fill part of the frame
var foreground_cover := .12       # fraction of the frame a prop must cover to be cleared
var foreground_max_size := 25.0   # metres: individual props only (merged scenery batches are never hidden)
var cleared: Array[GeometryInstance3D]=[]
var settle_frames := 0         # the follow camera catches up a frame or two after a cut; not counted
var SIDE := .42                 # radians the camera swings off a subject so the hero frames it instead of hiding it

# ---------- adapter: override these in the game ----------
func _load_world() -> void:pass                         # instantiate the game, disable saving, mute the music bus
func _produce(_id: String) -> void:pass                 # set up the fixture, call start_song(), then play_shots()
func _hero() -> Node3D:return null                      # the controlled character
func _camera() -> Camera3D:return null                  # the gameplay camera that follows the hero
func _view_yaw() -> float:return 0.0
func _set_view(_yaw: float,_pitch: float,_distance: float,_snap := false) -> void:pass  # ease pitch/distance unless snap
func _set_movement_yaw(_yaw: float) -> void:pass        # games that latch the movement frame while keys are held
func _set_flying(_on: bool) -> void:pass
func _is_flying() -> bool:return false
func _height_at(_x: float,_z: float) -> float:return 0.0
func _teleport(position: Vector3,facing_yaw: float,_flying: bool) -> void:
    _hero().global_position=position;_hero().rotation.y=facing_yaw
func _end_activity() -> void:pass                       # leave swings, wheels, menus before a cut
func _prepare_song(_id: String) -> float:return 0.0     # load cues, stop the game's own player; return song length
func _caption_starts() -> Array[float]:return []
func _update_captions(_t: float) -> void:pass
func _keep_layer(_layer: CanvasLayer) -> bool:return false  # captions layer(s) stay visible
## Put ambient life in front of the camera now ("still" at the start of a held shot, "beat" on a
## caption start). Return true if something was staged. Games without ambient systems leave it.
func _stage_ambient(_kind: String) -> bool:return false
## Text of caption `index` (same order as _caption_starts), for lyric-cued staging.
func _caption_text(_index: int) -> String:return ""
## Called every frame with the video time: drive beat-synced systems (dances, drums) from the song.
func _beat_clock(_t: float) -> void:pass
## Optional (0.6.0): where the follow camera would sit for this yaw, pitch and distance. The default orbits
## a point 1 m above the hero; override with the game's exact boom so the guard can test views before showing them.
func _camera_position_for(yaw: float,pitch: float,distance: float) -> Vector3:
    return _hero().global_position+Vector3.UP*1.0+Basis.from_euler(Vector3(pitch,yaw,0))*Vector3(0,0,distance)
## Optional: the follow camera's orientation for this yaw and pitch (used to test framing before showing a view).
func _camera_basis_for(yaw: float,pitch: float) -> Basis:return Basis.from_euler(Vector3(pitch,yaw,0))
## Optional: points on the hero that must stay visible (feet to head, both sides).
func _subject_points() -> Array[Vector3]:
    var h := _hero().global_position
    var cam := _camera()
    var side: Vector3=cam.global_basis.x if cam else Vector3.RIGHT
    side.y=0;side=side.normalized()*.35
    return [h+Vector3.UP*.35,h+Vector3.UP*.9,h+Vector3.UP*1.45,h+Vector3.UP*.9+side,h+Vector3.UP*.9-side]
## Optional: geometry the guard should ignore (a vehicle the hero rides, for example).
func _occluder_excluded(_node: Node) -> bool:return false
func _ray_exclude() -> Array[RID]:
    var hero := _hero()
    return [hero.get_rid()] if hero is CollisionObject3D else []

# ---------- entry ----------
func _initialize() -> void:call_deferred("_run")
func _run() -> void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--song="):song_id=arg.get_slice("=",1)
        if arg=="--frame-debug":frame_debug=true
    if OS.get_environment("MUSIC_VIDEO_FRAME_DEBUG")=="1":frame_debug=true
    await _load_world()
    await _produce(song_id)
    release()
    print("MUSIC_VIDEO_END t=",snappedf(t(),.01)," frame=",Engine.get_process_frames())
    quit()

# ---------- clock, captions, HUD, camera guard, input ----------
func t() -> float:return 0.0 if song_frame<0 else float(Engine.get_process_frames()-song_frame)/FPS
func start_song(id: String) -> void:
    song_length=_prepare_song(id)
    song_frame=Engine.get_process_frames()
    print("MUSIC_VIDEO_SONG_START frame=",song_frame," length=",song_length," recorder=",VERSION)
func step() -> void:
    if frame_guard and pending_solve:solve_at_cut()
    await process_frame
    for layer in hidden_layers:
        if is_instance_valid(layer):layer.visible=false
    if Engine.get_process_frames()%30==0:refresh_scene_lists()
    if hud_hidden and hide_world_labels:
        for label in labels:
            if is_instance_valid(label):label.visible=false
    if song_frame>=0:
        _update_captions(t())
        _beat_clock(t())
        if stage_beats>0:stage_on_beats()
        if not lyric_stage.is_empty():stage_on_lyrics()
    if frame_guard:frame_guard_step()
    elif guard_enabled:guard_camera()
    elif measure_unguarded:guard_camera(false)
func stage_on_beats() -> void:
    var starts: Array[float]=_caption_starts()
    while beat_index<starts.size() and starts[beat_index]<=t():
        beat_index+=1;beat_count+=1
        if beat_count%stage_beats==0 and _stage_ambient("beat"):print("MUSIC_VIDEO_STAGE beat t=",snappedf(t(),.01))
func stage_on_lyrics() -> void:
    var starts: Array[float]=_caption_starts()
    while lyric_index<starts.size() and starts[lyric_index]<=t():
        var i := lyric_index;lyric_index+=1
        if t()-last_lyric_stage<lyric_spacing:continue
        var text := _caption_text(i).to_lower()
        for keyword in lyric_stage:
            if text.contains(String(keyword)) and _stage_ambient("lyric:"+String(lyric_stage[keyword])):
                last_lyric_stage=t();print("MUSIC_VIDEO_STAGE lyric '",keyword,"' t=",snappedf(t(),.01));break
## Stage once per held shot (closeup, gaze, hold_camera) when stage_still is on.
func stage_still_shot() -> void:
    if not stage_still or staged_this_shot:return
    staged_this_shot=true
    if _stage_ambient("still"):print("MUSIC_VIDEO_STAGE still t=",snappedf(t(),.01))
func refresh_scene_lists() -> void:
    # Once a second: world labels to hide, and nearby props for the bounding-box camera check.
    var hero := _hero()
    labels.clear();props.clear()
    if hud_hidden and hide_world_labels:
        for node in root.find_children("*","Label3D",true,false):labels.append(node)
    if hero==null:return
    for node in root.find_children("*","GeometryInstance3D",true,false):
        var g := node as GeometryInstance3D
        if not g.is_visible_in_tree() or hero.is_ancestor_of(g):continue
        var box := g.get_aabb()
        if box.size.length()<.05:continue
        var world_box: AABB=g.global_transform*box
        if world_box.size.x>60 or world_box.size.z>60:continue   # terrain, ocean, sky: not props
        if world_box.get_center().distance_to(hero.global_position)>prop_radius:continue
        props.append(g)
    if frame_guard:refresh_occluders()
func prop_blocks(from: Vector3,to: Vector3) -> bool:
    # A prop's bounding box between camera and subject, or around the camera itself.
    var hero_point := _hero().global_position
    for g in props:
        if not is_instance_valid(g) or not g.is_visible_in_tree():continue
        var box: AABB=g.global_transform*g.get_aabb()
        if box.grow(.3).has_point(hero_point) or box.get_center().distance_to(to)<1.2:continue   # what the hero stands on or carries
        if box.grow(.2).has_point(from) or box.intersects_segment(from,to.lerp(from,.12)):return true
    return false
func wait_until(seconds: float) -> void:
    while t()<seconds:await step()
func hide_hud() -> void:
    hidden_layers.clear()
    for node in root.find_children("*","CanvasLayer",true,false):
        if not _keep_layer(node):hidden_layers.append(node)
    hud_hidden=true;refresh_scene_lists()
func guard_camera(swing := true) -> void:
    # Scenery between camera and subject: swing the camera around until the view clears (or only count it).
    var cam := _camera();var hero := _hero()
    if cam==null or hero==null or not cam.is_inside_tree():return
    var to: Vector3=hero.global_position+Vector3.UP*.9
    var query := PhysicsRayQueryParameters3D.create(cam.global_position,to)
    query.exclude=_ray_exclude()
    var hit := hero.get_world_3d().direct_space_state.intersect_ray(query)
    shot_samples+=1
    var ray_blocked: bool=not hit.is_empty() and hit.position.distance_to(to)>=.6
    if not ray_blocked and not prop_blocks(cam.global_position,to):
        blocked_time=0.0;return
    blocked_samples+=1;blocked_time+=1.0/FPS
    if swing and blocked_time>.25:
        cam_theta+=swing_dir*1.4/FPS
        set_view(view_yaw()+swing_dir*1.4/FPS,cam_pitch,cam_distance)
        if blocked_time>2.5:swing_dir=-swing_dir;blocked_time=.3
func key(code: int,pressed: bool) -> void:
    if held.get(code,false)==pressed:return
    held[code]=pressed
    var event := InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=pressed
    Input.parse_input_event(event)
func tap(code: int) -> void:
    key(code,true);await step();key(code,false)
func release() -> void:
    for code in held.keys():key(code,false)
func stop_moving() -> void:
    for code in [KEY_FORWARD,KEY_BACK,KEY_LEFT,KEY_RIGHT,KEY_RUN,KEY_UP,KEY_DOWN,KEY_BOOST]:key(code,false)

# ---------- framing guard (0.6.0) ----------
func view_yaw() -> float:return _view_yaw()-view_offset
func set_view(yaw: float,pitch: float,distance: float,snap := false) -> void:
    last_view=Vector3(yaw,pitch,distance)
    _set_view(yaw+view_offset,pitch+pitch_offset,distance*distance_scale,snap)
func reset_guard() -> void:
    restore_foreground()
    view_offset=0.0;pitch_offset=0.0;distance_scale=1.0;seeking=false;give_up_until=-1.0
    frame_targets.clear();frame_guard_shot=true;pending_solve=true;blocked_time=0.0;reported_block=false;settle_frames=2
func refresh_occluders() -> void:
    # Visible meshes near the hero, tested by their real triangles (batched props have no collision).
    occluders.clear()
    var hero := _hero()
    if hero==null:return
    var h := hero.global_position
    for node in root.find_children("*","GeometryInstance3D",true,false):
        if not (node is MeshInstance3D or node is MultiMeshInstance3D):continue
        var g := node as GeometryInstance3D
        if not g.is_visible_in_tree() or hero.is_ancestor_of(g) or g.transparency>=.5 or _occluder_excluded(g):continue
        var mesh: Mesh=(g as MeshInstance3D).mesh if g is MeshInstance3D else ((g as MultiMeshInstance3D).multimesh.mesh if (g as MultiMeshInstance3D).multimesh else null)
        if mesh==null:continue
        if g is MultiMeshInstance3D and mesh.get_aabb().size.length()<.6:continue   # grass and flowers do not hide a subject
        var box: AABB=g.global_transform*g.get_aabb()
        if box.size.length()<.4 or box.size.x>250 or box.size.z>250:continue        # bubbles and specks; terrain, ocean, sky
        var nearest := Vector3(clampf(h.x,box.position.x,box.end.x),clampf(h.y,box.position.y,box.end.y),clampf(h.z,box.position.z,box.end.z))
        if nearest.distance_to(h)<45.0:occluders.append(g)
func triangles(mesh: Mesh) -> TriangleMesh:
    if not tri_cache.has(mesh):tri_cache[mesh]=mesh.generate_triangle_mesh()
    return tri_cache[mesh]
func segment_blocked(from: Vector3,to: Vector3) -> bool:
    var hero := _hero()
    var query := PhysicsRayQueryParameters3D.create(from,to)
    query.exclude=_ray_exclude()
    var hit := hero.get_world_3d().direct_space_state.intersect_ray(query)
    if not hit.is_empty() and hit.position.distance_to(to)>.3:
        if frame_debug:block_reason="collider "+str(hit.collider.get_path() if hit.collider is Node else hit.collider)
        return true
    for g in occluders:
        if not is_instance_valid(g) or not g.is_visible_in_tree():continue
        var box: AABB=g.global_transform*g.get_aabb()
        if not box.has_point(from) and not box.intersects_segment(from,to):continue
        if g is MeshInstance3D:
            var tm := triangles((g as MeshInstance3D).mesh)
            if tm==null:continue
            var inv := g.global_transform.affine_inverse()
            if not tm.intersect_segment(inv*from,inv*to).is_empty():
                if frame_debug:block_reason="mesh "+str(g.get_path())
                return true
        else:
            var mm: MultiMesh=(g as MultiMeshInstance3D).multimesh
            var tm := triangles(mm.mesh)
            if tm==null:continue
            var local_box := mm.mesh.get_aabb()
            var count: int=mm.instance_count if mm.visible_instance_count<0 else mm.visible_instance_count
            for i in range(count):
                var xf: Transform3D=g.global_transform*mm.get_instance_transform(i)
                var ibox: AABB=xf*local_box
                if not ibox.has_point(from) and not ibox.intersects_segment(from,to):continue
                var inv := xf.affine_inverse()
                if not tm.intersect_segment(inv*from,inv*to).is_empty():
                    if frame_debug:block_reason="multimesh "+str(g.get_path())+" #"+str(i)
                    return true
    return false
func target_points() -> Array[Vector3]:
    var pts: Array[Vector3]=[]
    for fn in frame_targets:
        if fn.is_valid():pts.append(fn.call())
    return pts
## Whether `p` falls inside the frame of a camera at `cam_pos` with orientation `basis` (lens taken from `cam`).
func point_in_view(cam_pos: Vector3,basis: Basis,cam: Camera3D,p: Vector3,margin := .94) -> bool:
    var local := basis.inverse()*(p-cam_pos)
    if local.z>-.1:return false
    var half_v := tan(deg_to_rad(cam.fov)*.5)*margin
    var vp := cam.get_viewport().get_visible_rect().size
    var half_h := half_v*(vp.x/maxf(vp.y,1.0))
    return absf(local.y/-local.z)<=half_v and absf(local.x/-local.z)<=half_h
func view_blocked_from(cam_pos: Vector3,cam: Camera3D=null,basis := Basis(),hypothetical := false) -> bool:
    if hypothetical and cam:
        for p in _subject_points():
            if not point_in_view(cam_pos,basis,cam,p):return true
    if cam_pos.y<_height_at(cam_pos.x,cam_pos.z)+.25:   # inside the ground: rays from below a heightfield miss it
        if frame_debug:block_reason="camera below ground"
        return true
    for p in _subject_points():
        if cam and not cam.is_position_in_frustum(p):
            if frame_debug:block_reason="out of frame "+str(p.snappedf(.01))
            return true
        if segment_blocked(cam_pos,p.lerp(cam_pos,.04)):return true
    for p in target_points():
        var back := cam_pos.distance_to(p)
        if back>1.0 and segment_blocked(cam_pos,p.lerp(cam_pos,minf(.6/back,.5))):return true
    return false
## The nearest guard offsets (yaw, pitch, distance scale) that give a clear view, or Vector3.INF.
func solve_view() -> Vector3:
    var base := last_view
    for combo in [[0.0,1.0],[-.2,1.0],[0.0,.75],[-.38,.8],[-.2,.55],[-.5,.6]]:
        var steps: Array[float]=[0.0]
        for k in range(1,16):steps.append(k*.2);steps.append(-k*.2)   # nearest angle first, both ways round
        for dy in steps:
            var yaw_off: float=view_offset+dy
            var pos := _camera_position_for(base.x+yaw_off,base.y+combo[0],base.z*combo[1])
            if not view_blocked_from(pos,_camera(),_camera_basis_for(base.x+yaw_off,base.y+combo[0]),true):return Vector3(wrapf(yaw_off,-PI,PI),combo[0],combo[1])
    return Vector3.INF
func solve_at_cut() -> void:
    pending_solve=false
    if not frame_guard_shot or _hero()==null:return
    var goal := solve_view()
    if goal==Vector3.INF:
        if clear_foreground:clear_foreground_for(_camera_position_for(last_view.x+view_offset,last_view.y+pitch_offset,last_view.z*distance_scale),_camera_basis_for(last_view.x+view_offset,last_view.y+pitch_offset),foreground_cover)
        return
    view_offset=goal.x;pitch_offset=goal.y;distance_scale=goal.z
    _set_view(last_view.x+view_offset,last_view.y+pitch_offset,last_view.z*distance_scale,true)
    if goal!=Vector3(0,0,1):print("MUSIC_VIDEO_FRAME cut t=",snappedf(t(),.01)," yaw=",snappedf(goal.x,.01)," pitch=",goal.y," dist=",goal.z)
    if clear_foreground:clear_foreground_for(_camera_position_for(last_view.x+view_offset,last_view.y+pitch_offset,last_view.z*distance_scale),_camera_basis_for(last_view.x+view_offset,last_view.y+pitch_offset),foreground_cover)
func frame_guard_step() -> void:
    var cam := _camera()
    if cam==null or _hero()==null or not cam.is_inside_tree():return
    if settle_frames>0:settle_frames-=1;return
    if clear_foreground and frame_guard_shot and Engine.get_process_frames()%10==0:
        clear_foreground_for(cam.global_position,cam.global_basis.orthonormalized(),.25,6.0)   # what the moving camera brushes past
    var blocked := view_blocked_from(cam.global_position,cam)
    shot_samples+=1
    if blocked:
        blocked_samples+=1;blocked_time+=1.0/FPS
        if frame_debug and not reported_block:reported_block=true;print("MUSIC_VIDEO_BLOCK t=",snappedf(t(),.01)," ",block_reason)
    else:blocked_time=0.0
    if not frame_guard_shot:return
    if blocked and not seeking and blocked_time>.15 and t()>give_up_until:
        var goal := solve_view()
        if goal==Vector3.INF or goal==Vector3(view_offset,pitch_offset,distance_scale):give_up_until=t()+1.0
        else:view_goal=goal;seeking=true
    if seeking:
        var d := wrapf(view_goal.x-view_offset,-PI,PI)
        view_offset+=clampf(d,-orbit_speed/FPS,orbit_speed/FPS)
        pitch_offset=move_toward(pitch_offset,view_goal.y,.35/FPS)
        distance_scale=move_toward(distance_scale,view_goal.z,.4/FPS)
        _set_view(last_view.x+view_offset,last_view.y+pitch_offset,last_view.z*distance_scale)
        if absf(d)<.01 and is_equal_approx(pitch_offset,view_goal.y) and is_equal_approx(distance_scale,view_goal.z):seeking=false

## Fraction of the frame covered by `box` for a camera at `cam_pos` facing along `basis` (lens from the game camera).
func screen_cover(box: AABB,cam_pos: Vector3,basis: Basis) -> float:
    var cam := _camera()
    if cam==null:return 0.0
    var half_v := tan(deg_to_rad(cam.fov)*.5)
    var vp := cam.get_viewport().get_visible_rect().size
    var half_h := half_v*(vp.x/maxf(vp.y,1.0))
    var inv := basis.inverse()
    var lo := Vector2(INF,INF);var hi := Vector2(-INF,-INF);var behind := 0
    for i in range(8):
        var c := inv*(box.get_endpoint(i)-cam_pos)
        if c.z>-.05:behind+=1;continue
        var q := Vector2(c.x/(-c.z)/half_h,c.y/(-c.z)/half_v)
        lo=Vector2(minf(lo.x,q.x),minf(lo.y,q.y));hi=Vector2(maxf(hi.x,q.x),maxf(hi.y,q.y))
    if behind==8:return 0.0
    if behind>0:return 1.0 if box.grow(.3).has_point(cam_pos) else .5   # straddles the camera plane: right in front of the lens
    var w := clampf(hi.x,-1,1)-clampf(lo.x,-1,1);var h := clampf(hi.y,-1,1)-clampf(lo.y,-1,1)
    return maxf(0.0,w)*maxf(0.0,h)/4.0
## Hide props nearer than the subject that cover more than `cover` of the frame (within `near` metres if given).
func clear_foreground_for(cam_pos: Vector3,basis: Basis,cover: float,near := INF) -> void:
    var hero := _hero()
    if hero==null:return
    var subject := hero.global_position+Vector3.UP*.9
    var subject_d := cam_pos.distance_to(subject)
    var keep: Array[Vector3]=[hero.global_position,subject]
    keep.append_array(target_points())
    for g in occluders:
        if not is_instance_valid(g) or not g.visible or cleared.has(g):continue
        var box: AABB=g.global_transform*g.get_aabb()
        if box.size.length()>foreground_max_size:continue
        var holds_subject := false
        for p in keep:
            if box.grow(.4).has_point(p):holds_subject=true;break
        if holds_subject:continue
        var nearest := Vector3(clampf(cam_pos.x,box.position.x,box.end.x),clampf(cam_pos.y,box.position.y,box.end.y),clampf(cam_pos.z,box.position.z,box.end.z))
        var d := nearest.distance_to(cam_pos)
        if d>=subject_d-.4 or d>near:continue
        if screen_cover(box,cam_pos,basis)>=cover:
            g.visible=false;cleared.append(g)
            if frame_debug:print("MUSIC_VIDEO_CLEAR t=",snappedf(t(),.01)," ",g.get_path())
func restore_foreground() -> void:
    for g in cleared:
        if is_instance_valid(g):g.visible=true
    cleared.clear()

# ---------- camera-relative movement ----------
func camera(theta_deg: float,pitch: float,distance: float) -> void:
    cam_theta=deg_to_rad(theta_deg);cam_pitch=pitch;cam_distance=distance
    set_view(view_yaw(),pitch,distance)
func steer(direction: Vector3,ease := 3.0) -> void:
    # Aim the camera at travel-yaw + theta, then press the keys that move along `direction`
    # in the camera's frame. Convention: forward = -Z rotated by yaw (Godot default).
    if Vector2(direction.x,direction.z).length()<.05:return
    var travel_yaw := atan2(-direction.x,-direction.z)
    var yaw := lerp_angle(view_yaw(),travel_yaw+cam_theta,1-exp(-ease/FPS))
    set_view(yaw,cam_pitch,cam_distance)
    var actual := yaw+view_offset
    _set_movement_yaw(actual)
    var rel: float=travel_yaw-actual
    var local := Vector2(-sin(rel),-cos(rel))
    key(KEY_RIGHT,local.x>.38);key(KEY_LEFT,local.x<-.38);key(KEY_FORWARD,local.y<-.38);key(KEY_BACK,local.y>.38)
func hold_camera(until: float,face_target := Vector3.INF,drift := 0.0) -> void:
    stop_moving()
    stage_still_shot()
    while t()<until:
        var yaw := view_yaw()
        if face_target!=Vector3.INF:
            var d := face_target-_hero().global_position
            yaw=lerp_angle(yaw,atan2(-d.x,-d.z)+cam_theta,1-exp(-2.0/FPS))
        set_view(yaw+drift/FPS,cam_pitch,cam_distance)
        await step()
func travel(target: Vector3,until: float,run := false,radius := .7) -> void:
    key(KEY_RUN,run)
    while t()<until:
        var d := target-_hero().global_position
        if Vector2(d.x,d.z).length()<radius:break
        steer(d)
        await step()
    stop_moving()
func fly(target: Vector3,until: float,boost := false,jet := false) -> void:
    if not _is_flying():_set_flying(true)
    key(KEY_RUN,boost);key(KEY_BOOST,jet)
    while t()<until:
        var d := target-_hero().global_position
        if d.length()<1.5:break
        steer(d,2.0)
        key(KEY_UP,d.y>.5);key(KEY_DOWN,d.y<-.5)
        await step()
    stop_moving()

# ---------- placement ----------
func ground(p: Vector3,lift := .15) -> Vector3:
    return Vector3(p.x,_height_at(p.x,p.z)+lift,p.z)
func at(c: Vector2,angle: float,r: float,y := -1000.0) -> Vector3:
    var p := Vector3(c.x+cos(angle)*r,0,c.y+sin(angle)*r)
    return ground(p) if y<=-999 else Vector3(p.x,y,p.z)
func shore(c: Vector2,angle: float,inland := 2.0,y := -1000.0,sea_level := .05) -> Vector3:
    # Walk outward from an island centre until the land meets the sea; negative inland = offshore.
    var r := 3.0
    while r<160.0 and _height_at(c.x+cos(angle)*r,c.y+sin(angle)*r)>sea_level:r+=.5
    return at(c,angle,r-inland,y)
func cut_to(position: Vector3,facing: Vector3,flying := false) -> void:
    # A hard cut: end any activity, teleport, face the next subject, settle the camera instantly.
    stop_moving();_end_activity()
    var p := position if flying else ground(position)
    var d := facing-p
    var travel_yaw := atan2(-d.x,-d.z)
    _set_flying(flying)
    _teleport(p,travel_yaw,flying)
    reset_guard()
    refresh_scene_lists()
    _set_movement_yaw(travel_yaw+cam_theta)
    set_view(travel_yaw+cam_theta,cam_pitch,cam_distance,true)

# ---------- generic shots (each runs until `until`) ----------
func stroll(c: Vector2,a0: float,a1: float,until: float,theta := 90.0) -> void:
    camera(theta,-.1,5.2)
    var from := shore(c,a0);var to := shore(c,a1)
    cut_to(from,to);await travel(to,until)
    await hold_camera(until)
func run_front(c: Vector2,a0: float,a1: float,until: float) -> void:
    camera(180,-.08,6.0)
    var from := shore(c,a0);var to := shore(c,a1)
    cut_to(from,to);await travel(to,until,true)
    await hold_camera(until,Vector3.INF,.04)
func jumps(c: Vector2,a0: float,a1: float,until: float,theta := 60.0) -> void:
    camera(theta,-.12,6.0)
    var from := shore(c,a0);var to := shore(c,a1)
    cut_to(from,to)
    while t()<until-1.0:
        var d := to-_hero().global_position
        if Vector2(d.x,d.z).length()<.8:break
        steer(d);key(KEY_UP,int(t()*2.0)%2==0)
        await step()
    await hold_camera(until)
func takeoff(c: Vector2,angle: float,until: float,height := 13.0) -> void:
    camera(0,-.05,7.5)
    var from := shore(c,angle,6.0);var to := at(c,angle,6.0,from.y+height)
    cut_to(from,to)
    key(KEY_RUN,true);var go := t()+1.2
    while t()<go:steer(to-_hero().global_position);await step()
    await fly(to,until,true)
    await hold_camera(until,Vector3.INF,.05)
func glide(c: Vector2,a0: float,a1: float,until: float,out := 14.0,height := 5.0,theta := -70.0,jet := false) -> void:
    camera(theta,-.3,7.0)
    var from := shore(c,a0,-out);from.y=height+1
    var to := shore(c,a1,-out);to.y=height
    cut_to(from,to,true);await fly(to,until,jet,jet)
    await hold_camera(until)
func low_glide(c: Vector2,a0: float,a1: float,until: float,theta := 110.0) -> void:
    camera(theta,-.42,5.5)
    var from := shore(c,a0,-9.0);from.y=1.6
    var to := shore(c,a1,-9.0);to.y=1.4
    cut_to(from,to,true);await fly(to,until)
    await hold_camera(until)
func closeup(spot: Vector3,facing: Vector3,until: float,drift := .06) -> void:
    camera(180,-.04,3.4)
    cut_to(spot,facing)
    await hold_camera(until,Vector3.INF,drift)
func gaze(spot: Vector3,target: Vector3,until: float,theta := 0.0,pitch := .02,distance := 5.0,approach := 4.0) -> void:
    camera(theta,pitch,distance)
    var start := spot-(target-spot).normalized()*approach;start.y=spot.y
    cut_to(start,target)
    await travel(spot,minf(until,t()+approach*.9))
    await hold_camera(until,target)
func walk(from: Vector3,to: Vector3,until: float,theta := -35.0,run := false) -> void:
    camera(theta,-.14,5.5)
    cut_to(from,to);await travel(to,until,run)
    await hold_camera(until)

# ---------- edit plan ----------
func cut_times(from: float) -> Array[float]:
    # Cuts on caption starts at least MIN_SHOT apart; long uncaptioned stretches get evenly spaced cuts.
    var cuts: Array[float]=[]
    var last := from
    var starts: Array[float]=_caption_starts().duplicate()   # never mutate the game's own cue list
    starts.append(song_length+1.0)
    for s in starts:
        while s-last>MAX_SHOT*1.6:
            last+=MAX_SHOT*.95;cuts.append(last)
        if s-last>=MIN_SHOT and s<song_length-2:cuts.append(s);last=s
    cuts.append(song_length+1.0)
    return cuts
func play_shots(shots: Array[Callable],from: float,last_shot: Callable) -> void:
    var cuts := cut_times(from)
    var i := 0
    var cycle := 0
    var used: Dictionary={}
    for until in cuts:
        var started_at := t()
        var started_frame := Engine.get_process_frames()-song_frame
        var shot: Callable=last_shot if i==cuts.size()-1 else lyric_shot(started_at,until,used)
        if not shot.is_valid():
            shot=shots[cycle%shots.size()];cycle+=1
        blocked_samples=0;shot_samples=0;blocked_time=0;staged_this_shot=false;measure_unguarded=true
        await shot.call(until)
        await wait_until(until)
        var blocked := 100.0*blocked_samples/maxf(1,shot_samples)
        print("MUSIC_VIDEO_SHOT %d %.1f-%.1f blocked=%.0f%%%s"%[i,started_at,until,blocked," CHECK" if blocked>20 else ""])
        print("MUSIC_VIDEO_SHOT_FRAMES %d %d %d"%[i,started_frame,Engine.get_process_frames()-song_frame])
        i+=1
## 0.6.0: a planned edit. Rows are [start_seconds, Callable(until)]; each shot runs to the next row's start and
## the last to the end of the song. Rows whose start has already passed (a title sequence ran long) are skipped.
func play_plan(plan: Array) -> void:
    for i in range(plan.size()):
        var until: float=float(plan[i+1][0]) if i+1<plan.size() else song_length+1.0
        if t()>=until-.5:continue
        var started_at := t()
        var started_frame := Engine.get_process_frames()-song_frame
        blocked_samples=0;shot_samples=0;blocked_time=0;staged_this_shot=false;measure_unguarded=true
        reset_guard()   # shots that do not cut (a vehicle under way) still start with a fresh guard
        await (plan[i][1] as Callable).call(until)
        await wait_until(until)
        var blocked := 100.0*blocked_samples/maxf(1,shot_samples)
        print("MUSIC_VIDEO_SHOT %d %.1f-%.1f blocked=%.0f%%%s"%[i,started_at,until,blocked," CHECK" if blocked>20 else ""])
        print("MUSIC_VIDEO_SHOT_FRAMES %d %d %d"%[i,started_frame,Engine.get_process_frames()-song_frame])
    restore_foreground()
## The first unused lyric shot whose keyword appears in a caption line starting inside this cut, or
## an invalid Callable (the cut then takes the next shot of the song's list).
func lyric_shot(from: float,until: float,used: Dictionary) -> Callable:
    if lyric_shots.is_empty():return Callable()
    var starts: Array[float]=_caption_starts()
    for j in range(starts.size()):
        if starts[j]<from-.25 or starts[j]>until-lyric_shot_lead:continue
        var text := _caption_text(j).to_lower()
        for k in range(lyric_shots.size()):
            if used.has(k):continue
            if text.contains(String(lyric_shots[k][0]).to_lower()):
                used[k]=true
                print("MUSIC_VIDEO_LYRIC_SHOT '",lyric_shots[k][0],"' t=",snappedf(from,.01))
                return lyric_shots[k][1]
    return Callable()

# ---------- framing helpers (also used by asset_showcase.gd) ----------
## Camera yaw that looks past the hero toward `target`, swung by SIDE so the hero sits beside it.
func face_yaw(target: Vector3) -> float:
    var d := target-_hero().global_position
    return atan2(-d.x,-d.z)+SIDE

## The hero stands at `spot`; the camera tracks a (possibly moving) point beyond them.
func watch_point(spot: Vector3,target_fn: Callable,until: float,pitch := -.1,distance := 6.0) -> void:
    var target: Vector3=target_fn.call()
    cut_to(spot,target)
    guard_enabled=false;frame_targets.append(target_fn)
    set_view(face_yaw(target),pitch,distance,true)
    stage_still_shot()
    while t()<until:
        set_view(lerp_angle(view_yaw(),face_yaw(target_fn.call()),1-exp(-3.0/FPS)),pitch,distance)
        await step()

## The hero hovers `back` metres beyond `home` (away from `center`) and `lift` up, watching a target:
## nothing stands between camera and subject over open water or terrain.
func hover_watch(home: Vector3,center: Vector3,target_fn: Callable,until: float,back := 7.0,lift := 2.6,pitch := -.32) -> void:
    var out := Vector3(home.x-center.x,0,home.z-center.z).normalized()
    var spot := home+out*back+Vector3(0,lift,0)
    cut_to(spot,home,true)
    guard_enabled=false;frame_targets.append(target_fn)
    set_view(face_yaw(target_fn.call()),pitch,6.0,true)
    while t()<until:
        _hero().velocity=Vector3.ZERO;_hero().global_position=spot
        set_view(lerp_angle(view_yaw(),face_yaw(target_fn.call()),1-exp(-3.0/FPS)),pitch,6.0)
        await step()
    _set_flying(false)

## A high, slow look down at a subject, the hero hovering in the foreground.
func overview(spot: Vector3,target: Vector3,until: float,pitch := -.55,distance := 9.0) -> void:
    cut_to(spot,target,true)
    guard_enabled=false
    var d := target-spot
    var yaw := atan2(-d.x,-d.z)
    set_view(yaw,pitch,distance,true)
    while t()<until:
        _hero().velocity=Vector3.ZERO;_hero().global_position=spot
        set_view(yaw+t()*.008,pitch,distance)
        await step()
    _set_flying(false)
