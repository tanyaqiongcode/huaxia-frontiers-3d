# 《边缘行走》牲畜：绵羊、黄牛、马、牦牛（朝 +X，脚底在 z=0）。沿路径放样的圆滑体块，分部位材质 → GLB
# 用法：blender --background --factory-startup --python animals.py
import bpy, bmesh, math, os
from mathutils import Vector

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models"))

def lin(h):
    def c(v):
        v /= 255.0
        return v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4
    return (c((h >> 16) & 255), c((h >> 8) & 255), c(h & 255), 1.0)

class Builder:
    def __init__(self, name):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.name = name; self.v = []; self.f = []; self.fm = []; self.mats = []; self.mi = {}
    def M(self, key, hexc, rough=0.95):
        if key not in self.mi:
            m = bpy.data.materials.new("an_"+key); m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = lin(hexc); b.inputs["Roughness"].default_value = rough
            self.mi[key] = len(self.mats); self.mats.append(m)
        return self.mi[key]
    def tube(self, pts, mat, seg=10, wob=0.0, seed=0.0):
        """pts: [(x, y, z, ra, rb)]，ra 为横向（近 Y）半径，rb 为竖向半径；wob>0 时表面起伏（羊毛、长毛）"""
        mi = self.M(*mat); P = [Vector(p[:3]) for p in pts]; rows = []
        for j, p in enumerate(pts):
            t = (P[min(j+1, len(P)-1)] - P[max(j-1, 0)]).normalized()
            ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
            nb = t.cross(ref).normalized(); na = nb.cross(t).normalized()
            row = []
            for i in range(seg):
                a = 2*math.pi*i/seg
                k = 1.0 + wob*math.sin(i*2.7+j*1.9+seed)*math.cos(i*1.3-j*2.3+seed*0.7) if wob else 1.0
                q = P[j] + na*(math.cos(a)*p[3]*k) + nb*(math.sin(a)*p[4]*k)
                self.v.append(tuple(q)); row.append(len(self.v)-1)
            rows.append(row)
        for j in range(len(rows)-1):
            for i in range(seg):
                i2 = (i+1) % seg
                self.f.append([rows[j][i], rows[j][i2], rows[j+1][i2], rows[j+1][i]]); self.fm.append(mi)
        self.f.append(list(rows[0])); self.fm.append(mi)
        self.f.append(list(reversed(rows[-1]))); self.fm.append(mi)
    def ball(self, c, r, mat, seg=8, rings=6, wob=0.0, seed=0.0):
        pts = []
        for j in range(rings):
            ph = math.pi*(j+0.5)/rings
            pts.append((c[0]+r[0]*math.cos(ph), c[1], c[2], r[1]*math.sin(ph), r[2]*math.sin(ph)))
        self.tube(pts, mat, seg, wob, seed)
    def leg(self, x, y, top, r, mat, hoof, knee=0.0, hock=0.0, hr=1.25):
        """自上而下的一条腿：top 为与身体相接的高度；knee/hock 让关节前后略有折线"""
        zk = top*0.52
        self.tube([(x, y*0.92, top+r*2.2, r*1.6, r*2.6), (x, y, top, r*1.9, r*2.7), (x+knee*0.5, y, top*0.78, r*1.4, r*1.75), (x+knee, y, zk, r, r*1.05),
                   (x+knee*0.4+hock, y, top*0.26, r*0.82, r*0.86), (x+hock*0.3, y, 0.075, r*0.85, r*0.9)], mat, 8)
        self.tube([(x+hock*0.3, y, 0.085, r*hr*0.9, r*hr*0.9), (x+hock*0.3+0.012, y, 0.0, r*hr*1.05, r*hr*1.15)], hoof, 8)
    def export(self):
        me = bpy.data.meshes.new(self.name); me.from_pydata(self.v, [], self.f); me.update()
        for m in self.mats: me.materials.append(m)
        for p, mi in zip(me.polygons, self.fm): p.material_index = mi
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        try: me.shade_smooth()
        except Exception:
            for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(self.name, me); bpy.context.collection.objects.link(ob)
        path = os.path.join(OUT, self.name+".glb")
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_animations=False, export_yup=True)
        print("EXPORTED", self.name, len(self.v), "verts", os.path.getsize(path)//1024, "KB")

def sheep():
    b = Builder("sheep"); WOOL = ("wool", 0xe6e1d4); FACE = ("face", 0x2b2622); HOOF = ("hoof", 0x15130f); HORN = ("horn", 0xb9ab8c)
    b.tube([(-0.47, 0, 0.60, 0.07, 0.08), (-0.40, 0, 0.62, 0.19, 0.20), (-0.22, 0, 0.63, 0.255, 0.25), (0.0, 0, 0.62, 0.27, 0.255),
            (0.20, 0, 0.63, 0.25, 0.25), (0.34, 0, 0.66, 0.20, 0.21), (0.43, 0, 0.70, 0.13, 0.14)], WOOL, 12, 0.07, 1.0)
    b.tube([(0.36, 0, 0.72, 0.12, 0.13), (0.44, 0, 0.80, 0.105, 0.105), (0.50, 0, 0.86, 0.085, 0.08)], WOOL, 10, 0.06, 2.0)   # 颈、头顶的毛
    b.tube([(0.46, 0, 0.84, 0.068, 0.075), (0.55, 0, 0.80, 0.066, 0.07), (0.64, 0, 0.74, 0.05, 0.052), (0.69, 0, 0.705, 0.036, 0.036)], FACE, 10)
    for s in (-1, 1):
        b.tube([(0.50, 0.06*s, 0.845, 0.02, 0.03), (0.49, 0.12*s, 0.83, 0.028, 0.012), (0.48, 0.165*s, 0.80, 0.012, 0.008)], FACE, 6)       # 耳
        b.tube([(0.49, 0.045*s, 0.875, 0.022, 0.022), (0.44, 0.085*s, 0.90, 0.02, 0.02), (0.40, 0.11*s, 0.86, 0.016, 0.016),
                (0.43, 0.115*s, 0.82, 0.01, 0.01)], HORN, 6)                                                                              # 小弯角
        b.leg(0.27, 0.105*s, 0.50, 0.03, FACE, HOOF, knee=0.012, hock=0.0)
        b.leg(-0.30, 0.115*s, 0.52, 0.03, FACE, HOOF, knee=-0.02, hock=-0.035)
    b.ball((-0.50, 0, 0.60), (0.06, 0.05, 0.07), WOOL, 8, 5)
    b.export()

def cow():
    b = Builder("cow"); HIDE = ("hide", 0x9a6a3e); PALE = ("pale", 0xd9c3a0); HOOF = ("hoof", 0x1d1814); HORN = ("horn", 0xd8cdb4); DARK = ("dark2", 0x3a2a1e)
    b.tube([(-0.80, 0, 1.02, 0.10, 0.14), (-0.70, 0, 0.98, 0.25, 0.30), (-0.42, 0, 0.94, 0.31, 0.33), (-0.05, 0, 0.90, 0.33, 0.35),
            (0.30, 0, 0.94, 0.30, 0.33), (0.52, 0, 1.00, 0.25, 0.31), (0.68, 0, 1.04, 0.17, 0.24)], HIDE, 12)
    b.tube([(0.40, 0, 1.22, 0.10, 0.07), (0.50, 0, 1.25, 0.12, 0.08), (0.60, 0, 1.20, 0.09, 0.06)], HIDE, 8)               # 肩峰
    b.tube([(0.62, 0, 1.06, 0.16, 0.22), (0.80, 0, 1.12, 0.125, 0.165), (0.93, 0, 1.15, 0.105, 0.125)], HIDE, 10)          # 颈
    b.tube([(0.88, 0, 1.17, 0.11, 0.115), (1.00, 0, 1.13, 0.105, 0.11), (1.14, 0, 1.03, 0.08, 0.082), (1.22, 0, 0.965, 0.07, 0.066)], HIDE, 10)
    b.tube([(1.20, 0, 0.975, 0.072, 0.068), (1.26, 0, 0.94, 0.066, 0.058), (1.285, 0, 0.925, 0.045, 0.04)], PALE, 10)      # 口鼻
    b.tube([(0.70, 0, 0.84, 0.03, 0.10), (0.80, 0, 0.90, 0.025, 0.09), (0.90, 0, 0.99, 0.02, 0.05)], PALE, 6)              # 颈下垂皮
    for s in (-1, 1):
        b.tube([(0.93, 0.085*s, 1.20, 0.022, 0.03), (0.92, 0.17*s, 1.19, 0.03, 0.014), (0.91, 0.23*s, 1.17, 0.012, 0.008)], HIDE, 6)
        b.tube([(0.94, 0.06*s, 1.255, 0.03, 0.03), (0.95, 0.14*s, 1.30, 0.024, 0.024), (0.98, 0.18*s, 1.37, 0.016, 0.016), (1.0, 0.185*s, 1.42, 0.006, 0.006)], HORN, 6)
        b.leg(0.50, 0.17*s, 0.80, 0.047, HIDE, HOOF, knee=0.015)
        b.leg(-0.60, 0.18*s, 0.84, 0.047, HIDE, HOOF, knee=-0.03, hock=-0.05)
    b.tube([(-0.80, 0, 1.10, 0.022, 0.022), (-0.88, 0, 0.95, 0.018, 0.018), (-0.90, 0, 0.62, 0.014, 0.014), (-0.90, 0, 0.50, 0.03, 0.03), (-0.90, 0, 0.36, 0.012, 0.012)], DARK, 6)
    b.export()

def horse():
    b = Builder("horse"); COAT = ("coat", 0x6d4426); MANE = ("mane", 0x1c1512); HOOF = ("hoof", 0x15120f); SOCK = ("sock", 0x4d2f1b)
    b.tube([(-0.78, 0, 1.22, 0.10, 0.14), (-0.66, 0, 1.20, 0.23, 0.27), (-0.40, 0, 1.15, 0.26, 0.28), (-0.05, 0, 1.11, 0.265, 0.28),
            (0.28, 0, 1.14, 0.255, 0.29), (0.50, 0, 1.20, 0.22, 0.28), (0.62, 0, 1.25, 0.15, 0.22)], COAT, 12)
    b.tube([(0.54, 0, 1.24, 0.15, 0.22), (0.68, 0, 1.42, 0.115, 0.17), (0.80, 0, 1.60, 0.09, 0.125), (0.87, 0, 1.72, 0.08, 0.10)], COAT, 10)   # 颈
    b.tube([(0.83, 0, 1.74, 0.082, 0.095), (0.95, 0, 1.68, 0.078, 0.092), (1.10, 0, 1.55, 0.058, 0.066), (1.21, 0, 1.455, 0.05, 0.052), (1.25, 0, 1.42, 0.036, 0.036)], COAT, 10)
    b.tube([(0.88, 0, 1.84, 0.012, 0.03), (0.80, 0, 1.76, 0.02, 0.05), (0.70, 0, 1.60, 0.022, 0.055), (0.60, 0, 1.44, 0.02, 0.05), (0.52, 0, 1.36, 0.012, 0.03)], MANE, 6)  # 鬃
    b.tube([(0.90, 0, 1.80, 0.03, 0.02), (0.97, 0, 1.74, 0.03, 0.015)], MANE, 6)                                                              # 额发
    for s in (-1, 1):
        b.tube([(0.86, 0.05*s, 1.80, 0.02, 0.024), (0.85, 0.065*s, 1.87, 0.014, 0.02), (0.85, 0.07*s, 1.91, 0.005, 0.006)], COAT, 6)
        b.leg(0.50, 0.13*s, 1.02, 0.038, COAT, HOOF, knee=0.02, hr=1.4)
        b.leg(-0.60, 0.14*s, 1.08, 0.04, COAT, HOOF, knee=-0.045, hock=-0.07, hr=1.4)
    b.tube([(-0.78, 0, 1.30, 0.03, 0.03), (-0.90, 0, 1.22, 0.05, 0.05), (-0.98, 0, 0.95, 0.065, 0.06), (-1.0, 0, 0.62, 0.05, 0.045), (-0.99, 0, 0.44, 0.015, 0.015)], MANE, 8, 0.1, 3.0)
    b.export()

def yak():
    b = Builder("yak"); COAT = ("yak", 0x2a221d); SKIRT = ("yakhair", 0x1e1815); HORN = ("horn", 0xd8cdb4); HOOF = ("hoof", 0x100e0c); NOSE = ("nose", 0x6a5a50)
    b.tube([(-0.74, 0, 0.98, 0.12, 0.16), (-0.62, 0, 0.95, 0.30, 0.32), (-0.30, 0, 0.92, 0.36, 0.36), (0.05, 0, 0.94, 0.37, 0.39),
            (0.36, 0, 1.02, 0.34, 0.42), (0.56, 0, 1.06, 0.26, 0.36), (0.70, 0, 1.02, 0.17, 0.24)], COAT, 12, 0.05, 0.5)
    b.tube([(0.22, 0, 1.36, 0.14, 0.10), (0.40, 0, 1.44, 0.17, 0.11), (0.56, 0, 1.36, 0.12, 0.08)], COAT, 8, 0.08, 1.2)        # 高耸的肩峰
    # 腹侧垂下的长毛裙
    b.tube([(-0.62, 0, 0.66, 0.26, 0.20), (-0.30, 0, 0.56, 0.37, 0.26), (0.05, 0, 0.54, 0.38, 0.28), (0.40, 0, 0.58, 0.35, 0.28), (0.62, 0, 0.70, 0.22, 0.20)], SKIRT, 12, 0.13, 2.2)
    b.tube([(0.62, 0, 1.00, 0.17, 0.22), (0.80, 0, 0.92, 0.14, 0.17), (0.92, 0, 0.84, 0.125, 0.14)], COAT, 10, 0.05, 0.9)      # 低垂的颈
    b.tube([(0.86, 0, 0.88, 0.135, 0.14), (0.98, 0, 0.80, 0.125, 0.13), (1.10, 0, 0.68, 0.095, 0.095), (1.17, 0, 0.60, 0.08, 0.072)], COAT, 10)
    b.tube([(1.15, 0, 0.61, 0.082, 0.074), (1.21, 0, 0.565, 0.07, 0.06), (1.23, 0, 0.545, 0.045, 0.04)], NOSE, 10)
    b.tube([(0.80, 0, 0.78, 0.06, 0.12), (0.92, 0, 0.66, 0.05, 0.10), (1.0, 0, 0.58, 0.02, 0.04)], SKIRT, 8, 0.12, 4.0)        # 颈下长毛
    for s in (-1, 1):
        b.tube([(0.90, 0.11*s, 0.92, 0.024, 0.03), (0.89, 0.19*s, 0.90, 0.03, 0.015), (0.88, 0.24*s, 0.87, 0.012, 0.008)], COAT, 6)
        b.tube([(0.90, 0.09*s, 0.985, 0.036, 0.036), (0.91, 0.22*s, 1.02, 0.03, 0.03), (0.94, 0.33*s, 1.12, 0.022, 0.022),
                (0.97, 0.36*s, 1.24, 0.013, 0.013), (0.97, 0.34*s, 1.32, 0.004, 0.004)], HORN, 6)                              # 向外再上翘的角
        b.leg(0.46, 0.19*s, 0.66, 0.05, COAT, HOOF, knee=0.012)
        b.leg(-0.50, 0.20*s, 0.70, 0.05, COAT, HOOF, knee=-0.02, hock=-0.04)
    b.tube([(-0.74, 0, 1.04, 0.04, 0.04), (-0.86, 0, 0.92, 0.09, 0.09), (-0.92, 0, 0.62, 0.12, 0.11), (-0.92, 0, 0.36, 0.08, 0.075), (-0.91, 0, 0.24, 0.02, 0.02)], SKIRT, 8, 0.14, 5.0)
    b.export()

for fn in (sheep, cow, horse, yak): fn()
