# -*- coding: utf-8 -*-
"""2020s 总统讲话(SOTU 2020-2026 清噪) 选句:
从 sotu/2020s_清噪 里每文件按均分目标整句截取(可多不可少, 句子完整),
输出到 sotu/_每时期25000词_句净/2020s/{year}_{President}.txt
(2025 为特朗普第二次任期首场, 均命名 Donald J. Trump)
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录
SRC = os.path.join(ROOT, 'sotu', '2020s_清噪')
OUT = os.path.join(ROOT, 'sotu', '_每时期25000词_句净', '2020s')
TARGET = 25000
TOKEN = r"[A-Za-zÀ-ʯ0-9']+(?:-['A-Za-zÀ-ʯ0-9]+)*"
NAMES = {
    '2020': 'Donald J. Trump',
    '2021': 'Joseph R. Biden',
    '2022': 'Joseph R. Biden',
    '2023': 'Joseph R. Biden',
    '2024': 'Joseph R. Biden',
    '2025': 'Donald J. Trump',
    '2026': 'Donald J. Trump (2nd Term)',
}


def wc(l):
    return len(re.findall(TOKEN, l))


def main():
    files = [f for f in sorted(os.listdir(SRC)) if f.endswith('.txt')]
    N = len(files)
    quota = TARGET // N
    rem = TARGET % N
    target = {f: quota + (1 if i < rem else 0) for i, f in enumerate(files)}
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    tot = 0
    for f in files:
        lines = [l for l in open(os.path.join(SRC, f), encoding='utf-8').read().split('\n') if l]
        full = sum(wc(l) for l in lines)
        k = target[f]
        acc, keep = 0, []
        for ln in lines:
            keep.append(ln)
            acc += wc(ln)
            if acc >= k:
                break
        name = '{}_{}.txt'.format(f[:4], NAMES[f[:4]])
        open(os.path.join(OUT, name), 'w', encoding='utf-8').write('\n'.join(keep))
        tot += acc
        print('{}: 目标{} 实得{:>6,} 词 {}句 [{:>5,}+{:>5,}剩]'.format(
            name, k, acc, len(keep), acc, full - acc))
    print('总计 {:,} 词 -> {}'.format(tot, OUT))


if __name__ == '__main__':
    main()