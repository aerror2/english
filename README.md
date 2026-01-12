# english

## PDF 转 TXT + 搜索包含某个单词的 PDF

由于系统 Python 可能被 Homebrew 保护（PEP 668），推荐在本目录创建虚拟环境安装依赖。

### 安装（一次即可）

```bash
cd /Volumes/evo2T/src/english
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

### 1) 把 PDF 批量转成 TXT（可选）

```bash
cd /Volumes/evo2T/src/english
./.venv/bin/python pdf_tools/pdf_to_txt.py . -o pdf_txt
```

### 2) 查找“哪些 PDF 包含某个词/短语”

在整个目录递归扫描 PDF（默认会缓存提取的文本到 `./.pdf_text_cache`，第二次会快很多）：

```bash
cd /Volumes/evo2T/src/english
./.venv/bin/python pdf_tools/find_word_in_pdfs.py "protest" -d .
```

常用选项：
- `-i`: 忽略大小写
- `--whole-word`: 按“完整单词”匹配（避免匹配到子串）
- `--no-cache`: 不使用缓存（每次都从 PDF 重新提取文本）
