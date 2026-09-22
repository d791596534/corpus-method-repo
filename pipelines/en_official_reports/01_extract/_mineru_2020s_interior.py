# -*- coding: utf-8 -*-
"""英文公文 2020s reports of the interior MinerU 文字层提取 固定参数脚本。
- 源 PDF: 2020s reports of the interior/{year}.pdf (2020-2025)
- 参数固定: -b pipeline -t false -f false -m txt(电子档文字层, 同2004-2026)
- 断点续跑: 输出已有该年 content_list_v2 则跳过
- 提取 paragraph -> 英文公文2020s_正文/{year}.txt
用法: python _mineru_2020s_interior.py [--skip-ocr]
"""
import os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
BASE = os.path.join(ROOT, 'pdf_2020s_interior')     # <年>.pdf
OCR_OUT = os.path.join(ROOT, '_mineru_out_2020s')
CORPUS = os.path.join(ROOT, '英文公文2020s_正文')
YEARS = [y for y in range(2020, 2026)]
LOGF = os.path.join(ROOT, '_mineru_2020s_interior.log')


def year_pdf(y):
    p = os.path.join(BASE, '{}.pdf'.format(y))
    return p if os.path.exists(p) else None


def year_done(y):
    import glob
    return glob.glob(os.path.join(OCR_OUT, '{}'.format(y), 'txt', '*_content_list_v2.json'))


def do_ocr():
    log = open(LOGF, 'a', encoding='utf-8')
    todo = [y for y in YEARS if year_pdf(y) and not year_done(y)]
    print('待处理 {} 年: {}'.format(len(todo), todo), flush=True)
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
            log.write('{} rc={}\n'.format(y, r.returncode)); log.flush()
            print('    {} 完成 {:.0f}s rc={}'.format(y, time.time() - t0, r.returncode), flush=True)
        except subprocess.TimeoutExpired:
            print('    {} 超时(重跑续)'.format(y), flush=True)
        except Exception as exc:
            print('    {} 失败: {}'.format(y, str(exc)[:100]), flush=True)
    log.close()
    print('OCR 阶段结束', flush=True)


def do_extract():
    import glob, importlib.util
    spec = importlib.util.spec_from_file_location('e', os.path.join(HERE, '_extract_paragraphs.py'))
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    os.makedirs(CORPUS, exist_ok=True)
    tot = 0
    print('=== 提取 paragraph ===', flush=True)
    for y in YEARS:
        jps = year_done(y)
        if not jps:
            print('{} 无产物, 跳过'.format(y), flush=True)
            continue
        paras = e.extract_paragraphs(jps[0])
        with open(os.path.join(CORPUS, '{}.txt'.format(y)), 'w', encoding='utf-8') as fh:
            fh.write('\n\n'.join(paras))
        w = sum(len(re.findall(r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*", p)) for p in paras)
        tot += w
        print('{}: {}段 {:,}词'.format(y, len(paras), w), flush=True)
    print('合计 {:,} 词 -> {}'.format(tot, CORPUS))


if __name__ == '__main__':
    if '--skip-ocr' in sys.argv:
        do_extract()
    else:
        do_ocr()
        do_extract()