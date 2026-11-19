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
const VERSION := "0.4.0"
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
func _ray_exclude() -> Array[RID]:
    var hero := _hero()
    return [hero.get_rid()] if hero is CollisionObject3D else []

# ---------- entry ----------
func _initialize() -> void:call_deferred("_run")
func _run() -> void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--song="):song_id=arg.get_slice("=",1)
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
    if guard_enabled:guard_camera()
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
func guard_camera() -> void:
    # Scenery between camera and subject: swing the camera around until the view clears.
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
    if blocked_time>.25:
        cam_theta+=swing_dir*1.4/FPS
        _set_view(_view_yaw()+swing_dir*1.4/FPS,cam_pitch,cam_distance)
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

# ---------- camera-relative movement ----------
func camera(theta_deg: float,pitch: float,distance: float) -> void:
    cam_theta=deg_to_rad(theta_deg);cam_pitch=pitch;cam_distance=distance
    _set_view(_view_yaw(),pitch,distance)
func steer(direction: Vector3,ease := 3.0) -> void:
    # Aim the camera at travel-yaw + theta, then press the keys that move along `direction`
    # in the camera's frame. Convention: forward = -Z rotated by yaw (Godot default).
    if Vector2(direction.x,direction.z).length()<.05:return
    var travel_yaw := atan2(-direction.x,-direction.z)
    var yaw := lerp_angle(_view_yaw(),travel_yaw+cam_theta,1-exp(-ease/FPS))
    _set_view(yaw,cam_pitch,cam_distance)
    _set_movement_yaw(yaw)
    var rel: float=travel_yaw-yaw
    var local := Vector2(-sin(rel),-cos(rel))
    key(KEY_RIGHT,local.x>.38);key(KEY_LEFT,local.x<-.38);key(KEY_FORWARD,local.y<-.38);key(KEY_BACK,local.y>.38)
func hold_camera(until: float,face_target := Vector3.INF,drift := 0.0) -> void:
    stop_moving()
    stage_still_shot()
    while t()<until:
        var yaw := _view_yaw()
        if face_target!=Vector3.INF:
            var d := face_target-_hero().global_position
            yaw=lerp_angle(yaw,atan2(-d.x,-d.z)+cam_theta,1-exp(-2.0/FPS))
        _set_view(yaw+drift/FPS,cam_pitch,cam_distance)
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
    refresh_scene_lists()
    _set_movement_yaw(travel_yaw+cam_theta)
    _set_view(travel_yaw+cam_theta,cam_pitch,cam_distance,true)

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
    for until in cuts:
        var shot: Callable=last_shot if i==cuts.size()-1 else shots[i%shots.size()]
        var started_at := t()
        blocked_samples=0;shot_samples=0;blocked_time=0;staged_this_shot=false
        await shot.call(until)
        await wait_until(until)
        var blocked := 100.0*blocked_samples/maxf(1,shot_samples)
        print("MUSIC_VIDEO_SHOT %d %.1f-%.1f blocked=%.0f%%%s"%[i,started_at,until,blocked," CHECK" if blocked>20 else ""])
        i+=1
