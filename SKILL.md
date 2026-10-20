---
name: dsh-origin-replica
description: 把任意类型的参考图（论文插图/别人的成品图/截图）复刻成 Origin 图的通用 SOP：第 0 步像素量测取色与几何比例 → 规格卡 → 图元到 Origin 通道映射 → 2~3 轮「渲染-对照-差量修正」→ verify + 交付。含参考图红线（不反推数据/不抄文字水印/不承诺 1:1）、能力表（能/只能逼近/做不到）与实测硬坑清单。当用户给参考图说"画成这样""复刻这张图""照着排版"时使用。可由领域 SOP（如 dsh-xps-peakfit）委派来只做风格对齐。触发词：复刻 / 照着画 / 画成这样 / 模仿这张图 / 参考图排版 / replicate figure。
whenToUse: 用户提供一张参考图（或描述某张成品图）要求把自己的数据画成同样的风格、配色、排版，或要求对齐轴/图例/面板布局、对齐页面尺寸出投稿图时；或被领域 SOP 委派来做这类风格对齐
---

# 参考图复刻 SOP（通用版）

> v2.0：改成「任意类型图」的方法论——新增第 0 步强制量测（`measure_ref.py`，颜色和几何比例都从像素来，禁止目测）、图元→通道映射表、能力表（能/只能逼近/做不到）。v1.x 的单图经验收敛进硬坑清单。
> v2.1：加 `figure_metrics.py`（参考图 ↔ 成品图量化并排对照，收敛循环靠它而不是肉眼）；新增硬坑 11/12（COM 异常可 `origin_release` 救回但工程会丢、字号/点径的正确通道）。

目的：把"看着像"变成"逐字段对得上"。入口是量测 + 规格卡，出口是一张差量表为空的图。

## 先划红线（前 3 条违反=造假，用户硬要也要先明说）
1. 数据只能来自用户给的数值/文件；**禁止从参考图像素反推数据点**。像素只用来读"图形语法"（颜色、线型、布局、字号、比例）。
2. 不抄参考图里的文字、拟合参数、物相/峰标注、Logo、水印；标注内容一律用用户自己的。
3. 不承诺 1:1；交付话术固定为"布局与风格已对齐，数据为本实验数据"。
4. 参考图有、本插件没有的能力，如实说做不到，别硬凑一个近似品假装对齐（见能力表）。

## 上游委派接口（被领域 SOP 调用时，如 dsh-xps-peakfit）

被别的领域 SOP 委派进来时：**只接风格对齐这一段，不替上游做领域判断**。

| 上游交什么 | 我这里怎么用 |
|---|---|
| 数据文件 / 系列清单与含义 | 按清单建 series；**不改数值、不乱改系列序** |
| 轴标题与单位、版面约束（单栏 8.9cm、字号下限） | 落进规格卡的 canvas / fonts 行，不覆盖上游给的字号下限 |
| 要标注的峰位 / 占比 / 归属文本 | 原样上 `origin_annotate`——文本不润色、数值不改一个字符 |
| 禁止项（不许改数值、不许抄参考图里的拟合参数） | 叠加到本 skill 红线，**从严**执行 |

回给上游：规格卡 + 差量表结论 + 交付路径；**unknown 与未对齐项如实回报，不自行抹平**。

两种入口别混：**有参考图** → 走本 skill；**只有版面约束、没参考图** → 不套复刻流程，直接转 `origin-plotting` 常规建图。

## 第 0 步：量测（跳过这步 = 瞎画，返工一次就够）

```
python measure_ref.py 参考图.png --box band:330,282,470,300 --box peak:575,190,605,215
```

输出三样东西，分别对应后面要用的参数：
- `frame: rows/cols + plot pct` —— 外框占画幅的比例，倒推页面尺寸与图层几何（`origin_edit_page(page_size_cm=, layer_geometry_pct=)`）。
- `palette` —— 主色板，报的是**桶内真实平均色**（不是量化色）。占比最大的一般是背景/装饰条底色，先剔除再挑系列色。
- `box 区域取色` —— 指定矩形的主色，用来取"峰顶填充色 / 装饰条底色 / 文字颜色"这种局部色。

铁律：
1. **颜色必须来自像素**。目测配色是本 skill 最高频的返工原因（实测一次目测把 #DE90BA 估成 #D0618F、把深蓝文字估成黑色）。
2. **比例必须来自像素**（装饰带高占比、白缝高占比、外框占画幅），别用眼睛对齐。
3. 量不到的字段在卡里写 `unknown`，动手前一次性问用户，别猜两轮。

