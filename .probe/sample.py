
from PIL import Image
for k in ["index","colorfn","rgbsplit"]:
    im = Image.open(r"E:\\文档\\deepseek-harness\\dsh-origin-replica\\.probe\\v_%s.png" % k).convert("RGB")
    px = im.load(); w,h = im.size
    # bar 1 spans roughly x 175..300, baseline y~520, top y~440 (image 900x638)
    top = px[240, 455]; mid = px[240, 480]; bot = px[240, 515]
    print(k, "top", top, "mid", mid, "bot", bot)
