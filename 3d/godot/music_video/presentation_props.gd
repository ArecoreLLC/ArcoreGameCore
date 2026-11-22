extends RefCounted
## Lightweight engine-rendered typography and musical prop helpers; no game assets.
static func title(parent: Node3D, font: Font, text: String, width: float, color: Color) -> Node3D:
    var root=Node3D.new();parent.add_child(root)
    var face=MeshInstance3D.new();var mesh=TextMesh.new();mesh.font=font;mesh.font_size=128;mesh.pixel_size=.01;mesh.depth=.10;mesh.text=text
    mesh.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;mesh.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
    face.mesh=mesh
    var mat=StandardMaterial3D.new();mat.albedo_color=color;mat.roughness=.36;mat.metallic=.12;mat.emission_enabled=true;mat.emission=color;mat.emission_energy_multiplier=.12
    face.material_override=mat;root.add_child(face)
    var ratio=width/maxf(mesh.get_aabb().size.x,.01);root.scale=Vector3.ONE*ratio
    var back=MeshInstance3D.new();back.mesh=mesh;back.position=Vector3(.018,-.024,-.09)
    var edge=StandardMaterial3D.new();edge.albedo_color=Color("6a4ca0");edge.roughness=.45;back.material_override=edge;root.add_child(back)
    return root
static func trumpet(parent: Node3D) -> Node3D:
    var root=Node3D.new();parent.add_child(root)
    var gold=StandardMaterial3D.new();gold.albedo_color=Color("f6c65d");gold.metallic=.65;gold.roughness=.3
    # A hollow flared bell along +Z, with rounded lip and three valve buttons.
    var profile=[Vector2(.055,0),Vector2(.065,.32),Vector2(.11,.58),Vector2(.24,.82),Vector2(.27,.88),Vector2(.245,.88),Vector2(.215,.82),Vector2(.085,.58),Vector2(.04,.32),Vector2(.035,0)]
    var surface=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
    for row in range(profile.size()-1):
        for i in range(32):
            var a=TAU*i/32;var b=TAU*(i+1)/32;var p: Vector2=profile[row];var q: Vector2=profile[row+1]
            for v in [Vector3(cos(a)*p.x,sin(a)*p.x,p.y),Vector3(cos(b)*p.x,sin(b)*p.x,p.y),Vector3(cos(a)*q.x,sin(a)*q.x,q.y),Vector3(cos(b)*p.x,sin(b)*p.x,p.y),Vector3(cos(b)*q.x,sin(b)*q.x,q.y),Vector3(cos(a)*q.x,sin(a)*q.x,q.y)]:surface.add_vertex(v)
    surface.generate_normals();var bell=MeshInstance3D.new();bell.mesh=surface.commit();bell.material_override=gold;root.add_child(bell)
    for i in range(3):
        var valve=MeshInstance3D.new();var stem=CylinderMesh.new();stem.top_radius=.035;stem.bottom_radius=.035;stem.height=.16;valve.mesh=stem;valve.position=Vector3(0,.12,.2+i*.12);valve.material_override=gold;root.add_child(valve)
        var button=MeshInstance3D.new();var disk=CylinderMesh.new();disk.top_radius=.065;disk.bottom_radius=.065;disk.height=.025;button.mesh=disk;button.position=valve.position+Vector3(0,.08,0);button.material_override=gold;root.add_child(button)
    var loop=MeshInstance3D.new();var ring=TorusMesh.new();ring.inner_radius=.12;ring.outer_radius=.18;loop.mesh=ring;loop.rotation.x=PI/2;loop.position=Vector3(0,-.12,.28);loop.material_override=gold;root.add_child(loop)
    return root

static func tube(parent: Node3D, points: Array, radius: float, mat: Material) -> void:
    var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
    var rings: Array=[]
    for i in range(points.size()):
        var tangent: Vector3=(points[mini(i+1,points.size()-1)]-points[maxi(0,i-1)]).normalized()
        var axis=Vector3.FORWARD if absf(tangent.dot(Vector3.FORWARD))<.9 else Vector3.UP
        var side=tangent.cross(axis).normalized();var up=tangent.cross(side).normalized();var ring: Array=[]
        for j in range(16):ring.append(points[i]+radius*(side*cos(TAU*j/16)+up*sin(TAU*j/16)))
        rings.append(ring)
    for i in range(rings.size()-1):
        for j in range(16):
            var k=(j+1)%16
            for v in [rings[i][j],rings[i][k],rings[i+1][j],rings[i][k],rings[i+1][k],rings[i+1][j]]:st.add_vertex(v)
    st.generate_normals();var mesh=MeshInstance3D.new();mesh.mesh=st.commit();mesh.material_override=mat;parent.add_child(mesh)
