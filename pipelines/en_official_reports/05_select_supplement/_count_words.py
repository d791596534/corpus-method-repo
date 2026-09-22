# -*- coding: utf-8 -*-
"""按发布口径数词：连续字母、数字与词内撇号算一词，标点与杂符不计入。

    python pipelines/en_official_reports/05_select_supplement/_count_words.py data/en_official_reports/cleaned

输出「文件数 总词数」，用于核对 data/<单元>/README.md 里逐年代词数表的合计。
"""
import os
import re
import sys

TOKEN = re.compile(r"[A-Za-z\u00C0-\u02AF0-9']+(?:-['A-Za-z\u00C0-\u02AF0-9]+)*")


def count(root):
    files = words = 0
    for dp, _, fn in os.walk(root):
        for f in fn:
            if f.endswith(".txt"):
                files += 1
                text = open(os.path.join(dp, f), encoding="utf-8").read()
                words += len(TOKEN.findall(text))
    return files, words


if __name__ == "__main__":
    n, w = count(sys.argv[1] if len(sys.argv) > 1 else "cleaned")
    print("%d 个文件 %d 词" % (n, w))
