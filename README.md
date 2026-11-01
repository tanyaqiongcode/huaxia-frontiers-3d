# 华夏边缘 · The Frontiers of Huaxia — 3D 主题站

王明珂《华夏边缘：历史记忆与族群认同》3D 沉浸式主题网站。

> "当我们在一张纸上画一个圆形时，事实上是它的'边缘'让它看起来像个圆形。"

**在线访问**：https://tanyaqiongcode.github.io/huaxia-frontiers-3d/

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
├── assets/build.mp4 · render_01..03.png · plates/   # 造物记与图录
└── blender/build_complete.blend
```

## 复现 Blender 工程

```bash
blender --background --factory-startup --python build_scene.py
```

## 版权

站点为图书介绍与学术推广用途；推荐语版权归原作者；Blender 工程、渲染图、延时视频与主题图为本项目原创。
