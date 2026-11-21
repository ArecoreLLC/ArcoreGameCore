extends CanvasLayer
## Shared live studio. A game supplies callbacks; no game paths, characters or sky nodes here.
const VERSION := "0.1.0"
var folder := ""
var config := {}
var plan := {}
var saved := {}
var generation := 0
var frame := 0
var scope := -1
var time_of_day := "day"
var compare := false
var sampler
var apply_look: Callable
var set_day: Callable
var night_amount: Callable
var controls := {}
var status: Label
var elapsed := 0.0
var busy := false
var online := true
var last_error := ""

func configure(session_folder: String, apply: Callable, day: Callable, amount: Callable) -> void:
    folder=session_folder
    config=_read(folder.path_join("session.json"))
    plan=config.plan.duplicate(true)
    _integer_frames()
    saved=plan.profile.duplicate(true)
    frame=int(config.get("frame",0))
    apply_look=apply;set_day=day;night_amount=amount
    sampler=load(get_script().resource_path.get_base_dir().path_join("capture_lighting.gd")).new()
    process_mode=Node.PROCESS_MODE_ALWAYS
    process_priority=-100
    layer=100
    _build_ui()
    set_day.call(time_of_day)
    _sync()
    _apply()
    _publish()

func _read(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):return {}
    var value=JSON.parse_string(FileAccess.get_file_as_string(path))
    return value if value is Dictionary else {}

func _write(path: String, data: Dictionary) -> void:
    var file=FileAccess.open(path+".tmp",FileAccess.WRITE)
    if file==null:push_error("Cannot write studio state: "+path);return
    file.store_string(JSON.stringify(data));file.close()
    var error=DirAccess.rename_absolute(path+".tmp",path)
    if error!=OK:push_error("Cannot publish studio state: "+str(error))

func _settings() -> Dictionary:
    return plan.profile.defaults if scope<0 else plan.profile.scenes[scope].settings

func _apply() -> void:
    sampler.plan=plan
    var seconds=float(frame)*float(plan.fps_den)/float(plan.fps_num)
    var look: Dictionary=sampler.sample(seconds,float(night_amount.call()))
    var exposure=float(plan.profile.get("capture_exposure",1.0))
    if compare:look={"sunlight":1.0,"ambient":1.0,"camera_fill":0.0};exposure=1.0
    apply_look.call(look,exposure)
    controls["effective"].text="Live: %.0f%% exposure · %.0f%% fill" % [exposure*100,float(look.camera_fill)*100]

func _state() -> Dictionary:
    return {"online":online,"seen":Time.get_unix_time_from_system(),"generation":generation,
        "base_version":int(plan.version),"revision":int(plan.revision),"profile":plan.profile,
        "dirty":plan.profile!=saved,"frame":frame,"scope":scope,"time_of_day":time_of_day,
        "compare":compare,"error":last_error,"effective":controls["effective"].text,"studio_version":VERSION}

func _publish() -> void:
    _write(folder.path_join("state.json"),_state())
    status.text=("Unsaved preview" if plan.profile!=saved else "Saved lighting v%d" % int(plan.version))+" · "+last_error

func _process(delta: float) -> void:
    if folder.is_empty():return
    _apply()
    elapsed+=delta
    if elapsed<0.15 or busy:return
    elapsed=0
    _publish()
    var files=DirAccess.get_files_at(folder.path_join("commands"))
    files.sort()
    for filename in files:
        if not filename.ends_with(".json"):continue
        busy=true
        var path=folder.path_join("commands").path_join(filename)
        var command=_read(path)
        DirAccess.remove_absolute(path)
        var reply=await _command(command)
        _write(folder.path_join("ack-"+str(command.get("id","invalid"))+".json"),reply)
        busy=false
        if not online:get_tree().quit();return

func _command(c: Dictionary) -> Dictionary:
    if Time.get_unix_time_from_system()-float(c.get("created",0))>30:return {"ok":false,"error":"Expired command"}
    var action=str(c.get("action",""))
    if action in ["update","save","reload"] and int(c.get("expected_generation",-1))!=generation:
        return {"ok":false,"error":"Stale preview generation","generation":generation}
    last_error=""
    match action:
        "update":
            if c.has("scope"):scope=int(c.scope)
            if c.has("exposure"):plan.profile.capture_exposure=float(c.exposure)
            if c.has("camera_fill"):_settings().camera_fill=float(c.camera_fill)
            if c.has("frame"):frame=int(c.frame)
            if c.has("compare"):compare=bool(c.compare)
            if c.has("time_of_day"):time_of_day=str(c.time_of_day);set_day.call(time_of_day)
            generation+=1
            _sync()
        "save":_save()
        "reload":_reload(c.lighting)
        "screenshot":
            await RenderingServer.frame_post_draw
            var error=get_viewport().get_texture().get_image().save_png(str(c.path))
            return {"ok":error==OK,"path":c.path,"generation":generation}
        "close":online=false
        _:return {"ok":false,"error":"Unknown command"}
    _apply();_publish()
    return {"ok":last_error.is_empty(),"error":last_error,"generation":generation,"state":_state()}

