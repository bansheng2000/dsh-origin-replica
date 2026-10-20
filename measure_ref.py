"""measure_ref.py — 参考图量测:取色 + 几何比例(复刻第一步,别靠眼睛估).

用法:
  python measure_ref.py <ref.png>                 # 画布/边框/主色板
  python measure_ref.py <ref.png> --box name:x0,y0,x1,y1 [...]
  python measure_ref.py --selftest                # 自检

设计约束:
- 只读参考图像素,不反推数据(值域红线在 SKILL.md)。
- 颜色报"桶内真实平均色",不报量化色(量化会偏一档,#DD6600 vs #D55E00)。
"""
import sys
import numpy as np
from PIL import Image

BUCKET = 16


def frame_bbox(a):
    """最大深色矩形的外框行/列(图有外框时才有意义;忽略贴边黑边)。"""
    a = a[2:-2, 2:-2]
    dark = a.max(2) < 120
    rows = np.where(dark.sum(1) > a.shape[1] * 0.5)[0]
    cols = np.where(dark.sum(0) > a.shape[0] * 0.5)[0]
    if len(rows) < 2 or len(cols) < 2:
        return None
    return int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])


def dominant(a, n=12, min_sat=0, skip_near_white=True):
    """主色:按 BUCKET 分桶计数,回报桶内真实平均色。"""
    px = a.reshape(-1, 3)
    if skip_near_white:
        px = px[~((px.min(1) > 235) | (px.max(1) < 60))]
    if min_sat:
        px = px[(px.max(1) - px.min(1)) >= min_sat]
    if len(px) == 0:
        return []
    keys = (px // BUCKET).astype(np.int32)
    flat = keys[:, 0] * 10000 + keys[:, 1] * 100 + keys[:, 2]
    uniq, inv, cnt = np.unique(flat, return_inverse=True, return_counts=True)
    order = np.argsort(-cnt)[:n]
    out = []
    for i in order:
        m = inv == i
        avg = px[m].mean(0).round().astype(int)
        out.append(("#%02X%02X%02X" % tuple(avg), int(cnt[i])))
    return out


def box_stat(a, x0, y0, x1, y1, n=4):
    return dominant(a[y0:y1, x0:x1], n=n)


def band_proportions(a, color="#FCE4EA", tol=10, x_probe=None):
    """量一条纯色带占画幅的比例(复刻 area-ratio 条这类装饰带用)。"""
    c = np.array([int(color[i:i + 2], 16) for i in (1, 3, 5)])
    hit = (np.abs(a - c).max(2) <= tol)
    if x_probe is None:
        x_probe = int(a.shape[1] * 0.25)
    rows = np.where(hit[:, x_probe])[0]
    if len(rows) == 0:
        return None
    h = a.shape[0]
    return {"rows": [int(rows[0]), int(rows[-1])],
            "height_px": int(rows[-1] - rows[0] + 1),
            "pct_of_canvas": round(100.0 * (rows[-1] - rows[0] + 1) / h, 2)}


def report(path, boxes=None):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    print("size:", im.size)
    bb = frame_bbox(a)
    if bb:
        t, b, l, r = bb
        print("frame: rows %d..%d cols %d..%d (w=%d h=%d)" % (t, b, l, r, r - l + 1, b - t + 1))
        print("plot pct: top %.1f%% height %.1f%% left %.1f%% width %.1f%%" % (
            100.0 * t / a.shape[0], 100.0 * (b - t) / a.shape[0],
            100.0 * l / a.shape[1], 100.0 * (r - l) / a.shape[1]))
    print("palette:")
    for hexv, cnt in dominant(a):
        print("  ", hexv, cnt)
    for spec in boxes or []:
        name, coords = spec.split(":")
        x0, y0, x1, y1 = (int(v) for v in coords.split(","))
        print("box %-12s" % name, " ".join("%s(%d)" % (h, c) for h, c in box_stat(a, x0, y0, x1, y1)))


def selftest():
    a = np.full((100, 100, 3), 255, dtype=np.uint8)
    a[40:50, :] = (252, 228, 234)          # 10 行粉带 = 10%
    a[0, :] = 0
    a[:, 0] = 0
    a[99, :] = 0
    a[:, 99] = 0
    arr = a.astype(int)
    bp = band_proportions(arr, "#FCE4EA")
    assert bp and bp["height_px"] == 10, bp
    assert abs(bp["pct_of_canvas"] - 10.0) < 0.01, bp
    top = dominant(arr, n=1)
    assert top[0][0] == "#FCE4EA", top
    print("selftest ok", bp, top)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    else:
        import re
        is_box = re.compile(r"^\w+:\d+,\d+,\d+,\d+$")
        args = [x for x in sys.argv[1:] if not x.startswith("--") and not is_box.match(x)]
        boxes = [x for x in sys.argv[1:] if is_box.match(x)]
        report(args[0], boxes)
