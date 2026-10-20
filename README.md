# dsh-origin-replica

参考图复刻 SOP —— 一个给 AI agent 用的 skill（Agent Skills 目录形态，`SKILL.md` + 一个取色脚本）。

仓库：<https://github.com/bansheng2000/dsh-origin-replica>

干什么：给你一张「好看的参考图」（论文插图 / 别人的成品图 / 截图）和你自己的数据，在 OriginLab Origin 里画出**风格、配色、排版逐字段对得上**的图。

**四步，顺序是硬约束**：

| # | 步骤 | 产物 |
|---|---|---|
| 1 | 写规格卡 | 十字段卡：canvas / family / panels / x,y / y2 / series / yerr / legend / refs / fonts |
| 2 | 卡 → 工具映射 | dsh-origin MCP 调用（写数 / 领域模板 / 配色 / 轴 / 图例 / 页面 / 标注） |
| 3 | 收敛循环（最多 3 轮） | `origin_view_graph` 看自己的图 → 只列差项 → 一次批量 `origin_edit_*` → 再看 |
| 4 | 收尾 | `origin_verify_graph` + 页面尺寸 + 导出，回复里带差量表结论 |

## 红线（前 3 条违反=造假）

- 数据只能来自用户给的数值 / 文件；**禁止从参考图像素反推数据点**——像素只用来读图形语法（颜色、线型、布局、字号）
- 不抄参考图里的文字、拟合参数、物相 / 峰标注、Logo、水印
- 不承诺 1:1；交付话术固定为「布局与风格已对齐，数据为本实验数据」
- 参考图有、工具没有的能力，如实说做不到，不硬凑近似品

## 关键机制

- **规格卡先于动手**：十行固定字段，缺项写 `unknown`，动手前一次性问用户，不许脑补。
- **差量收敛**：每轮只列**差的项**（`字段 | 现状 | 目标 | 动作`），连续两轮差量表为空才停；仍有 unknown 项如实回报，不抹平。
- **交付前 8 条自检**：颜色必须等于卡上 hex（不是"差不多"）、系列数一致、轴标题含单位、页面尺寸 = 卡 canvas、verify 无 fail 等。
- **上游委派接口**：被领域 SOP（如 `dsh-xps-peakfit`）委派时只接风格对齐这一段——按上游系列清单建 series、不改数值、不润色标注文本、上游禁止项从严执行；回给上游规格卡 + 差量表 + 交付路径。**只有版面约束、没有参考图时不套复刻流程**，转 `origin-plotting` 常规建图。

## 文件

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 技能正文：红线 → 规格卡 → 卡到工具映射 → 收敛循环 → 收尾 → 自检 → 上游委派接口 |
| `extract_palette.py` | 参考图取色：量化分桶统计主色，输出 top-N **桶内真实平均 hex** + 占比 + 尺寸；`--selftest` 自带断言 |

取色用法（需要精确 hex 时才跑）：

```
python extract_palette.py 参考图.png --top 8
python extract_palette.py --selftest
```

占比最大的通常是背景 / 网格，挑系列色前先剔除；输出 hex 直接进 `style_overrides.series_colors`。

## 与另外两个技能的分工（三层，不合并）

| 层 | 技能 | 交什么 |
|---|---|---|
| 领域 SOP | `dsh-xps-peakfit` 等 | 数据、系列与含义、轴标题单位、要标注的文本、版面约束、禁止项 |
| 复刻方法论 | **本 skill** | 规格卡、渲染-对照-差量修正循环、verify |
| 工具层 | `origin-plotting` | 工具参数、错误码、失败恢复 |

分层理由是触发面、硬依赖（XPSPeak vs dsh-origin MCP）与复用面都不同，合并会让复刻件被绑死在单一领域；分工条款记录见 <https://github.com/bansheng2000/dsh-xps-peakfit/blob/main/docs/v2.4-figure-routing.md>。

## 使用

把本仓库目录放进 agent 的技能目录即可（例如 DSH 的 `~/.agents/skills/dsh-origin-replica/`）。

前置：本机装好 OriginLab Origin + `dsh-origin` MCP 插件（插件安装见 `install-dsh-origin` skill）。

触发词：复刻 / 照着画 / 画成这样 / 模仿这张图 / 参考图排版 / replicate figure。

## 边界（本 skill 不做什么）

- 不从参考图反推或抄写数据；不代做领域判断（峰归属、占比、拟合参数由上游 skill / 用户给）
- 不产生科学结论，不对数据「够不够发」下判断
- 不内置图像 diff 打分，也不承诺像素级一致
- 渐变填充柱/条/面积都验证过（LabTalk `-pfm 3` + `-pfb`/`-pff`；面积先 `-pf 1` 开填充）；渐变方向按绘图区高度统一插值，做不到「每根柱子各自独立渐变」以外的花式径向/角度渐变
- 渐变设色与导出必须分开调用（同一批会毒化 COM 会话），失败就重启 Origin 再来
- 没装 Origin / dsh-origin 插件的机器上不适用

## 版本

变更记录写在 `SKILL.md` 顶部（当前 v1.2：面积渐变已验证；v1.1 填充形态进卡；v1.0 初版）。

## 许可

暂未附 `LICENSE` 文件，默认保留所有权利；需要开源许可（MIT / CC-BY 等）请提出。
