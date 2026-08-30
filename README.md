# Snowline Home 3D

一个以“巫师女孩的雪山旅程”为叙事线索的交互式 3D 个人主页。

玩家会沿着星光雪线攀上山顶，乘坐缆车越过群峰，在月光牧场与小羊相遇，最后抵达篝火与星空下的终点。作品把个人主页的信息结构融入一段可探索的微型冒险，让“作品、关于、经历和联系”不再只是静态栏目，而是旅程中的章节与目的地。

[在线体验](https://riyata.github.io/personal-home-3d01/) · [GitHub Pages](https://riyata.github.io/personal-home-3d01/)

项目基于 React、Three.js、React Three Fiber 和 Drei 开发，使用 Blender 制作并拆分低多边形 GLB 模型，通过 Three.js 状态机驱动场景切换、角色移动、缆车旅程和轻量姿态动画。

## 模块地图

| 模块 | 内容 | 位置 | 状态 |
| --- | --- | --- | --- |
| 雪线攀登 | 路线移动、星光节点与山顶检查点 | [`src/App.jsx`](src/App.jsx) | 已整合 |
| 山顶缆车 | 乘车互动、越岭动画与镜头跟随 | [`src/App.jsx`](src/App.jsx) | 已整合 |
| 月光牧场 | 自由移动、寻找小羊与喂草互动 | [`src/App.jsx`](src/App.jsx) | 已整合 |
| 星火营地 | 篝火、星空与旅程终幕 | [`src/App.jsx`](src/App.jsx) | 已整合 |
| 3D 模型资产 | 环境、角色、缆车、小羊与营地模型 | [`public/models`](public/models) | 已整合 |
| 序章与分镜 | 开场单页、图片故事与十二格分镜 | [独立原型仓库](https://github.com/RIYATA/prologue-storyboard) | 独立原型 |
| 作品与个人信息 | 作品、关于、经历和联系方式 | — | 规划中 |

功能模块与版本历史分开管理：模块按功能持续演进，完整版本使用 Git 标签固定，避免复制多份项目文件。

## 版本历史

| 版本 | 内容 | 固定源码 | 在线体验 |
| --- | --- | --- | --- |
| `v0.1.0` 初始版本 | 完成雪线攀登、缆车、牧场、营地和基础 3D 角色互动 | [查看 v0.1.0](https://github.com/RIYATA/personal-home-3d01/tree/v0.1.0) | [打开网站](https://riyata.github.io/personal-home-3d01/) |

> Git 标签中的源码不会随后续开发改变；在线网站默认展示 `main` 分支的最新版本。

## 项目截图

### 巫师女孩

<p align="center">
  <img src="docs/images/witch-girl-character.png" width="520" alt="低多边形风格的蓝帽巫师女孩角色" />
</p>

蓝色尖帽、星星法杖与金色披风构成主角的核心视觉识别。角色采用低多边形造型，并预留手脚节点供网页端控制攀登、移动和互动姿态。

### 雪线世界

![由雪山、缆车与月光牧场组成的低多边形雪线世界](docs/images/snowline-world.png)

场景由雪山攀登路线、山顶缆车和火山口牧场串联而成。冷蓝色雪峰与暖色角色、花草和缆车形成对比，共同构成带有童话感的夜间冒险世界。

## 运行

```bash
npm install
npm run dev
```

## 操作

- `↑`：沿路线向上攀登
- `↓`：沿路线后退
- `←` / `→`：在登山路线两侧移动
- `Enter` / `Space`：乘坐缆车、给羊喂草
- 移动端：使用右下角触控方向键和互动键

## 当前流程

1. 沿雪线爬到山顶。
2. 按 `Enter` 乘坐缆车。
3. 到达牧场后按 `Enter` 给羊喂草。
4. 场景自动切换到夜晚篝火和星空。

## 节点图标

底部选关栏预留了五个图标插槽：

- `data-icon-slot="base"`：山脚
- `data-icon-slot="summit"`：山顶
- `data-icon-slot="cable"`：缆车
- `data-icon-slot="meadow"`：牧场
- `data-icon-slot="camp"`：篝火

将对应 `.checkpoint-icon` 内的编号占位替换为 SVG 或图片即可，节点跳转逻辑无需修改。

## 模型资产

Blender 源文件和导出脚本位于 `blender/`：

- `blender/build_web_models.py`：按参考图生成低多边形模型并导出 GLB。
- `blender/snowline_web_models.blend`：可打开继续编辑的 Blender 场景。
- `blender/snowline_web_models_preview.png`：Blender 预览图。

网页加载的模型位于 `public/models/`：

- `environment.glb`：雪山、云、路线、山顶平台和缆绳。
- `meadow.glb`：火山口牧场、草地、小花和台阶。
- `climber.glb`：巫师女孩角色，含可被 Three.js 控制的手脚节点。
- `sheep.glb`：低多边形羊，含可被 Three.js 控制的头部和草束节点。
- `cable-car.glb`：红色缆车。
- `camp.glb`：篝火、木柴和石头。

## 后续内容

- 将角色姿态升级为 Blender 动画片段，如 `Climb`、`FeedGrass`、`Sleep`。
- 将作品、关于、经历、联系方式绑定到路线站点。
- 增加真实个人文案、项目详情和外部链接。
- 补充音效、背景音乐和加载进度。
