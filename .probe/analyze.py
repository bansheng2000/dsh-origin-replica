
import sys
from PIL import Image
for m in [0,1,2,3]:
    p = r"E:\文档\deepseek-harness\dsh-origin-replica\.probe\mode%d.png" % m
    im = Image.open(p).convert("RGB")
    w,h = im.size
    # scan a vertical strip near the left bar; find the bar first
    col = [(x,y) for y in range(40,h-40) for x in range(w//6, w//4, 4)]
    px = im.load()
    band = [px[x, y] for x in range(w//6, w//4, 4) for y in range(50, h-60, 4)]
    uniq = len(set(band))
    # vertical profile at a fixed x in the first bar
    xs = w//6 + 10
    prof = [px[xs, y] for y in range(80, h-100, 6)]
    print(m, "size", (w,h), "distinct_in_band", uniq, "profile_head", prof[:6], "profile_tail", prof[-6:])
