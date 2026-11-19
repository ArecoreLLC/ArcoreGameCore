extends Node
## GameCore ambient chatter (workflow ambient-chatter): short proximity one-liners from bystanders
## (dock parrots asking "Which way?", puffers calling "Where's your boat?") that never interrupt the
## game's own dialogue. Each source has an actor, a speaker name, lines, a radius and an optional
## condition; a shared cooldown per source keeps them rare. The game supplies how to speak and when
## its dialogue is free. Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
signal said(key: String, text: String)

@export var player: Node3D
var speak := Callable()        # (actor: Node3D, who: String, text: String) -> void
var is_free := Callable()      # () -> bool, true when no other line is showing
var sources: Array[Dictionary]=[]
var said_count := 0

## Add a source. condition: optional (player: Node3D) -> bool (for example "only while flying").
func add_source(key: String, actor: Node3D, who: String, lines: Array, radius := 7.0, cooldown := 70.0, condition := Callable()) -> void:
    sources.append({"key":key,"actor":actor,"who":who,"lines":lines,"radius":radius,"cooldown":cooldown,"wait":0.0,"turn":0,"condition":condition})

func _process(delta: float) -> void:
    if not player or not speak.is_valid():return
    for s in sources:s.wait=maxf(0,float(s.wait)-delta)
    if is_free.is_valid() and not bool(is_free.call()):return
    for s in sources:
        var actor: Node3D=s.actor
        if float(s.wait)>0 or not is_instance_valid(actor) or not actor.is_visible_in_tree():continue
        if player.global_position.distance_to(actor.global_position)>float(s.radius):continue
        var condition: Callable=s.condition
        if condition.is_valid() and not bool(condition.call(player)):continue
        var lines: Array=s.lines
        var text: String=lines[int(s.turn)%lines.size()]
        speak.call(actor,s.who,text)
        s.turn=int(s.turn)+1;s.wait=s.cooldown;said_count+=1
        KIT.ping(actor.global_position,.8,2.0)
        said.emit(s.key,text)
        return
