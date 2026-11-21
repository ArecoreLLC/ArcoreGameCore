extends SceneTree
func _initialize() -> void:
    var sampler=load(get_script().resource_path.get_base_dir()+"/../capture_lighting.gd").new()
    sampler.plan={"fps_num":30,"fps_den":1,"profile":{"capture_exposure":.8,"defaults":{"sunlight":1.0,"ambient":1.0,"camera_fill":.15},"preserve_dusk_night":true,"transition_frames":30,"scenes":[{"start":30,"end":90,"settings":{"sunlight":.6,"ambient":1.2,"camera_fill":.3}}]}}
    var checks=[is_equal_approx(sampler.sample(0.0,0.0).sunlight,1.0),is_equal_approx(sampler.sample(1.0,0.0).sunlight,1.0),is_equal_approx(sampler.sample(1.5,0.0).sunlight,.8),is_equal_approx(sampler.sample(2.0,0.0).sunlight,.6),is_equal_approx(sampler.sample(3.5,0.0).sunlight,.8),is_equal_approx(sampler.sample(4.0,0.0).sunlight,1.0),is_equal_approx(sampler.sample(2.0,.55).sunlight,1.0),is_equal_approx(sampler.sample(2.0,1.0).ambient,1.0)]
    checks.append(is_equal_approx(sampler.sample(2.0,.55).camera_fill,0.0))
    checks.append(is_equal_approx(sampler.sample(2.0,0.0).camera_fill,.3))
    sampler.plan.profile.preserve_dusk_night=false
    checks.append(is_equal_approx(sampler.sample(2.0,1.0).sunlight,.6))
    if checks.all(func(value):return value):print("PASS capture lighting blend boundaries, dusk/night protection and unprotected override");quit(0)
    else:push_error(str(checks));quit(1)
