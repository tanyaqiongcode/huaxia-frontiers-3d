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
                     hat="brim", hatC=0x80705a, scarf=0xa33b2e, pack=0x3f3226, belt=0x2e261c, pockets=True,
                     hiking=(0x6a4a30, 0x1c1814, 0xd9a441)),     # 高帮登山靴
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
 # —— 可选的女性行走者，与路上遇到的男女老少 ——
 # 女行走者三套装束，配色依据 2026 秋冬户外与 WGSN/Coloro 2027 春夏关键色：
 # 一、鼠尾草绿冲锋衣 + 暖灰褐软壳裤 + 能量橙点缀；二、灰粉冲锋衣 + 巧克力棕裤 + 亮蓝点缀；三、亮蓝（2027 年度色）冲锋衣 + 炭灰裤 + 能量橙点缀
 "fig_player_f": dict(skin=0xdcb394, hair=0x231b17, top=0x94714f, legs=0x47443a, shoe=0x5c5a52,   # 公路片里的卡其棕夹克 + 水洗灰牛仔裤，与男行走者同款剪裁，米黄背包
                     hat="baseball", hatC=0x94714f, accent=0xf07a2e, pack=0xd9c7a0, belt=0x3a2a1e, pockets=True, scarf=0xa3b899,
                     slim=True, ponytailLong=True, hiking=(0x6e6a5e, 0xece6da, 0xf07a2e)),
 "fig_player_f2": dict(skin=0xdcb394, hair=0x231b17, top=0xd8a2a0, legs=0x4e3a30, shoe=0x4e3a30,
                     yoke=0xf1e9de, collar=True, zipper=0x2f7fd8, hat="baseball", hatC=0xf1e9de, accent=0x2f7fd8,
                     pack=0x5e4638, packStyle="tech", slim=True, ponytailLong=True,
                     hiking=(0xb9a796, 0xf1e9de, 0x2f7fd8)),
 "fig_player_f3": dict(skin=0xdcb394, hair=0x231b17, top=0x2f73d8, legs=0x3b3e44, shoe=0x3b3e44,
                     yoke=0x1e2a44, collar=True, zipper=0xf07a2e, hat="baseball", hatC=0xece6da, accent=0xf07a2e,
                     pack=0xece6da, packStyle="tech", slim=True, ponytailLong=True,
                     hiking=(0x55595f, 0xece6da, 0xf07a2e)),
 "fig_man":     dict(skin=0xc99b78, hair=0x17161a, top=0x39445a, legs=0x2a3044, shoe=0x2b2b33,
                     robe=0.46, vest=0x8a7355, fleece=0xd9cfb8, sash=0x2f5f8a, hat="wrap", hatC=0xe6e0d2,
                     legwrap=0xd8d2c2, yunyun=0x2f5f8a, trim=(0xd8d2c2,)),
 "fig_woman":   dict(skin=0xd8ad8c, hair=0x151515, top=0x9a3340, legs=0x26262c, shoe=0x7a2d2a,
                     robe=0.28, sash=0xd9a441, apron=0x23232b, hat="wrap", hatC=0x23232b, hatBand=0xd9a441,
                     yunyun=0xd9a441, trim=(0xd9a441, 0x2f5f8a), braids=True, slim=True),
 "fig_granny":  dict(skin=0xc49873, hair=0xb4b4b4, top=0x2b2f40, legs=0x22222a, shoe=0x2b2b33,
                     robe=0.24, sash=0x4a3b5a, apron=0x2a3350, hat="wrap", hatC=0xe6e0d2,
                     yunyun=0x8c2f2a, trim=(0x6a6f86,), bun=True, slim=True),
 "fig_oldman":  dict(skin=0xc49873, hair=0xb4b4b4, top=0x3a4250, legs=0x30333a, shoe=0x2a241e,
                     hat="wrap", hatC=0x2c2e36, beard=True, collar=True, belt=0x2e261c),
 # 河湟牧人：藏式长袍（深绛色，镶边，系腰带，毡帽，长靴）
 "fig_herder":  dict(skin=0xb9875f, hair=0x17161a, top=0x5a2a28, legs=0x2e2622, shoe=0x241a14,
                     robe=0.30, sash=0xd9a441, vest=0x5a2a28, fleece=0xcfc4a8, hat="brim", hatC=0x3a3028,
                     trim=(0xd9a441, 0x2f5f8a), legwrap=0x241a14),
 # 长城外牧人：北方草原的长袍（蓝袍、橙色腰带、高靴）
 "fig_mongol":  dict(skin=0xc08f68, hair=0x17161a, top=0x2f4f8a, legs=0x2a2a30, shoe=0x241a14,
                     robe=0.36, sash=0xd98a2f, hat="wrap", hatC=0x6e2a26, trim=(0xd98a2f,), legwrap=0x241a14),
 # 现代羌寨的年轻女子：日常便装，围一条羌绣围腰
 "fig_woman_m": dict(skin=0xd8ad8c, hair=0x151515, top=0xc0667a, legs=0x2f3a52, shoe=0xe2e0d8,
                     zipper=0xe6e0d2, collar=True, apron=0x23232b, ponytail=True, slim=True),
 "fig_boy":     dict(skin=0xd8ad8c, hair=0x141416, top=0xb5482f, legs=0x2c3038, shoe=0xd8d8d8,
                     zipper=0xe6e0d2, collar=True, child=True),
 "fig_girl":    dict(skin=0xdab192, hair=0x151515, top=0xb5506a, legs=0x26262c, shoe=0x7a2d2a,
                     robe=0.34, sash=0xd9a441, apron=0x2f5f8a, yunyun=0xd9a441, trim=(0xe6e0d2,),
                     braids=True, slim=True, child=True),
}

