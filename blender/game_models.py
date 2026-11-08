"""边缘行走 · 游戏模型（碉楼、羌寨石屋）——Blender 脚本生成，导出 GLB 供 three.js 加载。

用法（在仓库根目录）：
    blender --background --factory-startup --python blender/game_models.py

输出：assets/models/ 下的碉楼、羌寨石屋、汉长城墙段、烽燧、河湟遗址、三种树、绵羊、黄牛、马（*.glb）
材质只给名字和底色（stone / earth / wood / dark / white），贴图由游戏里已有的石、土、木纹理替换，
所以 GLB 很小、不含图片。坐标：Blender Z 向上，导出为 glTF 的 Y 向上；底面在原点高度 0。

造型依据：岷江上游羌族石砌碉楼（多角收分、小窗、木梁层带）与平顶石屋（退台、女儿墙、屋顶白石）。
"""
import math
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "models")
os.makedirs(OUT, exist_ok=True)

COLORS = {
    "stone": (0.74, 0.72, 0.67, 1),
    "earth": (0.81, 0.77, 0.66, 1),
    "wood": (0.45, 0.33, 0.22, 1),
    "dark": (0.09, 0.08, 0.07, 1),
    "white": (0.95, 0.94, 0.90, 1),
    "reed": (0.62, 0.53, 0.36, 1),      # 汉长城夯层间的芦苇、红柳层
    "loess": (0.66, 0.55, 0.38, 1),     # 河湟黄土
    "pottery": (0.72, 0.42, 0.25, 1),   # 齐家文化红陶
    "paint": (0.12, 0.09, 0.07, 1),     # 彩陶黑彩
    "needle": (0.16, 0.26, 0.19, 1),    # 冷杉针叶
    "leaf": (0.42, 0.55, 0.30, 1),      # 白杨叶
    "leaf2": (0.27, 0.42, 0.24, 1),     # 核桃等阔叶
    "bark": (0.30, 0.22, 0.16, 1),
    "bark_w": (0.78, 0.76, 0.70, 1),    # 白杨树皮
    "wool": (0.90, 0.88, 0.82, 1),
    "hide": (0.52, 0.34, 0.20, 1),      # 黄牛
    "horse": (0.36, 0.24, 0.16, 1),
    "gravel": (0.55, 0.52, 0.46, 1),
    "leafcard": (0.45, 0.58, 0.32, 1),  # 阔叶叶片卡（游戏里换成带透明的叶片贴图）
    "needlecard": (0.20, 0.32, 0.22, 1),  # 冷杉枝叶卡
}
CARD_MATS = {"leafcard", "needlecard"}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.diffuse_color = COLORS[name]
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = COLORS[name]
        bsdf.inputs["Roughness"].default_value = 0.95
    return m


