# 华夏边缘 · Huaxia Frontier — 3D 主题站

王明珂《华夏边缘：历史记忆与族群认同》3D 沉浸式主题网站。

> "当我们在一张纸上画一个圆形时，事实上是它的'边缘'让它看起来像个圆形。"

**在线访问**：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/

## 两个版本 · Two editions

- **沉浸版 · Immersive edition**（3D 动态叙事，主站）：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/
- **阅读版 · Reading edition**（轻量阅读，无障碍优先）：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/reading/
- **边缘行走 · Interactive reading guide**（互动导读：拾得 17 件史料，每件对应全书一个概念，看边界移动；场景与讲述者为虚构）：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/game/

## 站点内容

| 区块 | 内容 |
|---|---|
| 首屏 | Three.js 实时粒子场景（青铜边缘环＋发光内核＋记忆碎片），可调氛围：粒子密度、雾、晨昏 |
| 概念八章 | 从"什么是中国人"到"边缘研究法"，自然志卡片式排版 |
| 图录 | 四张主题图 |
| 3D 造物记 | 从 0 逐块搭建延时视频、渲染图、可下载 Blender 工程 |
| 推荐语 · 作者与版本 · 影像 · 首译 | 梁文道/罗新/刘苏里/岱峻；1997→2020 版本谱系；经核验的讲座直链；首译工程进行中 |

## 交互

- 顶部命令条：声音 `S` · 暂停 `P` · 绢本浅色主题 `T` · 隐去界面 `H`
- 右下氛围面板：粒子疏密、雾气、晨昏光色
- 深色青铜 / 浅色绢本双主题

## 仓库结构

```
├── index.html               # 单页站点（样式与交互内联）
├── assets/three.min.js      # Three.js r128（本地化）
├── assets/models/*.glb      # 游戏模型（碉楼、石屋、长城、烽燧、遗址、树、牲畜；blender/game_models.py 生成）
├── assets/build.mp4 · render_01..03.png · plates/   # 造物记与图录
└── blender/build_complete.blend
```

## 复现 Blender 工程

```bash
blender --background --factory-startup --python build_scene.py
```

游戏模型（碉楼、石屋、长城、烽燧、河湟遗址、树、牲畜）：

```bash
blender --background --factory-startup --python blender/game_models.py
```

## 版权

站点为图书介绍与学术推广用途；推荐语版权归原作者；Blender 工程、渲染图、延时视频与主题图为本项目原创。

## Credits
Planet textures: [Solar System Scope](https://www.solarsystemscope.com/textures/) (CC BY 4.0) · Earth & Moon imagery: NASA (via three.js examples) · Built on [three.js](https://threejs.org) (MIT) · Infographics & SVG figures: the editorial team.

## Credits

- 材质纹理：[Poly Haven](https://polyhaven.com)（CC0）——forrest_ground_01 / rock_wall / brown_mud_dry / weathered_planks（512px 漫反射，assets/game-textures.js）
- three.js r128（MIT）· 行星贴图 NASA / Solar System Scope（CC BY 4.0）
- 互动导读里的碉楼、羌寨平顶石屋、汉代夯土长城墙段与烽燧（夯层夹芦苇，依河西汉塞形制）、河湟齐家文化半地穴房址与彩陶罐、冷杉／白杨／核桃、绵羊／黄牛／马：均由 Blender 脚本建模（`blender/game_models.py`，本项目原创），导出为 `assets/models/*.glb`，由 three.js GLTFLoader（r128，MIT）加载
- 月面贴图：NASA（经 three.js examples）
- 互动导读的写实材质：Poly Haven（CC0）——aerial_grass_rock（地面）、stone_wall（碉楼石墙）、brown_mud_dry（夯土、黄土）、weathered_planks（木作）、white_plaster_02（北川白墙）、asphalt_02（国道）、pine_bark（树皮），1K 颜色／法线／粗糙度图，存于 `assets/tex/`
- 模型的环境光遮蔽由 Blender Cycles 烘焙进顶点色；树冠为叶片卡，叶片与针叶贴图由程序绘制
