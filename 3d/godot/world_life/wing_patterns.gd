extends RefCounted
## Parametric wing materials. Species text, palettes and models belong to the consumer.
const VERSION := "1.0.0"
const SHADER := """shader_type spatial;
render_mode cull_disabled, depth_draw_always;
uniform vec4 base:source_color;
uniform vec4 edge:source_color;
uniform vec4 spot:source_color;
uniform int pattern=0;
uniform vec3 center;
uniform vec3 half_size=vec3(1.0);
uniform ivec2 axes=ivec2(0,2);
varying vec3 lp;
void vertex(){lp=VERTEX;}
void fragment(){
    vec3 n=(lp-center)/max(half_size,vec3(1e-4));
    vec2 q=vec2(n[axes.x],n[axes.y]);
    float r=length(q);
    vec4 c=base;
    float border=smoothstep(0.72,0.86,r);
    if(pattern==0){
        c=mix(base,edge,border);
        float a=atan(q.y,q.x);
        float dots=step(0.62,fract(a*1.6))*step(0.87,r)*step(r,0.97);
        c=mix(c,spot,dots);
        c=mix(c,edge,smoothstep(0.035,0.0,abs(fract(a*0.95)-0.5)-0.46)*step(r,0.8)*0.8);
    } else if(pattern==1){
        float stripe=step(0.58,fract(q.x*2.6+q.y*0.4));
        c=mix(base,edge,max(stripe,border));
        c=mix(c,spot,step(0.88,r)*step(r,0.95)*step(0.5,fract(atan(q.y,q.x)*1.2)));
    } else if(pattern==2){
        c=mix(base,edge,border);
        float d=length(q-vec2(0.38,0.32));
        c=mix(c,vec4(0.05,0.04,0.06,1.0),step(d,0.24));
        c=mix(c,spot,step(d,0.17));
        c=mix(c,vec4(1.0,0.95,0.6,1.0),step(d,0.08));
    } else if(pattern==3){
        c=mix(base,edge,border);
        c=mix(c,spot,step(0.9,r)*step(0.6,fract(atan(q.y,q.x)*1.4)));
    } else {
        float band=smoothstep(0.4,0.45,r)*(1.0-smoothstep(0.62,0.67,r));
        c=mix(base,spot,band);
        c=mix(c,edge,border*0.7);
        c=mix(c,vec4(1.0),step(0.9,r)*step(0.7,fract(atan(q.y,q.x)*1.3)));
    }
    ALBEDO=c.rgb;ALPHA=c.a;ROUGHNESS=0.55;
    if(pattern==1 && base.r>0.5){SPECULAR=0.4;}
}"""
static var shader_cache: Shader

static func read_catalog(path: String) -> Array[Dictionary]:
    var result: Array[Dictionary]=[]
    var text := FileAccess.get_file_as_string(path)
    var data: Variant=JSON.parse_string(text)
    if not data is Dictionary or data.get("schema")!="gamecore.wing-species.v1" or not data.get("species") is Array:
        push_error("Invalid wing species catalog: "+path);return result
    for entry in data.species:
        if not entry is Dictionary or not entry.get("name") is String or not entry.get("from") is String:
            push_error("Species needs name and from text");return []
        var pattern: Variant=entry.get("pattern")
        if not (pattern is int or pattern is float) or not is_finite(float(pattern)) or float(pattern)!=floor(float(pattern)) or pattern<0 or pattern>4:
            push_error("Wing pattern must be 0..4");return []
        var converted: Dictionary=entry.duplicate(true)
        for key in ["base","edge","spot"]:
            var value: Variant=entry.get(key)
            if value is String and Color.html_is_valid(value):converted[key]=Color(value)
            elif value is Array and value.size()==4:
                for channel in value:
                    if not (channel is float or channel is int) or not is_finite(float(channel)) or channel<0 or channel>1:
                        push_error("RGBA channels must be finite 0..1");return []
                converted[key]=Color(value[0],value[1],value[2],value[3])
            else:
                push_error("Color must be hex or four RGBA channels");return []
        result.append(converted)
    return result

static func paint(butterfly: Node3D, sp: Dictionary, body_color := Color("2a2320")) -> void:
    if shader_cache==null:shader_cache=Shader.new();shader_cache.code=SHADER
    for side in ["WingL","WingR"]:
        var wing := butterfly.find_child(side,true,false)
        if wing==null:continue
        var meshes: Array=[wing] if wing is MeshInstance3D else wing.find_children("*","MeshInstance3D",true,false)
        for mi in meshes:
            var box: AABB=(mi as MeshInstance3D).mesh.get_aabb()
            var size := box.size
            var order := [0,1,2]
            order.sort_custom(func(x,y):return size[x]>size[y])
            var m := ShaderMaterial.new();m.shader=shader_cache
            m.set_shader_parameter("base",sp.base);m.set_shader_parameter("edge",sp.edge);m.set_shader_parameter("spot",sp.spot)
            m.set_shader_parameter("pattern",int(sp.pattern));m.set_shader_parameter("center",box.get_center())
            m.set_shader_parameter("half_size",size*.5);m.set_shader_parameter("axes",Vector2i(order[0],order[1]))
            (mi as MeshInstance3D).material_override=m
    var body := butterfly.find_child("Body",true,false)
    if body is MeshInstance3D:
        var bm := StandardMaterial3D.new();bm.albedo_color=body_color;bm.roughness=.7;(body as MeshInstance3D).material_override=bm

