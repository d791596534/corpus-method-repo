# -*- coding: utf-8 -*-
"""每时期>=25000词 句子完整选取(可多不可少)。
短文件整篇取用, 缺口由长文件按句子补齐; 2020s跳过。
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
BASE = os.path.join(ROOT, 'sotu')
OUT = os.path.join(ROOT, 'sotu', '_每时期25000词_句净')
DECS = [str(y) + 's' for y in range(1900, 2020, 10)]
TERM = '.!?'
CLOSE = '"\')\\]\u201d\u2019\u201c\u2018\u300d\u300f\u3009\u300b'
TOKEN = r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*"


def tokens(s):
    return re.findall(TOKEN, s)


def slice_complete(text, k):
    kth = None
    for i, m in enumerate(re.finditer(TOKEN, text)):
        if i == k - 1:
            kth = m.end()
            break
    if kth is None:
        return text
    pos = kth
    while pos < len(text):
        if text[pos] in TERM:
            q = pos + 1
            while q < len(text) and text[q] in CLOSE:
                q += 1
            if q >= len(text) or text[q].isspace():
                while q < len(text) and text[q].isspace():
                    q += 1
                return text[:q]
            pos = q
        else:
            pos += 1
    return text


def is_speech(fn):
    return re.match(r'^\d{4}(?:-\d{4})?_[A-Za-z\u4e00-\u9fff]', fn) is not None


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    grand = 0
    for dec in DECS:
        d = os.path.join(BASE, dec)
        if not os.path.isdir(d):
            continue
        files = [f for f in sorted(os.listdir(d)) if f.endswith('.txt') and is_speech(f)]
        if not files:
            continue
        N = len(files)
        quota = 25000 // N
        rem = 25000 % N
        full = {f: len(tokens(open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()))
                for f in files}
        target = {i: quota + (1 if i < rem else 0) for i in range(N)}
        # 短文件不足 -> 缺口由长文件补
        deficit = 0
        for i, f in enumerate(files):
            if full[f] < target[i]:
                deficit += target[i] - full[f]
        long_idx = [i for i in range(N) if full[files[i]] >= target[i]]
        if deficit and long_idx:
            bonus = deficit // len(long_idx)
            for idx in long_idx:
                target[idx] += bonus
            leftover = deficit % len(long_idx)
            for idx in long_idx[:leftover]:
                target[idx] += 1
        od = os.path.join(OUT, dec)
        os.makedirs(od, exist_ok=True)
        slices = {}
        for i, f in enumerate(files):
            c = open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()
            k = target[i]
            slices[f] = slice_complete(c, k) if full[f] >= k else c
        # 收尾补足: 不足25000时, 从有余量文件补完整句子
        while sum(len(tokens(s)) for s in slices.values()) < 25000:
            cand = [(f, full[f] - len(tokens(sl))) for f, sl in slices.items()]
            cand = [x for x in cand if x[1] > 0]
            if not cand:
                break
            f, _ = max(cand, key=lambda x: x[1])
            c = open(os.path.join(d, f), encoding='utf-8', errors='ignore').read()
            slices[f] = slice_complete(c, len(tokens(slices[f])) + 5)
        for f, sl in slices.items():
            open(os.path.join(od, f), 'w', encoding='utf-8').write(sl)
        dec_w = sum(len(tokens(s)) for s in slices.values())
        grand += dec_w
        print('{}: {}篇, 目标{}k, 实得{:,}词 {}'.format(
            dec, N, 25, dec_w, 'OK' if dec_w >= 25000 else '!!'))
    print('总计 {:,} 词 -> {}'.format(grand, OUT))


if __name__ == '__main__':
    main()