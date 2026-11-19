extends Node3D
## GameCore proximity notes (workflow proximity-music-stones): objects (standing stones, bells,
## flowers) that each sing a note when the player passes, and sing a chord together when several
## are played in a row. Notes are synthesised at load time (no audio files). Connect `sang(index)`
## and `chord_played()` for glows, rings or a reward. Do not edit the vendored copy.
const KIT := preload("world_life_kit.gd")
const VERSION := "0.1.0"
const PENTATONIC := [261.63,293.66,329.63,392.0,440.0,523.25,587.33,659.25]   # C major pentatonic from C4
signal sang(index: int)
signal chord_played()

@export var player: Node3D
@export var objects: Array[Node3D]=[]
@export var radius := 3.2
@export var cooldown := 2.5
@export var chord_count := 3          # this many notes within
@export var chord_window := 4.0       # seconds make a chord
@export var volume_db := -8.0
var notes: Array[float]=[]
var streams: Array[AudioStreamWAV]=[]
var chord_stream: AudioStreamWAV
var cool: Array[float]=[]
var recent: Array[float]=[]
var played := 0
var chords := 0

func _ready() -> void:
    if notes.is_empty():
        for i in range(objects.size()):notes.append(PENTATONIC[i%PENTATONIC.size()])
    for f in notes:streams.append(KIT.tone([f,f*2.0,f*3.01],2.4,1.6,.35))
    chord_stream=KIT.tone([notes[0],notes[min(2,notes.size()-1)],notes[min(3,notes.size()-1)]],3.5,1.1,.32) if notes.size()>0 else null
    cool.resize(objects.size());cool.fill(0.0)

func sing(i: int, sound := true) -> void:
    cool[i]=cooldown;played+=1
    if sound:KIT.play_at(self,streams[i],objects[i].global_position+Vector3(0,1,0),volume_db)
    KIT.ping(objects[i].global_position+Vector3(0,1.4,0),.7,1.5)
    sang.emit(i)

## Every object sings together.
func chord() -> void:
    for i in range(objects.size()):sing(i,false)
    chords+=1
    if chord_stream and objects.size()>0:KIT.play_at(self,chord_stream,objects[0].global_position,volume_db+2)
    chord_played.emit()

func _process(delta: float) -> void:
    if not player:return
    var t: float=KIT.time
    for i in range(objects.size()):
        cool[i]=maxf(0,cool[i]-delta)
        if cool[i]<=0 and player.global_position.distance_to(objects[i].global_position)<radius:
            sing(i)
            recent.append(t)
            while recent.size()>0 and t-recent[0]>chord_window:recent.pop_front()
            if recent.size()>=chord_count:recent.clear();chord()
