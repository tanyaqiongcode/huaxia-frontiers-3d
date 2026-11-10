# 《边缘行走》人物构建（参数化单角色）：骨骼+蒙皮+民族志服饰+idle/walk/run 三动画 → GLB
# 用法：blender --background --factory-startup --python npc_figure.py -- <variant>
import bpy, math, os, sys

VARIANT = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "fig_player"
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models"))
os.makedirs(OUT, exist_ok=True)
FPS = 24.0

bpy.ops.wm.read_factory_settings(use_empty=True)

# ── 材质（民族志配色） ──
def mat(name, rgb, rough=0.88):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = 0.0
    return m
M = {
 "skin":  mat("skin",  (0.78, 0.62, 0.50)),
 "jade":  mat("jade",  (0.20, 0.25, 0.33)),
 "indigo":mat("indigo",(0.22, 0.26, 0.34)),
 "grey":  mat("grey",  (0.40, 0.40, 0.42)),
 "khaki": mat("khaki", (0.45, 0.41, 0.32)),
 "wool":  mat("wool",  (0.45, 0.33, 0.24)),
 "felt":  mat("felt",  (0.18, 0.20, 0.24)),
 "shoe":  mat("shoe",  (0.16, 0.14, 0.13)),
 "dark":  mat("dark",  (0.10, 0.10, 0.12)),
 "red":   mat("red",   (0.64, 0.23, 0.18)),
 "boot":  mat("boot",  (0.17, 0.15, 0.13)),
 "white": mat("white", (0.80, 0.77, 0.70)),
 "hairM": mat("hairM", (0.09, 0.08, 0.09)),
}
m_grey_hair = mat("greyhair", (0.45, 0.45, 0.47))

# ── 变体配置 ──
V = {
 "fig_player":  dict(jacket="khaki", trouser="khaki", hairM="hairM", hat="brim", hatM="khaki",
                     pack=True, scarf=True, yunyun=False),
 "fig_elder":   dict(jacket="jade", trouser="indigo", hairM="hairM", hat="wrap", hatM="felt",
                     robe=True, robeM="jade", robeLen=1.05, vest=True, yunyun=True, legwrap=True, staff=True),
 "fig_arch":    dict(jacket="khaki", trouser="grey", hairM="hairM", hat="brim", hatM="khaki", pack=True),
 "fig_soldier": dict(jacket="grey", trouser="indigo", hairM="hairM", hat="wrap", hatM="felt",
                     legwrap=True, yunyun=True),
 "fig_youth":   dict(jacket="indigo", trouser="dark", hairM="hairM", vest=True),
 "fig_aunt":    dict(jacket="indigo", trouser="dark", hairM="hairM", hat="wrap", hatM="white",
                     apron=True, robe=True, robeM="indigo", robeLen=0.92, yunyun=True),
}[VARIANT]

def mesh_ob(name, verts, faces, material, groups):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    for gname, idxs in groups.items():
        vg = ob.vertex_groups.new(name=gname)
        vg.add(idxs, 1.0, 'REPLACE')
    return ob

def cyl(rtop, rbot, h, y0, seg=12, xz=1.0):
    vs, fs = [], []
    for i in range(seg):
        a = 2*math.pi*i/seg
        vs.append((math.sin(a)*rtop*xz, 0, y0+h))
    for i in range(seg):
        a = 2*math.pi*i/seg
        vs.append((math.sin(a)*rbot*xz, 0, y0))
    fs += [[i, (i+1)%seg, seg+(i+1)%seg, seg+i] for i in range(seg)]
    fs.append(list(range(seg)))
    fs.append([seg+seg-1-i for i in range(seg)])
    return vs, fs

def sph(r, x, y, z, seg=10, ring=8, sy=1.0):
    vs, fs = [], []
    for j in range(ring+1):
        ph = math.pi*j/ring
        for i in range(seg):
            th = 2*math.pi*i/seg
            vs.append((x+math.sin(ph)*math.cos(th)*r, z+math.sin(ph)*math.sin(th)*r*0.92, y+math.cos(ph)*r*sy))
    for j in range(ring):
        for i in range(seg):
            a=j*seg+i; b=j*seg+(i+1)%seg; c=(j+1)*seg+(i+1)%seg; d=(j+1)*seg+i
            if j==0: fs.append([a,b,c])
            elif j==ring-1: fs.append([a,b,d])
            else: fs.append([a,b,c,d])
    return vs, fs

