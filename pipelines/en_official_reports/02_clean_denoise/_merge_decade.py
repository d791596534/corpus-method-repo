# -*- coding: utf-8 -*-
"""按十年归并：把各批次的 *_分句_清残句 平铺目录按年代重新分目录。

    python _merge_decade.py                  # 产出 $CORPUS_ROOT/英文公文_分句_清残句_按十年
    python _merge_decade.py --verify <root>   # 只读比对已有归并层，不写任何文件

批次目录只到「一批年份平铺」一层，而配额抽样的单位是「年代 × 体裁」，所以下游
（_denoise_decade、_supplement_en250k）都按年代目录走。归并只改目录层级，
不改一个字节：源文件按原名 <年份>.txt 拷进 <年代>s/。
待归并的批次层由目录名自动发现，不写死年份区间。
"""
import os
import re
import shutil
import sys

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
OUT = '英文公文_分句_清残句_按十年'
LAYER = re.compile(r"^英文公文(.+)_分句_清残句$")


def dec_of(year):
    return '%ds' % (year // 10 * 10)


def gather(root):
    """{ 年份: 源文件路径 }——将 root 下所有 *_分句_清残句 批次层里的年份文件收齐。"""
    layers = sorted(f for f in os.listdir(root) if LAYER.match(f))
    if not layers:
        sys.exit('%s 下没有 *_分句_清残句 批次层，先跑 01_extract 与 02 的前几步' % root)
    found = {}
    for name in layers:
        d = os.path.join(root, name)
        ys = [int(f[:-4]) for f in os.listdir(d) if re.match(r"^\d{4}\.txt$", f)]
        for y in ys:
            if y in found:
                sys.exit('%d 年同时出现在 %s 与 %s，批次年份区间重叠' % (y, found[y][1], name))
            found[y] = (os.path.join(d, '%d.txt' % y), name)
        print('%-46s %d 个年份（%d—%d）' % (name, len(ys), min(ys), max(ys)))
    return found


def merge(root):
    found = gather(root)
    out = os.path.join(root, OUT)
    if os.path.isdir(out):
        shutil.rmtree(out)
    for y in sorted(found):
        d = os.path.join(out, dec_of(y))
        os.makedirs(d, exist_ok=True)
        shutil.copyfile(found[y][0], os.path.join(d, '%d.txt' % y))
    print('归并 %d 个年份 -> %d 个年代目录：%s' % (len(found), len(os.listdir(out)), out))


def verify(root):
    """只读：逐字节比对归并层与批次层，并核对年代目录归属。"""
    found = gather(root)
    out = os.path.join(root, OUT)
    if not os.path.isdir(out):
        sys.exit('找不到归并层 %s，先不带 --verify 跑一次' % out)
    on_disk = {}
    for d in os.listdir(out):
        dd = os.path.join(out, d)
        if not os.path.isdir(dd):
            continue
        for f in os.listdir(dd):
            if re.match(r"^\d{4}\.txt$", f):
                on_disk[int(f[:-4])] = (os.path.join(dd, f), d)
    ok = bad = 0
    for y in sorted(set(found) | set(on_disk)):
        if y not in found:
            print('  %d 只在归并层里，批次层没有' % y)
        elif y not in on_disk:
            print('  %d 漏归并' % y)
        elif open(found[y][0], 'rb').read() != open(on_disk[y][0], 'rb').read():
            print('  %d 与批次层逐字节不一致' % y)
        elif on_disk[y][1] != dec_of(y):
            print('  %d 放错年代目录（%s，应为 %s）' % (y, on_disk[y][1], dec_of(y)))
        else:
            ok += 1
            continue
        bad += 1
    print('回验：一致 %d，不一致 %d' % (ok, bad))
    print('输出 ->', out)
    return bad


if __name__ == '__main__':
    if '--verify' in sys.argv:
        i = sys.argv.index('--verify')
        root = sys.argv[i + 1] if i + 1 < len(sys.argv) else ROOT
        sys.exit(1 if verify(root) else 0)
    merge(ROOT)
