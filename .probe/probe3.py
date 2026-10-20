from PIL import Image
im = Image.open(r"E:/文档/deepseek-harness/dsh-origin-replica/.probe/area_grad.png").convert("RGB"); px = im.load(); w,h = im.size
vs = set(); hs = set()
for y in range(120, 520, 5): vs.add(px[240,y])
for x in range(200, 700, 20): hs.add(px[x,400])
print("area vert_uniq", len(vs), "horiz_uniq", len(hs), "top", px[240,150], "bottom", px[240,500])
