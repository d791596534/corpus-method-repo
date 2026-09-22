# 英文公文语料 · 数据

本目录放的是 [`pipelines/en_official_reports`](../../pipelines/en_official_reports) 的**产出**，
以及少量可再分发的**源件样本**，用来核对清洗前后的对应关系。

```
cleaned/    最终语料：13 个年代目录 / 247 个 txt / 324.5 万词
sources/    5 个源 PDF 样本（2004–2026 之间的政府原生电子档）
```

## cleaned/ 的命名

每个年代目录里有两类文件：

| 文件名 | 内容 |
|---|---|
| `1900.txt`、`2024.txt` | 该年度的部长年度报告（1900–1963 内政部，1964 年起劳工部，2020 年代含 APP&R） |
| `1900_William McKinley.txt` | 该年度总统国情咨文，按总统署名 |

两类都做过**句级抽样**：每个年代桶配额 25 万词，讲话取约 10%、报告补足其余，
不从句中切断，因此单个文件不等于原报告全文。词数口径同管线选句脚本的 `TOKEN`
（连续字母、数字与词内撇号算一词，标点杂符不计），实测每年代 24.1–25.1 万词；
只数纯字母序列的保守口径为合计 314.5 万。

## 逐年代词数

| 年代 | 文件 | 词 | 年代 | 文件 | 词 |
|---|---|---|---|---|---|
| 1900s | 20 | 250,503 | 1970s | 19 | 250,158 |
| 1910s | 20 | 250,333 | 1980s | 21 | 250,217 |
| 1920s | 20 | 250,420 | 1990s | 16 | 250,407 |
| 1930s | 19 | 250,280 | 2000s | 19 | 250,233 |
| 1940s | 17 | 250,150 | 2010s | 20 | 250,113 |
| 1950s | 21 | 250,252 | 2020s | 14 | 241,465 |
| 1960s | 21 | 250,385 | **合计** | **247** | **3,244,916** |

表里的数可以在**仓库根目录**下重算（不依赖 shell 的引号转义，bash 与 PowerShell 都能跑）：

```bash
python pipelines/en_official_reports/05_select_supplement/_count_words.py data/en_official_reports/cleaned
# 247 个文件 3244916 词
```

口径就是该脚本里的 `TOKEN`，与 `05` 选句时用的同一个正则。

## 版权与来源

源文件是美国联邦政府的年度出版物。依 **17 U.S.C. §105**，联邦政府作品不受著作权保护；
对其做 OCR 或抽取文字层不产生新的权利，因此本子库的正文与下列源件样本可以随仓库发布。
其余子库（小说、新闻、学术科技）不发布正文，只发布代码。

未随仓库发布的是 1900–1993 与 1998–2003 两个批次的源件：它们取自图书馆数字化本
（Google Books / Internet Archive 扫描），文本虽属公版，但扫描影像本身由数字化机构主张权利，
再分发受其服务条款限制。需要复现这两批的话，按图书馆目录自行获取即可，
管线只要求文件名对齐年份。

`2004_report of the secretary of labor.pdf` 首页文字与 `cleaned/2000s/2004.txt` 首句逐字对应，
可以直接抽查确认源件→成品的映射。

`*_总统姓名.txt` 那一类不附源件：国情咨文文本取自 GitHub 上一份公开的 SOTU 汇编表（xlsx），
那是别人整理的仓库，不往这里搬。讲话文本本身是总统发表的官方文件，属联邦作品，所以成品照发；
要重跑 `04_sotu_clean`，自备同列结构的纯文本即可，该脚本按行处理文本，不绑定具体来源格式。

## sources/ 清单

| 文件 | 页数 | 大小 | SHA-256 |
|---|---|---|---|
| `2004_report of the secretary of labor.pdf` | 278 | 3.00 MB | `cc19b3a5afc8df27894f1330cc2908865e4a5bd81923ae725b29b586fd8f52bd` |
| `2011_report of the secretary of labor.pdf` | 98 | 0.83 MB | `536b6fb2edd0b72b44eb1d5217b2cffa1fd6d8a07a19a4bbc940ad3283c845ab` |
| `2018_report of the secretary of labor.pdf` | 45 | 0.58 MB | `a156c3c69d78851b3afa6f13059243b07e10823cb8ee72c3680b07c2728adca7` |
| `2024_report of the secretary of labor.pdf` | 124 | 1.22 MB | `c9231ab1ab76e897696346df0fb43e434db9f6eaf8622e8a0b0c8ecff9a0b74e` |
| `2026_report of the secretary of labor.pdf` | 47 | 0.57 MB | `421da3fff712a3880ac86f59141756f44923a2c867616723616b4a5f5ba66bbd` |

这 5 个都是**政府原生电子档**：PDF 由 Word/PostScript 直接生成
（producer 为 Acrobat Distiller / Adobe PDF Library / Microsoft Word，署名为部门内部经办人），
平均 400 词/页、不足 0.2 图/页、10–15 KB/页，全文无图书馆水印。
缺 2005 与 1994–1997 的源件，见单元 README 的「数据缺口」。
