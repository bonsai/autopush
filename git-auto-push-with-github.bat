@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo GIT Auto Push with GitHub (Windows Batch)
echo ============================================

:: 引数処理
set "COMMIT_MESSAGE="
set "BRANCH="
set "FORCE_PUSH="
set "REPO_PATH=%1"

if "%REPO_PATH%"=="" (
    echo ❌ エラー: リポジトリパスを指定してください
    echo 使用方法: %0 ^<repo_path^> [-m "message"] [-b branch] [-f]
    exit /b 1
)

:parse_args
shift
if "%1"=="" goto :start
if "%1"=="-m" (
    set "COMMIT_MESSAGE=%2"
    shift
    shift
    goto :parse_args
)
if "%1"=="-b" (
    set "BRANCH=%2"
    shift
    shift
    goto :parse_args
)
if "%1"=="-f" (
    set "FORCE_PUSH=--force"
    shift
    goto :parse_args
)
shift
goto :parse_args

:start
:: 指定されたディレクトリに移動
cd /d "%REPO_PATH%" 2>nul
if %errorlevel% neq 0 (
    echo ❌ エラー: ディレクトリ '%REPO_PATH%' が見つかりません
    exit /b 1
)

echo 📂 リポジトリ: %CD%

:: GitHub CLIの確認
echo.
echo GitHub CLI の確認中...
gh --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  GitHub CLI (gh) が見つかりません
    echo GitHub CLI をインストールしてください: https://cli.github.com/
    goto :skip_github_check
)

echo ✅ GitHub CLI が利用可能です

:: GitHub 認証の確認
echo GitHub 認証の確認中...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  GitHub CLI の認証が必要です
    echo 'gh auth login' を実行してログインしてください
    goto :skip_github_check
)

echo ✅ GitHub 認証が確認されました

:: リポジトリ名を取得
for %%i in ("%CD%") do set "REPO_NAME=%%~ni"

:: GitHub リポジトリの存在確認
echo GitHub リポジトリの確認中...
gh repo view "%REPO_NAME%" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  GitHub リポジトリ '%REPO_NAME%' が見つかりません
    set /p "CREATE_REPO=GitHub リポジトリを作成しますか？ (y/n): "
    if /i "!CREATE_REPO!"=="y" (
        echo.
        echo リポジトリの可視性:
        echo 1. public (公開)
        echo 2. private (非公開)
        set /p "VISIBILITY=選択 (1/2): "
        
        if "!VISIBILITY!"=="1" (
            set "VISIBILITY_FLAG=--public"
        ) else if "!VISIBILITY!"=="2" (
            set "VISIBILITY_FLAG=--private"
        ) else (
            echo 無効な選択です。非公開に設定します
            set "VISIBILITY_FLAG=--private"
        )
        
        set /p "REPO_DESCRIPTION=リポジトリの説明 (オプション): "
        
        echo GitHub リポジトリを作成中...
        if "!REPO_DESCRIPTION!"=="" (
            gh repo create "!REPO_NAME!" !VISIBILITY_FLAG!
        ) else (
            gh repo create "!REPO_NAME!" !VISIBILITY_FLAG! --description "!REPO_DESCRIPTION!"
        )
        
        if %errorlevel% neq 0 (
            echo ❌ GitHub リポジトリの作成に失敗しました
            exit /b 1
        )
        
        echo ✅ GitHub リポジトリ '!REPO_NAME!' を作成しました
        
        :: リモートリポジトリを追加
        echo リモートリポジトリを追加中...
        for /f "tokens=*" %%a in ('gh api user --jq .login') do set "USERNAME=%%a"
        git remote add origin "https://github.com/!USERNAME!/!REPO_NAME!.git"
        if %errorlevel% neq 0 (
            echo ⚠️  リモートリポジトリの追加に失敗しました
        ) else (
            echo ✅ リモートリポジトリを追加しました
        )
    ) else (
        echo GitHub リポジトリの作成をスキップしました
    )
) else (
    echo ✅ GitHub リポジトリが存在します
)

:skip_github_check
:: 現在のブランチを取得
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%i"
if "!CURRENT_BRANCH!"=="" set "CURRENT_BRANCH=main"

:: ブランチが指定されていない場合は現在のブランチを使用
if "!BRANCH!"=="" set "BRANCH=!CURRENT_BRANCH!"

echo 🌿 ブランチ: !BRANCH!

:: 変更があるかチェック
git status --porcelain >nul 2>&1
if %errorlevel% neq 0 (
    echo ℹ️  変更がありません
    exit /b 0
)