精确取色补充：`extract_palette.py`（量化分桶 + 桶内真实平均）看全局色板；`measure_ref.py` 取局部区域 + 量比例。

**增量对照**（收敛循环每轮都跑，替代肉眼打分）：

```
python figure_metrics.py 参考图.png 成品图.png   # 并排输出可比的归一化量
```

统一口径 = 各自画幅归一化：`frame` left/top/w/h %、`band` 装饰带高/绘图高、白缝 %、`tick` 刻度长、`TEXT rows` 每行字高（刻度标签 / 轴标题 / 图内标注）、`dot` 点径、`PALETTE` 主色。两条判据：带的 `band/绘图高` 与参考差 <1%、`dot/绘图宽` 与参考差 <0.1%（参考 898 px 宽时 2 px 点 ≈ 0.22%，1800 px 宽等效 4 px）。

## 第 1 步：规格卡（先写卡再动手，缺项写 unknown）

| 字段 | 取值 | 怎么读 |
|---|---|---|
| canvas | 单栏 8.9cm / 双栏 18.3cm / 方形 / 其它；宽高比 | 目测 + 投稿惯用尺寸 |
| geometry | 外框占画幅 %、图层四周留白 %、装饰带高 %、白缝高 % | measure_ref.py `plot pct` + 竖扫像素 |
| family | 折线 / 散点 / 线+符号 / 柱 / 箱线 / 堆叠谱 / XRD / 双Y / 森林 / 多面板 | 目测 |
| panels | 1×1 / 2×1 / 2×2 …；是否共享 X 轴 | 目测 |
| x, y | 轴标题（物理量+单位）、范围、刻度类型（线性/log10/ln）、是否反向、刻度朝内/外 | 目测 |
| y2 | 有无次轴、次轴标题与范围 | 目测 |
| series | 逐条：颜色 #hex、线宽 pt、线型、符号形状/大小、透明度 | measure_ref.py `box` + 目测 |
| fill | 形态：none / 纯色 / 渐变（起止色 + 方向 + 是否逐形状独立）/ 图案；作用对象；下边界（轴底 / 背景曲线 / 装饰带） | 放大看是否渐变 + `box` 取顶部与底部色 |
| deco | 装饰元素：整幅宽色带（含条内文字）、面板字母、刻线、参考线、水印 | measure_ref.py 量带高占比 |
| yerr | 误差棒有无与样式 | 目测 |
| legend | 位置（tr/tl/br/bl）、字号、有无边框 | 目测 |
| refs | 参考线 / 阈值线 / 峰位刻线 | 目测 + `layout_info` 坐标 |
| fonts | 字体族（有无衬线）、轴标题/刻度/标注字号 pt、颜色 | `box` 取文字色 + 目测字形 |

## 第 2 步：图元 → Origin 通道（照着查，别自己发明）

| 参考图里的元素 | Origin 通道 | 关键点 |
|---|---|---|
| 原始数据点（密集小圆点） | `origin_edit_plot({"symbol_kind":2,"symbol_size":1.5,"color":"#hex"})`；不显示时用 LabTalk `plotxy iy:=[Book]1!2 plot:=201 ogl:=[Graph]1!` 重新追加 | 追加的 plot 永远在最上层；追加后必须 `origin_edit_axis(props={rescale:0})` 复位轴 |
| 包络线 / 拟合线 | `origin_edit_plot({"line_width_pt":2,"color":"#hex"})` | — |
| 柱/条/面积 纯色填充 | `set <Book>_<Col> -pfb color(r,g,b);`（边框 `-pbc`） | 数据集名是**列短名** |
| 柱/条/面积 渐变填充 | `set %C -pfm 3; -pfb color(顶); -pff color(底);`（面积/折线先 `-pfv 0; -pf 1;`） | 顶=起始色、底=终止色；`-pfm` 只试 0/1/2/3 |
| **峰填充止于背景曲线** | 白遮罩法：另起一列 `= 背景列 - 150`，`-pfm 0` + `-pfb color(255,255,255)` + 填到轴底，压住背景线以下的峰填充 | fill-to-next（`-pfv 9`）忽略 `-pfm`，只能纯色；白遮罩视觉等价且能带渐变 |
| 整幅宽装饰色带（area ratio 条） | 两条常数/派生曲线夹出填充区：底=轴下限常数、顶=`col(背景)-间距`；条色 `-pfb`、线色设成条色 | 与谱之间靠"背景列−间距"自动留白缝；条内文字 y 落在带内 |
| 峰位刻线 | `origin_add_line(graph, orientation="vertical", at=<峰位>, line_style=0)` | — |
| 文字（名称 + 数值，颜色不同） | `origin_annotate` 批量加，颜色/字号用 LabTalk 精调 `TextN.fsize=7; TextN.color=color(160,48,56);` | annotate 的 y=文字**顶边**，`layout_info` 报的 y=**底边**，差一个字高 |
| 图例 | `origin_edit_legend({"position":"tr","font_size_pt":11,"frame":false})` | 关自动更新后改文本 |
| 多面板 / 双 Y / 堆叠谱 / XRD | `origin_plot_template`：multi_panel / dual_y / stacked_spectra（`gradient=true`）/ xrd_pattern / forest | 面板数受数据份数限制 |
| 对数轴 / 反向轴 / 刻度数 | `origin_edit_axis(scale={2:log10,3:ln}, from_value, to_value, props={"rescale":0})` + `layer.x.majorTicks=9` | 改轴会挪文本，改完重排注释 |
| 页面尺寸 / 图层几何 | `origin_edit_page(page_size_cm={"width":8.9,"height":6.5}, layer_geometry_pct={...})` | 用第 0 步量到的 % |
| 导出 | `origin_export(fmt="png", width>=1800)`；整包 `origin_export_delivery` | 导出后裁掉页面外的杂散对象比在 Origin 里找快 |

