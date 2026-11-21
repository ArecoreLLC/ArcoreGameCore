extends RefCounted
## Deterministic scene-lighting sampler. No cloud geometry or shadow overrides.
const VERSION := "0.1.0"
var plan := {}
func load_plan(path: String) -> bool:
    var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
    if not parsed is Dictionary or parsed.get("schema","")!="gamecore.lighting.v1":return false
    plan=parsed
    return true
func _settings_at(frame: int) -> Dictionary:
    for scene in plan.profile.scenes:
        if frame>=int(scene.start) and frame<int(scene.end):return scene.settings
    return plan.profile.defaults
func sample(time: float, night_amount: float) -> Dictionary:
    var baseline={"sunlight":1.0,"ambient":1.0,"camera_fill":0.0}
    if plan.is_empty():return baseline
    var frame := int(floor(time*float(plan.fps_num)/float(plan.fps_den)))
    var boundary := 0
    for scene in plan.profile.scenes:
        if int(scene.start)<=frame:boundary=maxi(boundary,int(scene.start))
        if int(scene.end)<=frame:boundary=maxi(boundary,int(scene.end))
    var target := _settings_at(frame)
    var previous := _settings_at(boundary-1)
    var blend := 1.0 if int(plan.profile.transition_frames)==0 else smoothstep(0.0,float(plan.profile.transition_frames),float(frame-boundary))
    var daylight := 1.0-smoothstep(0.0,0.55,night_amount) if plan.profile.preserve_dusk_night else 1.0
    var result := {}
    for key in baseline:result[key]=lerpf(float(baseline[key]),lerpf(float(previous.get(key,baseline[key])),float(target.get(key,baseline[key])),blend),daylight)
    return result
