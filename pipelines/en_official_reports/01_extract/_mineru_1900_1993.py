# -*- coding: utf-8 -*-
"""英文公文扫描档 MinerU OCR + paragraph 提取（1900-1993）。
- 直接处理源文件夹内 PDF(不复制): {BASE}/{year}_report of the secretary of *.pdf
- 参数固定: -b pipeline -t false -f false -m ocr
- 断点续跑: 输出目录已有该年 content_list_v2 则跳过
- 跑完后提取 paragraph -> 英文公文{tag}_正文/{year}.txt

用法:
    python _mineru_1900_1993.py                      # 一次跑完 1900-1993，产出合并成一个目录
    python _mineru_1900_1993.py --years 1900 1920    # 分批跑，每批一个 _正文 目录
    python _mineru_1900_1993.py --years 1921 1993
    python _mineru_1900_1993.py --skip-ocr           # 只做提取，不重跑 OCR

年份区间只影响输出目录命名（`_mineru_out_<FROM>_<TO>` / `英文公文<FROM>-<TO>_正文`），
处理逻辑与参数对每一年都相同。
"""
import os, re, glob, subprocess, sys, time, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面

ap = argparse.ArgumentParser()
ap.add_argument('--years', type=int, nargs=2, default=[1900, 1993], metavar=('FROM', 'TO'))
ap.add_argument('--base', default=os.path.join(ROOT, 'pdf'),
                help='源 PDF 目录，按 <年>_report of the secretary of *.pdf 命名')
ap.add_argument('--skip-ocr', action='store_true')
_args = ap.parse_args()
YEAR0, YEAR1 = _args.years
TAG = '%d-%d' % (YEAR0, YEAR1)

BASE = _args.base
OCR_OUT = os.path.join(ROOT, '_mineru_out_' + TAG.replace('-', '_'))
CORPUS = os.path.join(ROOT, '英文公文%s_正文' % TAG)
LOGF = os.path.join(ROOT, '_mineru_%s.log' % TAG)
EXTRACT_PY = os.path.join(HERE, '_extract_paragraphs.py')


def year_pdf(y):
    hits = glob.glob(os.path.join(BASE, '{}_report of the secretary of *.pdf'.format(y)))
    return hits[0] if hits else None


def year_done(y):
    return glob.glob(os.path.join(OCR_OUT, '{}_report*'.format(y), 'ocr', '*_content_list_v2.json'))


def do_ocr():
    log = open(LOGF, 'a', encoding='utf-8')
    todo = []
    for y in range(YEAR0, YEAR1 + 1):
        if year_done(y):
            print('{} 已处理, 跳过'.format(y), flush=True)
        else:
            todo.append(y)
    print('待处理 {} 年: {}'.format(len(todo), todo[:10]), flush=True)
    for i, y in enumerate(todo, 1):
        pdf = year_pdf(y)
        if not pdf:
            print('{} 缺PDF, 跳过'.format(y), flush=True)
            continue
        t0 = time.time()
        print('[{}/{}] 处理 {} ({})'.format(i, len(todo), y, os.path.basename(pdf)), flush=True)
        try:
            r = subprocess.run(
                ['mineru', '-p', pdf, '-o', OCR_OUT, '-b', 'pipeline',
                 '-t', 'false', '-f', 'false', '-m', 'ocr'],
                capture_output=True, text=True, encoding='utf-8', errors='ignore',
                timeout=3000)
            log.write('{}\n'.format(y))
            log.flush()
            print('    {} 完成 {:.0f}s'.format(y, time.time() - t0), flush=True)
        except subprocess.TimeoutExpired:
            print('    {} 超时, 该年未完成(重跑会续)', flush=True)
        except Exception as e:
            print('    {} 失败: {}'.format(y, str(e)[:100]), flush=True)
    log.close()
    print('OCR 阶段结束', flush=True)


def do_extract():
    import importlib.util
    spec = importlib.util.spec_from_file_location('e', EXTRACT_PY)
    e = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e)
    os.makedirs(CORPUS, exist_ok=True)
    print('=== 提取 paragraph ===', flush=True)
    for y in range(YEAR0, YEAR1 + 1):
        jps = year_done(y)
        if not jps:
            print('{} 无ocr产物, 跳过'.format(y), flush=True)
            continue
        paras = e.extract_paragraphs(jps[0])
        text = '\n\n'.join(paras)
        with open(os.path.join(CORPUS, '{}.txt'.format(y)), 'w', encoding='utf-8') as fh:
            fh.write(text)
        w = sum(len(re.findall(r"[A-Za-zÀ-ȕ0-9']+(?:[-'][A-Za-zÀ-ȕ0-9]+)*", p)) for p in paras)
        print('{}: {}段 {:,}词'.format(y, len(paras), w), flush=True)
    # 汇总
    tot = 0
    by_dec = {}
    for y in range(YEAR0, YEAR1 + 1):
        p = os.path.join(CORPUS, '{}.txt'.format(y))
        if os.path.exists(p):
            t = open(p, encoding='utf-8').read()
            w = len(re.findall(r"[A-Za-zÀ-ȕ0-9']+(?:[-'][A-Za-zÀ-ȕ0-9]+)*", t))
            tot += w
            d = (y // 10) * 10
            by_dec[d] = by_dec.get(d, 0) + w
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