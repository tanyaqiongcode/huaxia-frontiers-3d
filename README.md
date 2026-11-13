# 华夏边缘 · Huaxia Frontiers

为王明珂《华夏边缘：历史记忆与族群认同》而建的一座 3D 主题站。

> "当我们在一张纸上画一个圆形时，事实上是它的'边缘'让它看起来像个圆形。"

一本书讲的是边界如何被画出、被记住、被遗忘；这座站想做的，是让读者站到那条线上，看它在脚下移动。

**在线访问**：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/

## 三种进入方式 · Three ways in

- **沉浸版 · Immersive edition**——青铜之环、发光的内核与漂浮的记忆碎片，在动态的星野里读完全书的骨架：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/
- **阅读版 · Reading edition**——去掉一切动效，只留文字与图，适合安静地读，也照顾读屏与弱网：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/reading/
- **边缘行走 · Interactive reading guide**——走过岷江河谷、河湟遗址、长城、国道边的羌寨与北川，听五段讲述，拾起十七件史料，每一处换得一张读书卡。场景与讲述者均为虚构，书中观点以原著为准：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/game/

## 站里有什么

| 区块 | 内容 |
|---|---|
| 首屏 | 一枚青铜边缘环，环抱发光的内核，记忆碎片在四周缓缓流转；粒子疏密、雾气与晨昏光色都可以随手调节 |
| 概念八章 | 从"什么是中国人"一路走到"边缘研究法"，以自然志卡片的样子排开 |
| 图录 | 四张主题图 |
| 3D 造物记 | 一段从空白场景开始、一块一块搭起来的延时影像，附渲染图与可下载的 Blender 文件 |
| 推荐语 · 作者与版本 · 影像 · 首译 | 梁文道、罗新、刘苏里、岱峻的推荐；1997 到 2020 年的版本流变；经核验的讲座影像；首译项目正在进行，这部书正走向汉语之外的读者 |

## 怎么看

- 顶部命令条：声音 `S` · 暂停 `P` · 绢本浅色 `T` · 隐去界面 `H`
- 右下氛围面板：粒子疏密、雾气、晨昏光色
- 两种底色：深色青铜，浅色绢本

## 仓库里有什么

```
├── index.html               # 沉浸版（单页，样式与交互内联）
├── reading/index.html       # 阅读版
├── game/index.html          # 边缘行走 · 互动导读
├── assets/three.min.js      # three.js r128（本地化）
├── assets/models/*.glb      # 导读里的碉楼、石屋、长城、烽燧、遗址、树与牲畜（由 blender/game_models.py 生成）
├── assets/tex/              # 写实材质
├── assets/build.mp4 · render_01..03.png · plates/   # 造物记与图录
└── blender/build_complete.blend
```

## 重新搭一遍

首页的 3D 场景：用 Blender 直接打开 `blender/build_complete.blend`。

导读里的模型（碉楼、石屋、长城、烽燧、河湟遗址、尔玛人家、树、牲畜）：

```bash
blender --background --factory-startup --python blender/game_models.py
```

## 版权

本站用于图书介绍与学术推广。推荐语的版权归原作者；Blender 文件、渲染图、延时影像与主题图为本项目原创。

首页时间轴里的四幅地图（`assets/book/svg/fig-104.svg`、`transparent/fig-099.svg`、`fig-113.svg`、`fig-127.svg`）依据原书第 104、99、113、127 页的插图重绘，并非本项目原创；版权归原书作者与出版方，仅用于图书介绍。

## 致谢 · Credits

- three.js r128（MIT）；行星贴图来自 [Solar System Scope](https://www.solarsystemscope.com/textures/)（CC BY 4.0）与 NASA；月面贴图来自 NASA（经 three.js examples）
- 互动导读里的碉楼、羌寨平顶石屋、汉代夯土长城与烽燧（夯层夹芦苇，依河西汉塞形制）、河湟齐家文化半地穴房址与彩陶罐、冷杉／白杨／核桃、绵羊／黄牛／马、北川"尔玛人家"碉房（石屋连小碉，供白石，挂羌红）：均以 Blender 脚本建模（`blender/game_models.py`，本项目原创），导出为 `assets/models/*.glb`，由 three.js GLTFLoader（r128，MIT）载入
- 写实材质来自 [Poly Haven](https://polyhaven.com)（CC0）：aerial_grass_rock（地面）、stone_wall（碉楼石墙）、brown_mud_dry（夯土、黄土）、weathered_planks（木作）、white_plaster_02（北川白墙）、asphalt_02（国道）、pine_bark（树皮），1K 颜色、法线、粗糙度贴图，存于 `assets/tex/`
- 模型的环境光遮蔽由 Blender Cycles 烘焙进顶点色；树冠为叶片卡，叶片与针叶贴图由程序绘制
- 人物与装束：Blender 脚本建模（`blender/npc_figure.py`，本项目原创，共 19 个骨骼人物（动作由游戏代码逐帧驱动，GLB 不含内嵌动画）），服饰参照岷江上游羌族与河湟民族志通例（包头帕、长衫、羊皮褂、绑腿、云云鞋）；人物均为虚构
- 动物与地景模型：`blender/animals.py` 与 `blender/game_models.py`（本项目原创）
- 重新生成模型：`blender --background --factory-startup --python blender/npc_figure.py -- all`（变体见脚本内 VARS）
- 单文件分享版由 `tools/build_single_html.py` 打包（内联 three.js、GLTFLoader、全部模型与贴图）；历史版本按日期存档（如 `华夏边缘_边缘行走_单文件版_20261109_优化前.html`）
- 信息图：编辑组 · Infographics: the editorial team
- 时间轴地图：据原书第 99、104、113、127 页插图重绘，© 原作者与出版方 · Timeline maps redrawn from figures in the original book, © the author and publisher
