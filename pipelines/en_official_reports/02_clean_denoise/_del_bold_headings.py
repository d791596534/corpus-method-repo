# -*- coding: utf-8 -*-
"""1998–2003 视觉 OCR 批次的去加粗 + 删标题行 + 丢废页。

    python _del_bold_headings.py --verify <英文公文根目录>   # 只读比对，不写任何文件
    python _del_bold_headings.py --write  <英文公文根目录>   # 真正产出 _去加粗_v2

输入 `英文公文1998-2003_OCR_v2/<年>/<页>.txt`，输出 `英文公文1998-2003_去加粗_v2/<年>/<页>.txt`。

判据（四条）
  1. 整页内容为 `空白` 或以 `[ERROR]` 开头 → 丢整页（文件数 1,173 → 1,156 就来自这条）。
  2. 整行被 `**…**` 包住 → 删该行。视觉模型按 prompt 把标题加粗了，所以这条同时是删标题行。
  3. 其余行就地剥 `**`，内容保留。
  4. 再删「不含小写字母且字母数字 >= 3」的单行，**列表行不删**。
"""
import os
import re
import sys

BOLD_LINE = re.compile(r"^\*\*[^*]+\*\*$")
CAP = re.compile(r"[a-z]")


def denoise_page(text):
    """四条判据作用在一页上，返回 (结果文本, 删掉的加粗行数)。"""
    if text.strip() == "空白" or text.startswith("[ERROR]"):
        return None, 0
    stripped = []
    dropped = 0
    for line in text.split("\n"):
        s = line.strip()
        if BOLD_LINE.match(s):
            dropped += 1
            continue
        stripped.append(s.replace("**", ""))
    keep = [s for s in stripped
            if not (s and not CAP.search(s) and sum(1 for c in s if c.isalnum()) >= 3)]
    return "\n".join(x for x in keep if x), dropped


def iter_pages(root, tag="1998-2003"):
    src = os.path.join(root, "英文公文%s_OCR_v2" % tag)
    if not os.path.isdir(src):
        return
    for y in sorted(os.listdir(src)):
        yd = os.path.join(src, y)
        if not os.path.isdir(yd):
            continue
        for f in sorted(x for x in os.listdir(yd) if x.endswith(".txt")):
            yield y, f, os.path.join(yd, f)


def verify(root):
    """把四条判据作用在 OCR_v2 上，与当时的 去加粗_v2 逐字节比对。只读。"""
    dst_root = os.path.join(root, "英文公文1998-2003_去加粗_v2")
    ok = bad = dropped = 0
    for y, f, p in iter_pages(root):
        text = open(p, encoding="utf-8", errors="replace").read()
        out, n = denoise_page(text)
        dropped += n
        q = os.path.join(dst_root, y, f)
        if out is None:
            if os.path.exists(q):
                bad += 1
                print("  %s/%s 应整页丢弃，但产物里还在" % (y, f))
            else:
                ok += 1
            continue
        if not os.path.exists(q):
            bad += 1
            print("  %s/%s 产物缺失" % (y, f))
            continue
        same = out.rstrip("\n") == open(q, encoding="utf-8", errors="replace").read().rstrip("\n")
        ok += 1 if same else 0
        bad += 0 if same else 1
        if not same:
            print("  %s/%s 不一致" % (y, f))
    print("回验：一致 %d 页，不一致 %d 页；剥除加粗/标题行 %d" % (ok, bad, dropped))
    return bad


def write_out(root):
    dst_root = os.path.join(root, "英文公文1998-2003_去加粗_v2")
    n = 0
    for y, f, p in iter_pages(root):
        out, _ = denoise_page(open(p, encoding="utf-8", errors="replace").read())
        if out is None:
            continue
        os.makedirs(os.path.join(dst_root, y), exist_ok=True)
        with open(os.path.join(dst_root, y, f), "w", encoding="utf-8") as fh:
            fh.write(out)
        n += 1
    print("已写 %d 页 -> %s" % (n, dst_root))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)
    mode, root = sys.argv[1], sys.argv[2]
    if mode == "--verify":
        sys.exit(1 if verify(root) else 0)
    if mode == "--write":
        write_out(root)
    else:
        print("模式只认 --verify / --write")
        sys.exit(2)
