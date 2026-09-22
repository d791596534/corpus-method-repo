# -*- coding: utf-8 -*-
"""1998-2003 英文公文 PDF -> 逐页 PNG(300dpi), 断点续跑。
源: {BASE}/{year}_report of the secretary of labor.pdf
出: {OUT}/{year}/{NNN}.png     (不存在/小于阈值才转)
"""
import os, glob, fitz, time

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
BASE = os.path.join(ROOT, 'pdf')                    # <年>_report of the secretary of *.pdf
OUT = os.path.join(ROOT, 'pdf_png_1998_2003')
YEARS = list(range(1998, 2004))
DPI = 300


def main():
    os.makedirs(OUT, exist_ok=True)
    for y in YEARS:
        hits = glob.glob(os.path.join(BASE, '{}_report of the secretary of *.pdf'.format(y)))
        if not hits:
            print('{} 缺失'.format(y), flush=True)
            continue
        pdf = hits[0]
        d = fitz.open(pdf)
        out_dir = os.path.join(OUT, str(y))
        os.makedirs(out_dir, exist_ok=True)
        n = d.page_count
        done = 0
        t0 = time.time()
        for i in range(n):
            png = os.path.join(out_dir, '{:03d}.png'.format(i + 1))
            if os.path.exists(png) and os.path.getsize(png) > 20000:
                done += 1
                continue
            pix = d[i].get_pixmap(dpi=DPI)
            pix.save(png)
            done += 1
        d.close()
        print('{}: {}页 -> {} ({:.0f}s)'.format(y, done, out_dir, time.time() - t0), flush=True)
    print('全部转换完成 -> {}'.format(OUT), flush=True)


if __name__ == '__main__':
    main()