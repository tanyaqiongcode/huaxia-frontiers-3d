"""把"边缘行走 · 互动导读"打包成一个可以离线双击打开的 HTML 文件。

用法（在仓库根目录）：
    python3 tools/build_single_html.py [输出路径]

默认输出到仓库上一级目录：华夏边缘_边缘行走_单文件版.html
做法：把 three.js、GLTFLoader、地面贴图脚本直接内联；11 个 GLB 模型和月面贴图转成 data: URI；
返回主站、阅读版的相对链接改成线上地址。线上的 game/index.html 本身不改。
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


def inline_script(src_attr, rel):
    # 内联脚本里不能出现 </script>，转义一下
    code = read(rel).replace("</script", "<\\/script")
    replace_once('<script src="%s"></script>' % src_attr, "<script>\n%s\n</script>" % code)


inline_script("../assets/game-textures.js", "assets/game-textures.js")
inline_script("../assets/three.min.js", "assets/three.min.js")
inline_script("../assets/GLTFLoader.js", "assets/GLTFLoader.js")

models = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "assets", "models")) if f.endswith(".glb"))
model_map = ",".join('"%s":"%s"' % (m, data_uri("assets/models/%s.glb" % m, "model/gltf-binary")) for m in models)
# 模型数据放在 </head> 前，保证游戏脚本运行时已经存在
replace_once("</head>", "<script>window.__MODEL_DATA={%s};</script>\n</head>" % model_map)

# 让加载器优先读内联数据
replace_once("_gl.load('../assets/models/'+name+'.glb',", "_gl.load(window.__MODEL_DATA[name]||('../assets/models/'+name+'.glb'),")
replace_once("loader.load('../assets/models/diaolou.glb',", "loader.load(window.__MODEL_DATA.diaolou,")
replace_once("loader.load('../assets/models/qiang_house.glb',", "loader.load(window.__MODEL_DATA.qiang_house,")
replace_once("new THREE.TextureLoader().load('../assets/book/moon.jpg')", "new THREE.TextureLoader().load('%s')" % data_uri("assets/book/moon.jpg", "image/jpeg"))

# 返回主站、阅读版：改成线上地址（离线时点了会去网上）
html = re.sub(r'href="\.\./reading/"', 'href="%sreading/"' % SITE, html)
html = re.sub(r'href="\.\./"', 'href="%s"' % SITE, html)

left = [x for x in re.findall(r"""['"]\.\./[^'"]*['"]""", html) if x != "'../assets/models/'"]  # 后者只是内联数据缺失时的后备路径
assert not left, "还有没处理的相对路径：%s" % left

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("已生成", OUT, "%.2f MB" % (os.path.getsize(OUT) / 1048576), "，内联模型：", "、".join(models))
