extends RefCounted
## Pure reveal envelope and grain samples. No shader, mesh, texture or actor ownership.
const VERSION := "1.0.0"

static func sample(age: float, model_height: float, footprint := .34, shrink_time := 1.4, print_time := 3.2, ready_time := 5.2, base_offset := -.08) -> Dictionary:
    for value in [age,model_height,footprint,shrink_time,print_time,ready_time,base_offset]:
        if not is_finite(value):return {}
    if model_height<=0 or footprint<0 or shrink_time<=0 or print_time<=0 or ready_time<shrink_time+print_time:return {}
    var progress := clampf((age-shrink_time)/print_time,0,1)
    var fade := smoothstep(shrink_time,shrink_time+print_time,age)
    return {"progress":progress,"printing":age>=shrink_time and age<shrink_time+print_time,
        "clip_enabled":age<shrink_time+print_time,"local_height":base_offset+progress*model_height,
        "picture_scale":lerpf(1.0,footprint,smoothstep(0,shrink_time,age)),
        "picture_alpha":1.0-fade,"picture_visible":fade<1.0,
        "animation_ready":age>=shrink_time+print_time,"follow_ready":age>ready_time}

static func grain(age: float, index: int, count: int, local_height: float) -> Dictionary:
    if not is_finite(age) or not is_finite(local_height) or count<=0 or index<0 or index>=count:return {}
    var phase := fmod(age*1.15+float(index)/count,1.0)
    var angle := index*2.39996+age*.5
    var radius := lerpf(.85,.48,phase)
    return {"position":Vector3(cos(angle)*radius,phase*maxf(.15,local_height),sin(angle)*radius),"scale":.5+sin(phase*PI)}
