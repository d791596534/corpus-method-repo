# -*- coding: utf-8 -*-
r"""2020s 总统国情咨文（白宫稿）去噪 + 分句。

源: `$CORPUS_ROOT/sotu/2020s/2020.txt … 2026.txt`
输出: `sotu/2020s_清噪/`（新目录，源不动），一句一行。

去噪规则:
1) 元数据行 (U.S. Capitol / Washington, D.C. / 时间戳 / END)
2) 舞台指示: [applause]/[Laughter]/[Inaudible]/...(方括号) 与 (Applause.)/(laughs)/...(圆括号) 整段删,
   "— (applause) —" 连破折号删掉; 词内括号 (401(k)) 不动
3) 讲话者标签: THE PRESIDENT:/The President. 剥标签留正文; 其余讲话者
   (THE VICE PRESIDENT: / Rep. Green / Speaker Johnson / Audience members / AUDIENCE: / Mr. President, / ...) 整行丢
4) 双破折号->单, 句首剥破折号

分句: 全稿拼一段, 自写分句器(保护缩写/小数点/单字母, 按 . ! ? … + 闭引号 + 句首大写切,
后续小写/逗号/冒号视为续句合并)。确定性实现, 不丢任何文本(不用 pySBD:
其列表项检测会吞 "27." "28." 等数字, 转义占位符又会丢整段)。
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录
SRC = os.path.join(ROOT, 'sotu', '2020s')           # 2020 年代国情咨文逐页/逐日纯文本
OUT = SRC + '_清噪'

META = re.compile(r'^(U\.S\. Capitol|Washington, D\.C\.|END)$')
TIME = re.compile(r'^\d{1,2}:\d{2}\s*(?:[AP]M|[AP]\.M\.)\s*E[S]?[DT]?')
SPK_WH_PREZ = re.compile(r'^THE PRESIDENT:\s*')
SPK_WH_OTHER = re.compile(r'^THE (?!PRESIDENT:)[A-Z ]*?:\s*')
AUDIENCE = re.compile(r'^(?:AUDIENCE:\s*|Audience members?\.)')
DD_AROUND = re.compile(r'\s*[—–]\s*\([^()]*\)\s*[—–]\s*')
PAREN = re.compile(r'(?<!\w)\([^()]*\)(?!\w)')
BRACK = re.compile(r'\[[^\]]*\]')
SPK_CR_PREZ = re.compile(r'^The President\.\s*')
# 非总统讲话者(标签需带尾点): 整行丢弃
DROP_TURN = re.compile(
    r'^(?:'
    r'Rep\.\s+\w+\.\s'
    r'|Representative\s+\w[\w. ,\'&-]*?\.\s'
    r'|Speaker\s+\w+\.\s'
    r'|Speaker of the House[^.]*\.\s'
    r'|The Speaker[^.]*\.\s'
    r'|Mr\. President(?=[,。)])'
    r'|Mr\.\s+\w+\.\s'
    r'|Ms\.\s+\w+\.\s'
    r'|Mrs\.\s+\w+\.\s'
    r'|Dr\.\s+\w+\.\s'
    r'|The Vice President\.\s'
    r'|Vice President\s+\w+\.\s'
    r'|(?:A )?Member[s]?\s+\w+\.\s'
    r'|Members?\.\s'
    r'|Leader\s+\w+\.\s'
    r'|Chairman\s+\w+\.\s'
    r'|Senator\s+\w+\.\s'
    r'|Congressman\s+\w+\.\s'
    r'|Hon\.\s+\w+\.\s'
    r')')
DASH_RUN = re.compile(r'([—–])[—–\s]+')
LEAD_DASH = re.compile(r'^[—–][\s—–]*')

ABBREVS = set('''mr mrs ms messrs dr prof sen senator rep gov hon rev supt det sgt gen col maj capt
lt cpl pvt esq sr jr st mt ft no nos jan feb mar apr jun jul aug sep sept oct nov dec etc vs
approx e.g i.e cf al dept misc inc ltd co corp a.m p.m m.p g.o.p u.s u.k u.n'''.split())


def _is_abbrev(text, i):
    """text[i]=='.': 判断是否缩写/小数点(不切句)"""
    if i + 1 < len(text) and text[i + 1].isdigit():
        return True                          # 小数点 1.6
    j = i - 1
    while j >= 0 and (text[j].isalnum() or text[j] == '.'):
        j -= 1
    tok = text[j + 1:i + 1]
    if not tok:
        return True
    if re.fullmatch(r'(?:[A-Za-z]\.)+', tok):     # J. / U.S. / U.S.A.
        return True
    base = tok.rstrip('.').lower()
    if base in ABBREVS:
        return True
    if re.fullmatch(r'\d+(?:st|nd|rd|th)?', base):
        return False                          # 28. / 28th. 是真句点(切句)
    return False


def split_sentences(text):
    """确定性分句: 永不丢文本"""
    out = []
    buf = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        buf.append(ch)
        if ch in '.!?…' and not (ch == '.' and _is_abbrev(text, i)):
            j = i + 1
            while j < n and text[j] in '”’"\')\u300d\u300f›»':
                buf.append(text[j])
                j += 1
            k = j
            while k < n and text[k].isspace():
                k += 1
            if k < n:
                nxt = text[k]
                if nxt.islower() or nxt in ',;:':
                    i = k                      # 续句, 整句继续
                    continue
            out.append(''.join(buf).strip())
            buf = []
            i = k
            continue
        i += 1
    if buf:
        out.append(''.join(buf).strip())
    return [s for s in out if s]


def clean_line(raw):
    s = raw.strip()
    if not s:
        return ''
    if META.match(s) or TIME.match(s):
        return ''
    if SPK_WH_OTHER.match(s):                # THE VICE PRESIDENT: 等非总统 -> 整行丢
        return ''
    s = SPK_WH_PREZ.sub('', s)               # THE PRESIDENT: 正文
    if AUDIENCE.match(s):
        return ''
    s = DD_AROUND.sub(' ', s)
    s = PAREN.sub('', s)
    s = BRACK.sub('', s)
    s = SPK_CR_PREZ.sub(' ', s)              # The President. 正文
    if DROP_TURN.match(s):
        return ''
    s = DASH_RUN.sub(r'\1', s)
    s = re.sub(r'[ \t]+', ' ', s).strip()
    return s


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    TOKEN = r"[A-Za-zÀ-ʯ0-9']+(?:-['A-Za-zÀ-ʯ0-9]+)*"
    grand_raw = grand_out = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith('.txt'):
            continue
        t = open(os.path.join(SRC, f), encoding='utf-8').read()
        chunks = [clean_line(l) for l in t.split('\n')]
        body = ' '.join(c for c in chunks if c)
        sents = split_sentences(body)
        out = []
        for s in sents:
            s = LEAD_DASH.sub('', s)
            s = DASH_RUN.sub(r'\1', s)
            s = re.sub(r'\s+', ' ', s).strip()
            if s:
                out.append(s)
        raw_w = len(re.findall(TOKEN, t))
        out_w = sum(len(re.findall(TOKEN, s)) for s in out)
        grand_raw += raw_w
        grand_out += out_w
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write('\n'.join(out))
        print('{}: 源{:,}词 -> 净{:,}句 {:,}词 (-{:,})'.format(
            f, raw_w, len(out), out_w, raw_w - out_w))
    print('总计 源{:,} -> 净{:,} 词 -> {}'.format(grand_raw, grand_out, OUT))


if __name__ == '__main__':
    main()