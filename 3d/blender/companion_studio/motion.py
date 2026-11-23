"""Keyframed clips for small rigid-limb companions, written for Blender's Python.

Module: gamecore.blender.companion-studio (see README.md beside this file).

Poses are described in armature axes (X = side, -Y = forward, Z = up, degrees), accumulated per
bone and converted to each bone's own frame, so one routine drives rigs whose bones point in
different directions. A child's rotation is carried by its parent (ordinary forward kinematics).
Bones a rig does not have are skipped, which is what lets differently built animals share one
routine: the consumer supplies settings, never a species branch in this file.

What is here
- timing helpers, Pose, Animator (bakes a pose function to an NLA clip at 30 fps from frame 0);
- blink and tail_wave: shared behaviours with per-animal settings;
- Stepper: planted feet for single-bone limbs. The stride is derived from the speed the game
  moves the character at and the limb slides along its own length to stay on the ground. Two
  modes: flat-footed (standing animals) and pendulum (short plush limbs). Measure the result with
  the ArcoreAnimate clip report; rigid one-bone limbs still slide somewhat;
- seated_clips: Idle / Walk / Greet for seated plush animals that walk on all fours.

The math helpers import without Blender; Animator needs bpy.
"""
import math

VERSION = '1.0.0'
TAU = math.tau
FPS = 30


# ---------- timing helpers ----------
def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def wave(t, cycles=1, phase=0.0):
    return math.sin((t * cycles + phase) * TAU)

def bump(t, centre, width):
    """Single soft pulse, 0 -> 1 -> 0, centred on `centre`."""
    d = abs(t - centre) / width
    return (1 - d * d) ** 2 if d < 1 else 0.0

def window(t, start, end, ramp=.15):
    """Ease in after `start`, hold, ease out before `end`."""
    return ease((t - start) / ramp) * ease((end - t) / ramp)

def stride(phase, stance=.6):
    """One leg of a walk as (position, lift): position runs -1 (reached forward) to +1 (pushed
    back) at constant speed through stance, then eases forward again while lift rises and falls."""
    phase %= 1.0
    if phase < stance: return -1 + 2 * phase / stance, 0.0
    s = (phase - stance) / (1 - stance)
    return 1 - 2 * ease(s), math.sin(math.pi * s) ** .5   # leaves and meets the ground briskly, so it is not near the floor while moving forward

def stride_half(speed, seconds, stance=.6):
    """Half the ground a planted foot covers, for a character moved at `speed` units per second."""
    return speed * stance * seconds / 2


class Pose:
    def __init__(self): self.rot = {}; self.loc = {}; self.scale = {}
    def r(self, bone, x=0.0, y=0.0, z=0.0):
        a = self.rot.setdefault(bone, [0.0, 0.0, 0.0]); a[0] += x; a[1] += y; a[2] += z
    def m(self, bone, x=0.0, y=0.0, z=0.0):
        a = self.loc.setdefault(bone, [0.0, 0.0, 0.0]); a[0] += x; a[1] += y; a[2] += z
    def s(self, bone, axis, value):
        key = (bone, 'xyz'.index(axis)); self.scale[key] = self.scale.get(key, 1.0) * value


