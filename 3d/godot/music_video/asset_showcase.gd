extends "res://addons/gamecore_music_video/music_video_recorder.gd"
## Asset showcase (workflow game-asset-showcase): one titled shot per new asset or effect, recorded
## with the music-video recorder's clock, camera guard and Movie Maker capture. A game extends this,
## implements the recorder adapter plus _setup_showcase() and _build_showcase() (calls add()), and
## runs it with tools/game_music_video.py record (video) or showcase (one PNG per shot and sheets).
## User args: --only=A,B keeps shots whose id starts with those letters; --snap=<dir> saves a PNG at
## 58 % of each shot. The title card layer stays visible; everything else in the HUD is hidden.
const SHOWCASE_VERSION := "0.1.0"
var SHOT := 6.5                  # seconds per asset (5–8 reads well)
var SIDE := .42                  # radians the camera swings off a subject so the hero frames it instead of hiding it
var only: PackedStringArray=[]
var snap_dir := ""
var shots: Array[Dictionary]=[]
var title_layer := CanvasLayer.new()
var title := Label.new()

# ---------- showcase adapter (override in the game) ----------
func _setup_showcase() -> void:pass          # fixtures: unlock areas, start the game, disable saving
func _build_showcase() -> void:pass          # add(id, label, func(until): await ...) per asset
func _clear_stages() -> void:pass            # end forced effects (weather, overrides) after each shot

# ---------- shot list ----------
func add(id: String,label: String,fn: Callable) -> void:
    if only.size()>0 and not (id.substr(0,1) in only):return
    shots.append({"id":id,"label":label,"fn":fn})

func _prepare_song(_id: String) -> float:return SHOT*shots.size()
func _keep_layer(layer: CanvasLayer) -> bool:return layer==title_layer

func _initialize() -> void:
    stage_still=false   # each showcase shot stages its own subject
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--only="):only=arg.get_slice("=",1).split(",")
        if arg.begins_with("--snap="):snap_dir=arg.get_slice("=",1)
    super._initialize()

func make_title() -> void:
    title_layer.layer=40;root.add_child(title_layer);title_layer.add_child(title)
    title.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE);title.offset_top=-86;title.offset_bottom=-30
    title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;title.add_theme_font_size_override("font_size",30)
    title.add_theme_color_override("font_color",Color("fffaf0"));title.add_theme_color_override("font_outline_color",Color(.05,.12,.16,.85))
    title.add_theme_constant_override("outline_size",9)

func _produce(id: String) -> void:
    await _setup_showcase()
    _build_showcase()
    make_title();hide_hud()
    for i in range(10):await step()
    start_song(id)
    var t0 := 0.0
    for s in shots:
        var until := t0+SHOT
        title.text=s.id+"  ·  "+s.label
        print("SHOWCASE_SHOT ",s.id," ",snappedf(t0,.01))
        if snap_dir!="":snap_later(String(s.id),until-SHOT*.42)
        await s.fn.call(until)
        while t()<until:await step()
        _clear_stages()
        t0=until

func snap_later(id: String,at: float) -> void:
    while t()<at:await process_frame
    root.get_texture().get_image().save_png(snap_dir.path_join("%s.png"%id))

# ---------- framing helpers ----------
## Camera yaw that looks past the hero toward `target`, swung by SIDE so the hero sits beside it.
func face_yaw(target: Vector3) -> float:
    var d := target-_hero().global_position
    return atan2(-d.x,-d.z)+SIDE

## The hero stands at `spot`; the camera tracks a (possibly moving) point beyond them.
func watch_point(spot: Vector3,target_fn: Callable,until: float,pitch := -.1,distance := 6.0) -> void:
    var target: Vector3=target_fn.call()
    cut_to(spot,target)
    guard_enabled=false
    _set_view(face_yaw(target),pitch,distance,true)
    while t()<until:
        _set_view(lerp_angle(_view_yaw(),face_yaw(target_fn.call()),1-exp(-3.0/FPS)),pitch,distance)
        await step()

## The hero hovers `back` metres beyond `home` (away from `center`) and `lift` up, watching a target:
## nothing stands between camera and subject over open water or terrain.
func hover_watch(home: Vector3,center: Vector3,target_fn: Callable,until: float,back := 7.0,lift := 2.6,pitch := -.32) -> void:
    var out := Vector3(home.x-center.x,0,home.z-center.z).normalized()
    var spot := home+out*back+Vector3(0,lift,0)
    cut_to(spot,home,true)
    guard_enabled=false
    _set_view(face_yaw(target_fn.call()),pitch,6.0,true)
    while t()<until:
        _hero().velocity=Vector3.ZERO;_hero().global_position=spot
        _set_view(lerp_angle(_view_yaw(),face_yaw(target_fn.call()),1-exp(-3.0/FPS)),pitch,6.0)
        await step()
    _set_flying(false)

## A high, slow look straight down at a subject, the hero hovering in the foreground.
func overview(spot: Vector3,target: Vector3,until: float,pitch := -.55,distance := 9.0) -> void:
    cut_to(spot,target,true)
    guard_enabled=false
    var d := target-spot
    var yaw := atan2(-d.x,-d.z)
    _set_view(yaw,pitch,distance,true)
    while t()<until:
        _hero().velocity=Vector3.ZERO;_hero().global_position=spot
        _set_view(yaw+t()*.008,pitch,distance)
        await step()
    _set_flying(false)

## The hero on a shore facing out to sea (camera behind, swung by SIDE) while something is staged.
func gaze_out(island: Vector2,angle: float,until: float,stage := Callable(),pitch := -.05,distance := 6.0) -> void:
    var spot := shore(island,angle,2.0)
    var target := at(island,angle,200.0,0.0)
    cut_to(spot,target)
    guard_enabled=false
    camera(rad_to_deg(SIDE),pitch,distance);_set_view(face_yaw(target),pitch,distance,true)
    for i in range(3):await step()
    if stage.is_valid():stage.call()
    await hold_camera(until,target)
