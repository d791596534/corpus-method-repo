# -*- coding: utf-8 -*-
"""2020s 报告两侧合并(Interior + Labor), 走正式清洗链并入 清噪 2020s:
1) Interior 段(英文公文2020s_正文, 已于extract_paragraphs清理) -> pySBD分句
2) 逐句: 清残句(clean_fragments.is_fragment) -> 清噪(strip_lead/纯大写/大小写混杂/残句)
3) 与现有 Labor 2020s 清噪句按年合并(2026无Interior新PDF, 仅Labor)
输出写回 英文公文_分句_清残句_按十年_清噪\2020s (先备份旧8文件)
"""
import os, re, shutil, importlib.util as ilu

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
INTERIOR = os.path.join(ROOT, '英文公文2020s_正文')
DECADE = os.path.join(ROOT, '英文公文_分句_清残句_按十年_清噪', '2020s')
BACKUP = os.path.join(ROOT, '_backup_2020s_清噪_labor')
YEARS = list(range(2020, 2027))
TOKEN = r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*"


def _load(name, path):
    spec = ilu.spec_from_file_location(name, path)
    m = ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


clean = _load('cf', os.path.join(HERE, '..', '02_clean_denoise', '_clean_fragments.py'))
noise = _load('nd', os.path.join(HERE, '..', '02_clean_denoise', '_denoise_decade.py'))
import pysbd
seg = pysbd.Segmenter(language='en', clean=False)


def interior_sentences(year):
    """Interior 段 -> 清残句+清噪后的句子"""
    p = os.path.join(INTERIOR, '{}.txt'.format(year))
    if not os.path.exists(p):
        return []
    text = open(p, encoding='utf-8').read()
    out = []
    for para in re.split(r'\n\s*\n', text):
        flat = re.sub(r'\s+', ' ', para).strip()
        if not flat:
            continue
        for s in seg.segment(flat):
            s = s.strip()
            if not s:
                continue
            if clean.is_fragment(s):
                continue
            s2 = noise.strip_lead(s)
            if not s2:
                continue
            body = s2.rstrip(noise.TRAIL)
            if not re.search(r'[a-z]', body) and sum(1 for c in body if c.isalnum()) >= 3:
                continue
            if noise.is_mixed_heading(s2):
                continue
            if noise.is_fragment(s2):
                continue
            out.append(s2)
    return out


def main():
    # 备份旧文件
    if os.path.isdir(BACKUP):
        shutil.rmtree(BACKUP)
    os.makedirs(BACKUP, exist_ok=True)
    total_int = total_lab = 0
    for y in YEARS:
        srcf = os.path.join(DECADE, '{}.txt'.format(y))
        if not os.path.exists(srcf):
            print('{}: 无Labor源, 跳过'.format(y))
            continue
        shutil.copy2(srcf, os.path.join(BACKUP, '{}.txt'.format(y)))
        lab = [l for l in open(srcf, encoding='utf-8').read().split('\n') if l]
        intr = interior_sentences(y)
        merged = lab + intr
        wl = sum(len(re.findall(TOKEN, l)) for l in lab)
        wi = sum(len(re.findall(TOKEN, l)) for l in intr)
        wm = sum(len(re.findall(TOKEN, l)) for l in merged)
        total_lab += wl
        total_int += wi
        open(srcf, 'w', encoding='utf-8').write('\n'.join(merged))
        print('{}: Labor {:,}词/{}句 + Interior {:,}词/{}句 = {:,}词/{}句'.format(
            y, wl, len(lab), wi, len(intr), wm, len(merged)))
    print('----')
    print('Labor 合计 {:,} + Interior 合计 {:,} = {:,} 词'.format(
        total_lab, total_int, total_lab + total_int))
    print('备份 ->', BACKUP)


if __name__ == '__main__':
    main()