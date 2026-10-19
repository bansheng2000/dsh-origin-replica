"""参考图取色：量化分桶统计主色，输出 top-N 真实平均 hex + 占比 + 图片尺寸。

用法:
    python extract_palette.py 参考图.png [--top 8] [--selftest]

用途: 参考图复刻时拿准确 hex 填 style_overrides.series_colors。
报告的是每桶内像素的平均色（不是量化后的近似值），可直接抄进 series_colors。
占比最大的通常是背景/网格，挑系列色前先剔除背景。
"""
import sys
from collections import Counter

from PIL import Image

BUCKET = 17  # 17 级分桶只看"是不是同一种颜色"，报告值用桶内真实平均色


def quant(v: int) -> int:
    return round(v / BUCKET) * BUCKET


def palette(path: str, top: int = 8, min_frac: float = 0.005) -> dict:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # 缩到 400px 宽再统计：抗噪又快，颜色占比基本不变
    small = im.resize((min(w, 400), max(1, round(min(w, 400) * h / w))), Image.NEAREST)
    data = small.tobytes()

    cnt: Counter = Counter()
    acc: dict = {}
    for i in range(0, len(data), 3):
        r, g, b = data[i], data[i + 1], data[i + 2]
        key = (quant(r), quant(g), quant(b))
        cnt[key] += 1
        a = acc.get(key)
        if a is None:
            acc[key] = [r, g, b]
        else:
            a[0] += r
            a[1] += g
            a[2] += b

    total = sum(cnt.values())
    colors = []
    for key, c in cnt.most_common():
        frac = c / total
        if frac < min_frac:
            break
        a = acc[key]
        colors.append(("#%02X%02X%02X" % (round(a[0] / c), round(a[1] / c), round(a[2] / c)), round(frac, 4)))
        if len(colors) >= top:
            break
    return {"size": [w, h], "colors": colors}


def selftest() -> None:
    import os
    import tempfile

    from PIL import ImageDraw

    im = Image.new("RGB", (100, 100), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 49, 99], fill=(255, 0, 0))
    d.rectangle([50, 0, 99, 99], fill=(0, 0, 255))
    path = os.path.join(tempfile.gettempdir(), "_origin_palette_selftest.png")
    im.save(path)
    got = palette(path, top=4)
    hexes = [c[0] for c in got["colors"]]
    assert got["size"] == [100, 100], got
    assert hexes[:2] == ["#FF0000", "#0000FF"], got  # 平均色必须还原原始色，不被分桶偏移
    print("selftest ok:", hexes)


def main(argv: list) -> int:
    if "--selftest" in argv:
        selftest()
        return 0
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 8
    r = palette(args[0], top=top)
    print("size: %dx%d" % tuple(r["size"]))
    for hex_, frac in r["colors"]:
        print("%s  %.2f%%" % (hex_, frac * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
