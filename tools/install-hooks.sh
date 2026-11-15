#!/bin/sh
# 把提交前检查装进本仓库的 .git/hooks
cd "$(git rev-parse --show-toplevel)" || exit 1
cp tools/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit && echo "已安装提交前检查：.git/hooks/pre-commit"