def finish(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(mat(material))
    return obj


def box(sx, sy, sz, x=0, y=0, z=0, material="stone", rz=0):
    """中心在 (x, y)，底面在 z 的长方体。"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + sz / 2))
    o = bpy.context.active_object
    o.scale = (sx, sy, sz)
    o.rotation_euler[2] = rz
    return finish(o, material)


def prism(sides, r_bottom, r_top, h, z=0, material="stone", x=0, y=0):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r_bottom, radius2=r_top, depth=h, location=(x, y, z + h / 2))
    return finish(bpy.context.active_object, material)


def stone_ball(r, x, y, z):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x, y, z + r * 0.8))
    o = bpy.context.active_object
    o.scale = (1.0, 0.85, 0.75)
    return finish(o, "white")


def _modifier(o, kind, **kw):
    m = o.modifiers.new(kind.lower(), kind)
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)


def _soften(objs, organic):
    """硬质构件倒小圆角（边缘能接住光）；牲畜等有机体做细分圆滑；叶片卡不动。"""
    for o in objs:
        mats = {m.name.split(".")[0] for m in o.data.materials if m}
        if mats & CARD_MATS:
            continue
        if organic:
            _modifier(o, "SUBSURF", levels=1, render_levels=1)
        else:
            d = min(x for x in o.dimensions if x > 1e-4)
            _modifier(o, "BEVEL", width=min(0.045, d * 0.18), segments=2 if d > 0.25 else 1, limit_method="ANGLE",
                      angle_limit=math.radians(35), harden_normals=False)


def _bake_ao(o, distance):
    """用 Cycles 把环境光遮蔽烘焙进顶点色（墙角、接地处、树冠内部自然变暗），运行时零开销。"""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.light_settings.distance = distance
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.005))   # 地面：让底部也有接地暗影（不导出）
    ground = bpy.context.active_object
    ca = o.data.color_attributes.new("AO", "BYTE_COLOR", "POINT")
    o.data.color_attributes.active_color = ca
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    sc.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="AO")
    bpy.data.objects.remove(ground, do_unlink=True)


def bake_and_export(name, organic=False, ao=0.9):
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    # 位置也一起应用：合并后原点就是世界原点，模型底面正好在高度 0
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    _soften(objs, organic)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    # 按世界尺度做立方投影 UV，石纹在各个面上大小一致（叶片卡另行展开为整张 0..1）
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=2.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    _card_uvs(o)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        bpy.ops.object.shade_smooth()
    _bake_ao(o, ao)
    path = os.path.join(OUT, name + ".glb")
    opts = dict(filepath=path, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                export_normals=True, export_texcoords=True, export_materials="EXPORT")
    try:
        bpy.ops.export_scene.gltf(**opts, export_vertex_color="ACTIVE")
    except TypeError:
        bpy.ops.export_scene.gltf(**opts, export_colors=True)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("exported", path, os.path.getsize(path), "bytes,", tris, "triangles")


def _card_uvs(o):
    """叶片卡（四边形）各自铺满整张贴图。"""
    uv = o.data.uv_layers.active.data
    idx = {i for i, m in enumerate(o.data.materials) if m and m.name.split(".")[0] in CARD_MATS}
    corners = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for p in o.data.polygons:
        if p.material_index in idx and len(p.loop_indices) == 4:
            for k, li in enumerate(p.loop_indices):
                uv[li].uv = corners[k]


# ---------------- 碉楼：八角收分、三道木梁层带、小窗、顶部女儿墙与白石 ----------------
def build_diaolou():
    reset()
    H, RB, RT, SIDES = 10.0, 1.62, 1.08, 8
    prism(SIDES, 1.82, 1.74, 0.45, 0, "stone")                       # 台基
    prism(SIDES, RB, RT, H, 0.45, "stone")                            # 收分塔身
    rad = lambda z: RB - (RB - RT) * (z - 0.45) / H                   # 某高度处的外接半径
    for z in (3.2, 5.9, 8.4):                                         # 木梁层带（略凸出）
        r = rad(z) + 0.06
        prism(SIDES, r, r - 0.01, 0.16, z, "wood")
    # 小窗：每层两三扇，开在八角形的面中心，深色窗洞+木窗楣
    face_ang = [math.pi / SIDES + k * 2 * math.pi / SIDES for k in range(SIDES)]
    for z, faces in ((2.1, (0, 4)), (4.4, (2, 6, 1)), (7.0, (0, 3, 5)), (9.3, (1, 2, 4, 6))):
        for k in faces:
            a = face_ang[k]
            ap = rad(z) * math.cos(math.pi / SIDES)                   # 面中心到轴线的距离
            x, y = ap * math.cos(a), ap * math.sin(a)
            box(0.07, 0.24, 0.42, x, y, z, "dark", rz=a)
            box(0.09, 0.36, 0.06, x * 1.01, y * 1.01, z + 0.44, "wood", rz=a)
    top = 0.45 + H
    prism(SIDES, RT + 0.08, RT + 0.12, 0.22, top, "wood")             # 檐口挑梁
    # 女儿墙：八段矮墙，留出转角缺口
    for k in range(SIDES):
        a = face_ang[k]
        ap = (RT + 0.02) * math.cos(math.pi / SIDES)
        side = 2 * (RT + 0.02) * math.sin(math.pi / SIDES)
        box(0.16, side * 0.72, 0.42, ap * math.cos(a), ap * math.sin(a), top + 0.22, "stone", rz=a)
    box(1.5, 1.5, 0.08, 0, 0, top + 0.22, "earth", rz=math.pi / 8)    # 平顶
    stone_ball(0.17, RT * 0.75, 0, top + 0.64)                        # 屋顶白石
    bake_and_export("diaolou")


# ---------------- 羌寨石屋：平顶、退台、女儿墙、木阳台、屋顶白石与小罩楼 ----------------
def build_house():
    reset()
    W, D = 2.8, 2.4
    box(W, D, 1.7, 0, 0, 0, "earth")                                   # 一层（底层石砌）
    box(W + 0.08, D + 0.08, 0.1, 0, 0, 1.7, "wood")                    # 一层顶的木梁出头
    box(W, D * 0.55, 1.3, 0, -D * 0.225, 1.8, "earth")                 # 二层退台（后半）
    box(W + 0.06, D * 0.55 + 0.06, 0.1, 0, -D * 0.225, 3.1, "wood")
    # 一层平台女儿墙（前沿与两侧）
    box(W, 0.14, 0.32, 0, D / 2 - 0.07, 1.8, "earth")
    for sx in (-1, 1):
        box(0.14, D * 0.45, 0.32, sx * (W / 2 - 0.07), D * 0.275, 1.8, "earth")
    # 二层屋顶女儿墙与四角白石
    rz0, d2 = -D * 0.225, D * 0.55
    for sy in (-1, 1):
        box(W, 0.12, 0.28, 0, rz0 + sy * (d2 / 2 - 0.06), 3.2, "earth")
    for sx in (-1, 1):
        box(0.12, d2, 0.28, sx * (W / 2 - 0.06), rz0, 3.2, "earth")
    for sx in (-1, 1):
        for sy in (-1, 1):
            stone_ball(0.11, sx * (W / 2 - 0.08), rz0 + sy * (d2 / 2 - 0.08), 3.46)
    # 屋顶小罩楼（木构）
    box(0.8, 0.6, 0.55, -0.6, rz0 - 0.1, 3.2, "wood")
    box(0.95, 0.75, 0.06, -0.6, rz0 - 0.1, 3.75, "dark")
    # 门与小窗（正面朝 +Y）
    box(0.55, 0.06, 1.05, 0.55, D / 2, 0, "dark")
    box(0.7, 0.08, 0.08, 0.55, D / 2 + 0.01, 1.05, "wood")
    for x in (-0.7,):
        box(0.32, 0.06, 0.38, x, D / 2, 0.85, "dark")
    for x in (-0.55, 0.45):
        box(0.3, 0.06, 0.4, x, 0.01, 2.35, "dark")                     # 二层朝平台的窗
    for sx in (-1, 1):
        box(0.06, 0.28, 0.34, sx * W / 2, 0.2, 0.9, "dark")           # 侧窗
    # 平台上的木栏杆
    box(1.4, 0.06, 0.06, 0.4, D / 2 - 0.2, 2.35, "wood")
    for x in (-0.25, 0.4, 1.05):
        box(0.06, 0.06, 0.5, x, D / 2 - 0.2, 1.85, "wood")
    bake_and_export("qiang_house")


def cyl(r, h, x=0, y=0, z=0, material="wood", verts=8, rx=0, ry=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(x, y, z))
    o = bpy.context.active_object
    o.rotation_euler = (rx, ry, 0)
    return finish(o, material)


def blob(r, x, y, z, sx=1, sy=1, sz=1, material="leaf", sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(x, y, z))
    o = bpy.context.active_object
    o.scale = (sx, sy, sz)
    return finish(o, material)


def ring(r_out, r_in, h, x=0, y=0, z=0, material="loess", verts=16, gap=None):
    """环形矮墙（半地穴房址的穴壁）；gap 为门道方向（弧度），在该处开口。"""
    cyl(r_out, h, x, y, z + h / 2, material, verts)
    outer = bpy.context.active_object
    cyl(r_in, h * 3, x, y, z + h / 2, material, verts)
    inner = bpy.context.active_object
    mod = outer.modifiers.new("cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"; mod.object = inner
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier="cut")
    bpy.data.objects.remove(inner, do_unlink=True)
    if gap is not None:
        box(0.7, r_out - r_in + 0.4, h * 3, x + (r_in + r_out) / 2 * math.cos(gap), y + (r_in + r_out) / 2 * math.sin(gap), z - h, material, rz=gap + math.pi / 2)
        door = bpy.context.active_object
        mod = outer.modifiers.new("door", "BOOLEAN")
        mod.operation = "DIFFERENCE"; mod.object = door
        bpy.context.view_layer.objects.active = outer
        bpy.ops.object.modifier_apply(modifier="door")
        bpy.data.objects.remove(door, do_unlink=True)
    return outer


def jitter(i, k=1.0):
    """可复现的小扰动（不用随机数，保证每次导出一致）。"""
    return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0 - 0.5


# ---------------- 汉代长城墙段：夯土分层，层间夹芦苇（河西走廊汉塞的做法），顶部风蚀不齐 ----------------
def build_hangtu_wall():
    reset()
    L, H, WB, WT, N = 4.6, 2.5, 1.9, 1.25, 8
    lh = H / N
    for i in range(N):
        z = i * lh
        w = WB - (WB - WT) * (i / (N - 1))
        ln = L + 0.18 * jitter(i, 1)
        box(ln, w + 0.04 * jitter(i, 2), lh * 0.86, 0.06 * jitter(i, 3), 0, z, "earth")
        box(ln + 0.06, w + 0.06, lh * 0.14, 0.06 * jitter(i, 3), 0, z + lh * 0.86, "reed")
    for k, (x, hh) in enumerate(((-1.5, 0.42), (-0.2, 0.18), (1.1, 0.55))):   # 顶部风蚀残块
        box(1.2 + 0.2 * jitter(k, 4), WT * 0.9, hh, x, 0, H, "earth")
    bake_and_export("hangtu_wall")


# ---------------- 汉代烽燧：方形收分夯土台、芦苇夹层、脚窝、顶部望楼矮墙，旁边坞墙与积薪 ----------------
def build_fengsui():
    reset()
    N, H, B, T = 14, 5.4, 3.0, 2.0
    lh = H / N
    for i in range(N):
        s = B - (B - T) * i / (N - 1)
        box(s, s, lh * 0.9, 0, 0, i * lh, "earth")
        if i % 3 == 2:
            box(s + 0.05, s + 0.05, lh * 0.1, 0, 0, i * lh + lh * 0.9, "reed")
    for i in range(10):                                                # 一侧墙面上的脚窝
        z = 0.5 + i * 0.48
        s = B - (B - T) * (z / H)
        box(0.2, 0.06, 0.12, 0.35 * (1 if i % 2 else -1), -s / 2 - 0.01, z, "dark")
    top = H
    for sx, sy, ln, rz in ((0, 1, T, 0), (0, -1, T, 0), (1, 0, T, math.pi / 2), (-1, 0, T, math.pi / 2)):
        box(ln, 0.18, 0.38, sx * (T / 2 - 0.09), sy * (T / 2 - 0.09), top, "earth", rz=rz)
    for k in range(4):                                                 # 顶部木椽
        box(T * 0.9, 0.08, 0.08, 0, -0.6 + k * 0.4, top + 0.38, "wood")
    # 坞：烽燧脚下的矮围墙（L 形）
    box(4.2, 0.4, 1.0, 1.2, 2.4, 0, "earth")
    box(0.4, 3.0, 1.0, 3.1, 1.1, 0, "earth")
    # 积薪：交叉码放的柴垛，三堆
    for j, (x, y) in enumerate(((-2.6, 1.6), (-2.6, -0.2), (-2.6, -2.0))):
        for layer in range(4):
            for m in range(3):
                if layer % 2 == 0:
                    cyl(0.07, 1.1, x, y - 0.3 + m * 0.3, 0.08 + layer * 0.15, "wood", 6, ry=math.pi / 2)
                else:
                    cyl(0.07, 1.1, x - 0.3 + m * 0.3, y, 0.08 + layer * 0.15, "wood", 6, rx=math.pi / 2)
    bake_and_export("fengsui")


# ---------------- 河湟遗址（齐家文化，约 4000 年前）：两座半地穴房址、灶坑、柱洞、彩陶双耳罐、散石 ----------------
def build_hehuang_site():
    reset()
    for (x, y, gap) in ((-1.6, 0.4, 0.3), (1.9, -0.6, 2.6)):
        ring(1.55, 1.25, 0.42, x, y, 0, "loess", 18, gap)
        cyl(1.25, 0.04, x, y, 0.02, "dark", 18)                         # 居住面（白灰面已剥落，偏暗）
        cyl(0.32, 0.06, x, y, 0.05, "paint", 10)                       # 灶坑
        for k in range(6):
            a = k * math.pi / 3 + 0.2
            blob(0.09, x + 0.38 * math.cos(a), y + 0.38 * math.sin(a), 0.07, material="gravel", sub=1)
        for k in range(4):                                             # 柱洞
            a = k * math.pi / 2 + 0.6
            cyl(0.07, 0.03, x + 0.8 * math.cos(a), y + 0.8 * math.sin(a), 0.05, "paint", 8)
    # 彩陶双耳罐 ×2（红陶、黑彩带纹）
    for (x, y, s) in ((0.2, 1.6, 1.0), (0.75, 1.45, 0.7)):
        blob(0.32 * s, x, y, 0.36 * s, 1, 1, 1.15, "pottery", 2)
        cyl(0.15 * s, 0.22 * s, x, y, 0.78 * s, "pottery", 12)
        cyl(0.335 * s, 0.05 * s, x, y, 0.42 * s, "paint", 16)
        cyl(0.27 * s, 0.04 * s, x, y, 0.62 * s, "paint", 16)
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(major_segments=10, minor_segments=4, major_radius=0.1 * s, minor_radius=0.025 * s,
                                             location=(x + sx * 0.25 * s, y, 0.62 * s), rotation=(math.pi / 2, 0, 0))
            finish(bpy.context.active_object, "pottery")
    for k in range(9):                                                 # 散落石块
        blob(0.12 + 0.08 * (jitter(k, 5) + 0.5), 3.0 * jitter(k, 6) * 2, 2.2 * jitter(k, 7) * 2, 0.06, 1, 0.8, 0.6, "gravel", 1)
    bake_and_export("hehuang_site")


# ---------------- 树：岷江冷杉、白杨、核桃——树干＋叶片卡（贴透明叶片图后接近真树的轮廓） ----------------
def card(cx, cy, cz, w, h, yaw, pitch, material):
    """以 (cx, cy, cz) 为根、朝 yaw 方向伸出的一张叶片卡，pitch 为下垂角。"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object
    o.scale = (h, w, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in o.data.vertices:                     # 根部对齐原点、向 +X 伸出
        v.co.x += h / 2
    o.rotation_euler = (0, pitch, yaw)
    o.location = (cx, cy, cz)
    return finish(o, material)


def trunk(r0, r1, h, material="bark", x=0, y=0, z=0, tilt=(0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r0, radius2=r1, depth=h, location=(x, y, z + h / 2))
    o = bpy.context.active_object
    o.rotation_euler = (tilt[0], tilt[1], 0)
    return finish(o, material)


def build_trees():
    reset()                                        # 冷杉：层层下垂的枝叶，越往上越短
    trunk(0.2, 0.04, 5.6, "bark")
    tiers = 11
    for k in range(tiers):
        z = 0.9 + k * 0.44
        r = 1.6 * (1 - k / tiers) + 0.25
        n = 7 if k < 8 else 5
        for m in range(n):
            yaw = m * 2 * math.pi / n + k * 0.55 + 0.2 * jitter(k * 9 + m, 1)
            card(0.05 * math.cos(yaw), 0.05 * math.sin(yaw), z, 0.75 * r + 0.15, r, yaw, math.radians(16 + 10 * jitter(k + m, 2)), "needlecard")
    card(0, 0, 5.3, 0.35, 0.6, 0, -math.pi / 2, "needlecard")
    bake_and_export("tree_fir", ao=1.4)

    reset()                                        # 白杨：灰白树干、向上收拢的窄长树冠
    trunk(0.15, 0.05, 6.4, "bark_w")
    for m in range(46):
        z = 1.9 + 4.4 * (m + 0.5) / 46
        k = math.sin(math.pi * (z - 1.9) / 4.6)
        yaw = m * 2.4
        card(0.06 * math.cos(yaw), 0.06 * math.sin(yaw), z, 0.7, 0.55 + 0.45 * k, yaw, math.radians(-55 + 15 * jitter(m, 3)), "leafcard")
    bake_and_export("tree_poplar", ao=1.2)

    reset()                                        # 核桃：粗短主干分三杈，圆阔树冠
    trunk(0.22, 0.12, 2.0, "bark")
    for k, (rx, ry) in enumerate(((0.45, 0.1), (-0.4, 0.3), (0.05, -0.5))):
        trunk(0.1, 0.05, 1.6, "bark", 0, 0, 1.8, (rx, ry))
    for m in range(70):
        u = (m + 0.5) / 70
        th, ph = m * 2.399963, math.acos(1 - 2 * u)
        r = 1.15 + 0.25 * jitter(m, 4)
        x, y, z = r * math.sin(ph) * math.cos(th), r * math.sin(ph) * math.sin(th), 3.0 + 0.8 * r * math.cos(ph)
        card(x * 0.55, y * 0.55, z, 0.95, 1.0, th, math.radians(-25 + 50 * jitter(m, 5)), "leafcard")
    bake_and_export("tree_walnut", ao=1.2)


# ---------------- 牲畜：绵羊、黄牛、马（朝 +X） ----------------
def legs(xs, ys, h, r, material):
    for x in xs:
        for y in ys:
            cyl(r, h, x, y, h / 2, material, 6)


def build_animals():
    reset()
    blob(0.42, 0, 0, 0.62, 1.25, 0.85, 0.8, "wool", 2)
    box(0.24, 0.2, 0.24, 0.56, 0, 0.66, "dark")
    blob(0.13, 0.5, 0, 0.8, 1, 1.1, 0.8, "wool", 1)
    legs((-0.25, 0.25), (-0.15, 0.15), 0.36, 0.045, "dark")
    bake_and_export("sheep", organic=True, ao=0.5)

    reset()
    box(1.35, 0.55, 0.6, 0, 0, 0.62, "hide")
    box(0.4, 0.5, 0.25, 0.3, 0, 1.15, "hide")
    box(0.36, 0.3, 0.34, 0.86, 0, 0.88, "hide")
    box(0.12, 0.26, 0.16, 1.07, 0, 0.82, "dark")
    for sy in (-1, 1):
        cyl(0.03, 0.22, 0.86, sy * 0.19, 1.1, "white", 5, rx=sy * 0.8)
    legs((-0.5, 0.48), (-0.18, 0.18), 0.62, 0.07, "hide")
    cyl(0.03, 0.6, -0.72, 0, 0.85, "hide", 5, ry=0.35)
    bake_and_export("cow", organic=True, ao=0.5)

    reset()
    box(1.4, 0.45, 0.55, 0, 0, 0.98, "horse")
    box(0.32, 0.26, 0.75, 0.66, 0, 1.25, "horse").rotation_euler[1] = 0.6
    box(0.5, 0.22, 0.24, 1.08, 0, 1.78, "horse").rotation_euler[1] = 0.5
    box(0.06, 0.08, 0.8, 0.58, 0, 1.3, "dark").rotation_euler[1] = 0.6
    legs((-0.55, 0.52), (-0.15, 0.15), 0.98, 0.055, "horse")
    cyl(0.05, 0.7, -0.82, 0, 0.98, "dark", 5, ry=0.5)
    bake_and_export("horse", organic=True, ao=0.5)


build_diaolou()
build_house()
build_hangtu_wall()
build_fengsui()
build_hehuang_site()
build_trees()
build_animals()
