extends Node
## GameCore beat-synced dance (workflow beat-synced-dance): makes a character hop, squash and swing
## its limbs on the beat of the playing song, and emits `stomped` on every landing (for dust puffs,
## drum taps or footstep sounds). Add it as a child of the character and set `body` (the node to
## move) and optionally `limbs` (arm and leg pivots, swung about X; arms first, then legs).
## The beat comes from the world-life kit (KIT.beat_phase / KIT.on_beat), which the game sets each
## frame with KIT.set_beat() from a beat map (tools/song_beats.py). Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
signal stomped(at: Vector3)

@export var body: Node3D
@export var limbs: Array[Node3D]=[]
@export var hop_height := .22            # metres at the top of each hop
@export var squash := .1                 # scale squash on landing
@export var swing := .6                  # limb swing (radians)
@export var beats_per_hop := 1           # 2 = hop every other beat
@export var phase_offset := 0.0          # 0..1 of a hop; stagger dancers in a group
@export var enabled := true
var rest_position := Vector3.INF
var rest_scale := Vector3.ONE
var hops := 0

func _ready() -> void:
    if not body and get_parent() is Node3D:body=get_parent()
    if body:rest_position=body.position;rest_scale=body.scale

## Hop phase 0..1 for the current beat (0 = landing).
func phase() -> float:
    var beat: float=KIT.beat_index+KIT.beat_phase
    return fposmod(beat/maxf(1.0,beats_per_hop)+phase_offset,1.0)

func _process(_delta: float) -> void:
    if not body or not enabled:return
    if rest_position==Vector3.INF:rest_position=body.position;rest_scale=body.scale
    var u := phase()
    var hop := sin(u*PI)
    body.position=rest_position+Vector3(0,hop*hop_height,0)
    var land := 1.0-smoothstep(0.0,.18,u)
    body.scale=rest_scale*Vector3(1.0+squash*land*.8,1.0-squash*land,1.0+squash*land*.8)
    for i in range(limbs.size()):
        var side := 1.0 if i%2==0 else -1.0
        var leg := i>=2
        limbs[i].rotation.x=sin(u*TAU)*swing*side*(.6 if leg else 1.0)
    if KIT.on_beat and int(KIT.beat_index)%maxi(1,beats_per_hop)==0:
        hops+=1;stomped.emit(body.global_position)

## Re-anchor after the game moves the dancer (for example, when a dance group walks somewhere).
func set_rest(position: Vector3) -> void:
    rest_position=position
