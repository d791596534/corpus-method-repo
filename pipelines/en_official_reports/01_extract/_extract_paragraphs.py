# -*- coding: utf-8 -*-
"""从 MinerU content_list_v2.json 提取纯正文(仅 type=paragraph)。
每文档: 遍历各页顺序, 收集 paragraph, 段落文本拼接, 输出 {文档}.txt(段间空行)。
用法: python _extract_paragraphs.py <MinerU输出目录> <正文输出目录>
"""
import os, json, glob, re

LEDGER_SEP = re.compile(r'[_\-]{2,}')


def is_ledger_line(line):
    """账目/表格行判定: 下划线破折号填充 + 数字, 词汇少"""
    letters = sum(1 for ch in line if ch.isascii() and ch.isalpha())
    digits = sum(1 for ch in line if ch.isdigit())
    num_groups = len(re.findall(r'\b\d[\d,.\s]*\d\b|\b\d\b', line))
    runs2 = len(LEDGER_SEP.findall(line))
    runs3 = len(re.findall(r'[_\-]{3,}', line))
    if runs3 and digits >= 2:               # 长填充 + 小数字(Virgin Islands_-- 21)
        return True
    if runs2 and digits >= 4:               # 填充 + 数字(Total available__------ 5,432,991)
        return True
    if runs2 and num_groups >= 2:           # 合并单元格行(多数字+填充)
        return True
    if digits >= 12 and letters * 2 < digits:  # 数字压倒性多于字母
        return True
    return False


def clean_ledger(paras):
    """删除账目行 + 清理杂符(¬)与上标/下标标签(<sup>/<sub>); 净化后空段丢弃"""
    out = []
    for p in paras:
        keep = []
        for l in p.split('\n'):
            l = l.replace('¬', '')
            l = re.sub(r'</?sup>|</?sub>', '', l)   # 去上/下标标签,保留内容
            if l.strip() and not is_ledger_line(l):
                keep.append(l)
        t = '\n'.join(keep).strip()
        if t:
            out.append(t)
    return out


def extract_paragraphs(json_path, clean=True):
    """返回段落文本列表(按文档顺序). clean=True 时过滤账目/表格行"""
    d = json.load(open(json_path, encoding='utf-8'))
    paras = []

    def walk(x):
        if isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, dict):
            if x.get('type') == 'paragraph':
                pc = (x.get('content') or {}).get('paragraph_content') or []
                text = ''.join(it.get('content', '') or '' for it in pc if isinstance(it, dict))
                text = text.strip()
                if text:
                    paras.append(text)
            for v in x.values():
                walk(v)

    walk(d)
    return clean_ledger(paras) if clean else paras


def find_json(src_root):
    """递归找所有 *_content_list_v2.json"""
    hits = []
    for r, d, f in os.walk(src_root):
        for x in f:
            if x.endswith('_content_list_v2.json'):
                hits.append(os.path.join(r, x))
    return sorted(hits)


def main(src_root, out_root):
    os.makedirs(out_root, exist_ok=True)
    total_doc = total_par = 0
    for jp in find_json(src_root):
        # 文档名 = json 所在目录名(去后缀)
        doc = os.path.basename(jp).replace('_content_list_v2.json', '')
        paras = extract_paragraphs(jp)
        op = os.path.join(out_root, doc + '.txt')
        with open(op, 'w', encoding='utf-8') as fh:
            fh.write('\n\n'.join(paras))
        total_doc += 1
        total_par += len(paras)
        print('{}: {} 段'.format(doc, len(paras)), flush=True)
    print('共 {} 文档 / {} 段 -> {}'.format(total_doc, total_par, out_root), flush=True)
    return out_root


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        sys.exit('用法: python _extract_paragraphs.py <MinerU输出目录> <正文输出目录>')
    src, out = sys.argv[1], sys.argv[2]
    main(src, out)