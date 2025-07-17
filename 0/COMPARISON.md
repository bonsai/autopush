# GitHub CLI vs 自作スクリプト 機能比較表

## 🔍 機能比較

| 機能 | GitHub CLI (`gh`) | 自作スクリプト (`git-auto-push.py`) | 備考 |
|------|-------------------|-------------------------------------|------|
| **基本的なGit操作** | ❌ | ✅ | |
| `git add` | ❌ | ✅ | CLIはGit操作をしない |
| `git commit` | ❌ | ✅ | CLIはGit操作をしない |
| `git push` | ❌ | ✅ | CLIはGit操作をしない |
| **GitHub操作** | ✅ | ✅ | |
| リポジトリ作成 | ✅ (`gh repo create`) | ✅ | CLIを内部で使用 |
| リポジトリ表示 | ✅ (`gh repo view`) | ✅ | CLIを内部で使用 |
| ブラウザで開く | ✅ (`gh repo view --web`) | ✅ | CLIを内部で使用 |
| 認証管理 | ✅ (`gh auth login`) | ❌ | CLIの認証を利用 |
| **自動化機能** | ❌ | ✅ | |
| ワンコマンド実行 | ❌ | ✅ | add → commit → push を自動化 |
| 対話式確認 | ❌ | ✅ | 各ステップで確認 |
| エラーハンドリング | ❌ | ✅ | ロックファイル処理等 |
| **プロジェクト管理** | ✅ | ❌ | |
| Issue管理 | ✅ (`gh issue`) | ❌ | GitHub特有の機能 |
| PR管理 | ✅ (`gh pr`) | ❌ | GitHub特有の機能 |
| Actions管理 | ✅ (`gh workflow`) | ❌ | GitHub特有の機能 |
| **統合機能** | ❌ | ✅ | |
| VSCode統合 | ❌ | ✅ | タスク、デバッグ設定 |
| 複数プラットフォーム | ✅ | ✅ | Windows、Mac、Linux |
| バッチ処理 | ❌ | ✅ | .batファイルも提供 |

## 📋 使用場面の違い

### GitHub CLI (`gh`) が適している場面：
- **GitHub特有の機能**を使いたい場合
- Issue、PR、Actionsの管理
- リポジトリの詳細な設定
- チーム開発での協業
- GitHubのAPI操作

### 自作スクリプト (`git-auto-push.py`) が適している場面：
- **日常的なGit操作**を自動化したい場合
- add → commit → push を一発で実行
- 初心者にとって分かりやすい操作
- ローカル開発の効率化
- エラー時の自動復旧

## 🤝 両者の関係

実際には、**自作スクリプトがGitHub CLIを内部で使用**している関係です：

```python
# 自作スクリプト内でGitHub CLIを使用
subprocess.run("gh repo create", shell=True)
subprocess.run("gh repo view", shell=True)
subprocess.run("gh auth status", shell=True)
```

## 🎯 結論

- **GitHub CLI**: GitHubプラットフォーム特有の機能に特化
- **自作スクリプト**: 日常的なGit操作の自動化に特化

両者は**補完関係**にあり、自作スクリプトはGitHub CLIの機能を活用しながら、より使いやすい形で提供しています。

### 推奨使用パターン：
1. **GitHub CLI**: 最初の認証設定 (`gh auth login`)
2. **自作スクリプト**: 日常的な開発作業 (`python git-auto-push.py .`)
3. **GitHub CLI**: 高度な機能 (`gh pr create`, `gh issue list`)
