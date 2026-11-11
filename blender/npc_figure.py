# 《边缘行走》人物构建：放样体块 + 骨骼蒙皮 + 分部位材质 → GLB（无内置动画，动作由游戏按骨骼驱动）
# 用法：blender --background --factory-startup --python npc_figure.py -- <variant|all>
# 朝向：Blender 里面朝 -Y（导出后在 three.js 里面朝 +Z）；骨名带 L 的在 x<0 一侧，与游戏里的 legL/armL 一致。
import bpy, bmesh, math, os, sys

ARG = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "all"
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models"))
os.makedirs(OUT, exist_ok=True)

def lin(h):
    def c(v):
        v /= 255.0
        return v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4
    return (c((h >> 16) & 255), c((h >> 8) & 255), c(h & 255), 1.0)

# 各角色：服饰参照岷江上游羌族常见装束（包头帕、长衫、羊皮褂、腰带、围腰、绑腿、云云鞋），
# 行走者与考古者按 1990 年代田野工作者，返乡青年为当代装束，戍卒按汉代戍卒（赤帻、短袍、革甲、行縢）。
VARS = {
 "fig_player":  dict(skin=0xd2a583, hair=0x1e1c1c, top=0x6d6a4e, legs=0x47443a, shoe=0x2a241e,
                     hat="brim", hatC=0x80705a, scarf=0xa33b2e, pack=0x3f3226, belt=0x2e261c, pockets=True),
 "fig_elder":   dict(skin=0xc49873, hair=0xa9a9a9, top=0x2f3a55, legs=0x2a3044, shoe=0x2b2b33,
                     robe=0.30, vest=0x8a7355, fleece=0xd9cfb8, sash=0x8c2f2a, hat="wrap", hatC=0x22242c,
                     legwrap=0xd8d2c2, yunyun=0xa33b2e, beard=True, trim=(0xd8d2c2,)),
 "fig_arch":    dict(skin=0xd2a583, hair=0x26221f, top=0xc8c2b0, legs=0x55585c, shoe=0x3a2e22,
                     hat="brim", hatC=0x8a7a5f, vest=0x7a7052, belt=0x2e261c, pockets=True),
 "fig_soldier": dict(skin=0xc99b78, hair=0x17161a, top=0x6e3b2e, legs=0x4b4336, shoe=0x241f19,
                     robe=0.52, vest=0x4a3b2c, lamellar=True, belt=0x1f1812, hat="wrap", hatC=0x8c2f2a,
                     legwrap=0x6b6248),
 "fig_youth":   dict(skin=0xd6ab8a, hair=0x141416, top=0x3f566b, legs=0x2c3038, shoe=0xd8d8d8,
                     zipper=0xc9c9c9, collar=True),
 "fig_aunt":    dict(skin=0xd2a583, hair=0x151515, top=0x3b5f8a, legs=0x26262c, shoe=0x7a2d2a,
                     robe=0.26, sash=0xb5382f, apron=0x23232b, hat="wrap", hatC=0xe6e0d2, hatBand=0xb5382f,
                     yunyun=0xd9a441, trim=(0xb5382f, 0xe6e0d2), bun=True, slim=True),
}