class Animator:
    """Bakes pose functions to clips on a Blender armature. `fn(pose, t)` fills a Pose for t in 0..1."""
    def __init__(self, rig, fps=FPS):
        import bpy
        self.bpy = bpy; self.rig = rig; self.rest = {}; self.last = {}; self.clips = []; self.fps = fps
        bpy.context.scene.render.fps = fps
        for pb in rig.pose.bones:
            pb.rotation_mode = 'QUATERNION'; self.rest[pb.name] = pb.bone.matrix_local.to_3x3()
        if not rig.animation_data: rig.animation_data_create()
    def has(self, name): return name in self.rest
    def head(self, name): return self.rig.data.bones[name].head_local.copy()
    def tail(self, name): return self.rig.data.bones[name].tail_local.copy()
    def chain(self, prefix, limit=12):
        """Bones named <prefix>.1, <prefix>.2 ... that exist, or [<prefix>] for a single bone."""
        found = [n for n in (f'{prefix}.{i}' for i in range(1, limit + 1)) if self.has(n)]
        return found or ([prefix] if self.has(prefix) else [])
    def apply(self, pose):
        from mathutils import Euler, Vector
        for pb in self.rig.pose.bones:
            B = self.rest[pb.name]; inverse = B.inverted()
            x, y, z = pose.rot.get(pb.name, (0, 0, 0))
            q = (inverse @ Euler((math.radians(x), math.radians(y), math.radians(z)), 'XYZ').to_matrix() @ B).to_quaternion()
            previous = self.last.get(pb.name)
            if previous is not None and previous.dot(q) < 0: q.negate()   # stay on one hemisphere through full turns
            self.last[pb.name] = q.copy(); pb.rotation_quaternion = q
            pb.location = inverse @ Vector(pose.loc.get(pb.name, (0, 0, 0)))
            scale = [1.0, 1.0, 1.0]
            for (bone, axis), value in pose.scale.items():
                if bone != pb.name: continue
                local = max(range(3), key=lambda i: abs(B[axis][i])); scale[local] *= value   # bone axis nearest that armature axis
            pb.scale = scale
    def clip(self, name, frames, fn, step=1):
        """Key `fn` every `step` frames over `frames` frames (the last frame is always keyed)."""
        action = self.bpy.data.actions.new(name); self.rig.animation_data.action = action; self.last = {}
        for frame in sorted(set(range(0, frames, step)) | {frames}):
            pose = Pose(); fn(pose, frame / frames); self.apply(pose)
            for pb in self.rig.pose.bones:
                for prop in ('rotation_quaternion', 'location', 'scale'): pb.keyframe_insert(prop, frame=frame, group=pb.name)
        track = self.rig.animation_data.nla_tracks.new(); track.name = name; track.strips.new(name, 0, action)
        self.rig.animation_data.action = None; self.clips.append(name)
    def seconds(self, frames): return frames / self.fps
    def rest_pose(self):
        self.last = {}; self.apply(Pose())


# ---------- shared behaviours ----------
def blink(p, t, moments, width=.03, eyes=('Eye.L', 'Eye.R')):
    k = 1.0
    for moment in moments: k = min(k, 1 - .9 * bump(t, moment, width))
    for eye in eyes: p.s(eye, 'z', k)

def tail_wave(p, t, chain, side=4.0, fore=0.0, cycles=1, lag=.12, axis='y', curl=0.0, flick=None, phase=0.0, energy=1.0):
    """One travelling wave for every tail; the settings are the animal's personality.
    side/fore: swing per segment in degrees; lag: how far each segment trails the one before;
    curl: tip curling and uncurling; flick: (moment, degrees) quick twitch of the tip."""
    n = len(chain)
    for i, bone in enumerate(chain):
        grow = .55 + .45 * i / max(1, n - 1)
        p.r(bone, **{axis: side * energy * grow * wave(t, cycles, phase - lag * i)})
        if fore: p.r(bone, x=fore * energy * grow * wave(t, cycles, phase - lag * i + .25))
        if curl: p.r(bone, **{axis: curl * (i / max(1, n - 1)) ** 2 * wave(t, 1, phase + .1)})
    if flick:
        moment, amount = flick
        for back, share in ((1, 1.0), (2, .5)):
            if n >= back: p.r(chain[-back], **{axis: amount * share * bump(t, moment, .09) * math.sin((t - moment) * TAU * 9)})


def limb_geometry(head, tail, pivot, pitch=0.0, lift=0.0, floor=0.0, to_floor=True):
    """Length, rest lean (degrees forward of straight down) and the vertical offset that puts a
    limb's ground contact back on the floor once the body is pitched forward about `pivot` and
    lifted. With to_floor the limb is measured from the head of the bone to the point on the floor
    under its tail (where the foot touches the ground); without it, to the tail of the bone.
    head/tail/pivot are (x, y, z); pure math, used by Stepper."""
    if to_floor: tail = (tail[0], tail[1], min(tail[2], floor) if head[2] > floor else tail[2])
    dy, dz = tail[1] - head[1], tail[2] - head[2]
    length = math.sqrt((tail[0] - head[0]) ** 2 + dy * dy + dz * dz)
    lean = math.degrees(math.atan2(-dy, -dz)); th = math.radians(pitch)
    posed_height = pivot[2] + lift + (head[1] - pivot[1]) * math.sin(th) + (head[2] - pivot[2]) * math.cos(th)
    return length, lean, tail[2] - (posed_height - length)

