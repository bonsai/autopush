#!/bin/bash

# GIT Auto Push Script (Linux/Mac)
# 自動的にgit add, commit, pushを実行するスクリプト

set -e  # エラー時に終了

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 引数処理
COMMIT_MESSAGE=""
BRANCH=""
FORCE_PUSH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_PUSH="--force"
            shift
            ;;
        *)
            echo "未知のオプション: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}GIT Auto Push (Linux/Mac)${NC}"
echo "================================"

# Gitリポジトリかチェック
if [ ! -d ".git" ]; then
    echo -e "${RED}エラー: これはGitリポジトリではありません${NC}"
    exit 1
fi

# 現在のブランチを取得
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# ブランチが指定されていない場合は現在のブランチを使用
if [ -z "$BRANCH" ]; then
    BRANCH="$CURRENT_BRANCH"
fi

echo -e "${BLUE}リポジトリ: $(pwd)${NC}"
echo -e "${BLUE}ブランチ: $BRANCH${NC}"

# 変更があるかチェック
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}変更がありません${NC}"
    exit 0
fi

echo -e "${GREEN}変更を検出しました${NC}"

# 変更をステージング
echo -e "${BLUE}変更をステージング中...${NC}"
git add .
echo -e "${GREEN}ステージング完了${NC}"

# コミットメッセージを設定
if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# コミット
echo -e "${BLUE}コミット中: $COMMIT_MESSAGE${NC}"
git commit -m "$COMMIT_MESSAGE"
echo -e "${GREEN}コミット完了${NC}"

# プッシュ
echo -e "${BLUE}${BRANCH}ブランチにプッシュ中...${NC}"
if [ -z "$FORCE_PUSH" ]; then
    git push origin "$BRANCH"
else
    git push origin "$BRANCH" $FORCE_PUSH
fi
echo -e "${GREEN}プッシュ完了${NC}"

echo -e "${GREEN}自動プッシュ完了!${NC}" 