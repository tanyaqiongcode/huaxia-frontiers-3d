#!/bin/sh
# 提交前检查：① 主站 / 阅读版与共用源码一致；② 无头浏览器回归（五场景 × 五天气 × 两画风、两站中英文、拍照存档）
# 安装：sh tools/install-hooks.sh     临时跳过：git commit --no-verify
cd "$(git rev-parse --show-toplevel)" || exit 1
changed=$(git diff --cached --name-only)
if echo "$changed" | grep -qE '^(index\.html|reading/index\.html|src/site\.src\.html)$'; then
  python3 tools/site_src.py check || exit 1
fi
if echo "$changed" | grep -qE '^(index\.html|reading/|game/|src/|assets/|tools/qa_run\.mjs)'; then
  echo "运行回归测试（约 2 分钟）…"
  node tools/qa_run.mjs || { echo "回归未通过，提交已中止。"; exit 1; }
fi
exit 0
