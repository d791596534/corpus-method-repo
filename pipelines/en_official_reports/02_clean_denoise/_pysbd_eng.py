# -*- coding: utf-8 -*-
"""英文公文四段 pySBD 断句: 每年度每句一行。
源: 各段权威正文  出: 各段_分句(+年度txt)
"""
import os, re
import pysbd

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
SRCS = [
    ('1900-1993', r'英文公文1900-1993_正文_去大写'),
    ('1998-2003', r'英文公文1998-2003_正文'),
    ('2004-2026', r'英文公文2004-2026_正文_去大写_去sub'),
]
PYR = {y: pysbd.Segmenter(language='en', clean=False) for y in range(1900, 2027)}


def main():
    for tag, src_name in SRCS:
        src = os.path.join(ROOT, src_name)
        dst = os.path.join(ROOT, src_name + '_分句')
        os.makedirs(dst, exist_ok=True)
        seg = PYR[int(tag[:4])]
        y0 = int(tag[:4])
        y1 = int(tag[-4:])
        ns = nw = 0
        for y in range(y0, y1 + 1):
            if y == 2005:
                continue
            p = os.path.join(src, '{}.txt'.format(y))
            if not os.path.exists(p):
                continue
            text = open(p, encoding='utf-8').read()
            # 分段(空行) -> 每段压成一行 -> pySBD段内断句 (快且不越段)
            nyr = 0
            with open(os.path.join(dst, '{}.txt'.format(y)), 'w', encoding='utf-8') as fh:
                for para in re.split(r'\n\s*\n', text):
                    flat = re.sub(r'\s+', ' ', para).strip()
                    if not flat:
                        continue
                    for s in seg.segment(flat):
                        s = s.strip()
                        if s:
                            fh.write(s + '\n')
                            nyr += 1
                            nw += len(re.findall(r"[A-Za-zÀ-ȕ0-9']+(?:[-'][A-Za-zÀ-ȕ0-9]+)*", s))
            ns += nyr
        print('{}: {:>7,}句 / {:>9,}词 -> {}'.format(tag, ns, nw, dst))
    print('完成')


if __name__ == '__main__':
    main()