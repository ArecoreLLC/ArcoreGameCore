extends RefCounted
## GameCore idle scheduler (workflow idle-fidgets-and-visitors): decides when a character who stands
## still should fidget (look around, stretch, yawn …) and when a small visitor should come by
## (a butterfly, a bird, a crab). The game plays the actual motion; this keeps the timing honest.
## Call update(delta, still) every frame; it returns {"fidget": name or "", "visitor": name or ""}
## for this frame's starts. progress() gives 0..1 through the running fidget. Do not edit the vendored copy.
const VERSION := "0.1.0"

var fidgets: Array[String]=["look_around","stretch","tail_swish","sniff","yawn"]
var fidget_seconds: Dictionary={}   # name -> seconds (default 2.0)
var visitors: Array[String]=[]
var fidget_after := 3.5             # still this long before the first fidget
var fidget_gap := Vector2(4.5,7.0)  # seconds between fidgets
var visitor_after := 6.0
var visitor_gap := Vector2(9.0,15.0)
var still_time := 0.0
var current := ""
var elapsed := 0.0
var wait := 0.0
var visitor_wait := 0.0
var count := 0
var visitor_count := 0
var rng := RandomNumberGenerator.new()

func _init(seed_value := 1) -> void:
    rng.seed=seed_value;wait=rng.randf_range(fidget_gap.x,fidget_gap.y)*.5;visitor_wait=rng.randf_range(visitor_gap.x,visitor_gap.y)*.5

func duration(name: String) -> float:
    return float(fidget_seconds.get(name,2.0))

func progress() -> float:
    return clampf(elapsed/duration(current),0,1) if current!="" else 0.0

## still: on the ground, not moving, not busy. Interrupting (still = false) cancels the fidget.
func update(delta: float, still: bool) -> Dictionary:
    var started := {"fidget":"","visitor":""}
    if not still:
        still_time=0.0;current="";return started
    still_time+=delta
    if current!="":
        elapsed+=delta
        if elapsed>=duration(current):current=""
    elif still_time>=fidget_after and not fidgets.is_empty():
        wait-=delta
        if wait<=0:
            current=fidgets[count%fidgets.size()];count+=1;elapsed=0.0
            wait=rng.randf_range(fidget_gap.x,fidget_gap.y);started.fidget=current
    if still_time>=visitor_after and not visitors.is_empty():
        visitor_wait-=delta
        if visitor_wait<=0:
            visitor_wait=rng.randf_range(visitor_gap.x,visitor_gap.y)
            started.visitor=visitors[visitor_count%visitors.size()];visitor_count+=1
    return started