## 第 3 步：能力表（接活前先对照，别承诺做不到的）

| 能做到 | 说明 |
|---|---|
| 颜色精确到 hex | `-pfb/-pff/-pbc`、`TextN.color`、`origin_edit_plot(color=)` |
| 线型/线宽/符号/透明度 | `origin_edit_plot` |
| 渐变（柱/条/面积） | `-pfm 3`；按**整个绘图区高度**插值，不是逐形状独立 |
| 峰填充止于背景曲线 | 白遮罩法（见上表） |
| 整幅宽装饰带 + 条内文字 | 两条曲线夹填充 + `TextN` 定位 |
| 轴范围/刻度类型/反向/刻度数 | `origin_edit_axis` + LabTalk |
| 页面尺寸与图层几何 | `origin_edit_page` + `layer_geometry_pct` |
| 导出多格式与高 DPI | `origin_export` / `origin_export_delivery` |

| 只能逼近 | 差距 |
|---|---|
| fill-to-next 模式的渐变 | 该模式忽略 `-pfm`，只能用「填充到轴底 + 白遮罩截断」逼近；截断边跟白遮罩曲线走，不是逐点贴合 |
| 每个峰各自从峰顶饱和渐变 | 渐变按绘图区高度统一插值，峰越矮越淡 |

| 做不到（如实说） | 原因 / 替代 |
|---|---|
| 按字体名指定字体 | `TextN.font$="Arial"`、`layer.x.label.font$="Arial"`、`layer.x.font$` 全是静默 no-op（2026-10-20 复测）；数字索引只会把字变坏（实测 0→等宽、1→粗体无衬线）。**字体族只能由用户在 Origin GUI 里改**，agent 侧只能对齐字号/字重/位置 |
| 从参考图读数据 | 红线，禁止 |
| 像素级 1:1 | 不承诺；差量表为空即交付 |
| 参考图有两份数据而用户只有一份 | 如实说"少一个面板"，不复制数据凑数 |

## 第 4 步：收敛循环（照跑，最多 3 轮）
1. `origin_view_graph(graph)` 看自己画的；像素级差异用导出后取色核对，别只靠肉眼。
2. 与参考图**逐字段**对照，只列**差的项**：`字段 | 现状 | 目标 | 动作`。
3. 一次 `origin_edit_*` / 一条 LabTalk 改完（多句合并进一个 call）→ 回第 1 步。
4. 连续两轮差量表为空 → 停；仍有 unknown → 如实告诉用户哪几项对不上。

## 第 5 步：收尾（完成判据）
- `origin_verify_graph(graph, expected_series=卡上系列数, min_font_pt=8)`：`fail` 必修，`warn` 提一句。
- 页面尺寸按卡 canvas 定；导出 `width>=1800`；要完整交付用 `origin_export_delivery`。
- 回复 = 交付文件路径 + 差量表结论（哪几项没对齐、为什么，含能力表里的"只能逼近/做不到"）。