static func arc_points(center: Vector3, radius: float, start: float, end: float) -> Array:
    var points: Array=[]
    for i in range(25):
        var a=lerpf(start,end,float(i)/24);points.append(center+Vector3(cos(a)*radius,sin(a)*radius,0))
    return points
static func baritone(parent: Node3D) -> Node3D:
    var root=Node3D.new();parent.add_child(root)
    var brass=StandardMaterial3D.new();brass.albedo_color=Color("f4c966");brass.metallic=.72;brass.roughness=.27;brass.cull_mode=BaseMaterial3D.CULL_DISABLED
    var silver=StandardMaterial3D.new();silver.albedo_color=Color("dae1e1");silver.metallic=.8;silver.roughness=.3;silver.cull_mode=BaseMaterial3D.CULL_DISABLED
    # Upright oval baritone: wide lower bow, parallel return tube and upward flared bell.
    var body: Array=[Vector3(-.48,.45,.25),Vector3(-.48,-1.0,.25)]
    body.append_array(arc_points(Vector3(0,-1.0,.25),.48,PI,TAU))
    body.append_array([Vector3(.48,-.2,.25),Vector3(.42,.45,.25)])
    tube(root,body,.095,brass)
    tube(root,[Vector3(.42,.45,.25),Vector3(.42,.6,.25),Vector3(.40,.75,.25)],.11,brass)
    var profile=[Vector2(.105,0),Vector2(.13,.25),Vector2(.20,.50),Vector2(.39,.75),Vector2(.46,.83),Vector2(.43,.83),Vector2(.36,.75),Vector2(.17,.50),Vector2(.10,.25),Vector2(.08,0)]
    var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
    for row in range(profile.size()-1):
        for i in range(48):
            var a=TAU*i/48;var b=TAU*(i+1)/48;var p: Vector2=profile[row];var q: Vector2=profile[row+1]
            for v in [Vector3(cos(a)*p.x,p.y,sin(a)*p.x),Vector3(cos(b)*p.x,p.y,sin(b)*p.x),Vector3(cos(a)*q.x,q.y,sin(a)*q.x),Vector3(cos(b)*p.x,p.y,sin(b)*p.x),Vector3(cos(b)*q.x,q.y,sin(b)*q.x),Vector3(cos(a)*q.x,q.y,sin(a)*q.x)]:st.add_vertex(v)
    st.generate_normals();var bell=MeshInstance3D.new();bell.mesh=st.commit();bell.position=Vector3(.4,.70,.25);bell.rotation.z=-.12;bell.material_override=brass;root.add_child(bell)
    # Mouthpiece and leadpipe reach back toward the player's mouth.
    tube(root,[Vector3(0,0,-.15),Vector3(-.18,0,-.05),Vector3(-.48,-.05,.1),Vector3(-.55,-.2,.3),Vector3(-.3,-.3,.38)],.045,brass)
    tube(root,[Vector3(0,0,-.22),Vector3(0,0,-.12)],.075,silver)
    for i in range(3):
        var x=-.23+float(i)*.2
        tube(root,[Vector3(x,-.9,.40),Vector3(x,-.28,.40)],.055,silver)
        tube(root,[Vector3(x,-.28,.40),Vector3(x,-.11,.40)],.022,silver)
        var button=MeshInstance3D.new();var disk=CylinderMesh.new();disk.height=.035;disk.top_radius=.07;disk.bottom_radius=.07;button.mesh=disk;button.position=Vector3(x,-.1,.4);button.material_override=silver;root.add_child(button)
        var slide: Array=[Vector3(x,-.43,.45),Vector3(x+.08,-.43,.57),Vector3(x+.08,-1.03,.57)]
        slide.append_array(arc_points(Vector3(x,-1.03,.57),.08,0,-PI))
        slide.append(Vector3(x-.08,-.6,.57));tube(root,slide,.028,brass)
    root.scale=Vector3.ONE*1.1
    return root