func _save() -> void:
    _publish()
    var result_path=folder.path_join("save-result.json")
    if FileAccess.file_exists(result_path):DirAccess.remove_absolute(result_path)
    var output=[]
    var exit_code=OS.execute(str(config.backend),["--root",str(config.root),"--studio-save",str(config.session)],output,true,false)
    var result=_read(result_path)
    if exit_code!=0 or not result.get("ok",false):
        last_error=str(result.get("error","Save failed: "+str(output)))
        return
    _reload(result.result)

func _reload(lighting: Dictionary) -> void:
    plan.profile=lighting.profile.duplicate(true)
    plan.version=int(lighting.version);plan.revision=int(lighting.revision)
    _integer_frames()
    saved=plan.profile.duplicate(true)
    scope=-1
    generation+=1
    _sync()

func _local_update(key: String, value) -> void:
    var c={"action":"update","expected_generation":generation,"created":Time.get_unix_time_from_system()}
    c[key]=value
    _command(c)

func _slider(box: VBoxContainer, title: String, key: String, minimum: float, maximum: float, increment: float) -> void:
    var label=Label.new();label.text=title;box.add_child(label)
    var slider=HSlider.new();slider.min_value=minimum;slider.max_value=maximum;slider.step=increment
    slider.custom_minimum_size.x=285;box.add_child(slider);controls[key]=slider
    slider.value_changed.connect(func(value):_local_update(key,value))

func _build_ui() -> void:
    var panel=PanelContainer.new();panel.position=Vector2(18,18);add_child(panel)
    var margin=MarginContainer.new()
    for side in ["left","right","top","bottom"]:margin.add_theme_constant_override("margin_"+side,14)
    panel.add_child(margin)
    var box=VBoxContainer.new();box.add_theme_constant_override("separation",8);margin.add_child(box)
    var heading=Label.new();heading.text="ArcoreCut · Lighting studio";box.add_child(heading)
    var choices=OptionButton.new();box.add_child(choices);controls.scope=choices
    choices.item_selected.connect(func(index):_local_update("scope",index-1))
    _slider(box,"Capture exposure · 0.8 = 80%","exposure",0.1,2.0,0.01)
    _slider(box,"Soft camera fill · 0.35 = 35%","camera_fill",0.0,1.0,0.01)
    var day=OptionButton.new()
    for item in ["Day","Dusk","Night"]:day.add_item(item)
    box.add_child(day);controls.time_of_day=day
    day.item_selected.connect(func(index):_local_update("time_of_day",["day","dusk","night"][index]))
    var label=Label.new();label.text="Profile sample frame (does not seek gameplay)";box.add_child(label)
    var sample=SpinBox.new();sample.max_value=float(plan.frames)-1;sample.step=1;box.add_child(sample);controls.frame=sample
    sample.value_changed.connect(func(value):_local_update("frame",int(value)))
    var toggle=CheckBox.new();toggle.text="Compare with original game lighting";box.add_child(toggle);controls.compare=toggle
    toggle.toggled.connect(func(value):_local_update("compare",value))
    var effective=Label.new();box.add_child(effective);controls.effective=effective
    var save=Button.new();save.text="Save lighting to ArcoreCut";box.add_child(save)
    save.pressed.connect(func():_save();_publish())
    var reset=Button.new();reset.text="Revert preview to loaded profile";box.add_child(reset)
    reset.pressed.connect(func():plan.profile=saved.duplicate(true);generation+=1;last_error="";_sync();_publish())
    status=Label.new();status.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;status.custom_minimum_size.x=285;box.add_child(status)

func _sync() -> void:
    var choices: OptionButton=controls.scope
    choices.clear();choices.add_item("Production default")
    for scene in plan.profile.scenes:choices.add_item("Frames %d-%d" % [scene.start,scene.end])
    choices.select(scope+1)
    controls.exposure.set_value_no_signal(float(plan.profile.get("capture_exposure",1.0)))
    controls.camera_fill.set_value_no_signal(float(_settings().get("camera_fill",0.0)))
    controls.frame.set_value_no_signal(frame)
    controls.compare.set_pressed_no_signal(compare)
    controls.time_of_day.select(["day","dusk","night"].find(time_of_day))

func _integer_frames() -> void:
    plan.profile.transition_frames=int(plan.profile.transition_frames)
    for row in plan.profile.scenes:
        row.start=int(row.start);row.end=int(row.end)

func _exit_tree() -> void:
    if folder.is_empty():return
    online=false
    _write(folder.path_join("state.json"),_state())
