extends SceneTree
const COVERAGE := preload("res://addons/gamecore_world_life/painting_coverage.gd")
const REVEAL := preload("res://addons/gamecore_world_life/sand_reveal.gd")
const FOLLOW := preload("res://addons/gamecore_world_life/companion_follow.gd")
var failures: Array[String]=[]
var checks := 0
func check(ok: bool,label: String):
    checks+=1
    if not ok:failures.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
    var coverage := COVERAGE.new()
    var labels := PackedInt32Array()
    for i in range(18*16):labels.append(i%6-1)
    check(coverage.configure(Vector2i(18,16),labels,5),"arbitrary dimensions and palette")
    labels[0]=4
    check(coverage.groups[0]==-1,"input labels copied")
    var old_marked := PackedByteArray();old_marked.resize(18*16);old_marked.fill(0)
    var old_counts := [0,0,0,0,0]
    for color in range(5):
        for k in range(8):
            var point := Vector2(k*3-2,k*2)
            for y in range(maxi(0,int(point.y)-9),mini(16,int(point.y)+10)):
                for x in range(maxi(0,int(point.x)-9),mini(18,int(point.x)+10)):
                    var index := y*18+x
                    if Vector2(x,y).distance_squared_to(point)>81:continue
                    if coverage.groups[index]!=color or old_marked[index]==1:continue
                    old_marked[index]=1;old_counts[color]+=1
            var changed := coverage.dab(point,color)
            check(coverage.marked==old_marked and coverage.counts==old_counts,"legacy brush parity")
            check(changed.size()<=coverage.counts[color],"delta indices only")
        if old_counts[color]>=ceili(coverage.totals[color]*.85):
            for index in range(coverage.groups.size()):
                if coverage.groups[index]==color and old_marked[index]==0:old_marked[index]=1;old_counts[color]+=1
        coverage.assist(color)
        check(coverage.marked==old_marked and coverage.counts==old_counts,"edge assist parity")
    check(coverage.is_complete(),"complete after all groups")
    coverage.reset();check(coverage.counts==[0,0,0,0,0] and not coverage.is_complete(),"replay resets coverage")
    check(not coverage.configure(Vector2i(2,2),PackedInt32Array([0]),1),"reject invalid dimensions")
    check(coverage.width==18,"invalid configure preserves state")
    check(coverage.dab(Vector2(NAN,0),0).is_empty(),"reject nonfinite brush")
    check(coverage.dab(Vector2.ZERO,-1).is_empty(),"paper cannot be selected")
    check(coverage.assist(0,1.1).is_empty(),"invalid assist threshold")
    var sparse := COVERAGE.new();sparse.configure(Vector2i(10,1),PackedInt32Array([0,0,0,0,0,0,0,0,0,0]),2)
    sparse.stroke(Vector2.ZERO,Vector2(7,0),0,0,1)
    check(sparse.counts[0]==8 and sparse.assist(0,.85).is_empty(),"no early assist at 80 percent")
    sparse.dab(Vector2(8,0),0,0);check(sparse.assist(0,.85).size()==1 and sparse.is_complete(),"assist after threshold; empty group irrelevant")
    check(sparse.percent(1)==0 and sparse.dab(Vector2(8,0),0,0).is_empty(),"empty group and duplicate dab")
    var blank := COVERAGE.new();blank.configure(Vector2i(1,1),PackedInt32Array([-1]),1)
    check(not blank.is_complete(),"blank canvas does not auto-complete")
    for i in range(160):
        var age := i*.05
        var state := REVEAL.sample(age,2.75,.34)
        var progress := clampf((age-1.4)/3.2,0,1)
        check(is_equal_approx(state.local_height,-.08+progress*2.75),"print height parity")
        check(is_equal_approx(state.picture_scale,lerpf(1,.34,smoothstep(0,1.4,age))),"shrink parity")
        check(is_equal_approx(state.picture_alpha,1-smoothstep(1.4,4.6,age)),"fade parity")
        check(state.printing==(age>=1.4 and age<4.6) and state.follow_ready==(age>5.2),"phase boundaries")
    check(REVEAL.sample(3,2.75,.34,1.4,0).is_empty(),"invalid print duration")
    check(not REVEAL.sample(4.6,2.75).printing and REVEAL.sample(4.6,2.75).animation_ready,"print ends exactly")
    check(not REVEAL.sample(5.2,2.75).follow_ready,"follow uses original strict boundary")
    check(REVEAL.grain(2,0,0,1).is_empty(),"zero grain count")
    for i in range(48):
        var age := 2.7;var height := 1.2
        var phase := fmod(age*1.15+float(i)/48,1)
        var angle := i*2.39996+age*.5;var radius := lerpf(.85,.48,phase)
        var expected := Vector3(cos(angle)*radius,phase*maxf(.15,height),sin(angle)*radius)
        check(REVEAL.grain(age,i,48,height).position.distance_to(expected)<.000001,"grain parity")
    var position := Vector3.ZERO;var yaw := 0.0
    for i in range(100):
        var leader := Vector3(sin(i*.1)*30,5,cos(i*.1)*10)
        var delta := .016
        var target := leader+Vector3(2,0,1)
        if Vector2(target.x,target.z).length()>22:target=Vector3.ZERO
        var old_position := position;var old_yaw := yaw;var moving := false
        var distance := Vector2(target.x-position.x,target.z-position.z).length()
        if distance>1.3:
            var direction := target-position;direction.y=0;direction=direction.normalized()
            old_position+=direction*minf(distance,1.8*delta)
            old_yaw=lerp_angle(yaw,atan2(-direction.x,-direction.z),1-exp(-5*delta));moving=true
        var result := FOLLOW.step(position,yaw,leader,Vector3.ZERO,delta)
        check(result.position.distance_to(old_position)<.000001 and is_equal_approx(result.yaw,old_yaw) and result.moving==moving,"following trajectory parity")
        position=result.position;yaw=result.yaw
    var large := FOLLOW.step(Vector3(0,7,0),0,Vector3(2,99,0),Vector3.ZERO,100,Vector3.ZERO)
    check(large.position==Vector3(2,7,0),"no overshoot; caller retains height")
    check(FOLLOW.step(Vector3.ZERO,0,Vector3.ZERO,Vector3.ZERO,1,Vector3.ZERO).moving==false,"stop at target")
    check(FOLLOW.step(Vector3.ZERO,0,Vector3(100,0,0),Vector3.ZERO,1).returning_home,"leash returns home")
    check(not FOLLOW.step(Vector3.ZERO,0,Vector3.ONE,Vector3.ZERO,-1).moving,"negative delta rejected")
    print("PAINTING_MODULES ","PASS" if failures.is_empty() else "FAIL"," checks=",checks)
    quit(0 if failures.is_empty() else 1)