def build(VARIANT):
    V = VARS[VARIANT]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats, mat_ix = [], {}
    def M(hexc, rough=0.9):
        if hexc not in mat_ix:
            m = bpy.data.materials.new("c%06x" % hexc); m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = lin(hexc)
            b.inputs["Roughness"].default_value = rough
            b.inputs["Metallic"].default_value = 0.0
            mat_ix[hexc] = len(mats); mats.append(m)
        return mat_ix[hexc]

    verts, faces, fmat, vw = [], [], [], []
    def addv(p, w):
        ww = w(*p) if callable(w) else w
        s = sum(ww.values()) or 1.0
        verts.append(p); vw.append({k: v/s for k, v in ww.items() if v > 1e-4}); return len(verts)-1

    def tube(rings, mat, w, seg=12, at=(0.0, 0.0), caps=(True, True), arc=None):
        """rings: [(z, rx, ry[, dx, dy])]，水平椭圆环自下而上或自上而下均可"""
        mi = M(mat) if not isinstance(mat, tuple) else M(*mat)
        n = seg if arc is None else seg+1
        ids = []
        for r in rings:
            z, rx, ry = r[0], r[1], r[2]
            cx = at[0] + (r[3] if len(r) > 3 else 0.0); cy = at[1] + (r[4] if len(r) > 4 else 0.0)
            row = []
            for i in range(n):
                a = (2*math.pi*i/seg) if arc is None else (arc[0] + (arc[1]-arc[0])*i/seg)
                row.append(addv((cx+math.cos(a)*rx, cy+math.sin(a)*ry, z), w))
            ids.append(row)
        for j in range(len(ids)-1):
            for i in range(n if arc is None else n-1):
                i2 = (i+1) % n
                faces.append([ids[j][i], ids[j][i2], ids[j+1][i2], ids[j+1][i]]); fmat.append(mi)
        if arc is None:
            if caps[0]: faces.append(list(ids[0])); fmat.append(mi)
            if caps[1]: faces.append(list(reversed(ids[-1]))); fmat.append(mi)

    def ell(c, r, mat, w, seg=10, rings=7):
        rs = []
        for j in range(rings):
            ph = math.pi*(j+0.5)/rings
            rs.append((c[2]+r[2]*math.cos(ph), r[0]*math.sin(ph), r[1]*math.sin(ph)))
        tube(rs, mat, w, seg, at=(c[0], c[1]))

    def box(c, s, mat, w):
        mi = M(mat); x, y, z = c; a, b, d = s[0]/2, s[1]/2, s[2]/2
        i = [addv((x+sx*a, y+sy*b, z+sz*d), w) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        for f in ([0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]):
            faces.append([i[k] for k in f]); fmat.append(mi)

    cl = lambda t: max(0.0, min(1.0, t))
    def w_torso(x, y, z):
        if z >= 1.20: return {"chest": 1}
        if z >= 1.04: t = (z-1.04)/0.16; return {"chest": t, "spine": 1-t}
        if z >= 0.92: return {"spine": 1}
        if z >= 0.84: t = (z-0.84)/0.08; return {"spine": t, "hips": 1-t}
        # 下摆：随两条大腿摆动
        k = cl((0.84-z)/0.30)*0.62; wl = cl(0.5 - x/0.14)
        return {"hips": 1-k, "thighL": k*wl, "thighR": k*(1-wl)}
    def w_arm(S):
        def f(x, y, z):
            t = cl((z-0.96)/0.12); return {"upArm"+S: t, "foreArm"+S: 1-t}
        return f
    def w_leg(S):
        def f(x, y, z):
            if z > 0.80: t = cl((z-0.80)/0.07); return {"hips": t*0.6, "thigh"+S: 1-t*0.6}
            t = cl((z-0.35)/0.11); return {"thigh"+S: t, "shin"+S: 1-t}
        return f
    def w_neck(x, y, z):
        t = cl((z-1.40)/0.10); return {"head": t, "chest": 1-t}
    HEAD = {"head": 1}

    slim = 0.93 if V.get("slim") else 1.0
    SK, TOP, LEG = V["skin"], V["top"], V["legs"]

    # ── 躯干（上衣 / 长衫） ──
    hem = V.get("robe")
    rings = [(1.425, 0.062, 0.058), (1.385, 0.105, 0.078), (1.335, 0.150*slim, 0.094), (1.24, 0.168*slim, 0.108),
             (1.12, 0.160*slim, 0.106), (0.99, 0.142*slim, 0.097), (0.90, 0.150*slim, 0.103), (0.80, 0.160*slim, 0.110)]
    if hem:
        rings += [(0.66, 0.178*slim, 0.124), (0.50, 0.196*slim, 0.138)]
        if hem < 0.48: rings += [(0.38, 0.208*slim, 0.148), (hem, 0.218*slim, 0.156)]
    else:
        rings += [(0.745, 0.158*slim, 0.110)]
    tube(rings, TOP, w_torso, 14)
    zb = rings[-1][0]; rb = rings[-1]
    for k, tc in enumerate(V.get("trim", ())):      # 下摆绣边
        tube([(zb+0.035+0.03*k, rb[1]*0.985+0.004, rb[2]*0.985+0.004), (zb+0.008+0.03*k, rb[1]+0.004, rb[2]+0.004)], tc, w_torso, 14, caps=(False, False))
    if V.get("collar"):
        tube([(1.455, 0.068, 0.066), (1.40, 0.082, 0.074)], TOP, {"chest": 1}, 12, caps=(False, False))
    if V.get("zipper"):
        box((0, -0.107, 1.10), (0.012, 0.012, 0.56), V["zipper"], w_torso)
    if V.get("pockets"):
        for sx in (-1, 1):
            box((0.075*sx, -0.112 if V.get("vest") else -0.104, 1.19), (0.07, 0.014, 0.075), V.get("vest", TOP), {"chest": 1})
            box((0.075*sx, -0.115 if V.get("vest") else -0.107, 1.225), (0.074, 0.012, 0.018), V.get("belt", TOP), {"chest": 1})
    # 羊皮褂 / 田野马甲 / 革甲
    if V.get("vest"):
        vc = V["vest"]
        tube([(1.375, 0.112, 0.088), (1.33, 0.150*slim, 0.104), (1.22, 0.176*slim, 0.118), (1.05, 0.170*slim, 0.116), (0.84, 0.172*slim, 0.120)],
             vc, w_torso, 14, caps=(False, False))
        if V.get("fleece"):                           # 羊皮褂翻毛边
            fc = V["fleece"]
            tube([(0.86, 0.176, 0.124), (0.82, 0.178, 0.126)], fc, w_torso, 14, caps=(False, False))
            tube([(1.39, 0.104, 0.084), (1.35, 0.138, 0.100)], fc, w_torso, 14, caps=(False, False))
            box((0, -0.121, 1.10), (0.026, 0.012, 0.50), fc, w_torso)
        if V.get("lamellar"):                         # 甲片横缝
            for zz in (0.92, 1.01, 1.10, 1.19, 1.28):
                tube([(zz+0.006, 0.19, 0.124), (zz-0.006, 0.19, 0.124)], 0x2a2018, w_torso, 14, caps=(False, False))
    if V.get("sash"):
        tube([(1.025, 0.150*slim+0.012, 0.112), (0.955, 0.150*slim+0.012, 0.112)], V["sash"], w_torso, 14, caps=(False, False))
        box((-0.09, -0.118, 0.90), (0.04, 0.012, 0.20), V["sash"], w_torso)
    if V.get("belt"):
        tube([(0.925, 0.154, 0.108), (0.885, 0.156, 0.109)], V["belt"], w_torso, 14, caps=(False, False))
        box((0, -0.112, 0.905), (0.036, 0.012, 0.03), 0xb89a5a, w_torso)
    if V.get("apron"):                                # 围腰：前片 + 绣花带
        A0, A1 = -math.pi/2-0.95, -math.pi/2+0.95
        tube([(0.955, 0.158, 0.118), (0.70, 0.186, 0.136), (0.40, 0.208, 0.156)], V["apron"], w_torso, 10, arc=(A0, A1))
        tube([(0.47, 0.205, 0.154), (0.42, 0.211, 0.158)], 0xb5382f, w_torso, 10, arc=(A0, A1))
        tube([(0.52, 0.201, 0.151), (0.49, 0.204, 0.153)], 0xd9a441, w_torso, 10, arc=(A0, A1))
    if V.get("scarf"):
        tube([(1.455, 0.070, 0.068), (1.40, 0.086, 0.080), (1.37, 0.092, 0.084)], V["scarf"], {"chest": 1}, 12, caps=(False, False))
        box((0.03, -0.098, 1.30), (0.05, 0.02, 0.14), V["scarf"], {"chest": 1})
    if V.get("pack"):
        pc = V["pack"]
        box((0, 0.165, 1.14), (0.27, 0.13, 0.36), pc, w_torso)
        box((0, 0.172, 1.325), (0.28, 0.14, 0.05), 0x4a3520, {"chest": 1})
        tube([(1.0, 0.055, 0.055), (1.0, 0.055, 0.055)], pc, w_torso, 8)  # 占位，避免空材质
        for sx in (-1, 1):
            box((0.10*sx, -0.108, 1.20), (0.04, 0.012, 0.30), 0x3a2f22, {"chest": 1})
            box((0.10*sx, 0.0, 1.372), (0.04, 0.22, 0.012), 0x3a2f22, {"chest": 1})
        ell((0, 0.165, 1.385), (0.15, 0.055, 0.055), 0x8a7a5f, {"chest": 1}, 8, 5)   # 铺盖卷

    # ── 手臂 ──
    for sd, S in ((-1, "L"), (1, "R")):
        X = 0.192*sd*slim
        tube([(1.352, 0.026, 0.030), (1.335, 0.046, 0.052), (1.30, 0.053, 0.058), (1.22, 0.053, 0.057), (1.08, 0.047, 0.050), (1.02, 0.045, 0.048),
              (0.92, 0.043, 0.045), (0.80, 0.040, 0.041)], TOP, w_arm(S), 10, at=(X, 0))
        for k, tc in enumerate(V.get("trim", ())):   # 袖口绣边
            tube([(0.835-0.028*k, 0.0425, 0.0435), (0.808-0.028*k, 0.0425, 0.0435)], tc, w_arm(S), 10, at=(X, 0), caps=(False, False))
        tube([(0.805, 0.030, 0.032), (0.775, 0.028, 0.030)], SK, {"foreArm"+S: 1}, 8, at=(X, 0))
        ell((X, -0.004, 0.725), (0.026, 0.040, 0.058), SK, {"foreArm"+S: 1}, 8, 6)
        ell((X-0.022*sd, -0.03, 0.74), (0.012, 0.014, 0.03), SK, {"foreArm"+S: 1}, 6, 4)   # 拇指
    # ── 腿 ──
    for sd, S in ((-1, "L"), (1, "R")):
        X = 0.088*sd
        tube([(0.86, 0.080, 0.092), (0.70, 0.078, 0.086), (0.52, 0.064, 0.070), (0.41, 0.057, 0.062, 0, -0.004),
              (0.30, 0.056, 0.060, 0, 0.008), (0.16, 0.046, 0.049), (0.07, 0.042, 0.046)], LEG, w_leg(S), 10, at=(X, 0))
        if V.get("legwrap"):                          # 绑腿 / 行縢
            tube([(0.375, 0.060, 0.065), (0.30, 0.061, 0.066, 0, 0.008), (0.17, 0.051, 0.054), (0.085, 0.047, 0.051)],
                 V["legwrap"], {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
            for zz in (0.33, 0.25, 0.17):
                tube([(zz+0.006, 0.062, 0.067, 0, 0.006), (zz-0.006, 0.062, 0.067, 0, 0.006)], 0x8a8474, {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
        ell((X, -0.045, 0.046), (0.050, 0.118, 0.047), V["shoe"], {"shin"+S: 1}, 10, 6)
        if V.get("yunyun"):                           # 云云鞋：翘头 + 绣花鞋面
            ell((X, -0.150, 0.066), (0.026, 0.030, 0.030), V["yunyun"], {"shin"+S: 1}, 8, 5)
            ell((X, -0.085, 0.078), (0.036, 0.050, 0.014), V["yunyun"], {"shin"+S: 1}, 8, 4)
        elif V["shoe"] > 0xa0a0a0:                    # 运动鞋底
            box((X, -0.045, 0.012), (0.094, 0.232, 0.022), 0x8a8a8a, {"shin"+S: 1})

    # ── 颈与头 ──
    tube([(1.50, 0.044, 0.046), (1.40, 0.050, 0.052)], SK, w_neck, 10)
    hz = 1.602
    hr = []
    for j in range(9):
        ph = math.pi*(j+0.5)/9; cz = math.cos(ph); sn = math.sin(ph)
        jaw = 1.0 - 0.20*cl(-cz)**1.5                 # 下巴收窄
        hr.append((hz+0.124*cz, 0.097*sn*jaw, 0.108*sn*(1.0-0.08*cl(-cz)), 0, 0.012*cl(-cz)))
    tube(hr, SK, HEAD, 14)
    for sx in (-1, 1):
        ell((0.097*sx, 0.012, 1.60), (0.012, 0.020, 0.030), SK, HEAD, 6, 4)             # 耳
        ell((0.037*sx, -0.094, 1.617), (0.0145, 0.008, 0.0095), 0xf1ece2, HEAD, 8, 4)    # 眼白
        ell((0.037*sx, -0.099, 1.616), (0.0085, 0.006, 0.0085), 0x1a1614, HEAD, 6, 4)    # 瞳
        box((0.038*sx, -0.098, 1.640), (0.036, 0.010, 0.007), V["hair"], HEAD)           # 眉
    ell((0, -0.106, 1.588), (0.0125, 0.020, 0.026), SK, HEAD, 8, 5)                      # 鼻
    box((0, -0.097, 1.543), (0.040, 0.010, 0.007), 0x8c5a52, HEAD)                       # 嘴
    HC = V["hair"]
    ell((0, 0.024, 1.628), (0.103, 0.107, 0.112), HC, HEAD, 14, 7)                       # 头发
    if V.get("beard"):
        ell((0, -0.075, 1.505), (0.050, 0.034, 0.050), HC, HEAD, 8, 5)
        box((0, -0.098, 1.556), (0.058, 0.012, 0.012), HC, HEAD)
    if V.get("bun"):
        ell((0, 0.105, 1.60), (0.05, 0.045, 0.05), HC, HEAD, 8, 5)
    if V.get("hat") == "brim":
        hc = V["hatC"]
        tube([(1.69, 0.112, 0.118, 0, 0.012), (1.74, 0.106, 0.112, 0, 0.012), (1.772, 0.088, 0.094, 0, 0.012)], hc, HEAD, 14)
        tube([(1.700, 0.205, 0.215, 0, 0.012), (1.692, 0.215, 0.225, 0, 0.012), (1.682, 0.205, 0.215, 0, 0.012)], hc, HEAD, 16)
        tube([(1.712, 0.114, 0.120, 0, 0.012), (1.694, 0.115, 0.121, 0, 0.012)], 0x2e261c, HEAD, 14, caps=(False, False))
    if V.get("hat") == "wrap":                        # 包头帕：层层缠绕
        hc = V["hatC"]
        tube([(1.655, 0.108, 0.116, 0, 0.012), (1.672, 0.121, 0.129, 0, 0.012), (1.705, 0.126, 0.134, 0, 0.012),
              (1.74, 0.122, 0.130, 0, 0.012), (1.765, 0.104, 0.110, 0, 0.012), (1.772, 0.07, 0.074, 0, 0.012)], hc, HEAD, 14)
        band = V.get("hatBand", None)
        for zz in (1.688, 1.722, 1.752):
            dark = band if (band and zz == 1.688) else (((hc >> 1) & 0x7f7f7f) if hc < 0x808080 else (hc - 0x222222))
            rr = 0.1285 if zz < 1.70 else (0.1275 if zz < 1.74 else 0.117)
            tube([(zz+0.005 if not band or zz != 1.688 else zz+0.013, rr, rr+0.008, 0, 0.012), (zz-0.005, rr, rr+0.008, 0, 0.012)], dark, HEAD, 14, caps=(False, False))

    # ── 网格 ──
    me = bpy.data.meshes.new(VARIANT)
    me.from_pydata(verts, [], faces); me.update()
    for m in mats: me.materials.append(m)
    for p, mi in zip(me.polygons, fmat): p.material_index = mi
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    try: me.shade_smooth()
    except Exception:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(VARIANT, me); bpy.context.collection.objects.link(ob)

    # ── 骨架 ──
    ad = bpy.data.armatures.new("Armature"); arm = bpy.data.objects.new("Armature", ad)
    bpy.context.collection.objects.link(arm); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    e = ad.edit_bones
    def B(name, h, t, parent=None):
        b = e.new(name); b.head = h; b.tail = t
        if parent: b.parent = e[parent]
    B("root", (0, 0, 0), (0, 0, 0.1))
    B("hips", (0, 0, 0.86), (0, 0, 0.98), "root")
    B("spine", (0, 0, 0.98), (0, 0, 1.16), "hips")
    B("chest", (0, 0, 1.16), (0, 0, 1.40), "spine")
    B("head", (0, 0, 1.50), (0, 0, 1.70), "chest")
    for sd, S in ((-1, "L"), (1, "R")):
        x = 0.192*sd*slim
        B("upArm"+S, (x, 0, 1.33), (x, 0, 1.02), "chest")
        B("foreArm"+S, (x, 0, 1.02), (x, 0, 0.76), "upArm"+S)
        x2 = 0.088*sd
        B("thigh"+S, (x2, 0, 0.82), (x2, 0, 0.40), "hips")
        B("shin"+S, (x2, 0, 0.40), (x2, 0, 0.06), "thigh"+S)
    bpy.ops.object.mode_set(mode='OBJECT')
    names = set()
    for d in vw: names.update(d.keys())
    vgs = {n: ob.vertex_groups.new(name=n) for n in names}
    for i, d in enumerate(vw):
        for n, w in d.items(): vgs[n].add([i], w, 'REPLACE')
    mod = ob.modifiers.new("Arm", type='ARMATURE'); mod.object = arm
    ob.parent = arm

    path = os.path.join(OUT, VARIANT+".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_animations=False,
                              export_skins=True, export_morph=False, export_yup=True)
    print("EXPORTED", VARIANT, len(verts), "verts", len(faces), "faces", len(mats), "mats", os.path.getsize(path)//1024, "KB")

for name in (VARS.keys() if ARG == "all" else [ARG]):
    build(name)
