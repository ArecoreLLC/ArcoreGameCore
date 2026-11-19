extends SceneTree
## Headless test of the GameCore world-life components on a flat test world (land for z < 5, water
## beyond). tools/tests/test_world_life_godot.py copies the module into a temporary Godot project
## and runs this when $GODOT points at a Godot 4 executable. Components are driven by hand at a
## fixed 1/30 s step, so results do not depend on how fast headless frames run.
const DIR := "res://addons/gamecore_world_life/"
const DT := 1.0/30.0
var KIT: GDScript
var world: Node3D
var results := {}

func _initialize() -> void:
    call_deferred("run")

func tick(nodes: Array, seconds: float, each := Callable()) -> void:
    var steps := int(seconds/DT)
    for i in range(steps):
        KIT.time+=DT
        if each.is_valid():each.call(i)
        for n in nodes:n._process(DT)

func run() -> void:
    KIT=load(DIR+"world_life_kit.gd")
    KIT.reset()
    world=Node3D.new();world.set_script(load("res://flat_world.gd"));root.add_child(world)
    var cam := Camera3D.new();root.add_child(cam);cam.position=Vector3(0,3,10);cam.current=true
    await process_frame
    # Kit: merged meshes, shore placement, beat clock.
    var mesh: ArrayMesh=KIT.merge([[KIT.sphere_mesh(8),KIT.xf(Vector3.ZERO,Vector3.ONE),Color.RED],[KIT.box_mesh(),KIT.xf(Vector3(1,0,0),Vector3.ONE*.5),Color.BLUE]])
    results.kit_merge=mesh.get_surface_count()==1 and mesh.surface_get_array_len(0)>40
    var edge: Vector3=KIT.shore(world,Vector2.ZERO,PI*.5,0.0)
    results.kit_shore_finds_waterline=absf(edge.z-5.0)<.6
    KIT.set_beat({"s":{"bpm":120.0,"offset":0.0}},"s",1.25)
    results.kit_set_beat=KIT.beat_index==2 and absf(KIT.beat_phase-.5)<.001 and KIT.bpm==120.0
    # Beat dance: hops and stomps on the beat.
    var dancer := Node3D.new();root.add_child(dancer)
    var dance: Node=load(DIR+"beat_dance.gd").new();dance.body=dancer;dancer.add_child(dance);dance.set_process(false)
    # Lambdas capture locals by value: shared state lives in a dictionary.
    var state := {"song":0.0,"top":0.0}
    tick([dance],4.0,func(_i):
        state.song+=DT;KIT.set_beat({"s":{"bpm":120.0,"offset":0.0}},"s",state.song)
        state.top=maxf(state.top,dancer.position.y))
    results.dance_stomps_on_beats=dance.hops>=7 and dance.hops<=9
    results.dance_hops=state.top>.18
    # Attention glance: looks at a ping in front, then rests.
    var head := Transform3D(Basis.IDENTITY,Vector3(0,1.6,0))
    var glance: RefCounted=load(DIR+"attention_glance.gd").new()
    for i in range(30):
        KIT.time+=DT;KIT.ping(Vector3(3,1.6,-6),1.0,.4);glance.update(DT,head,Vector3(0,0,-1))
    results.glance_turns_head=glance.weight>.5 and glance.look.x>.1
    for i in range(110):
        KIT.time+=DT;KIT.ping(Vector3(3,1.6,-6),1.0,.4);glance.update(DT,head,Vector3(0,0,-1))
    results.glance_rests=glance.resting>0 and glance.weight<.5
    # Idle scheduler: a fidget after standing still, a visitor later, cancelled by moving.
    var idle: RefCounted=load(DIR+"idle_scheduler.gd").new(3)
    idle.visitors.assign(["butterfly"])
    var fidget := "";var visitor := ""
    for i in range(int(16.0/DT)):
        var r: Dictionary=idle.update(DT,true)
        if r.fidget!="" and fidget=="":fidget=r.fidget
        if r.visitor!="" and visitor=="":visitor=r.visitor
    results.idle_fidget_and_visitor=fidget!="" and visitor=="butterfly"
    idle.update(DT,false)
    results.idle_moving_cancels=idle.current=="" and idle.still_time==0.0
    # Escort formation: joins the moving leader, leaves when inactive.
    var leader := Node3D.new();root.add_child(leader);leader.position=Vector3(0,0,20)
    var escort: Node=load(DIR+"escort_formation.gd").new();root.add_child(escort);escort.set_process(false)
    var f1 := Node3D.new();var f2 := Node3D.new();root.add_child(f1);root.add_child(f2)
    escort.leader=leader;escort.followers.assign([f1,f2]);escort.slots.assign([Vector3(-4,0,6),Vector3(4,0,6)]);escort.active=true
    tick([escort],4.0,func(_i):leader.position.z+=.2)
    var want: Vector3=escort.frame()*Vector3(-4,0,6)
    results.escort_joins=f1.visible and Vector2(f1.global_position.x-want.x,f1.global_position.z-want.z).length()<2.5
    escort.active=false
    tick([escort],5.0)
    results.escort_leaves=not f1.visible and escort.blend==0.0
    # Proximity notes: three objects passed quickly make a chord.
    var notes: Node3D=load(DIR+"proximity_notes.gd").new()
    var walker := Node3D.new();root.add_child(walker)
    var stones: Array[Node3D]=[]
    for i in range(3):
        var s := Node3D.new();root.add_child(s);s.position=Vector3(i*4.0,0,0);stones.append(s)
    notes.player=walker;notes.objects=stones;root.add_child(notes);notes.set_process(false)
    tick([notes],3.0,func(i):walker.position=Vector3(-2.0+i*DT*5.0,0,0))
    results.notes_sing_and_chord=notes.played>=6 and notes.chords==1
    # Time of day: night mode publishes KIT.night and dims the sun.
    var sun := DirectionalLight3D.new();sun.light_energy=1.0;root.add_child(sun)
    var env := Environment.new();env.background_energy_multiplier=1.0;env.ambient_light_energy=.4
    var tod: Node3D=load(DIR+"time_of_day.gd").new();tod.sun=sun;tod.environment=env;root.add_child(tod);tod.set_process(false)
    tod.set_mode(2,true);tod._process(DT)
    results.night_mode=KIT.night==1.0 and sun.light_energy<.2 and env.background_energy_multiplier<.2
    tod.set_mode(0,true);tod._process(DT)
    results.day_restores=KIT.night==0.0 and absf(sun.light_energy-1.0)<.01
    # Ambient chatter: one line when near and free, then a cooldown.
    var chatter: Node=load(DIR+"ambient_chatter.gd").new();root.add_child(chatter);chatter.set_process(false)
    var parrot := Node3D.new();root.add_child(parrot);parrot.position=Vector3(1,0,0)
    var heard: Array[String]=[]
    chatter.player=walker;walker.position=Vector3.ZERO
    chatter.speak=func(_actor,_who,text):heard.append(text)
    chatter.is_free=func():return true
    chatter.add_source("parrots",parrot,"Dock parrots",["Which way?","Onward through!"],5.0,60.0)
    tick([chatter],2.0)
    results.chatter_once=heard==["Which way?"]
    # Route gates: built along the route; passing one fires once.
    var gates: Node3D=load(DIR+"route_gates.gd").new();root.add_child(gates);gates.set_process(false)
    var count: int=gates.build(Vector3(0,0,100),Vector3(200,0,100))
    var boat := {"at":Vector3(40,0,100)}
    gates.vehicle_position=func():return boat.at
    tick([gates],2.0,func(i):boat.at=Vector3(40+i*DT*8.0,0,100))
    results.gates_built=count==4
    results.gate_passed_once=gates.passes==1
    # Celebration: three volleys, then quiet.
    var party: Node3D=load(DIR+"celebration_burst.gd").new();root.add_child(party);party.set_process(false)
    party.add_cannon(Vector3(0,0,0),Vector3(0,0,1));party.add_cannon(Vector3(2,0,0),Vector3(0,0,1));party.fire()
    tick([party],2.5)
    results.celebration_fires=party.fired==1 and party.queue.is_empty() and party.emitters.size()==2
    # Splash pool and leap arcs.
    var splash: Node3D=load(DIR+"splash_pool.gd").new();root.add_child(splash);splash.set_process(false)
    splash.spawn(Vector3(0,0,10),1.0,false);tick([splash],.5)
    var BREACH: GDScript=load(DIR+"sea_breach.gd")
    results.splash_and_leap=splash.spawned==1 and absf(BREACH.arc_point(Vector3.ZERO,Vector3.FORWARD,4.0,1.0,.5).y-1.0)<.001
    var passed := results.values().all(func(v):return v==true)
    for k in results:print("WORLD_LIFE_COMPONENT ",k,"=",results[k])
    print("WORLD_LIFE_COMPONENTS ",("PASS" if passed else "FAIL"))
    quit(0 if passed else 1)
