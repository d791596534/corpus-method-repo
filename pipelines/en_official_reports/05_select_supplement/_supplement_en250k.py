# -*- coding: utf-8 -*-
r"""每时期250000词: 讲话25k(10%) + 报告225k(90%, 均分到各年份文件, 句完整)。
宿主: $CORPUS_ROOT/sotu/_每时期250000词/{dec}/
- 讲话: 复制 _每时期25000词_句净 切片(句子完整)
- 报告: 按十年库 每年份文件按行取足 225000/年份数 词(每句一行, 不断句)
2020s 报告源不足(仅~13.5万), 报告有什么取什么(可少于225k, 打印 !! 标注)。
"""
import os, re, shutil

ROOT = os.environ.get('CORPUS_ROOT', os.getcwd())   # 语料根目录：源 PDF 与中间产物都在它下面
CR = os.path.join(ROOT, 'sotu')
SPEECH_SRC = os.path.join(CR, '_每时期25000词_句净')
DEEP_SRC = os.path.join(ROOT, '英文公文_分句_清残句_按十年_清噪')
OUT = os.path.join(CR, '_每时期250000词')
DECS = [str(y) + 's' for y in range(1900, 2030, 10)]
TOKEN = r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*"


def wc(s):
    return len(re.findall(TOKEN, s))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    grand = 0
    for dec in DECS:
        od = os.path.join(OUT, dec)
        os.makedirs(od, exist_ok=True)
        # 1) 讲话(25k, 10%)
        sd = os.path.join(SPEECH_SRC, dec)
        sp_w = 0
        if os.path.isdir(sd):
            for f in os.listdir(sd):
                if f.endswith('.txt'):
                    shutil.copy2(os.path.join(sd, f), os.path.join(od, f))
                    sp_w += wc(open(os.path.join(sd, f), encoding='utf-8').read())
        # 2) 报告 225k: 均分到年份文件(短文件全取, 缺口长文件补, 可多不可少)
        dd = os.path.join(DEEP_SRC, dec)
        yearfiles = sorted(f for f in os.listdir(dd)) if os.path.isdir(dd) else []
        N = len(yearfiles)
        if N == 0:
            print('{}: 无报告文件'.format(dec))
            continue
        full = {}
        texts = {}
        for yf in yearfiles:
            p = os.path.join(dd, yf)
            lines = [l.rstrip() for l in open(p, encoding='utf-8').read().split('\n')]
            texts[yf] = lines
            full[yf] = sum(wc(l) for l in lines)
        quota = 225000 // N
        rem = 225000 % N
        target = {i: quota + (1 if i < rem else 0) for i in range(N)}
        deficit = sum(target[i] - full[yearfiles[i]]
                      for i in range(N) if full[yearfiles[i]] < target[i])
        long_idx = [i for i in range(N) if full[yearfiles[i]] >= target[i]]
        if deficit and long_idx:
            bonus = deficit // len(long_idx)
            for i in long_idx:
                target[i] += bonus
            for i in long_idx[:deficit % len(long_idx)]:
                target[i] += 1
        dp_w = 0
        slices = {}
        for i, yf in enumerate(yearfiles):
            k = target[i]
            acc = 0
            keep = []
            for ln in texts[yf]:
                keep.append(ln)
                acc += wc(ln)
                if acc >= k:
                    break
            slices[yf] = keep
            dp_w += acc
        # 逐句补足: 报告<225000 时, 从还有余量的文件补整句
        while dp_w < 225000:
            best = None
            for yf in yearfiles:
                rem = [l for l in texts[yf][len(slices[yf]):] if l.strip()]
                avail = full[yf] - sum(wc(l) for l in slices[yf])
                if rem and avail > 0 and (best is None or avail > best[1]):
                    best = (yf, avail, rem[0])
            if not best:
                break
            slices[best[0]].append(best[2])
            dp_w += wc(best[2])
        for yf, keep in slices.items():
            open(os.path.join(od, yf), 'w', encoding='utf-8').write('\n'.join(keep))
        dp_w = sum(sum(wc(l) for l in sl) for sl in slices.values())
        dec_w = sp_w + dp_w
        grand += dec_w
        print('{}: 讲话{:,}({:.0f}%) + 报告{:,}({:.0f}%) = {:,}词 ({})'.format(
            dec, sp_w, 100 * sp_w / dec_w, dp_w, 100 * dp_w / dec_w, dec_w,
            'OK' if dec_w >= 250000 else '!!'))
    print('总计 {:,} 词 -> {}'.format(grand, OUT))


if __name__ == '__main__':
    main()