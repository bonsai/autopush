# Git Push 自動化スクリプト

GITプロジェクト用のgit push自動化スクリプトです。変更を自動的に検出し、コミット・プッシュを実行します。

## 📁 ファイル構成

- `git-auto-push.py` - Pythonスクリプト（クロスプラットフォーム）
- `git-auto-push.bat` - Windows用バッチファイル
- `git-auto-push.sh` - Linux/Mac用シェルスクリプト

## 🚀 使用方法

### Pythonスクリプト（推奨）

```bash
# 基本的な使用（リポジトリパスを指定）
python git-auto-push.py .

# カスタムメッセージ付き
python git-auto-push.py . -m "README更新"

# 特定のブランチにプッシュ
python git-auto-push.py . -b develop

# 強制プッシュ
python git-auto-push.py . -f

# 別のリポジトリ
python git-auto-push.py /path/to/repo

# 複数オプション組み合わせ
python git-auto-push.py /path/to/repo -m "機能追加" -b develop
```

### Windows バッチファイル

```cmd
# 基本的な使用
git-auto-push.bat

# カスタムメッセージ付き
git-auto-push.bat -m "README更新"

# 特定のブランチにプッシュ
git-auto-push.bat -b develop

# 強制プッシュ
git-auto-push.bat -f
```

### Linux/Mac シェルスクリプト

```bash
# 実行権限を付与
chmod +x git-auto-push.sh

# 基本的な使用
./git-auto-push.sh

# カスタムメッセージ付き
./git-auto-push.sh -m "README更新"

# 特定のブランチにプッシュ
./git-auto-push.sh -b develop

# 強制プッシュ
./git-auto-push.sh -f
```

## ⚙️ オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `repo` | リポジトリパス（必須） | `. または /path/to/repo` |
| `-m, --message` | コミットメッセージ | `-m "機能追加"` |
| `-b, --branch` | プッシュするブランチ | `-b develop` |
| `-f, --force` | 強制プッシュ | `-f` |

## 🔧 機能

### 自動検出
- Gitリポジトリかどうかを自動チェック
- 変更があるかどうかを自動検出
- 変更がない場合はスキップ

### 安全な実行
- エラーハンドリング
- 詳細なログ出力
- エラー時の適切な終了コード

### 柔軟な設定
- カスタムコミットメッセージ
- ブランチ指定
- 強制プッシュオプション

## 📋 実行例

### 成功例
```
🤖 GIT Auto Push 開始
📂 リポジトリ: /path/to/git
📝 変更を検出しました
📁 変更をステージング中...
✅ ステージング完了
💾 コミット中: Auto commit: 2024-01-15 14:30:25
✅ コミット完了
🚀 mainブランチにプッシュ中...
✅ プッシュ完了
🎉 自動プッシュ完了!
```

### 変更なしの場合
```
🤖 GIT Auto Push 開始
📂 リポジトリ: /path/to/git
ℹ️  変更がありません
```

### エラーの場合
```
🤖 GIT Auto Push 開始
📂 リポジトリ: /path/to/git
❌ エラー: これはGitリポジトリではありません
```

## 🛠️ セットアップ

### 1. ファイルをダウンロード
```bash
# 必要なファイルをプロジェクトにコピー
cp git-auto-push.py your-project/
cp git-auto-push.bat your-project/  # Windows
cp git-auto-push.sh your-project/   # Linux/Mac
```

### 2. 実行権限を付与（Linux/Mac）
```bash
chmod +x git-auto-push.sh
```

### 3. テスト実行
```bash
python git-auto-push.py --help
python git-auto-push.py . --help
```

## 🔄 自動化の設定

### Git Hooks との連携

#### pre-commit hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python git-auto-push.py . -m "Pre-commit: $(date)"
```

#### post-commit hook
```bash
#!/bin/bash
# .git/hooks/post-commit
python git-auto-push.py . -m "Post-commit: $(date)"
```

### スケジュール実行（cron）

#### Linux/Mac
```bash
# 毎時実行
0 * * * * cd /path/to/git && python git-auto-push.py .

