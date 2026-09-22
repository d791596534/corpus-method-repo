# -*- coding: utf-8 -*-
"""1998–2003 视觉 OCR 批次的页→年归并：把逐页 txt 拼成年度文件，与其它批次的 `_正文` 层对齐。

    python _merge_pages.py                  # 产出 $CORPUS_ROOT/英文公文<批次>_正文
    python _merge_pages.py --verify <root>   # 只读比对已有 `_正文` 层，不写任何文件

该批次的清洗链（`_del_bold_headings.py`）作用在**一页一个文件**上，而 MinerU 那些批次的
`type=paragraph` 抽取本来就一年一个文件。各条链要在 `_正文` 这一层汇合，所以这里按页码
升序把页文件拼成 `<年>.txt`：页内容原样保留，不改一行。

页界段落判据——两处页界之间要不要空一行（即另起一段）：
  下一页首行不以小写字母开头，或上一页末行以句末终止符收尾（允许终止符后跟右引号、右括号）
  → 断开；否则视为句子被版面折在页界处，接在同一段里。
"""
import os
import re
import shutil
import sys

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
SRC = re.compile(r"^英文公文(.+)_去加粗_v2$")
TERM = set('.!?')
CLOSE = set('”’")]}…')


def ends_term(s):
    """剥掉行尾的右引号/右括号后，末字符是否句末终止符。"""
    j = len(s) - 1
    while j >= 0 and s[j] in CLOSE:
        j -= 1
    return j >= 0 and s[j] in TERM


def year_files(src_dir):
    """[(年份, [页文件路径])]，页按文件名升序（页码是 001、002 这样的定宽编号）。"""
    out = []
    for y in sorted(x for x in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, x))):
        yd = os.path.join(src_dir, y)
        out.append((y, [os.path.join(yd, f) for f in sorted(os.listdir(yd)) if f.endswith('.txt')]))
    return out


def build(pages):
    chunks = [[l.strip() for l in open(p, encoding='utf-8').read().split('\n') if l.strip()]
              for p in pages]
    chunks = [c for c in chunks if c]
    out = []
    for k, c in enumerate(chunks):
        if k:
            out.append('\n\n' if (not c[0][0].islower() or ends_term(chunks[k - 1][-1])) else '\n')
        out.append('\n'.join(c))
    return ''.join(out)


def merge(root):
    tags = sorted(x for x in os.listdir(root) if SRC.match(x))
    if not tags:
        sys.exit('%s 下没有 *_去加粗_v2 层，先跑 _del_bold_headings.py --write' % root)
    for tag in tags:
        src = os.path.join(root, tag)
        dst = os.path.join(root, "英文公文%s_正文" % SRC.match(tag).group(1))
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        yrs = year_files(src)
        for y, pages in yrs:
            open(os.path.join(dst, '%s.txt' % y), 'w', encoding='utf-8').write(build(pages))
        print('%s：%d 页 → %d 个年度文件 -> %s' % (
            tag, sum(len(p) for _, p in yrs), len(yrs), dst))


def verify(root):
    """只读：拼接结果与已有 `_正文` 层逐字符比对。"""
    ok = bad = 0
    for tag in sorted(x for x in os.listdir(root) if SRC.match(x)):
        src = os.path.join(root, tag)
        dst = os.path.join(root, "英文公文%s_正文" % SRC.match(tag).group(1))
        if not os.path.isdir(dst):
            print('  %s 无 _正文 对照层，跳过' % tag)
            continue
        for y, pages in year_files(src):
            p = os.path.join(dst, '%s.txt' % y)
            got = open(p, encoding='utf-8', errors='replace').read().rstrip('\n') if os.path.exists(p) else None
            if got is None:
                print('  %s 年未归并' % y)
            elif got != build(pages):
                print('  %s 拼接结果与 _正文 不一致（我 %d 字符，它 %d）' % (y, len(build(pages)), len(got)))
            else:
                ok += 1
                continue
            bad += 1
    print('回验：一致 %d，不一致 %d' % (ok, bad))
    return bad


if __name__ == '__main__':
    if '--verify' in sys.argv:
        i = sys.argv.index('--verify')
        sys.exit(1 if verify(sys.argv[i + 1] if i + 1 < len(sys.argv) else ROOT) else 0)
    merge(ROOT)
