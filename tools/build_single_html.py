"""把"边缘行走 · 互动导读"打包成一个可以离线双击打开的 HTML 文件。

用法（在仓库根目录）：
    python3 tools/build_single_html.py [输出路径]

默认输出到仓库上一级目录：华夏边缘_边缘行走_单文件版.html
做法：把 three.js、GLTFLoader 直接内联；11 个 GLB 模型、21 张 PBR 贴图和月面贴图转成 data: URI；
"主站、阅读版"两个按钮指向线上站点，除此之外不放任何站外链接。线上的 game/index.html 本身不改。
"""
import base64
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://tanyaqiongcode.github.io/huaxia-frontiers-3d/"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "华夏边缘_边缘行走_单文件版.html")


def read(rel, mode="r"):
    with open(os.path.join(ROOT, rel), mode, **({} if "b" in mode else {"encoding": "utf-8"})) as f:
        return f.read()


def data_uri(rel, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(read(rel, "rb")).decode())


html = read("game/index.html")


def replace_once(old, new):
    global html
    n = html.count(old)
    assert n == 1, "期望恰好出现一次：%r（实际 %d 次）" % (old[:60], n)
    html = html.replace(old, new)


LIBS = []


def inline_script(src_attr, rel):
    # 内联脚本里不能出现 </script>，转义一下
    code = read(rel).replace("</script", "<\\/script")
    LIBS.append(code)
    replace_once('<script src="%s"></script>' % src_attr, "<script>\n%s\n</script>" % code)


inline_script("../assets/three.min.js", "assets/three.min.js")
inline_script("../assets/GLTFLoader.js", "assets/GLTFLoader.js")

models = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "assets", "models")) if f.endswith(".glb"))
model_map = ",".join('"%s":"%s"' % (m, data_uri("assets/models/%s.glb" % m, "model/gltf-binary")) for m in models)
# PBR 贴图（assets/tex/*.jpg）同样转成 data: URI
texs = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "assets", "tex")) if f.endswith(".jpg"))
tex_map = ",".join('"%s":"%s"' % (t, data_uri("assets/tex/%s.jpg" % t, "image/jpeg")) for t in texs)
# 模型与贴图数据放在 </head> 前，保证游戏脚本运行时已经存在
replace_once("</head>", "<script>window.__MODEL_DATA={%s};window.__TEX={%s};</script>\n</head>" % (model_map, tex_map))

# 让加载器优先读内联数据
replace_once("_gl.load('../assets/models/'+name+'.glb',", "_gl.load(window.__MODEL_DATA[name]||('../assets/models/'+name+'.glb'),")
replace_once("loader.load('../assets/models/diaolou.glb',", "loader.load(window.__MODEL_DATA.diaolou,")
replace_once("loader.load('../assets/models/qiang_house.glb',", "loader.load(window.__MODEL_DATA.qiang_house,")
replace_once("new THREE.TextureLoader().load('../assets/book/moon.jpg')", "new THREE.TextureLoader().load('%s')" % data_uri("assets/book/moon.jpg", "image/jpeg"))

# "主站 / 阅读版"按钮保留，离线文件里没有这两页，所以指向线上站点；带网址的分享预览标签对本地文件没用，去掉
html = re.sub(r'href="\.\./reading/"', 'href="%sreading/"' % SITE, html)
html = re.sub(r'href="\.\./"', 'href="%s"' % SITE, html)
html = re.sub(r'<meta (property|name)="(og:url|og:image|twitter:image)"[^>]*>\n?', '', html)

left = [x for x in re.findall(r"""['"]\.\./[^'"]*['"]""", html) if x not in ("'../assets/models/'", "'../assets/tex/'")]  # 这两个只是内联数据缺失时的后备路径
assert not left, "还有没处理的相对路径：%s" % left
own = html
for code in LIBS:          # three.js、GLTFLoader 自带的注释不算
    own = own.replace(code, '')
ext = [u for u in re.findall(r'href=["\'](https?://[^"\']+)', own) if not u.startswith(SITE)]
assert not ext, "分享版里有站外链接：%s" % ext   # 只允许回到本站的"主站 / 阅读版"
assert 'github.com' not in own.lower(), "分享版里有 GitHub 仓库链接"

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("已生成", OUT, "%.2f MB" % (os.path.getsize(OUT) / 1048576), "，内联模型：", "、".join(models), "；贴图", len(texs), "张")
