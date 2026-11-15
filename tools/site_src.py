#!/usr/bin/env python3
"""主站（沉浸体验）与阅读版共用一份源码：src/site.src.html

源码里绝大部分是两页共用的行；只属于某一页的行用独占一行的标记包起来：
    @@imm      只出现在主站（index.html）
    @@read     只出现在阅读版（reading/index.html）
    @@end      结束
路径写成 {{R}}assets/…、{{R}}game/…，生成主站时 {{R}} 为空，生成阅读版时为 ../

用法：
    python3 tools/site_src.py build    由源码生成 index.html 与 reading/index.html
    python3 tools/site_src.py check    检查两页是否与源码一致（提交前钩子用；不一致退出码 1）
    python3 tools/site_src.py init     （只用一次）由现有两页反推出源码
改内容时只改 src/site.src.html，再 build。"""
import difflib, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'site.src.html'
OUT = {'imm': ROOT / 'index.html', 'read': ROOT / 'reading' / 'index.html'}
PREFIX = {'imm': '', 'read': '../'}


def tokenize(text, which):
    if which == 'imm':
        return re.sub(r'(["\'(])(assets|game)/', r'\1{{R}}\2/', text)
    return re.sub(r'(["\'(])\.\./(assets|game)/', r'\1{{R}}\2/', text)


def render(src, which):
    out, mode = [], None
    for line in src.splitlines(keepends=True):
        tag = line.strip()
        if tag in ('@@imm', '@@read'):
            mode = tag[2:]; continue
        if tag == '@@end':
            mode = None; continue
        if mode is None or mode == which:
            out.append(line)
    return ''.join(out).replace('{{R}}', PREFIX[which])


def init():
    a = tokenize(OUT['imm'].read_text(encoding='utf-8'), 'imm').splitlines(keepends=True)
    b = tokenize(OUT['read'].read_text(encoding='utf-8'), 'read').splitlines(keepends=True)
    merged = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            merged += a[i1:i2]; continue
        if i2 > i1:
            merged += ['@@imm\n'] + a[i1:i2] + ([] if a[i2 - 1].endswith('\n') else ['\n']) + ['@@end\n']
        if j2 > j1:
            merged += ['@@read\n'] + b[j1:j2] + ([] if b[j2 - 1].endswith('\n') else ['\n']) + ['@@end\n']
    SRC.parent.mkdir(exist_ok=True)
    SRC.write_text(''.join(merged), encoding='utf-8')
    shared = sum(1 for _ in a) - sum(i2 - i1 for op, i1, i2, _, _ in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op != 'equal')
    print(f'源码已生成：{SRC.relative_to(ROOT)}；共用 {shared} 行，主站 {len(a)} 行，阅读版 {len(b)} 行')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'init':
        init(); cmd = 'check'
    src = SRC.read_text(encoding='utf-8')
    bad = []
    for which, path in OUT.items():
        html = render(src, which)
        if cmd == 'build':
            path.write_text(html, encoding='utf-8'); print('已生成', path.relative_to(ROOT))
        elif path.read_text(encoding='utf-8') != html:
            bad.append(str(path.relative_to(ROOT)))
    if bad:
        print('以下文件和 src/site.src.html 不一致（请改源码后运行 python3 tools/site_src.py build）：', ', '.join(bad)); sys.exit(1)
    if cmd == 'check':
        print('主站与阅读版和源码一致')


if __name__ == '__main__':
    main()