## 交付前自检（10 条有一条 no 就别交付）
1. 数据一项都不来自参考图像素？ 2. 系列数 = 卡上？ 3. 每条颜色 = 卡上 hex（像素验过，不是"差不多"）？
4. 轴标题含单位、范围一致？ 5. 次轴/反向轴/刻度朝内朝外按要求？ 6. 图例位置字号对齐？
7. 页面尺寸与图层几何 = 卡上？ 8. verify 无 fail？ 9. 填充形态（纯色/渐变/起止色/下边界）与卡一致？
10. 装饰带高度与白缝比例 = 量测值（不是估的）？

## 硬坑清单（实测，别重踩）
1. **LabTalk 数据集名 = 列短名**（`Book3_H`），写列名（`Comp1`）静默无效：导出字节和上次一模一样就是没生效的判据。动手前 `origin_inspect_graph` 读真实 dataset 名。
2. **`origin_column_formula` 的 target 用 0 基列索引**；传字符串列名会静默写到别的列（还把结果列变 NaN）。写常数用 LabTalk `range rN=[Book3]1!14; rN=2600;`。
3. **面积填充的下边界锁在设色/首绘时的轴下限**：之后改轴下限填充不跟随。顺序=先定轴范围→再设填充色→再导出。
4. **渐变设色与导出必须分两次调用**：同一批会毒化 COM 会话（`origin_export` 三通道全失败 + `Datasheet_FindCol` 异常），恢复只能重启 Origin。
5. **fill-to-next（`-pfv 9`）忽略 `-pfm`**，要渐变先 `-pfv 0`；想"止于背景曲线"用白遮罩法。
6. **叠放顺序 = plot 追加顺序**，`plotxy` 追加的永远在最上层；因此"白遮罩→装饰带"要求装饰带必须是后追加的。`plotxy` 会触发轴自动重缩放，之后必须 `origin_edit_axis(props={rescale:0})` 复位。
7. **`origin_annotate` 的 y 是文字顶边、`layout_info` 报的底边**（差一个字高）；`style.size` 常被忽略，用 `TextN.fsize=..;` 强制 + 读回复核。`label -r TextN;` 删掉后 layout_info 会留 x/y/fsize 全 NaN 的幽灵条目，不影响渲染，按名删一次就够。
8. **渐变/填充是否生效只能像素验**：导出后在峰中心取一条竖列，`uniq` 色数 <20 就是纯色。文字颜色同理用 `box` 取色核对。
9. **`doc -o` 切工程前先存当前工程**：有未保存修改时切项目，Origin 弹「是否保存」模态框，之后所有 COM 调用 60s 超时（`origin_status` 也超时），只能人工点掉弹窗或重启。正确顺序：`origin_save_project(临时路径)` → `doc -o 目标.opju`。
10. **别乱动字体属性**：`TextN.font$` / `layer.x.label.font$` 静默 no-op；`TextN.font=<索引>` 会把字变等宽或粗体，且 `layer.x.font` 改不回原样——想保字体就别碰，改坏了重开已存的 opju 恢复。
11. **COM 报 `<built-in function ApplicationBase_Path> returned a result with an exception set` = 会话中毒**：诱因是 `origin_labtalk` 里跑带 `$()` 的 `type` 命令、或渐变设色与导出挤在同一批调用。救法=先 `origin_release`，下个调用自动重连（`origin_status` 恢复 ok）；**但 release 会丢掉当前工程**（`list_pages` 变空），所以每次改动前先 `origin_save_project`，救回后 `doc -o 该 opju` 重开。release 救不回时再重启 Origin。
12. **字号/点径只有两条通道，别瞎试**：刻度标签字号=`origin_edit_axis(axis="x", props={label_font_pt:11})`（读回 `x.label.fsize`）；轴标题字号=`layer.x.label.pt`；**`layer.x.pt`/`layer.y.pt` 不是刻度字号（设了静默无效）**；散点= `origin_edit_plot(edits=[{plot:i, symbol_size:..}])`，参照 `symbol_size`≈1.0 @1800 px 宽 ≈ 4~5 px 点径（参考图 0.3% 绘图宽）——1.5 偏粗、0.8 几乎看不见。

## 备注
- 参数、错误码、失败恢复动作全在 **origin-plotting** skill；本 skill 只管"参考图 → 参数"。
- 参考图小字/细线读不准：读卡阶段问一次，别猜。
- 参考图里的面板字母、水印、页面外杂散对象：数据里没有就别硬造，导出后 `im.crop((x,0,w,h))` 裁掉最快。
- 一次生成的图先存 `_raw.png`（未裁）再裁出交付版，方便下轮改。