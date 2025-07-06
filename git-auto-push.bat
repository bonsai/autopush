@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo GIT Auto Push (Windows Batch)
echo ================================

:: 引数処理
set "COMMIT_MESSAGE="
set "BRANCH="
set "FORCE_PUSH="

:parse_args
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
:: Gitリポジトリかチェック
if not exist ".git" (
    echo  エラー: これはGitリポジトリではありません
    exit /b 1
)

:: 現在のブランチを取得
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "CURRENT_BRANCH=%%i"
if "!CURRENT_BRANCH!"=="" set "CURRENT_BRANCH=main"

:: ブランチが指定されていない場合は現在のブランチを使用
if "!BRANCH!"=="" set "BRANCH=!CURRENT_BRANCH!"

echo  リポジトリ: %CD%
echo ブランチ: !BRANCH!

:: 変更があるかチェック
git status --porcelain >nul 2>&1
if %errorlevel% neq 0 (
    echo  変更がありません
    exit /b 0
)

echo  変更を検出しました

:: 変更をステージング
echo 変更をステージング中...
git add .
if %errorlevel% neq 0 (
    echo ステージングエラー
    exit /b 1
)
echo ステージング完了

:: コミットメッセージを設定
if "!COMMIT_MESSAGE!"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "DATE=%%a"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIME=%%a"
    set "COMMIT_MESSAGE=Auto commit: !DATE! !TIME!"
)

:: コミット
echo コミット中: !COMMIT_MESSAGE!
git commit -m "!COMMIT_MESSAGE!"
if %errorlevel% neq 0 (
    echo コミットエラー
    exit /b 1
)
echo コミット完了

:: プッシュ
echo !BRANCH!ブランチにプッシュ中...
if "!FORCE_PUSH!"=="" (
    git push origin !BRANCH!
) else (
    git push origin !BRANCH! !FORCE_PUSH!
)
if %errorlevel% neq 0 (
    echo プッシュエラー
    exit /b 1
)
echo プッシュ完了

echo 自動プッシュ完了!
exit /b 0 