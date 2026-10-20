
from PIL import Image
def probe(p):
    im = Image.open(p).convert("RGB"); px = im.load(); w,h = im.size
    vset = set(); hset = set()
    for y in range(430, 520, 3): vset.add(px[240, y])
    for x in range(180, 300, 3): hset.add(px[x, 490])
    return len(vset), len(hset), px[240,455], px[240,515]
for m in [2,3,4,5,6,-1]:
    p = r"E:\\文档\\deepseek-harness\\dsh-origin-replica\\.probe\\m_%d.png" % m
    try: print("mode", m, "vert_uniq,horiz_uniq,top,bottom =", probe(p))
    except Exception as e: print("mode", m, "ERR", e)
print("area", probe(r"E:\\文档\\deepseek-harness\\dsh-origin-replica\\.probe\\area_grad.png"))