# 毎日午前9時に実行
0 9 * * * cd /path/to/git && python git-auto-push.py .
```

#### Windows (Task Scheduler)
1. タスクスケジューラーを開く
2. 新しいタスクを作成
3. トリガーを設定（毎日、毎時など）
4. アクション: `python git-auto-push.py .`

## 🚨 注意事項

### セキュリティ
- 強制プッシュ（`-f`）は慎重に使用
- 機密情報がコミットされていないことを確認
- リモートリポジトリの権限を確認

### パフォーマンス
- 大きなファイルの変更は手動でコミット
- 定期的なクリーンアップを実行
- 不要なファイルは`.gitignore`に追加

### トラブルシューティング

#### よくあるエラー

**1. 認証エラー**
```bash
# Git認証情報を設定
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**2. リモートブランチが存在しない**
```bash
# ブランチを作成してプッシュ
git push -u origin main
```

**3. 競合が発生**
```bash
# 手動で解決
git pull origin main
# 競合を解決後
python git-auto-push.py .
```

#### 実行時のエラー

**1. 引数エラー**
```bash
# ❌ 間違った使い方（リポジトリパスが必須）
python git-auto-push.py

# ❌ ファイル名を引数にしてしまう間違い
python git-auto-push.py git-auto-push.py

# ✅ 正しい使い方
python git-auto-push.py .                    # 現在のディレクトリ
python git-auto-push.py autopush            # autopushフォルダ
python git-auto-push.py . -m "コミットメッセージ"
python git-auto-push.py /path/to/repo -m "コミットメッセージ"
```

**2. バッチファイルをPythonで実行**
```bash
# ❌ 間違った使い方
python git-auto-push.bat

# ✅ 正しい使い方（Windows）
git-auto-push.bat
# または
./git-auto-push.bat
```

**3. Git ロックファイルエラー**
```bash
# エラー: "Another git process seems to be running"
# 解決方法: デバッグモードで実行
python git-auto-push.py . --debug

# ロックファイルを手動削除
rm .git/index.lock
# または（Windows）
del .git\index.lock
```

**4. 文字エンコーディングエラー**
```bash
# 日本語文字が原因のエラーが発生した場合
# 以下の環境変数を設定
set PYTHONIOENCODING=utf-8
# その後スクリプトを実行
python git-auto-push.py .
```

**3. スクリプトファイルが見つからない**
```bash
# ファイル名を確認
ls -la git-auto-push.*
# または（Windows）
dir git-auto-push.*
```

## 📈 拡張機能

### カスタムフック
```python
# git-auto-push.py に追加
def custom_hook():
    """カスタムフック処理"""
    print("🔧 カスタム処理を実行中...")
    # ここにカスタム処理を追加
```

### 通知機能
```python
# Slack通知の例
import requests

def notify_slack(message):
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    payload = {"text": f"GIT Auto Push: {message}"}
    requests.post(webhook_url, json=payload)
```

## 🤝 貢献

1. バグ報告や機能要求はIssueで
2. プルリクエストは歓迎
3. テストケースの追加もお願い

## 📄 ライセンス

MIT License - 自由に使用・改変可能

---

**GIT Auto Push** - Git操作を自動化して開発効率を向上！🚀

## 🚀 GitHub リポジトリ自動作成機能

### 前提条件

#### GitHub CLI のインストール
- **Windows**: https://cli.github.com/ からダウンロードしてインストール
- **macOS**: `brew install gh`
- **Linux**: `sudo apt install gh` または `sudo yum install gh`

#### GitHub CLI の認証
```bash
gh auth login
```
- ブラウザまたはトークンで認証
- 必要な権限を付与

### 自動作成機能の流れ

1. **リポジトリ存在確認**
   - `gh repo view <repository_name>` でリポジトリの存在を確認
   - 存在しない場合は作成を提案

2. **インタラクティブな作成**
   - 可視性の選択（public/private）
   - 説明文の入力（オプション）
   - 確認後にリポジトリ作成

3. **リモートリポジトリの設定**
   - `origin` リモートの自動追加
   - 初回プッシュ時の upstream 設定

### GitHub CLI が利用できない場合

GitHub CLI が利用できない場合は、以下の手順で手動でリポジトリを作成してください：

1. GitHub でリポジトリを作成
2. ローカルリポジトリにリモートを追加：
   ```bash
   git remote add origin https://github.com/username/repository.git
   ```
3. 通常通りスクリプトを実行