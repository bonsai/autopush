# Git Auto Push VS Code Extension

PythonスクリプトをTypeScriptでVS Code拡張として再実装したプロジェクトです。

## 🚀 機能

- 自動的に `git add`, `git commit`, `git push` を実行
- 対話式確認で各ステップを制御
- ディレクトリ分析機能
- ブランチ分岐の自動検出と解決
- GitHub CLI統合
- クロスプラットフォーム対応

## 📦 開発

### 前提条件

- Node.js 16.x以上
- VS Code 1.74.0以上
- TypeScript 4.9以上

### セットアップ

```bash
# 依存関係のインストール
npm install

# TypeScriptコンパイル
npm run compile

# ウォッチモードでコンパイル
npm run watch
```

### 拡張機能のテスト

1. VS Codeでこのプロジェクトを開く
2. F5キーを押して新しいExtension Development Hostウィンドウを開く
3. コマンドパレット（Ctrl+Shift+P）で「Git Auto Push」を実行

## 🔧 設定

VS Codeの設定から以下を変更できます：

- `gitAutoPush.defaultCommitMessage`: デフォルトのコミットメッセージ
- `gitAutoPush.autoOpenBrowser`: プッシュ後にブラウザを自動で開くか
- `gitAutoPush.enableDebugMode`: デバッグモードの有効化

## 📝 ファイル構成

```
src/
├── extension.ts          # メインの拡張機能エントリーポイント
└── gitAutoPushCore.ts    # Git操作のコアロジック
package.json              # 拡張機能の設定とメタデータ
tsconfig.json            # TypeScript設定
COMPARISON.md            # GitHub CLI vs 自作スクリプトの比較
```

## 🎯 今後の開発計画

- [ ] パッケージ化（.vsixファイル作成）
- [ ] Visual Studio Code Marketplaceへの公開
- [ ] より詳細な設定オプション
- [ ] Git操作のプレビュー機能
- [ ] 複数リポジトリの同時処理

## 📋 元のPythonスクリプトとの比較

| 機能 | Pythonスクリプト | VS Code拡張 |
|------|-----------------|-------------|
| Git操作 | ✅ | ✅ |
| GitHub統合 | ✅ | ✅ |
| VS Code統合 | ❌ | ✅ |
| GUI | ❌ | ✅ |
| 設定管理 | ❌ | ✅ |
| 配布 | スクリプトファイル | 拡張機能パッケージ |
