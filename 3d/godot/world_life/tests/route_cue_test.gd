extends SceneTree
const ROUTE = preload("res://addons/gamecore_world_life/terrain_ring_clearance.gd")
const CURSOR = preload("res://addons/gamecore_world_life/timed_cue_cursor.gd")
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
    checks+=1
    if not ok:failures+=1;push_error(label)
func _initialize() -> void:
    var height := func(x: float,z: float):return sin(x*.3)+cos(z*.4)-3
    for i in range(150):
        var home := Vector3(i*.17,-1.1 if i%2==0 else -1.6,i*.07)
        var radius := 1.0 if i%2==0 else 2.2
        var margin := .45 if i%2==0 else 1.35
        var expected := true
        for j in range(32):
            var p := home+Vector3(cos(j*TAU/32),0,sin(j*TAU/32))*(radius+margin)
            if height.call(p.x,p.z)>home.y-margin:expected=false;break
        expected=expected and height.call(home.x,home.z)<home.y-margin
        check(ROUTE.clear(home,radius,margin,height)==expected,"legacy ring parity")
    check(ROUTE.clear(Vector3(0,5,0),4,.2,func(_x,_z):return 0,8),"alternate elevated ring and sample count")
    check(not ROUTE.clear(Vector3.ZERO,1,0,func(_x,_z):return 0),"center equality blocked")
    check(ROUTE.clear(Vector3.ZERO,1,0,func(x,z):return -1 if x==0 and z==0 else 0),"ring equality accepted")
    check(not ROUTE.clear(Vector3.ZERO,1,0,func(_x,_z):return NAN),"nonfinite terrain rejected")
    check(not ROUTE.clear(Vector3.ZERO,1,0,func(_x,_z):return "bad"),"nonnumeric terrain rejected")
    check(not ROUTE.clear(Vector3.ZERO,1,0,Callable()),"missing sampler rejected")
    check(not ROUTE.clear(Vector3.ZERO,-1,0,height),"invalid radius")
    check(not ROUTE.clear(Vector3.ZERO,1,0,height,2),"invalid sample count")
    var cursor := CURSOR.new()
    var cues := [{"start":0,"end":2},{"start":2,"end":5}]
    check(cursor.observe("song",0,cues)==0,"first cue")
    check(cursor.observe("song",1,cues)==-1,"duplicate suppressed")
    check(cursor.observe("song",2,cues)==1,"half open boundary")
    check(cursor.observe("song",5,cues)==-1,"end excluded")
    check(cursor.observe("song",1,cues)==0,"rewind replays cue")
    check(cursor.observe("song",.8,cues)==-1,"small clock jitter ignored")
    check(cursor.observe("other",.8,cues)==0,"track switch distinct")
    cursor.reset()
    check(cursor.observe("tutorial",1,[{"start":0,"end":3},{"start":1,"end":4}])==0,"first overlap wins")
    check(cursor.observe("tutorial",2,[{"start":0,"end":3},{"start":1,"end":4}])==-1,"no second overlap dispatch")
    check(cursor.observe("tutorial",3,[{"start":0,"end":3},{"start":1,"end":4}])==1,"second interval after first ends")
    cursor.reset()
    check(cursor.observe("x",1,[{},null,{"start":0,"end":2}])==2,"malformed entries skipped")
    check(cursor.observe("x",NAN,cues)==-1,"nonfinite clock ignored")
    cursor.reset()
    # Observing during a consumer cooldown consumes the cue, without dispatch retries.
    check(cursor.observe("x",0,cues)==0 and cursor.observe("x",1,cues)==-1,"cooldown observation contract")
    print("ROUTE_CUE_MODULES ","PASS" if failures==0 else "FAIL"," checks=",checks)
    quit(0 if failures==0 else 1)
