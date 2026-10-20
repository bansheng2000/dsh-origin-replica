---
name: dsh-origin-replica
description: 把一张「好看的参考图」（论文插图/别人的成品图/截图）复刻成 Origin 图的 SOP：先产出固定字段的图形规格卡 → 卡字段映射到 dsh-origin MCP 工具 → 2~3 轮「渲染-对照-差量修正」收敛 → verify + 交付。含参考图红线（不反推数据/不抄文字水印/不承诺 1:1）与精确取色脚本。当用户给参考图说"画成这样""复刻这张图""照着排版"时使用。可由领域 SOP（如 dsh-xps-peakfit）委派来只做风格对齐。触发词：复刻 / 照着画 / 画成这样 / 模仿这张图 / 参考图排版 / replicate figure。
whenToUse: 用户提供一张参考图（或描述某张成品图）要求把自己的数据画成同样的风格、配色、排版，或要求对齐轴/图例/面板布局、对齐页面尺寸出投稿图时；或被领域 SOP 委派来做这类风格对齐
---

# 参考图复刻 SOP

> v1.4：补「底部装饰条（area ratio 长条）要贴基线」的做法——条顶别用常数，改成背景曲线列（`Book3_L = Book3_C;`），否则倾斜基线和常数条之间会留白缝；条线色设成填充色，否则像一条浮着的独立长条。v1.3：补两条实测坑——渐变只对「填充到基线」生效（`-pfv 9` fill-to-next 会**忽略** `-pfm` 保持纯色，须先 `-pfv 0`）；LabTalk 里的数据集名是列短名（`Book3_H`），写列名（`Comp1`）不认且静默无效，动手前用 `origin_inspect_graph` 读真实 dataset。v1.2：面积/折线填充也验证了同一条渐变通道（`-pf 1` + `-pfm 3` + `-pfb`/`-pff`，顶起始色→底终止色；`v11area` 实测 270 个纵向色阶）。v1.1：填充形态（纯色 / 渐变）进规格卡与映射——柱/条渐变走 `set %C -pfm 3 -pfb -pff`（Origin 2026b 实测），并记下渐变设色与导出必须分开调用的坑。v1.0：规格卡 → 工具映射 → 差量收敛 → verify；含上游委派接口（被 dsh-xps-peakfit 等领域 SOP 调用时的交接与分流护栏）与 `extract_palette.py` 取色。

目的：把"看着像"变成"逐字段对得上"。入口是一张**规格卡**，出口是一张**差量表为空**的图。

## 先划红线（前 3 条违反=造假，用户硬要也要先明说）
1. 数据只能来自用户给的数值/文件；**禁止从参考图像素反推数据点**。像素只用来读"图形语法"（颜色、线型、布局、字号）。
2. 不抄参考图里的文字、拟合参数、物相/峰标注、Logo、水印；标注内容一律用用户自己的。
3. 不承诺 1:1；交付话术固定为"布局与风格已对齐，数据为本实验数据"。
4. 参考图有、本插件没有的能力，如实说做不到，别硬凑一个近似品假装对齐。

## 上游委派接口（被领域 SOP 调用时，如 dsh-xps-peakfit）

被别的领域 SOP 委派进来时：**只接风格对齐这一段，不替上游做领域判断**。

| 上游交什么 | 我这里怎么用 |
|---|---|
| 数据文件 / 系列清单与含义 | 按清单建 series；**不改数值、不乱改系列序** |
| 轴标题与单位、版面约束（单栏 8.9cm、字号下限） | 落进规格卡的 canvas / fonts 行，不覆盖上游给的字号下限 |
| 要标注的峰位 / 占比 / 归属文本 | 原样上 `origin_annotate`——文本不润色、数值不改一个字符 |
| 禁止项（不许改数值、不许抄参考图里的拟合参数） | 叠加到本 skill 红线，**从严**执行 |

回给上游：规格卡 + 差量表结论 + 交付路径；**unknown 与未对齐项如实回报，不自行抹平**。

两种入口别混：**有参考图** → 走本 skill 的规格卡流程；**只有版面约束、没参考图** → 不套复刻流程，直接转 `origin-plotting` 常规建图。

## 第一步：写规格卡（先写卡再动手，缺项写 unknown，不许脑补）