echo 📝 変更を検出しました

:: 変更されたファイルを表示
echo 📝 変更されたファイル:
git status --porcelain

:: ステージングの確認
set /p stage="変更をステージングしますか？ (y/n): "
if /i not "!stage!"=="y" (
    echo 処理を中止しました
    exit /b 0
)

:: 変更をステージング
echo 📁 変更をステージング中...
git add .
if %errorlevel% neq 0 (
    echo ❌ ステージングエラー
    exit /b 1
)
echo ✅ ステージング完了

:: コミットの確認
set /p commit="コミットしますか？ (y/n): "
if /i not "!commit!"=="y" (
    echo 処理を中止しました
    exit /b 0
)

:: コミットメッセージを設定
if "!COMMIT_MESSAGE!"=="" (
    set /p COMMIT_MESSAGE="コミットメッセージを入力してください: "
    if "!COMMIT_MESSAGE!"=="" (
        for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "DATE=%%a"
        for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIME=%%a"
        set "COMMIT_MESSAGE=Auto commit: !DATE! !TIME!"
    )
)

:: コミット
echo 💾 コミット中: !COMMIT_MESSAGE!
git commit -m "!COMMIT_MESSAGE!"
if %errorlevel% neq 0 (
    echo ❌ コミットエラー
    exit /b 1
)
echo ✅ コミット完了

:: プッシュの確認
set /p push="'!BRANCH!' ブランチにプッシュしますか？ (y/n): "
if /i not "!push!"=="y" (
    echo プッシュをキャンセルしました
    exit /b 0
)

:: リモートリポジトリの存在確認
echo 🔍 リモートリポジトリを確認中...
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  リモートリポジトリが設定されていません
    call :create_github_repo
    if %errorlevel% neq 0 exit /b 1
) else (
    :: リモートURLを取得
    for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set "REMOTE_URL=%%i"
    echo 🔗 リモートURL: !REMOTE_URL!
    
    :: GitHub上でリポジトリの存在確認
    echo !REMOTE_URL! | findstr "github.com" >nul
    if !errorlevel! equ 0 (
        :: GitHub リポジトリの存在確認をスキップ（簡略化）
        echo ℹ️  GitHubリポジトリとして認識しました
    )
)

:: プッシュ
echo 🚀 !BRANCH!ブランチにプッシュ中...
if "!FORCE_PUSH!"=="" (
    git push origin !BRANCH!
) else (
    git push origin !BRANCH! !FORCE_PUSH!
)

if %errorlevel% neq 0 (
    echo 🔄 初回プッシュのようです。upstream を設定してリトライします...
    git push -u origin !BRANCH!
    if %errorlevel% neq 0 (
        echo ❌ プッシュエラー
        exit /b 1
    )
)
echo ✅ プッシュ完了

echo.
echo ==================================================
echo           GIT Auto Push Completed!
echo ==================================================
echo Repository: %REPO_PATH%
echo Branch: !CURRENT_BRANCH!
echo Commit: !COMMIT_MESSAGE!
echo ==================================================

REM ブラウザでの確認を提案
if defined USERNAME if defined REPO_NAME (
    set /p "OPEN_BROWSER=GitHubリポジトリをブラウザで確認しますか？ (y/n): "
    if /i "!OPEN_BROWSER!"=="y" (
        echo ブラウザでGitHubリポジトリを開きます...
        start "" "https://github.com/!USERNAME!/!REPO_NAME!"
    )
)

cd /d "%ORIGINAL_DIR%"
exit /b 0

:create_github_repo
echo 📦 GitHubリポジトリを作成します
for %%i in ("%CD%") do set "REPO_NAME=%%~ni"
echo リポジトリ名: !REPO_NAME!

set /p private="プライベートリポジトリにしますか？ (y/n): "
set /p description="リポジトリの説明（オプション）: "

set "CREATE_CMD=gh repo create !REPO_NAME!"

if /i "!private!"=="y" (
    set "CREATE_CMD=!CREATE_CMD! --private"
) else (
    set "CREATE_CMD=!CREATE_CMD! --public"
)

if not "!description!"=="" (
    set "CREATE_CMD=!CREATE_CMD! --description "!description!""
)

set "CREATE_CMD=!CREATE_CMD! --source=. --remote=origin --push"

echo 🚀 実行中: !CREATE_CMD!
!CREATE_CMD!
if %errorlevel% neq 0 (
    echo ❌ GitHubリポジトリの作成に失敗しました
    exit /b 1
)
echo ✅ GitHubリポジトリを作成しました
exit /b 0
