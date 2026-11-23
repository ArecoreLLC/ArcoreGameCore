extends RefCounted
## Horizontal direct following, not collision avoidance or navigation. Y stays consumer-owned.
const VERSION := "1.0.0"

static func step(position: Vector3, yaw: float, leader: Vector3, home: Vector3, delta: float, offset := Vector3(2,0,1), leash := 22.0, stop_distance := 1.3, speed := 1.8, turn_rate := 5.0) -> Dictionary:
    var result := {"position":position,"yaw":yaw,"moving":false,"returning_home":false}
    if not position.is_finite() or not leader.is_finite() or not home.is_finite() or not offset.is_finite():return result
    for value in [yaw,delta,leash,stop_distance,speed,turn_rate]:
        if not is_finite(value):return result
    if delta<0 or leash<0 or stop_distance<0 or speed<0 or turn_rate<0:return result
    var target := leader+offset
    if Vector2(target.x-home.x,target.z-home.z).length()>leash:
        target=home;result.returning_home=true
    var distance := Vector2(target.x-position.x,target.z-position.z).length()
    if distance>stop_distance:
        var direction := target-position;direction.y=0;direction=direction.normalized()
        result.position=position+direction*minf(distance,speed*delta)
        result.yaw=lerp_angle(yaw,atan2(-direction.x,-direction.z),1-exp(-turn_rate*delta))
        result.moving=true
    return result