# ── 骨架 ──
arm_data = bpy.data.armatures.new("Armature")
arm = bpy.data.objects.new("Armature", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
e = arm_data.edit_bones
def B(name, h, t, parent=None):
    b = e.new(name); b.head = h; b.tail = t
    if parent: b.parent = e[parent]
    return b
B("root",  (0,0,0),    (0,0,0.06))
B("hips",  (0,0,0.86), (0,0,0.98), "root")
B("spine", (0,0,0.98), (0,0,1.18), "hips")
B("chest", (0,0,1.18), (0,0,1.36), "spine")
B("neck",  (0,0,1.36), (0,0,1.45), "chest")
B("head",  (0,0,1.45), (0,0,1.62), "neck")
for sd, N in ((-1,"L"), (1,"R")):
    x = 0.175*sd
    B(f"upArm{N}",   (x,0,1.33), (x,0,1.04), "chest")
    B(f"foreArm{N}", (x,0,1.04), (x,0,0.76), f"upArm{N}")
    B(f"hand{N}",    (x,0,0.76), (x,0,0.68), f"foreArm{N}")
    x2 = 0.095*sd
    B(f"thigh{N}", (x2,0,0.84), (x2,0,0.44), "hips")
    B(f"shin{N}",  (x2,0,0.44), (x2,0,0.07), f"thigh{N}")
    B(f"foot{N}",  (x2,0,0.07), (x2,0.14,0.02), f"shin{N}")
bpy.ops.object.mode_set(mode='OBJECT')

# ── 网格拼装（顶点组→骨名） ──
vs_all, fs_all, grp = [], [], {}
def add(verts, faces, gname, mo):
    base = len(vs_all)
    vs_all.extend(verts)
    for f in faces: fs_all.append([i+base for i in f])
    grp.setdefault(gname, []).extend(range(base, base+len(verts)))
def part_cyl(rtop, rbot, h, y0, gname, mo, seg=12, xz=1.0):
    v, f = cyl(rtop, rbot, h, y0, seg, xz); add(v, f, gname, mo)
def part_sph(r, x, y, z, gname, mo, sy=1.0, seg=10, ring=8):
    v, f = sph(r, x, y, z, seg, ring, sy); add(v, f, gname, mo)

part_cyl(0.168, 0.152, 0.24, 1.12, "chest", M[V["jacket"]], 12, 0.62)
part_cyl(0.152, 0.15, 0.20, 0.92, "spine", M[V["jacket"]], 12, 0.66)
part_cyl(0.152, 0.15, 0.10, 0.84, "hips", M[V["trouser"]], 12, 0.66)
part_cyl(0.05, 0.056, 0.1, 1.40, "neck", M["skin"], 8)
part_sph(0.118, 0, 1.585, 0, "head", M["skin"], 1.05)
part_sph(0.02, -0.045, 1.60, 0.093, "head", M["dark"], 1.0, 6, 5)
part_sph(0.02, 0.045, 1.60, 0.093, "head", M["dark"], 1.0, 6, 5)
add([(0,1.573,0.114),(-0.015,1.573,0.094),(0.015,1.573,0.094),(0,1.598,0.112)], [[0,1,2],[0,2,3]], "head", M["skin"])
add([(-0.032,1.626,0.094),(0.032,1.626,0.094)], [[0,1]], "head", M["dark"])
part_sph(0.126, 0, 1.602, 0, "head", M[V["hairM"]], 0.72, 12, 6)
if V.get("hat")=="brim":
    part_cyl(0.118, 0.13, 0.1, 1.655, "head", M[V["hatM"]], 12)
    part_cyl(0.208, 0.213, 0.02, 1.645, "head", M[V["hatM"]], 14)
if V.get("hat")=="wrap":
    part_cyl(0.132, 0.14, 0.135, 1.595, "head", M[V["hatM"]], 12)
if V.get("scarf"): part_cyl(0.098, 0.098, 0.09, 1.30, "chest", M["red"], 8)
for sd, N in ((-1,"L"),(1,"R")):
    x = 0.19*sd
    part_cyl(0.052, 0.048, 0.3, 1.03, f"upArm{N}", M[V["jacket"]], 8)
    part_cyl(0.045, 0.042, 0.26, 0.79, f"foreArm{N}", M["skin"], 8)
    part_sph(0.05, x, 0.71, 0, f"hand{N}", M["skin"], 0.9, 8, 6)
    x2 = 0.095*sd
    part_cyl(0.063, 0.056, 0.42, 0.42, f"thigh{N}", M[V["trouser"]], 10)
    part_cyl(0.052, 0.046, 0.36, 0.08, f"shin{N}", M[V["trouser"]], 10)
    if V.get("legwrap"): part_cyl(0.058, 0.052, 0.25, 0.10, f"shin{N}", M["felt"], 10)
    if V.get("yunyun"): part_cyl(0.056, 0.062, 0.09, 0.012, f"foot{N}", M["shoe"], 10, 0.62)
    else: part_cyl(0.05, 0.057, 0.08, 0.015, f"foot{N}", M["boot"], 10, 0.66)
if V.get("robe"):
    L = V["robeLen"]
    part_cyl(0.175, 0.27, L, 0.98-L, "spine", M[V["robeM"]], 12, 0.88)
    part_cyl(0.27, 0.28, 0.05, 0.93-L, "spine", M[V["robeM"]], 12, 0.88)
if V.get("vest"): part_cyl(0.188, 0.178, 0.3, 1.0, "chest", M["wool"], 12, 0.72)
if V.get("apron"): part_cyl(0.165, 0.19, 0.34, 0.5, "spine", M["red"], 12, 0.6)
if V.get("pack"): part_cyl(0.14, 0.152, 0.36, 0.92, "chest", M["boot"], 10, 0.72)

body_ob = mesh_ob(VARIANT, vs_all, fs_all, M["skin"], grp)
mod = body_ob.modifiers.new("Arm", type='ARMATURE'); mod.object = arm
body_ob.parent = arm

# ── 动画（Idle/Walk/Run，循环） ──
arm.pose.bones["root"].rotation_mode = 'XYZ'
for pb in arm.pose.bones: pb.rotation_mode = 'XYZ'
def act(name, nframes, fn):
    a = bpy.data.actions.new(name)
    arm.animation_data_create(); arm.animation_data.action = a
    a.frame_start = 1; a.frame_end = nframes
    # 末帧复制首帧（u=1）实现无缝循环；Blender5 无 fcurves/CYCLES
    for f in range(1, nframes+2):
        u = min(1.0, (f-1)/nframes)
        r = fn(u)
        for bn, (rx, ry, rz) in r.items():
            pb = arm.pose.bones.get(bn)
            if not pb: continue
            pb.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
            pb.keyframe_insert("rotation_euler", frame=f)
    return a
A_IDLE = act("Idle", 72, lambda u: {
    "spine": (2.2*math.sin(u*6.283), 0, 0),
    "chest": (1.4*math.sin(u*6.283+0.6), 3.0*math.sin(u*3.142), 0),
    "head": (0, 5.0*math.sin(u*3.142+1.2), 0),
    "upArmL": (1.5*math.sin(u*6.283), 0, 3.5),
    "upArmR": (1.5*math.sin(u*6.283+0.4), 0, -3.5)})
A_WALK = act("Walk", 32, lambda u: {
    "thighL": (26*math.sin(u*6.283), 0, 0),
    "thighR": (-26*math.sin(u*6.283), 0, 0),
    "shinL": (-30*max(0.0, math.sin(u*6.283-0.9)), 0, 0),
    "shinR": (-30*max(0.0, math.sin(u*6.283+2.24)), 0, 0),
    "upArmL": (-16*math.sin(u*6.283), 0, 4),
    "upArmR": (16*math.sin(u*6.283), 0, -4),
    "foreArmL": (-16, 0, 0), "foreArmR": (-16, 0, 0),
    "hips": (0, 4.5*math.sin(u*6.283), 0),
    "chest": (2.5, -4.5*math.sin(u*6.283), 0),
    "head": (0, 2*math.sin(u*6.283), 0)})
A_RUN = act("Run", 20, lambda u: {
    "thighL": (44*math.sin(u*6.283), 0, 0),
    "thighR": (-44*math.sin(u*6.283), 0, 0),
    "shinL": (-55*max(0.0, math.sin(u*6.283-0.8)), 0, 0),
    "shinR": (-55*max(0.0, math.sin(u*6.283+2.14)), 0, 0),
    "upArmL": (-30*math.sin(u*6.283), 0, 6),
    "upArmR": (30*math.sin(u*6.283), 0, -6),
    "foreArmL": (-55, 0, 0), "foreArmR": (-55, 0, 0),
    "hips": (0, 7*math.sin(u*6.283), 0),
    "chest": (7, -7*math.sin(u*6.283), 0)})

# 手杖（elder）：细柱挂在 handR 骨上
if V.get("staff"):
    svs = [(math.sin(2*math.pi*i/8)*0.022, 0, 0.02 - i*0.1875) for i in range(9)]
    sfs = [[i, (i+1)%8] for i in range(8)]
    stick = mesh_ob(VARIANT+"_stick", svs, sfs, M["boot"], {"handR": list(range(9))})
    stick.parent = arm; stick.parent_type = 'BONE'; stick.parent_bone = 'handR'

# ── 导出 ──
bpy.context.view_layer.objects.active = arm
arm.select_set(True); body_ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, VARIANT+".glb"), export_format='GLB',
    export_animations=True, export_skins=True, export_morph=False, export_yup=True)
print("EXPORTED", VARIANT, "->", os.path.join(OUT, VARIANT+".glb"))