| 字段 | 取值 | 怎么读 |
|---|---|---|
| canvas | 单栏 8.9cm / 双栏 18.3cm / 方形 / 其它；宽高比 | 目测 + 投稿惯用尺寸 |
| family | 折线 / 散点 / 线+符号 / 柱 / 箱线 / 堆叠谱 / XRD / 双Y / 森林 / 多面板 | 目测 |
| panels | 1×1 / 2×1 / 2×2 …；是否共享 X 轴 | 目测 |
| x, y | 轴标题（物理量+单位）、范围、刻度类型（线性 / log10 / ln）、是否反向 | 目测 |
| y2 | 有无次轴、次轴标题与范围 | 目测 |
| series | 逐条：颜色 #hex、线宽 pt、线型、符号、透明度 | extract_palette.py + 目测 |
| fill | 填充形态：none / 纯色 / **渐变（起止两色 #hex + 方向 + 是否每根柱子独立）** / 图案；作用对象：柱·条·面积 | 目测放大看是否渐变 + extract_palette.py |
| yerr | 误差棒有无与样式 | 目测 |
| legend | 位置（tr/tl/br/bl）、字号、有无边框 | 目测 |
| refs | 参考线 / 阈值线 / 峰位标注 | 目测 |
| fonts | 轴标题与刻度字号 pt、是否加粗 | 目测 |

卡里只留**能映射成参数**的行。读不准的项写 unknown，动手前**一次性**问用户（只问这一轮，别来回确认）。

取色（需要精确 hex 时才跑，别当固定步骤）：
```
python extract_palette.py 参考图.png [--top 8]
```
输出 top-N 主色 hex + 占比 + 图片尺寸。占比最大的常是背景/网格，**先剔除背景色再挑系列色**；hex 直接进 `style_overrides.series_colors`。

## 第二步：卡 → 工具映射（工具细节见 origin-plotting skill，本 skill 不重抄）

| 卡字段 | 调用 |
|---|---|
| 数据进 Origin | `origin_load_file(path)` 或 `origin_write_data(columns)` |
| 领域图型 | `origin_plot_template(template_id=...)`：dual_y / multi_panel / stacked_spectra / xrd_pattern / forest |
| 一般图型 | `origin_plot(worksheet, plot_type=..., x_column=, y_columns=)` |
| 配色+线宽+轴标题一次到位 | `origin_plot(..., style_overrides={"series_colors":["#hex"...],"line_width_pt":2.0,"x_title":"..","y_title":".."})` |
| 轴范围/刻度类型/网格/字号 | `origin_edit_axis(graph, axis="y", from_value=, to_value=, scale={2:log10,3:ln}, props={...})` |
| 单条曲线精修 | `origin_edit_plot(graph, [{"plot":i,"color":"#..","line_width_pt":2.5,"line_style":1,"symbol_kind":2,"transparency":20}])` |
| 柱/条 **纯色填充** | `origin_labtalk(graph, "set Book1_A -pfb color(221,94,0);")`（要边框色：`-pbc color(...)`） |
| 柱/条/面积 **渐变填充** | `origin_labtalk(graph, "set Book1_A -pfm 3; set Book1_A -pfb color(221,94,0); set Book1_A -pff color(0,114,178);")`（面积/折线先 `-pfv 0; -pf 1` 开填充——**fill-to-next（`-pfv 9`）下 `-pfm` 会被忽略、导出仍是纯色**）——顶=起始色、底=终止色；反向就把两色对调；`-pfbr 221 94 0` / `-pffr 0 114 178` 是同效写法。**mode 只试 0/1/2/3**：0/1 关闭、2 单色渐变（实际偏黑）、3 双色线性；试 4/5 等无效值会把 Origin 会话弄坏 |
| 渐变读回 | 读回不可靠（`Book1_A.pfm` 读回 NaN）：只能用 `origin_view_graph` 目视，或导出后取色核对（`extract_palette.py`） |
| 图例位置/字号/边框 | `origin_edit_legend(graph, {"position":"tr","font_size_pt":11,"frame":false})` |
| 页面尺寸 / 图层几何 | `origin_edit_page(graph, page_size_cm={"width":8.9,"height":6.5})` / `layer_geometry_pct` |
| 参考线 / 峰标注 | `origin_add_line(graph, ...)` / `origin_annotate(graph, items=[...])`（先 `origin_layout_info` 算坐标，别渲染-看图试错） |
| 整图换排版/调色板 | `origin_apply_style(graph, style_mode="journal", family=...)` |

