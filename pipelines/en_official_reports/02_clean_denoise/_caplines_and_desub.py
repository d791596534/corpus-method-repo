# -*- coding: utf-8 -*-
"""两步行级清洗：删纯大写单行（去大写）、剥 <sub>/<sup> 外壳（去sub）。

    python _caplines_and_desub.py --write              # 产出 _去大写 / _去大写_去sub 层
    python _caplines_and_desub.py --verify <root>      # 只读比对已有产物，不写任何文件

根目录取自 `CORPUS_ROOT`（不设则当前目录）；`--verify` 可显式传一个根目录，
用来核对过程中任一层的产物。

输入是 `01` 的 `英文公文<批次>_正文/<年>.txt`，逐年处理、逐年写回，
下游 `_pysbd_eng.py` 吃的就是这里产出的目录名。

哪些批次过哪一步（1998–2003 不在列：它的纯大写行已由 `02/_del_bold_headings.py`
的第 4 条判据在同一遍里删掉了）：
  1900–1993  去大写
  2004–2026  去大写 + 去sub   （MinerU 文字层把小号数字误判成下标，2011 年最严重）

判据
  去大写：删掉「非空 + 整行不含小写字母 + 字母数字个数 >= 3」的行。
          注意不是 str.isupper()——那样会漏掉 'INT 1900—12' 这类带数字与破折号的行，
          也留不下 '兴 兴 兴' 这种无小写字符的行。
  去sub ：只剥 <sub> </sub> <sup> </sup> 四种外壳，保留壳内文字。
          剥壳而非连内容删，因为这些壳是 MinerU 文字层把小号数字误判成上下标产生的，
          数字本身没错。
"""
import os
import re
import shutil
import sys

ROOT = os.environ.get("CORPUS_ROOT", os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
CHAINS = [('1900-1993', ['去大写']),
          ('2004-2026', ['去大写', '去sub'])]

CAP = re.compile(r"[a-z]")
SUBTAG = re.compile(r"</?(?:sub|sup)>")


def caplines(text):
    """去掉纯大写单行（含数字/符号行），其余原样保留。"""
    keep = []
    for line in text.split("\n"):
        if line.strip() and not CAP.search(line) and sum(1 for c in line if c.isalnum()) >= 3:
            continue
        keep.append(line)
    return "\n".join(keep)


def desub(text):
    return SUBTAG.sub("", text)


def _read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def write(root):
    """按 CHAINS 逐批次往下游一层。源目录不动，产出目录整层重建，可重跑。"""
    for tag, steps in CHAINS:
        cur = os.path.join(root, "英文公文%s_正文" % tag)
        if not os.path.isdir(cur):
            sys.exit("缺少上一级产物目录：%s" % cur)
        for step in steps:
            unit = "行" if step == "去大写" else "个标签"
            dst = cur + "_" + step
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            os.makedirs(dst)
            n = gone = 0
            for f in sorted(x for x in os.listdir(cur) if x.endswith(".txt")):
                text = _read(os.path.join(cur, f))
                out = caplines(text) if step == "去大写" else desub(text)
                if step == "去大写":
                    gone += len(text.split("\n")) - len(out.split("\n"))
                else:
                    gone += len(SUBTAG.findall(text)) - len(SUBTAG.findall(out))
                open(os.path.join(dst, f), "w", encoding="utf-8").write(out)
                n += 1
            print("%-10s %-6s %d 个文件，删 %d %s" % (tag, step, n, gone, unit))
            cur = dst
        print("  ->", cur)


def verify(root):
    """把两条规则作用在上一级产物上，与已有的下一级产物比对。只读，不写任何文件。"""
    ok = bad = 0
    for tag in sorted({m.group(1) for f in os.listdir(root)
                       for m in [re.match(r"英文公文(.+?)_正文$", f)] if m}):
        src = os.path.join(root, "英文公文%s_正文" % tag)
        dst = os.path.join(root, "英文公文%s_正文_去大写" % tag)
        if not (os.path.isdir(src) and os.path.isdir(dst)):
            print("%s 无 _去大写 对照层，跳过（1998–2003 走 _del_bold_headings 那条链）" % tag)
            continue
        for f in sorted(x for x in os.listdir(dst) if x.endswith(".txt")):
            sp = os.path.join(src, f)
            if not os.path.exists(sp):
                continue
            same = caplines(_read(sp)).rstrip("\n") == _read(os.path.join(dst, f)).rstrip("\n")
            ok += 1 if same else 0
            bad += 0 if same else 1
            if not same:
                print("  去大写 %s/%s 不一致" % (tag, f))
    a = os.path.join(root, "英文公文2004-2026_正文_去大写")
    b = os.path.join(root, "英文公文2004-2026_正文_去大写_去sub")
    if os.path.isdir(a) and os.path.isdir(b):
        for f in sorted(x for x in os.listdir(b) if x.endswith(".txt")):
            same = desub(_read(os.path.join(a, f))).rstrip("\n") == _read(os.path.join(b, f)).rstrip("\n")
            ok += 1 if same else 0
            bad += 0 if same else 1
            if not same:
                print("  去sub %s 不一致" % f)
    print("回验：一致 %d，不一致 %d" % (ok, bad))
    return bad


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    mode = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else ROOT
    if mode == "--verify":
        sys.exit(1 if verify(root) else 0)
    if mode == "--write":
        write(root)
    else:
        print("模式只认 --verify / --write")
        sys.exit(2)
