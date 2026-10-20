"""figure_metrics.py — 参考图/成品图的量化对照（复刻收敛用）。

只读像素，输出可比的归一化几何量与色值：
  frame(外框) canvas%、装饰带高度%、白缝%、刻度长度、刻度标签字高、轴标题字高、点径、线宽、关键色。

用法：
  python figure_metrics.py <img.png> [--json]
  python figure_metrics.py ref.png ours.png        # 并排对照
"""
import sys, json
import numpy as np
from PIL import Image

WHITE = 245


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(int)


def frame_rect(a, pad=24):
    """内层绘图框（跳过图像外圈黑边）。返回 (t,b,l,r) 或 None。"""
    h, w, _ = a.shape
    sub = a[pad:h - pad, pad:w - pad]
    dark = sub.max(2) < 130
    rows = np.where(dark[:, max(0, sub.shape[1] // 4):sub.shape[1] * 3 // 4].mean(1) > 0.6)[0]
    cols = np.where(dark[sub.shape[0] // 4:sub.shape[0] * 3 // 4, :].mean(0) > 0.6)[0]
    if len(rows) < 2 or len(cols) < 2:
        return None
    return int(rows[0] + pad), int(rows[-1] + pad), int(cols[0] + pad), int(cols[-1] + pad)


def band_span(a, t, b, l, r, hexv="#FCE4EA", tol=12):
    """框内纯色装饰带：返回 (top,bot,height_px, pct_of_plot_h)。"""
    c = np.array([int(hexv[i:i + 2], 16) for i in (1, 3, 5)])
    x0, x1 = l + int(0.15 * (r - l)), l + int(0.30 * (r - l))
    hit = (np.abs(a[t:b + 1, x0:x1] - c).max(2) <= tol).mean(1) > 0.9
    idx = np.where(hit)[0]
    if len(idx) == 0:
        return None
    return int(t + idx[0]), int(t + idx[-1]), int(idx[-1] - idx[0] + 1), round(100.0 * (idx[-1] - idx[0] + 1) / (b - t + 1), 2)


def white_gap(a, t, b, l, r, band_top):
    """装饰带上方的纯白缝高度。"""
    x0, x1 = l + int(0.15 * (r - l)), l + int(0.30 * (r - l))
    white = (a[t:band_top, x0:x1] > WHITE).all(2).mean(1) > 0.9
    idx = np.where(white)[0]
    if len(idx) == 0:
        return 0, 0.0
    seg_end = idx[-1]
    seg_start = seg_end
    while seg_start - 1 in set(idx.tolist()):
        seg_start -= 1
    h = seg_end - seg_start + 1
    return int(h), round(100.0 * h / (b - t + 1), 2)


def text_groups_below(a, b, l, r, scan=160):
    """框下方文字/刻度的行分段：返回 [(top,bot,height_px)]。"""
    y0, y1 = b + 1, min(a.shape[0], b + 1 + scan)
    dark = (a[y0:y1, l:r].max(2) < 160).mean(1) > 0.002
    groups, start = [], None
    for i, v in enumerate(dark):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= 2:
                groups.append((int(y0 + start), int(y0 + i - 1), int(i - start)))
            start = None
    if start is not None and len(dark) - start >= 2:
        groups.append((int(y0 + start), int(y0 + len(dark) - 1), int(len(dark) - start)))
    return groups


def tick_length(a, b, l, r, n=30):
    """主TICK len度：框下 0..25px 内，深色像素列的连续行数众数。"""
    y0, y1 = b + 1, min(a.shape[0], b + 26)
    dark = (a[y0:y1, l:r].max(2) < 160)
    colsum = dark.sum(0)
    runs = colsum[colsum >= 3]
    return int(np.median(runs)) if len(runs) else 0


def dot_diameter(a, t, b, l, r, hexv="#DE90BA", tol=26):
    """散点直径估计：匹配色区域的横向游程中位数。"""
    c = np.array([int(hexv[i:i + 2], 16) for i in (1, 3, 5)])
    sub = (np.abs(a[t:b + 1, l:r + 1] - c).max(2) <= tol)
    runs = []
    for row in sub[::3]:
        idx = np.where(row)[0]
        if len(idx) < 2:
            continue
        start = idx[0]; prev = idx[0]
        for i in idx[1:]:
            if i != prev + 1:
                runs.append(prev - start + 1); start = i
            prev = i
        runs.append(prev - start + 1)
    runs = [x for x in runs if 1 <= x <= 12]
    return round(float(np.median(runs)), 1) if runs else None


def dominant(a, n=6, skip_white=True):
    px = a.reshape(-1, 3)
    if skip_white:
        px = px[~((px.min(1) > 235) | (px.max(1) < 60))]
    keys = (px // 16).astype(np.int32)
    flat = keys[:, 0] * 10000 + keys[:, 1] * 100 + keys[:, 2]
    uniq, inv, cnt = np.unique(flat, return_inverse=True, return_counts=True)
    out = []
    for i in np.argsort(-cnt)[:n]:
        avg = px[inv == i].mean(0).round().astype(int)
        out.append("#%02X%02X%02X" % tuple(avg))
    return out


def metrics(path, band_hex="#FCE4EA", dot_hex="#DE90BA"):
    a = load(path)
    H, W, _ = a.shape
    fr = frame_rect(a)
    m = {"file": path.split("/")[-1], "size": [W, H], "aspect": round(W / H, 3)}
    if not fr:
        return m
    t, b, l, r = fr
    pw, ph = r - l + 1, b - t + 1
    m["frame_pct"] = {"left": round(100 * l / W, 1), "top": round(100 * t / H, 1),
                      "width": round(100 * pw / W, 1), "height": round(100 * ph / H, 1)}
    m["plot_px"] = [pw, ph]
    bs = band_span(a, t, b, l, r, band_hex)
    if bs:
        m["band"] = {"height_px": bs[2], "pct_plot_h": bs[3],
                     "from_bottom_pct": round(100 * (b - bs[1]) / ph, 1)}
        m["gap"] = white_gap(a, t, b, l, r, bs[0])
    m["tick_px"] = tick_length(a, b, l, r)
    m["text_below"] = text_groups_below(a, b, l, r)
    m["dot_px"] = dot_diameter(a, t, b, l, r, dot_hex)
    m["palette"] = dominant(a, 6)
    return m


def show(m):
    print("==", m["file"], m.get("size"), "aspect", m.get("aspect"))
    if "frame_pct" in m:
        f = m["frame_pct"]
        print("   FRAME left %.1f%% top %.1f%% w %.1f%% h %.1f%%  (plot %s px)" % (f["left"], f["top"], f["width"], f["height"], m["plot_px"]))
    if "band" in m:
        bd = m["band"]
        print("   BAND h %dpx = %.1f%% 绘图高, 距框底 %.1f%% | 白缝 %s px (%s%%)" % (bd["height_px"], bd["pct_plot_h"], bd["from_bottom_pct"], m["gap"][0], m["gap"][1]))
    print("   TICK len %s px | 点径 %s px" % (m.get("tick_px"), m.get("dot_px")))
    print("   TEXT rows (top,bot,h):", m.get("text_below"))
    print("   PALETTE:", " ".join(m.get("palette", [])))


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(0)
    for p in args:
        show(metrics(p))
