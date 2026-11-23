extends RefCounted
## Asset-free flutter trajectories. Caller owns time, placement, rig and gameplay.
const VERSION := "1.0.0"

static func swarm_position(center: Vector3, time: float, phase: float, spread := 1.0) -> Vector3:
    return center+Vector3((sin(time*.7+phase)*2.2+sin(time*1.9+phase*2)*.6)*spread,1.0+sin(time*1.3+phase)*.6+.4*sin(time*3.1+phase),(cos(time*.6+phase)*2.2+cos(time*2.3+phase)*.5)*spread)

static func orbit_position(home: Vector3, time: float) -> Vector3:
    return home+Vector3(cos(time*.8)*.65+sin(time*1.9)*.10,sin(time*1.5)*.12+sin(time*3.1)*.03,sin(time*.8)*.39+cos(time*1.3)*.08)

static func burst_amplitude(time: float, glides := true) -> float:
    return .65*(.25+.75*smoothstep(-.3,.3,sin(time*1.7))) if glides else .65

## Moving perch is intentionally sampled by the caller each frame. No actor lock.
static func visit_position(start: Vector3, perch: Vector3, departure: Vector3, time: float, approach := 2.2, depart_at := 5.5, finish := 7.5) -> Vector3:
    if approach<=0 or depart_at<approach or finish<=depart_at:return perch
    if time<approach:
        var t := maxf(0,time)
        return start.lerp(perch,smoothstep(0,approach,t))+Vector3(0,sin(t*6)*.15*(1-t/approach),0)
    if time<depart_at:return perch
    return perch.lerp(departure,smoothstep(depart_at,finish,time))
