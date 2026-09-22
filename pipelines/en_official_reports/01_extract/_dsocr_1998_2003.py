# -*- coding: utf-8 -*-
"""1998-2003 英文公文 DeepSeek vision OCR。
- 源: 中文. pdf_png_1998_2003/{year}/*.png
- 出: 英文公文1998-2003_OCR/{year}/*.txt (每页)
- api.deepseek.com deepseek-v4-flash-vision-exp, thinking关, temp0, max_tokens20000, 并发, 断点续跑
用法: python _dsocr_1998_2003.py [--limit N] [--workers N]
"""
import os, time, json, base64, io, argparse, urllib.request, re
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

API = 'https://api.deepseek.com/chat/completions'
KEY = 'YOUR KEY'
MODEL = 'deepseek-v4-flash-vision-exp'
MAX_TOKENS = 20000
BIG_W = 2400
MAX_W = 2000

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
SRC = os.path.join(ROOT, 'pdf_png_1998_2003')
OUT = os.path.join(ROOT, '英文公文1998-2003_OCR_v2')

PROMPT = (
    '你是一个专业的文档结构分析专家。请先识别该图像的整体布局。'
    '如果图像中包含明显的表格、财务报表或数据矩阵，请将整个表格区域'
    '（包括表头、行标题、列标题、数据单元格、以及表格内的说明文字）'
    '视为一个整体对象，并严格“忽略”或“屏蔽”该区域内的一切文字内容。\n\n'
    '【必须忽略的内容】：页眉、页脚、页码、水印、数字签名、图表、坐标轴数字，'
    '以及所有表格内的文字（包括表格第一列的行标题、顶部的列标题，以及其中的各项数据）。\n'
    '【必须提取的内容】：仅提取表格外部、作为独立段落存在的纯文字描述、'
    '页面边缘的侧边栏文字、以及大标题。\n'
    '【必须遵守的格式】：必须把标题加粗。'
    '如果除了表格外没有任何纯文字段落，则仅返回“空白”两字。'
)


def make_img_b64(path):
    im = Image.open(path)
    if im.mode != 'L':
        im = im.convert('L')
    w, h = im.size
    if w > BIG_W:
        im = im.resize((MAX_W, int(h * MAX_W / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=90)   # 页面图用JPEG更小
    return base64.b64encode(buf.getvalue()).decode()


def ocr_one(fpath):
    """单张图非流式OCR; 每请求全新messages(仅当前图), 无上下文累积"""
    b64 = make_img_b64(fpath)
    body = {"model": MODEL,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
                {"type": "text", "text": PROMPT}]}],
            "max_tokens": MAX_TOKENS, "temperature": 0,
            "thinking": {"type": "disabled"}}
    if os.environ.get('DSDEBUG'):
        msg = body['messages'][0]
        print('[debug] len(messages)={} n_blocks={} img_b64_len={} text_head={!r:.36}'.format(
            len(body['messages']), len(msg['content']), len(b64),
            msg['content'][1]['text'][:36]), flush=True)
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + KEY})
    resp = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return resp['choices'][0]['message']['content'].strip()


def collect():
    tasks = []
    for y in sorted(os.listdir(SRC)):
        yd = os.path.join(SRC, y)
        if not os.path.isdir(yd):
            continue
        for f in sorted(os.listdir(yd)):
            if f.endswith('.png'):
                tasks.append((y, f, os.path.join(yd, f)))
    return tasks


def process(task):
    y, fname, fpath = task
    out_art = os.path.join(OUT, y)
    os.makedirs(out_art, exist_ok=True)
    tpath = os.path.join(out_art, fname.replace('.png', '.txt'))
    if os.path.exists(tpath):
        c = open(tpath, encoding='utf-8').read()
        if not c.startswith('[ERROR]'):
            return True
    for attempt in range(5):
        try:
            text = ocr_one(fpath)
            if text:
                with open(tpath, 'w', encoding='utf-8') as fh:
                    fh.write(text)
                return True
        except Exception as e:
            if attempt == 4:
                with open(tpath, 'w', encoding='utf-8') as fh:
                    fh.write('[ERROR] ' + str(e)[:100])
                return False
            time.sleep(2 * (attempt + 1))
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--workers', type=int, default=8)
    args = ap.parse_args()
    tasks = collect()
    if args.limit:
        tasks = tasks[:args.limit]
    print('待OCR: {} 张'.format(len(tasks)), flush=True)
    ok = bad = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(process, tasks), 1):
            if res:
                ok += 1
            else:
                bad += 1
            if i % 50 == 0:
                print('[{}] 完成{} 失败{} {:.0f}s'.format(i, ok, bad, time.time() - t0), flush=True)
    print('完成: 成功{} 失败{} 用时{:.0f}分'.format(ok, bad, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()