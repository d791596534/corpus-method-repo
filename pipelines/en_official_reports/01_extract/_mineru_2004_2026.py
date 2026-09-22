# -*- coding: utf-8 -*-
"""英文公文 2004-2026 MinerU 文字层提取 固定参数脚本。
- 直接处理源 PDF(不复制): {BASE}/{year}_report of the secretary of labor.pdf
- 参数固定: -b pipeline -t false -f false -m txt(文字层,电子档)
- 断点续跑: 输出已有该年 content_list_v2 则跳过
- 跑完提取 paragraph -> 英文公文2004-2026_正文/{year}.txt
用法: python _mineru_2004_2026.py [--skip-ocr]   # --skip-ocr 只管提取
"""
import os, re, glob, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
BASE = os.path.join(ROOT, 'pdf')            # <年>_report of the secretary of *.pdf
OCR_OUT = os.path.join(ROOT, '_mineru_out_2004_2026')
CORPUS = os.path.join(ROOT, '英文公文2004-2026_正文')
YEARS = [y for y in range(2004, 2027) if y != 2005]   # 2005 源缺失
LOGF = os.path.join(ROOT, '_mineru_2004_2026.log')


def year_pdf(y):
    hits = glob.glob(os.path.join(BASE, '{}_report of the secretary of *.pdf'.format(y)))
    return hits[0] if hits else None


def year_done(y):
    return glob.glob(os.path.join(OCR_OUT, '{}_report*'.format(y), 'txt', '*_content_list_v2.json'))


def do_ocr():
    log = open(LOGF, 'a', encoding='utf-8')
    todo = [y for y in YEARS if year_pdf(y) and not year_done(y)]
    print('待处理 {} 年: {}'.format(len(todo), todo[:12]), flush=True)
    for i, y in enumerate(todo, 1):
        pdf = year_pdf(y)
        t0 = time.time()
        print('[{}/{}] 处理 {}'.format(i, len(todo), y), flush=True)
        try:
            r = subprocess.run(
                ['mineru', '-p', pdf, '-o', OCR_OUT, '-b', 'pipeline',
                 '-t', 'false', '-f', 'false', '-m', 'txt'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore',
                timeout=3000)
            log.write('{}\n'.format(y)); log.flush()
            print('    {} 完成 {:.0f}s'.format(y, time.time() - t0), flush=True)
        except subprocess.TimeoutExpired:
            print('    {} 超时(重跑续)', flush=True)
        except Exception as e:
            print('    {} 失败: {}'.format(y, str(e)[:100]), flush=True)
    log.close()
    print('OCR 阶段结束', flush=True)


def do_extract():
    import importlib.util
    spec = importlib.util.spec_from_file_location('e', os.path.join(HERE, '_extract_paragraphs.py'))
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    os.makedirs(CORPUS, exist_ok=True)
    print('=== 提取 paragraph ===', flush=True)
    by_dec = {}
    tot = 0
    for y in YEARS:
        jps = year_done(y)
        if not jps:
            print('{} 无产物, 跳过'.format(y), flush=True)
            continue
        paras = e.extract_paragraphs(jps[0])
        with open(os.path.join(CORPUS, '{}.txt'.format(y)), 'w', encoding='utf-8') as fh:
            fh.write('\n\n'.join(paras))
        w = sum(len(re.findall(r"[A-Za-zÀ-ȕ0-9']+(?:[-'][A-Za-zÀ-ȕ0-9]+)*", p)) for p in paras)
        tot += w
        d = (y // 10) * 10
        by_dec[d] = by_dec.get(d, 0) + w
        print('{}: {}段 {:,}词'.format(y, len(paras), w), flush=True)
    print('合计 {:,} 词'.format(tot))
    for d in sorted(by_dec):
        print('{}-{}: {:,} 词'.format(d, d + 9, by_dec[d]))
    print('语料 ->', CORPUS)


if __name__ == '__main__':
    if '--skip-ocr' in sys.argv:
        do_extract()
    else:
        do_ocr()
        do_extract()