def planted(length, lean, base, pitch, position, lift, reach, step_height=.07, max_swing=20.0, body_dz=0.0, foot_radius=0.0, flat_feet=True):
    """Rotation (degrees about X) and the (y, z) offset in the pitched body's frame that keep a
    single-bone limb's ground contact on the floor: the limb swings at most `max_swing` either
    side of its rest lean, slides along its own length to stay down, and any stride the swing
    cannot reach is made up by translation.
    position/lift come from stride(); reach is stride_half(). foot_radius: half the length of the
    rigid foot; the limb rises by the amount its toe or heel would otherwise dip as it rolls."""
    # flat_feet: the stride is centred where the foot rests flat (the rest pose) and the limb swings
    # about that angle, so a rigid foot never tips far. Otherwise the limb swings like a pendulum
    # about straight down, which reads as a stride on short plush limbs but tips the foot more.
    centre = -math.radians(lean) if flat_feet else 0.0; want = length * math.tan(centre) + reach * position
    a = max(centre - math.radians(max_swing), min(centre + math.radians(max_swing), math.atan(want / length))); tan_a = math.tan(a)
    extend = length * (1 / math.cos(a) - 1)
    world_y = extend * math.sin(a) + (want - length * tan_a)
    roll = foot_radius * abs(math.sin(a + math.radians(lean)))      # the foot is flat in the rest pose
    world_z = -extend * math.cos(a) + base + roll + step_height * lift - body_dz
    th = math.radians(pitch)
    return lean - pitch + math.degrees(a), world_y * math.cos(th) + world_z * math.sin(th), -world_y * math.sin(th) + world_z * math.cos(th)


class Stepper:
    """Planted feet for limbs made of one bone each (children of a 'Body' bone)."""
    def __init__(self, an, limbs, pitch=0.0, lift=0.0, step_height=.07, max_swing=20.0, foot_radius=.10, flat_feet=True):
        self.pitch = pitch; self.step_height = step_height; self.max_swing = max_swing; self.foot_radius = foot_radius; self.flat_feet = flat_feet; self.fit = {}
        pivot = tuple(an.head('Body')) if an.has('Body') else (0.0, 0.0, 0.0)
        for limb in limbs:
            if an.has(limb): self.fit[limb] = limb_geometry(tuple(an.head(limb)), tuple(an.tail(limb)), pivot, pitch, lift)   # always sized to the ground contact, so the stride matches the speed
    def step(self, p, limb, phase, reach, stance=.6, body_dz=0.0):
        if limb not in self.fit: return
        position, lift = stride(phase, stance); length, lean, base = self.fit[limb]
        angle, y, z = planted(length, lean, base, self.pitch, position, lift, reach, self.step_height, self.max_swing, body_dz, self.foot_radius, self.flat_feet)
        p.r(limb, x=angle); p.m(limb, y=y, z=z)


# ---------- seated plush animals that walk on all fours ----------
SEATED_DEFAULTS = dict(
    pitch=30, lift=.12, roll=3.5, yaw=3.0, walk_frames=18, speed=1.8, stance=.6, bob=.02, step_height=.07, foot_radius=.10, max_swing=26.0, flat_feet=False, tail_back=20,
    breaths=2, look=8, tilt=4, blinks=(.22, .71), blink_width=.03, ear_flicks=(),
    greet='wave', greet_arms='LR', raise_out=118, raise_fwd=18, waves=3, wave_amp=11, hop=0.0, greet_tilt=0,
    idle_frames=150, greet_frames=66, idle_extra=None,
    # (limb, phase, share of the full stride).
    limbs=(('Arm.L', 0.0, 1.0), ('Foot.R', .05, 1.0), ('Arm.R', .5, 1.0), ('Foot.L', .55, 1.0)))

