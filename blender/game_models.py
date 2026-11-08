"""边缘行走 · 游戏模型（碉楼、羌寨石屋）——Blender 脚本生成，导出 GLB 供 three.js 加载。

用法（在仓库根目录）：
    blender --background --factory-startup --python blender/game_models.py

输出：assets/models/diaolou.glb、assets/models/qiang_house.glb
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
}


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


def bake_and_export(name):
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    # 按世界尺度做立方投影 UV，石纹在各个面上大小一致
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=2.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_flat()
    path = os.path.join(OUT, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_normals=True,
                              export_texcoords=True, export_materials="EXPORT")
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("exported", path, os.path.getsize(path), "bytes,", tris, "triangles")


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


build_diaolou()
build_house()
