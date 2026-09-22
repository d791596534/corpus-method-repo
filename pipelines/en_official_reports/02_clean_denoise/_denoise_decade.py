# -*- coding: utf-8 -*-
"""英文公文 按十年 继续清噪:
1) 纯大写(可带尾点)单行 -> 删
2) 大小写混杂(词内出现非首字大写, 且占比>=50%且行短) -> 删
3) 符号打头 -> 剥符号后按残句规则(小写开头/不以.?!结尾)判断
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
SRC = os.path.join(ROOT, '英文公文_分句_清残句_按十年')
OUT = SRC + '_清噪'
STRIP_LEAD = set('-–—*•‣▪([{`‘"“\u3001\u300a\u2018\u201c')
TRAIL = '.”’"!?…)\u201d\u2019\u300d\u300f'
TERM = set('.!?…')
CLOSE = set('”’"\')]\u300d\u300f\u201d\u2019')
TOKEN = r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*"


def strip_lead(s):
    """剥掉行首所有非字母/数字字符(标点/符号/控制符/空白)"""
    i = 0
    while i < len(s) and not s[i].isalnum():
        i += 1
    return s[i:].strip()


def is_mixed_heading(s):
    """词内非首字大写比例>=0.5 且行<80字符 -> OCR错乱标题"""
    if len(s) >= 80:
        return False
    words = re.findall(TOKEN, s)
    if not words or len(words) < 2:
        return False
    off = 0
    for w in words:
        if any(ch.isupper() for ch in w[1:]):
            off += 1
    return off / len(words) >= 0.5


def is_fragment(s):
    if not s:
        return True
    i = 0
    while i < len(s) and s[i] in '"[“‘（( -':
        i += 1
    if i >= len(s):
        return True
    if s[i].islower():
        return True
    j = len(s) - 1
    while j >= 0 and s[j] in CLOSE:
        j -= 1
    if j < 0:
        return True
    return s[j] not in TERM


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    c_all = c_mix = c_frag = 0
    grand_in = grand_out = 0
    for dec in sorted(os.listdir(SRC)):
        sd = os.path.join(SRC, dec)
        if not os.path.isdir(sd):
            continue
        od = os.path.join(OUT, dec)
        os.makedirs(od, exist_ok=True)
        for yf in sorted(os.listdir(sd)):
            if not yf.endswith('.txt'):
                continue
            keeps = []
            for ln in open(os.path.join(sd, yf), encoding='utf-8').read().split('\n'):
                s = ln.strip()
                if not s:
                    keeps.append('')
                    continue
                grand_in += 1
                s = strip_lead(s)
                if not s:
                    c_frag += 1
                    continue
                body = s.rstrip(TRAIL)
                if not re.search(r'[a-z]', body) and sum(1 for ch in body if ch.isalnum()) >= 3:
                    c_all += 1
                    continue
                if is_mixed_heading(s):
                    c_mix += 1
                    continue
                if is_fragment(s):
                    c_frag += 1
                    continue
                keeps.append(s)
                grand_out += 1
            open(os.path.join(od, yf), 'w', encoding='utf-8').write('\n'.join(keeps))
    print('清噪: 纯大写删{} | 大小写混杂删{} | 残句删{} | 句 {:,}->{:,}'.format(
        c_all, c_mix, c_frag, grand_in, grand_out))
    print('输出 ->', OUT)


if __name__ == '__main__':
    main()