extends RefCounted
## Pixel coverage only. Consumer owns segmentation, color pixels, texture and input UI.
const VERSION := "1.0.0"
var width := 0
var height := 0
var groups := PackedInt32Array()
var marked := PackedByteArray()
var totals: Array=[]
var counts: Array=[]

## -1 is paper; other values are zero-based palette IDs. Invalid input preserves state.
func configure(dimensions: Vector2i, labels: PackedInt32Array, colors: int) -> bool:
    if dimensions.x<=0 or dimensions.y<=0 or colors<=0 or dimensions.x*dimensions.y!=labels.size():return false
    for label in labels:
        if label< -1 or label>=colors:return false
    width=dimensions.x;height=dimensions.y;groups=labels.duplicate()
    totals.resize(colors);totals.fill(0)
    for label in groups:
        if label>=0:totals[label]+=1
    reset()
    return true

func reset() -> void:
    marked.resize(groups.size());marked.fill(0)
    counts.resize(totals.size());counts.fill(0)

func dab(point: Vector2, color: int, radius := 9.0) -> PackedInt32Array:
    var changed := PackedInt32Array()
    if not point.is_finite() or not is_finite(radius) or radius<0 or color<0 or color>=counts.size():return changed
    var extent := ceili(radius)
    for y in range(maxi(0,int(point.y)-extent),mini(height,int(point.y)+extent+1)):
        for x in range(maxi(0,int(point.x)-extent),mini(width,int(point.x)+extent+1)):
            if Vector2(x,y).distance_squared_to(point)>radius*radius:continue
            var index := y*width+x
            if groups[index]!=color or marked[index]==1:continue
            marked[index]=1;counts[color]+=1;changed.append(index)
    return changed

func stroke(from: Vector2, to: Vector2, color: int, radius := 9.0, spacing := 3.0) -> PackedInt32Array:
    var changed := PackedInt32Array()
    if not from.is_finite() or not to.is_finite() or not is_finite(spacing) or spacing<=0:return changed
    var steps := maxi(1,ceili(from.distance_to(to)/spacing))
    for i in range(steps+1):changed.append_array(dab(from.lerp(to,float(i)/steps),color,radius))
    return changed

## Complete tiny edges only when the selected group's threshold has been reached.
func assist(color: int, threshold := .85) -> PackedInt32Array:
    var changed := PackedInt32Array()
    if color<0 or color>=counts.size() or not is_finite(threshold) or threshold<0 or threshold>1:return changed
    if totals[color]==0 or counts[color]<ceili(totals[color]*threshold):return changed
    for index in range(groups.size()):
        if groups[index]==color and marked[index]==0:
            marked[index]=1;counts[color]+=1;changed.append(index)
    return changed

func percent(color: int) -> int:
    if color<0 or color>=counts.size():return 0
    return roundi(100.0*counts[color]/maxi(1,totals[color]))

func is_complete() -> bool:
    return not totals.is_empty() and totals.max()>0 and counts==totals