## 第三步：收敛循环（照跑，最多 3 轮）
1. `origin_view_graph(graph)` 看自己画的。
2. 与参考图**逐字段**对照，只列**差的项**：`字段 | 现状 | 目标 | 动作`。
3. 一次 `origin_edit_*` 改完（多条合并进一个 edits 列表）→ 回第 1 步。
4. 连续两轮差量表为空 → 停，进收尾。仍有 unknown 项 → 如实告诉用户哪几项对不上，不许糊过去。

## 第四步：收尾（复刻的完成判据）
- `origin_verify_graph(graph, expected_series=卡上系列数, min_font_pt=8)`：`fail` 必修，`warn` 在回复里提一句。
- 页面尺寸按 canvas 定（投稿图 `origin_edit_page` 到 8.9 / 18.3cm）。
- 导出 `origin_export(fmt="png", width>=1800)`；要完整交付物用 `origin_export_delivery(graph, source_path=数据文件, fmts="png,pdf")`。
- 回复 = 交付文件路径 + 差量表结论一句话（哪几项没对齐、为什么）。

## 交付前自检（8 条有一条 no 就别交付）
1. 没有一项数据来自参考图像素？ 2. 系列数 = 卡上系列数？ 3. 每条系列颜色 = 卡上 hex（不是"差不多"）？
4. 轴标题含单位、范围一致？ 5. 次轴 / 反向轴按要求？ 6. 图例位置字号对齐？ 7. 页面尺寸 = 卡 canvas？ 8. verify 无 fail？ 9. 填充形态 = 卡上（纯色 / 渐变、方向、起止色都对，**不能拿纯色顶渐变**）？

## 备注
- 参数、错误码、失败恢复动作全在 **origin-plotting** skill；本 skill 只管"参考图 → 参数"这一段。
- 参考图小字/细线读不准：读卡阶段问一次，别猜。
- **LabTalk 数据集名是列短名**（`Book3_H`），不是数据列名（`Comp1`）：名字错了 `-pfm/-pfb/-pff` **静默无效**、导出字节和上次一模一样。先 `origin_inspect_graph` 看 plot 的实际 dataset 名再设。
- **渐变是否真生效只能靠像素验，不能靠肉眼**：导出后在峰值中心取一条竖列，`uniq` 色数 < 20 就是没渐变（纯色最多 1~3 色）。
- **渐变设色与导出必须分开调用**：同一批「设渐变 → 导出」在 Origin 2026b 上实测会毒化 COM 会话（之后 `origin_export` 三通道全失败、`origin_plot` 报 `Datasheet_FindCol` 异常、`origin_diagnose` 报 `ApplicationBase_Path` 线程错误）。先设色→单独导出→失败就重启 Origin，别在同一会话反复重试。
- 折线/面积填充：先 `set %C -pf 1` 开填充，再同柱/条一样 `-pfm 3` + `-pfb`/`-pff` —— **2026-10-20 实测面积渐变成立**（曲线下填充区顶起始色→底终止色，270 个纵向色阶）。插值方向是整个绘图区高度，不是按每根柱子独立。
- **底部装饰条（area ratio / 占比长条）必须贴住基线**：条=两条常数曲线的填充区时，把**顶边那条的数据换成背景列**（`Book3_L = Book3_C;`），条就跟着谱的基线走；条的两条曲线线色设成填充色（`set Book3_L -c color(...)`）并把边框去掉，否则视觉上像一条浮在谱下方、和谱之间有缝的独立长条；轴下限要给条留够高度（y 从 2000 降到 1500 才够放 6.5pt 文字）。
- 参考图里的整幅宽淡粉条、面板字母、水印这类**装饰**，数据里没有就别硬造进图页；导出后裁掉（`im.crop((x,0,w,h))`）比在 Origin 里找那个对象快。
- `extract_palette.py` 只在需要精确取色时跑；只按需调。
