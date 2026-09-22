# -*- coding: utf-8 -*-
"""残句清洗: 小写开头 或 不以.?!结尾 的行视为残句删除。
对 *_分句 目录 -> 输出 *_分句_清残句
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
SRCS = [
    ('1900-1993', '英文公文1900-1993_正文_去大写_分句'),
    ('1998-2003', '英文公文1998-2003_正文_分句'),
    ('2004-2026', '英文公文2004-2026_正文_去大写_去sub_分句'),
]
TERM = set('.?!…')
CLOSE = set('”’"\')]」』')


def is_fragment(s):
    if not s:
        return True
    i = 0
    while i < len(s) and s[i] in '"[“‘（( -':
        i += 1
    if i >= len(s):
        return True
    if s[i].islower():          # 小写开头 -> 残句
        return True
    j = len(s) - 1
    while j >= 0 and s[j] in CLOSE:
        j -= 1
    if j < 0:
        return True
    return s[j] not in TERM      # 不以.?!结尾 -> 残句


def wc(t):
    return len(re.findall(r"[A-Za-zÀ-ȕ0-9']+(?:[-'][A-Za-zÀ-ȕ0-9]+)*", t))


def main():
    for tag, src_name in SRCS:
        src = os.path.join(ROOT, src_name)
        dst = os.path.join(ROOT, src_name + '_清残句')
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(dst, exist_ok=True)
        y0, y1 = int(tag[:4]), int(tag[-4:])
        n_in = n_out = w_in = w_out = 0
        for y in range(y0, y1 + 1):
            if y == 2005:
                continue
            p = os.path.join(src, '{}.txt'.format(y))
            if not os.path.exists(p):
                continue
            lines = [l.strip() for l in open(p, encoding='utf-8').read().split('\n') if l.strip()]
            keep = [l for l in lines if not is_fragment(l)]
            w_in += sum(wc(l) for l in lines)
            w_out += sum(wc(l) for l in keep)
            n_in += len(lines)
            n_out += len(keep)
            open(os.path.join(dst, '{}.txt'.format(y)), 'w', encoding='utf-8').write('\n'.join(keep))
        print('{}: 句 {:,}->{:,} (-{:,}) | 词 {:,}->{:,} (-{:,})'.format(
            tag, n_in, n_out, n_in - n_out, w_in, w_out, w_in - w_out))
    print('完成')


if __name__ == '__main__':
    main()