def seated_clips(an, style, tail=None):
    """Idle, Walk and Greet for a seated animal with Body, Head, Arm.L/R, Foot.L/R and optional
    Eye.*, Ear.* and Tail(.n) bones.

    style overrides SEATED_DEFAULTS: pitch/lift (how far it drops onto all fours), speed (the speed
    the game moves it at; the stride follows), flat_feet (False: limbs swing like pendulums), roll/yaw/bob, breathing and blink timing, ear flicks,
    greet ('wave' or 'beckon') and which arms. idle_extra(pose, t) adds a species gesture.
    tail: tail_wave settings. Returns the clip names."""
    s = {**SEATED_DEFAULTS, **style}; tail = tail or dict(side=3.0); chain = an.chain('Tail')
    stepper = Stepper(an, [limb[0] for limb in s['limbs']], s['pitch'], s['lift'], s['step_height'], s['max_swing'], s['foot_radius'], s['flat_feet'])
    reach = stride_half(s['speed'], an.seconds(s['walk_frames']), s['stance'])

    def idle(p, t):
        breath = wave(t, s['breaths'])
        p.m('Body', z=.011 * breath); p.r('Body', x=.7 * breath)
        p.r('Head', z=s['look'] * wave(t, 1), y=s['tilt'] * wave(t, 1, .2), x=1.5 * wave(t, 2, .1))
        blink(p, t, s['blinks'], s['blink_width'])
        for moment, side in s['ear_flicks']:
            sign = 1 if side == 'R' else -1; k = bump(t, moment, .035)
            p.r('Ear.' + side, y=sign * 16 * k, x=9 * k)
        for side in 'LR': p.r('Arm.' + side, x=1.1 * breath)
        if s['idle_extra']: s['idle_extra'](p, t)
        tail_wave(p, t, chain, **tail)

    def walk(p, t):
        th = s['pitch']; bob = wave(t, 2); dz = s['bob'] * bob
        p.r('Body', x=th, y=s['roll'] * wave(t, 1), z=s['yaw'] * wave(t, 1, .25))
        p.m('Body', z=s['lift'] + dz, y=.6 * math.sin(math.radians(th)))   # keep the mass over the root
        p.r('Head', x=-th * .9 + 2.0 * wave(t, 2, .15), z=-s['yaw'] * wave(t, 1, .25), y=-s['roll'] * .7 * wave(t, 1))
        blink(p, t, (.5,), s['blink_width'] + .01)
        for limb, phase, share in s['limbs']: stepper.step(p, limb, t + phase, reach * share, s['stance'], dz)
        for side in 'LR': p.r('Ear.' + side, x=3 * bob)
        if chain:
            p.r(chain[0], x=-(th + s['tail_back']))
            tail_wave(p, t, chain, **{**tail, 'cycles': 1, 'flick': None}, energy=1.6)

    def greet(p, t):
        k = window(t, .08, .92, .16); beat = wave(t, s['waves'])
        for side in s['greet_arms']:
            sign = 1 if side == 'R' else -1
            if s['greet'] == 'beckon':   # the paw dips forward and back
                p.r('Arm.' + side, x=-s['raise_fwd'] * k + s['wave_amp'] * k * beat, y=-sign * s['raise_out'] * k)
            else:                        # arms up and waving
                p.r('Arm.' + side, x=-s['raise_fwd'] * k, y=-sign * (s['raise_out'] + s['wave_amp'] * beat) * k)
        p.m('Body', z=s['hop'] * k * abs(wave(t, s['waves'] / 2)))
        p.r('Body', x=-4 * k); p.r('Head', x=-7 * k, y=s['greet_tilt'] * k + 3 * k * beat)
        blink(p, t, (.5,), s['blink_width'] + .005)
        for side in 'LR': p.r('Ear.' + side, y=(1 if side == 'R' else -1) * 8 * k * max(0, beat))
        tail_wave(p, t, chain, **{**tail, 'flick': None}, energy=1 + 1.2 * k)

    an.clip('Idle', s['idle_frames'], idle, 2); an.clip('Walk', s['walk_frames'], walk); an.clip('Greet', s['greet_frames'], greet, 2)
    return ['Idle', 'Walk', 'Greet']


def quadruped_legs(p, t, stepper, reach, phases, stance=.6, body_dz=0.0):
    """Drive a standing quadruped's legs. phases: ((limb, phase), ...): a trot pairs diagonals at
    0 and .5; a four-beat walk steps 0, .25, .5, .75."""
    for limb, phase in phases: stepper.step(p, limb, t + phase, reach, stance, body_dz)