def build(VARIANT):
    V = VARS[VARIANT]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats, mat_ix = [], {}
    # 材质按"质地"命名（cloth 布、wool 皮毛、fleece 翻毛、leather 皮革、trim 绣边、skin、hair、eye、lip、metal、rubber），游戏里据此贴不同的纹理
    KIND = {0xf1ece2: "eye", 0x3a2414: "eye", 0x0c0a0a: "eye", 0xb5544e: "lip", 0x9a5c52: "lip",
            0x2e261c: "leather", 0x3a2f22: "leather", 0x4a3520: "leather", 0x2a2018: "leather", 0xb89a5a: "metal",
            0xb5382f: "trim", 0xd9a441: "trim"}
    for k_, kind_ in (("shoe", "leather"), ("belt", "leather"), ("pack", "leather"), ("fleece", "fleece"), ("zipper", "metal"),
                      ("yunyun", "trim"), ("hatBand", "trim")):
        if V.get(k_) is not None: KIND[V[k_]] = kind_
    if V.get("vest") is not None: KIND[V["vest"]] = "wool" if V.get("fleece") else ("leather" if V.get("lamellar") else "cloth")
    for tc_ in V.get("trim", ()): KIND[tc_] = "trim"
    if V.get("hiking"): KIND[V["hiking"][0]] = "leather"; KIND[V["hiking"][1]] = "rubber"; KIND[V["hiking"][2]] = "trim"
    KIND[V["top"]] = "cloth"; KIND[V["skin"]] = "skin"; KIND[V["hair"]] = "hair"
    def M(hexc, rough=0.9):
        if hexc not in mat_ix:
            m = bpy.data.materials.new("%s_%06x" % (KIND.get(hexc, "cloth"), hexc)); m.use_nodes = True
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = lin(hexc)
            b.inputs["Roughness"].default_value = rough
            b.inputs["Metallic"].default_value = 0.0
            mat_ix[hexc] = len(mats); mats.append(m)
        return mat_ix[hexc]

    verts, faces, fmat, vw, uvs = [], [], [], [], []
    def addv(p, w, uv=(0.0, 0.0)):
        uvs.append(uv)
        ww = w(*p) if callable(w) else w
        s = sum(ww.values()) or 1.0
        verts.append(p); vw.append({k: v/s for k, v in ww.items() if v > 1e-4}); return len(verts)-1

    def tube(rings, mat, w, seg=12, at=(0.0, 0.0), caps=(True, True), arc=None):
        """rings: [(z, rx, ry[, dx, dy])]，水平椭圆环自下而上或自上而下均可"""
        mi = M(mat) if not isinstance(mat, tuple) else M(*mat)
        n = seg+1                                    # 接缝处多放一列顶点，贴图坐标才不会倒卷
        ids = []; vv = 0.0; prev = None
        for r in rings:
            z, rx, ry = r[0], r[1], r[2]
            cx = at[0] + (r[3] if len(r) > 3 else 0.0); cy = at[1] + (r[4] if len(r) > 4 else 0.0)
            if prev is not None: vv += math.hypot(z-prev[0], (rx+ry)/2-prev[1])
            prev = (z, (rx+ry)/2)
            row = []
            for i in range(n):
                a = (2*math.pi*i/seg) if arc is None else (arc[0] + (arc[1]-arc[0])*i/seg)
                row.append(addv((cx+math.cos(a)*rx, cy+math.sin(a)*ry, z), w, (i/seg, vv)))
            ids.append(row)
        for j in range(len(ids)-1):
            for i in range(seg):
                faces.append([ids[j][i], ids[j][i+1], ids[j+1][i+1], ids[j+1][i]]); fmat.append(mi)
        if arc is None:
            if caps[0]: faces.append(list(ids[0][:seg])); fmat.append(mi)
            if caps[1]: faces.append(list(reversed(ids[-1][:seg]))); fmat.append(mi)

    def ell(c, r, mat, w, seg=12, rings=8):
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
    tube(rings, TOP, w_torso, 20)
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
    if V.get("yoke"):                                 # 冲锋衣肩部拼色
        tube([(1.400, 0.098, 0.077), (1.372, 0.130*slim, 0.090), (1.345, 0.150*slim, 0.096)], V["yoke"], w_torso, 20, caps=(False, False))
        for sd in (-1, 1):
            tube([(1.354, 0.028, 0.032), (1.337, 0.048, 0.054), (1.300, 0.055, 0.060), (1.262, 0.055, 0.059)], V["yoke"], {"upArm"+("L" if sd < 0 else "R"): 1}, 14, at=(0.192*sd*slim, 0))
    if V.get("pack") and V.get("packStyle") == "tech":   # 轻量徒步包：流线包身、细肩带、胸带
        pc = V["pack"]; ac = V.get("accent", pc)
        ell((0, 0.150, 1.170), (0.118, 0.072, 0.200), pc, w_torso, 14, 9)
        ell((0, 0.205, 1.130), (0.070, 0.022, 0.090), ac, w_torso, 10, 5)
        for sx in (-1, 1):
            box((0.085*sx, -0.106, 1.215), (0.030, 0.010, 0.300), pc, {"chest": 1})
            box((0.085*sx, 0.010, 1.372), (0.030, 0.200, 0.010), pc, {"chest": 1})
        box((0, -0.110, 1.255), (0.170, 0.008, 0.014), pc, {"chest": 1})
    elif V.get("pack"):
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
              (0.92, 0.043, 0.045), (0.80, 0.040, 0.041)], TOP, w_arm(S), 14, at=(X, 0))
        for k, tc in enumerate(V.get("trim", ())):   # 袖口绣边
            tube([(0.835-0.028*k, 0.0425, 0.0435), (0.808-0.028*k, 0.0425, 0.0435)], tc, w_arm(S), 10, at=(X, 0), caps=(False, False))
        tube([(0.805, 0.030, 0.032), (0.775, 0.028, 0.030)], SK, {"foreArm"+S: 1}, 8, at=(X, 0))
        ell((X, -0.004, 0.742), (0.024, 0.036, 0.038), SK, {"foreArm"+S: 1}, 8, 6)        # 手掌
        for k in range(4):                                                              # 四指
            ell((X, -0.029+0.0165*k, 0.693-0.004*abs(k-1.5)), (0.0088, 0.0082, 0.029), SK, {"foreArm"+S: 1}, 6, 5)
        ell((X-0.022*sd, -0.03, 0.74), (0.012, 0.014, 0.03), SK, {"foreArm"+S: 1}, 6, 4)   # 拇指
    # ── 腿 ──
    for sd, S in ((-1, "L"), (1, "R")):
        X = 0.088*sd
        tube([(0.86, 0.080, 0.092), (0.70, 0.078, 0.086), (0.52, 0.064, 0.070), (0.41, 0.057, 0.062, 0, -0.004),
              (0.30, 0.056, 0.060, 0, 0.008), (0.16, 0.046, 0.049), (0.07, 0.042, 0.046)], LEG, w_leg(S), 14, at=(X, 0))
        if V.get("legwrap"):                          # 绑腿 / 行縢
            tube([(0.375, 0.060, 0.065), (0.30, 0.061, 0.066, 0, 0.008), (0.17, 0.051, 0.054), (0.085, 0.047, 0.051)],
                 V["legwrap"], {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
            for zz in (0.33, 0.25, 0.17):
                tube([(zz+0.006, 0.062, 0.067, 0, 0.006), (zz-0.006, 0.062, 0.067, 0, 0.006)], 0x8a8474, {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
        if V.get("hiking"):                           # 行走者的鞋：厚底、高帮、亮色鞋带
            up, sole, lace = V["hiking"]
            ell((X, -0.048, 0.056), (0.054, 0.124, 0.046), up, {"shin"+S: 1}, 10, 6)
            box((X, -0.048, 0.014), (0.104, 0.250, 0.028), sole, {"shin"+S: 1})
            tube([(0.150, 0.050, 0.054), (0.075, 0.052, 0.058)], up, {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
            tube([(0.156, 0.052, 0.056), (0.144, 0.052, 0.056)], sole, {"shin"+S: 1}, 10, at=(X, 0), caps=(False, False))
            for zz, yy in ((0.088, -0.105), (0.098, -0.082), (0.106, -0.060)):
                box((X, yy, zz), (0.05, 0.012, 0.008), lace, {"shin"+S: 1})
        else:
            ell((X, -0.045, 0.046), (0.050, 0.118, 0.047), V["shoe"], {"shin"+S: 1}, 10, 6)
        if V.get("yunyun"):                           # 云云鞋：翘头 + 绣花鞋面
            ell((X, -0.150, 0.066), (0.026, 0.030, 0.030), V["yunyun"], {"shin"+S: 1}, 8, 5)
            ell((X, -0.085, 0.078), (0.036, 0.050, 0.014), V["yunyun"], {"shin"+S: 1}, 8, 4)
        elif V["shoe"] > 0xa0a0a0 and not V.get("hiking"):                    # 运动鞋底
            box((X, -0.045, 0.012), (0.094, 0.232, 0.022), 0x8a8a8a, {"shin"+S: 1})

    # ── 颈与头 ──
    tube([(1.50, 0.044, 0.046), (1.40, 0.050, 0.052)], SK, w_neck, 10)
    hz = 1.602
    hr = []
    for j in range(13):
        ph = math.pi*(j+0.5)/13; cz = math.cos(ph); sn = math.sin(ph)
        jaw = 1.0 - 0.20*cl(-cz)**1.5                 # 下巴收窄
        hr.append((hz+0.124*cz, 0.097*sn*jaw, 0.108*sn*(1.0-0.08*cl(-cz)), 0, 0.012*cl(-cz)))
    tube(hr, SK, HEAD, 28)
    old = bool(V.get("beard")) or ((V["hair"] >> 16) & 255) > 0x90
    fem = bool(V.get("slim")); kid = bool(V.get("child"))
    LIP = 0x9a655c if old else (0xb5544e if fem else 0x9a5c52)
    KIND[LIP] = "lip"
    for sx in (-1, 1):
        ell((0.097*sx, 0.012, 1.60), (0.012, 0.020, 0.030), SK, HEAD, 6, 4)              # 耳
        ell((0.0375*sx, -0.1005, 1.6165), (0.0178, 0.0084, 0.0116), 0xf1ece2, HEAD, 10, 5)   # 眼白
        ell((0.0365*sx, -0.1058, 1.6160), (0.0088, 0.005, 0.0092), 0x3a2414, HEAD, 10, 4)  # 虹膜
        ell((0.0365*sx, -0.1092, 1.6160), (0.0042, 0.003, 0.0044), 0x0c0a0a, HEAD, 8, 3)
        ell((0.0345*sx+0.002, -0.1112, 1.6190), (0.0014, 0.001, 0.0014), 0xf1ece2, HEAD, 6, 3)   # 眼神光  # 瞳孔
        ell((0.0375*sx, -0.1022, 1.6290), (0.0195, 0.0090, 0.0052), SK, HEAD, 10, 4)        # 上眼睑
        ell((0.0375*sx, -0.1012, 1.6050), (0.0180, 0.0075, 0.0036), SK, HEAD, 10, 3)        # 下眼睑
        ell((0.0400*sx, -0.1025, 1.6475), (0.0210, 0.0060, 0.0034 if not fem else 0.0026), V["hair"], HEAD, 8, 3)  # 眉
        ell((0.0105*sx, -0.1020, 1.5810), (0.0062, 0.0075, 0.0056), SK, HEAD, 6, 4)        # 鼻翼
    ell((0, -0.1045, 1.6120), (0.0070, 0.0090, 0.0240), SK, HEAD, 8, 5)                   # 鼻梁
    ell((0, -0.1085, 1.5865), (0.0100, 0.0130, 0.0105), SK, HEAD, 8, 5)                   # 鼻尖
    ell((0, -0.0885, 1.5480), (0.0190 if not kid else 0.016, 0.0062, 0.0043), LIP, HEAD, 8, 3)   # 上唇
    ell((0, -0.0868, 1.5405), (0.0160 if not kid else 0.014, 0.0066, 0.0052), LIP, HEAD, 8, 3)   # 下唇
    if old:                                                                               # 浅浅的抬头纹
        WR = ((((V["skin"] >> 16) & 255)*7//8) << 16) | ((((V["skin"] >> 8) & 255)*7//8) << 8) | ((V["skin"] & 255)*7//8)
        KIND[WR] = "skin"
        for zz, ww in ((1.664, 0.056), (1.6755, 0.044)):
            ell((0, -0.0925+0.5*(zz-1.664), zz), (ww/2, 0.003, 0.0010), WR, HEAD, 8, 3)
    HC = V["hair"]
    ell((0, 0.024, 1.628), (0.103, 0.107, 0.112), HC, HEAD, 14, 7)                       # 头发
    if not V.get("hat"):
        ell((0, -0.016, 1.713), (0.093, 0.084, 0.034), HC, HEAD, 12, 5)                  # 额前的发际
    if V.get("beard"):
        for sx in (-1, 1):
            ell((0.016*sx, -0.0935, 1.5575), (0.0170, 0.0060, 0.0052), HC, HEAD, 8, 4)      # 八字胡
            ell((0.034*sx, -0.0860, 1.5490), (0.0090, 0.0050, 0.0080), HC, HEAD, 6, 4)
            ell((0.030*sx, -0.0760, 1.5080), (0.0180, 0.0080, 0.0170), HC, HEAD, 8, 4)      # 贴着下颌的短须
        tube([(1.530, 0.0300, 0.0130, 0, -0.0800), (1.505, 0.0340, 0.0200, 0, -0.0760), (1.470, 0.0270, 0.0190, 0, -0.0760),
              (1.430, 0.0170, 0.0130, 0, -0.0790), (1.395, 0.0060, 0.0050, 0, -0.0820)], HC, HEAD, 10)   # 山羊须，向下收尖
    if V.get("ponytailLong"):                         # 从帽后开口穿出的长马尾 + 两鬓垂下的碎发
        ell((0, 0.046, 1.570), (0.101, 0.080, 0.096), HC, HEAD, 18, 8)                   # 后脑和颈后的头发
        ell((0, 0.104, 1.640), (0.028, 0.024, 0.030), HC, HEAD, 8, 5)
        tube([(1.640, 0.026, 0.024, 0, 0.118), (1.600, 0.030, 0.026, 0, 0.132), (1.540, 0.031, 0.026, 0, 0.140),
              (1.470, 0.027, 0.022, 0, 0.140), (1.400, 0.020, 0.016, 0, 0.134), (1.350, 0.008, 0.006, 0, 0.126)], HC, HEAD, 12)
    if V.get("ponytail"):                             # 低马尾
        ell((0, 0.105, 1.53), (0.034, 0.036, 0.075), HC, HEAD, 8, 5)
        ell((0, 0.115, 1.42), (0.028, 0.030, 0.085), HC, HEAD, 8, 5)
    if V.get("braids"):                               # 两条辫子
        for sx in (-1, 1):
            ell((0.075*sx, 0.055, 1.50), (0.024, 0.026, 0.07), HC, HEAD, 6, 5)
            ell((0.082*sx, 0.035, 1.39), (0.020, 0.022, 0.07), HC, HEAD, 6, 5)
            ell((0.082*sx, 0.030, 1.315), (0.022, 0.022, 0.018), 0xb5382f, HEAD, 6, 3)
    if V.get("bun"):
        ell((0, 0.105, 1.60), (0.05, 0.045, 0.05), HC, HEAD, 8, 5)
    if V.get("hat") == "baseball":                    # 棒球帽：六片拼的圆冠、顶扣、向前下弯的帽檐、后面的开口露出马尾
        hc = V["hatC"]
        tube([(1.664, 0.105, 0.113, 0, 0.010), (1.690, 0.106, 0.114, 0, 0.010), (1.722, 0.100, 0.108, 0, 0.008),
              (1.748, 0.084, 0.091, 0, 0.006), (1.766, 0.056, 0.061, 0, 0.004), (1.774, 0.020, 0.022, 0, 0.003)], hc, HEAD, 24)
        for k in range(6):                                                            # 拼缝
            a6 = k*math.pi/3
            box((0.078*math.cos(a6), 0.010+0.084*math.sin(a6), 1.722), (0.004, 0.004, 0.090), V.get("accent", hc), HEAD) if False else None
        ell((0, 0.004, 1.776), (0.011, 0.011, 0.006), hc, HEAD, 8, 3)                 # 顶扣
        tube([(1.674, 0.082, 0.050, 0, -0.140), (1.668, 0.088, 0.060, 0, -0.152), (1.658, 0.084, 0.058, 0, -0.160)], hc, HEAD, 18)   # 帽檐
        tube([(1.6705, 0.076, 0.012, 0, -0.105), (1.6655, 0.076, 0.012, 0, -0.105)], V.get("accent", hc), HEAD, 14)            # 帽檐下的色条
    if V.get("hat") == "cap":                         # 运动帽：贴头的帽冠 + 前檐
        hc = V["hatC"]
        tube([(1.668, 0.106, 0.114, 0, 0.012), (1.700, 0.105, 0.113, 0, 0.012), (1.730, 0.094, 0.102, 0, 0.012),
              (1.750, 0.070, 0.076, 0, 0.012), (1.760, 0.030, 0.034, 0, 0.012)], hc, HEAD, 20)
        tube([(1.676, 0.074, 0.072, 0, -0.118), (1.670, 0.076, 0.074, 0, -0.120), (1.664, 0.074, 0.072, 0, -0.118)], hc, HEAD, 16)
        ell((0, 0.012, 1.762), (0.010, 0.010, 0.004), V.get("accent", hc), HEAD, 8, 3)
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

    if V.get("child"):                                # 孩子：头相对大一些（整体缩小在游戏里做）
        for i, d in enumerate(vw):
            if len(d) == 1 and "head" in d:
                x, y, z = verts[i]; verts[i] = (x*1.22, y*1.22, 1.47+(z-1.47)*1.22)
    # ── 网格 ──
    me = bpy.data.meshes.new(VARIANT)
    me.from_pydata(verts, [], faces); me.update()
    for m in mats: me.materials.append(m)
    for p, mi in zip(me.polygons, fmat): p.material_index = mi
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    uvl = me.uv_layers.new(name="UVMap")
    for lp in me.loops: uvl.data[lp.index].uv = uvs[lp.vertex_index]
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
