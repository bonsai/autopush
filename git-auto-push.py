#!/usr/bin/env python3
"""
GIT Auto Push Script
自動的にgit add, commit, pushを実行するスクリプト
"""

import os
import sys
import subprocess
import datetime
import argparse
from pathlib import Path
import json
import webbrowser
import urllib.parse

class GitAutoPush:
    def __init__(self, repo_path=".", debug=False):
        self.repo_path = Path(repo_path).resolve()
        self.git_path = self.repo_path / ".git"
        self.debug = debug
        self.last_error = None
        self.github_cli_available = self.check_github_cli()
        
    def check_github_cli(self):
        """GitHub CLI (gh) が利用可能かチェック"""
        try:
            result = subprocess.run(
                "gh --version",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                self.debug_print("GitHub CLI (gh) が利用可能です")
                return True
            else:
                self.debug_print("GitHub CLI (gh) が見つかりません")
                return False
        except Exception as e:
            self.debug_print(f"GitHub CLI チェックエラー: {e}")
            return False
    
    def check_github_auth(self):
        """GitHub CLI の認証状態をチェック"""
        if not self.github_cli_available:
            return False
        
        try:
            result = subprocess.run(
                "gh auth status",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                self.debug_print("GitHub CLI 認証済み")
                return True
            else:
                self.debug_print("GitHub CLI 認証が必要")
                return False
        except Exception as e:
            self.debug_print(f"GitHub CLI 認証チェックエラー: {e}")
            return False
    
    def get_repo_name(self):
        """リポジトリ名を取得"""
        return self.repo_path.name
    
    def get_github_username(self):
        """GitHub ユーザー名を取得"""
        if not self.github_cli_available:
            return None
        
        try:
            result = subprocess.run(
                "gh api user",
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                user_data = json.loads(result.stdout)
                username = user_data.get('login')
                self.debug_print(f"GitHub ユーザー名: {username}")
                return username
        except Exception as e:
            self.debug_print(f"GitHub ユーザー名取得エラー: {e}")
        
        return None
    
    def check_remote_repo_exists(self):
        """リモートリポジトリが存在するかチェック"""
        if not self.github_cli_available:
            return None
        
        repo_name = self.get_repo_name()
        username = self.get_github_username()
        
        if not username:
            return None
        
        try:
            result = subprocess.run(
                f"gh repo view {username}/{repo_name}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.debug_print(f"GitHub リポジトリ {username}/{repo_name} が存在します")
                return True
            else:
                self.debug_print(f"GitHub リポジトリ {username}/{repo_name} が見つかりません")
                return False
        except Exception as e:
            self.debug_print(f"リモートリポジトリチェックエラー: {e}")
            return None
    
    def create_github_repo(self):
        """GitHub リポジトリを作成"""
        if not self.github_cli_available:
            print("❌ GitHub CLI (gh) が利用できません。手動でリポジトリを作成してください。")
            return False
        
        if not self.check_github_auth():
            print("❌ GitHub CLI の認証が必要です。'gh auth login' を実行してください。")
            return False
        
        repo_name = self.get_repo_name()
        
        print(f"📦 GitHub リポジトリ '{repo_name}' を作成しています...")
        
        # リポジトリの可視性を選択
        print("\nリポジトリの可視性を選択してください:")
        print("1. public (公開)")
        print("2. private (非公開)")
        
        while True:
            choice = input("選択 (1/2): ").strip()
            if choice == "1":
                visibility = "--public"
                break
            elif choice == "2":
                visibility = "--private"
                break
            else:
                print("1 または 2 を選択してください")
        
        # 説明文を入力
        description = self.get_user_input("リポジトリの説明 (オプション)", "")
        
        # GitHub リポジトリ作成コマンドを構築
        cmd = f"gh repo create {repo_name} {visibility}"
        if description:
            cmd += f' --description "{description}"'
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            
            if result.returncode == 0:
                print(f"✅ GitHub リポジトリ '{repo_name}' を作成しました")
                
                # リモートを追加
                username = self.get_github_username()
                if username:
                    remote_url = f"https://github.com/{username}/{repo_name}.git"
                    add_remote_result = self.run_command(f"git remote add origin {remote_url}")
                    if add_remote_result:
                        print(f"✅ リモートリポジトリを追加しました: {remote_url}")
                        return True
                    else:
                        print("⚠️  リモートリポジトリの追加に失敗しました")
                        return False
                else:
                    print("⚠️  GitHub ユーザー名の取得に失敗しました")
                    return False
            else:
                print(f"❌ GitHub リポジトリの作成に失敗しました: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ GitHub リポジトリ作成エラー: {e}")
            return False
    
    def handle_github_repository(self):
        """GitHub リポジトリの確認と作成処理"""
        if not self.github_cli_available:
            print("ℹ️  GitHub CLI が利用できません。手動でリポジトリを確認してください。")
            return True
        
        # リモートリポジトリの存在確認
        repo_exists = self.check_remote_repo_exists()
        
        if repo_exists is True:
            print("✅ GitHub リポジトリが存在します")
            return True
        elif repo_exists is False:
            print("⚠️  GitHub リポジトリが見つかりません")
            
            if self.confirm_action("GitHub リポジトリを作成しますか？"):
                return self.create_github_repo()
            else:
                print("GitHub リポジトリの作成をスキップしました")
                print("⚠️  プッシュ時にエラーが発生する可能性があります")
                return True
        else:
            print("ℹ️  GitHub リポジトリの確認をスキップしました")
            return True
    
    def run_command(self, command, cwd=None):
        """コマンドを実行"""
        if cwd is None:
            cwd = self.repo_path
        
        try:
            self.debug_print(f"実行中: {command}")
            # Windows環境での文字エンコーディング問題を解決
            if os.name == 'nt':
                # Windowsの場合はUTF-8を強制し、エラー時は無視
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                # Unix系の場合は通常通り
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            
            # git initは成功時でも標準エラー出力に出力することがある
            if result.returncode == 0:
                self.debug_print(f"成功: stdout={result.stdout}, stderr={result.stderr}")
                return result
            else:
                self.last_error = result.stderr
                self.debug_print(f"失敗: returncode={result.returncode}, stderr={result.stderr}")
                return None
        except UnicodeDecodeError as e:
            self.debug_print(f"文字エンコーディングエラー: {e}")
            # 文字エンコーディングエラーの場合は、バイナリモードで再実行
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True
                )
                # バイナリを適切にデコード
                stdout = result.stdout.decode('utf-8', errors='ignore') if result.stdout else ""
                stderr = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""
                
                # 結果オブジェクトを作成
                class Result:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr
                
                decoded_result = Result(result.returncode, stdout, stderr)
                
                if result.returncode == 0:
                    self.debug_print(f"成功 (デコード後): stdout={stdout}, stderr={stderr}")
                    return decoded_result
                else:
                    self.last_error = stderr
                    self.debug_print(f"失敗 (デコード後): returncode={result.returncode}, stderr={stderr}")
                    return None
            except Exception as fallback_e:
                self.last_error = str(fallback_e)
                self.debug_print(f"フォールバック実行も失敗: {fallback_e}")
                return None
        except Exception as e:
            self.last_error = str(e)
            self.debug_print(f"例外: {e}")
            return None
    
    def debug_print(self, message):
        """デバッグメッセージを出力"""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def init_git_repo(self):
        """Gitリポジトリを初期化"""
        print("🔧 Gitリポジトリを初期化しています...")
        
        # 既にGitリポジトリの場合は成功として扱う
        if self.is_git_repo():
            print("✅ 既にGitリポジトリとして初期化されています")
            return True
        
        result = self.run_command("git init")
        if result:
            print("✅ Gitリポジトリを初期化しました")
            return True
        else:
            print("❌ Gitリポジトリの初期化に失敗しました")
            if hasattr(self, 'last_error') and self.last_error:
                print(f"エラー詳細: {self.last_error}")
            return False
    
    def is_git_repo(self):
        """Gitリポジトリかどうかをチェック"""
        return self.git_path.exists()
    
    def get_user_input(self, prompt, default=None):
        """ユーザー入力を取得"""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{prompt}: ").strip()
    
    def confirm_action(self, message):
        """アクションの確認"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("'y' または 'n' を入力してください")
    
    def check_git_processes(self):
        """実行中のGitプロセスをチェック"""
        self.debug_print("実行中のGitプロセスをチェック中...")
        try:
            # Windowsの場合
            if os.name == 'nt':
                result = subprocess.run(
                    'tasklist /FI "IMAGENAME eq git.exe"',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if "git.exe" in result.stdout:
                    print("⚠️  実行中のGitプロセスが見つかりました:")
                    print(result.stdout)
                    return True
            # Unix系の場合
            else:
                result = subprocess.run(
                    'ps aux | grep git',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                git_processes = [line for line in result.stdout.split('\n') if 'git' in line and 'grep' not in line]
                if git_processes:
                    print("⚠️  実行中のGitプロセスが見つかりました:")
                    for process in git_processes:
                        print(process)
                    return True
            
            self.debug_print("実行中のGitプロセスはありません")
            return False
        except Exception as e:
            self.debug_print(f"プロセスチェックエラー: {e}")
            return False
    
    def clean_git_locks(self):
        """全てのGitロックファイルを強制的にクリーンアップ"""
        print("🧹 Gitロックファイルを強制クリーンアップ中...")
        lock_patterns = [
            "index.lock",
            "HEAD.lock", 
            "config.lock",
            "refs/heads/*.lock",
            "refs/remotes/*/**.lock"
        ]
        
        cleaned = 0
        for pattern in lock_patterns:
            lock_path = self.git_path / pattern
            # 直接のファイル
            if lock_path.exists():
                try:
                    lock_path.unlink()
                    print(f"✅ 削除: {lock_path}")
                    cleaned += 1
                except Exception as e:
                    print(f"❌ 削除失敗: {lock_path} - {e}")
            
            # パターンマッチング
            if "*" in pattern:
                parent_dir = self.git_path / pattern.split("*")[0].rstrip("/")
                if parent_dir.exists():
                    for lock_file in parent_dir.rglob("*.lock"):
                        try:
                            lock_file.unlink()
                            print(f"✅ 削除: {lock_file}")
                            cleaned += 1
                        except Exception as e:
                            print(f"❌ 削除失敗: {lock_file} - {e}")
        
        if cleaned > 0:
            print(f"🎯 {cleaned}個のロックファイルを削除しました")
        else:
            print("ℹ️  削除するロックファイルはありませんでした")
        
        return cleaned > 0
    
    def check_git_locks(self):
        """Gitロックファイルをチェック"""
        self.debug_print("Gitロックファイルをチェック中...")
        lock_files = [
            self.git_path / "index.lock",
            self.git_path / "HEAD.lock",
            self.git_path / "config.lock"
        ]
        
        found_locks = []
        for lock_file in lock_files:
            if lock_file.exists():
                print(f"⚠️  ロックファイル発見: {lock_file}")
                found_locks.append(lock_file)
        
        if found_locks:
            print("ロックファイルが見つかりました。以下から選択してください:")
            print("1. 個別に確認して削除")
            print("2. 全て削除")
            print("3. スキップ")
            
            choice = input("選択 (1/2/3): ").strip()
            
            if choice == "1":
                for lock_file in found_locks:
                    if self.confirm_action(f"{lock_file}を削除しますか？"):
                        try:
                            lock_file.unlink()
                            print(f"✅ ロックファイル削除: {lock_file}")
                        except Exception as e:
                            print(f"❌ ロックファイル削除失敗: {lock_file} - {e}")
            elif choice == "2":
                return self.clean_git_locks()
            else:
                print("ロックファイルの処理をスキップしました")
            
            return True
        else:
            self.debug_print("ロックファイルはありません")
            return False
    
    def get_status(self):
        """git statusを取得"""
        result = self.run_command("git status --porcelain -u")
        if result:
            return result.stdout.strip()
        return ""
    
    def has_changes(self):
        """変更があるかどうかをチェック"""
        status = self.get_status()
        return bool(status)
    
    def get_branches(self):
        """利用可能なブランチを取得"""
        result = self.run_command("git branch")
        if result:
            branches = []
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().replace('* ', '')
                if branch:
                    branches.append(branch)
            return branches
        return ["main"]
    
    def get_current_branch(self):
        """現在のブランチを取得"""
        result = self.run_command("git branch --show-current")
        if result and result.stdout.strip():
            return result.stdout.strip()
        return "main"
    
    def add_all(self):
        """すべての変更をステージング"""
        print("📁 変更をステージング中...")
        result = self.run_command("git add .")
        if result:
            print("✅ ステージング完了")
            return True
        return False
    
    def commit(self, message=None):
        """コミットを実行"""
        if not message:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_message = f"Auto commit: {timestamp}"
            message = self.get_user_input("コミットメッセージを入力してください", default_message)
        
        print(f"💾 コミット中: {message}")
        result = self.run_command(f'git commit -m "{message}"')
        if result:
            print("✅ コミット完了")
            return True
        return False
    
    def push(self, branch=None):
        """プッシュを実行"""
        if not branch:
            current_branch = self.get_current_branch()
            branches = self.get_branches()
            
            print(f"\n利用可能なブランチ: {', '.join(branches)}")
            print(f"現在のブランチ: {current_branch}")
            
            branch = self.get_user_input("プッシュするブランチを選択してください", current_branch)
            if branch not in branches:
                print(f"⚠️  ブランチ '{branch}' は存在しません。新しいブランチとして作成されます。")
        
        if not self.confirm_action(f"'{branch}' ブランチにプッシュしますか？"):
            print("プッシュをキャンセルしました")
            return False
        
        print(f"🚀 {branch}ブランチにプッシュ中...")
        result = self.run_command(f"git push origin {branch}")
        if result:
            print("✅ プッシュ完了")
            return True
        else:
            # リモートリポジトリが存在しない可能性をチェック
            print("🔄 プッシュに失敗しました。リモートリポジトリを確認中...")
            
            if self.handle_github_repository():
                # リモートリポジトリが作成された場合、再度プッシュを試行
                print("🔄 リモートリポジトリが設定されました。再度プッシュします...")
                result = self.run_command(f"git push -u origin {branch}")
                if result:
                    print("✅ プッシュ完了")
                    return True
            else:
                # 初回プッシュの場合、upstream を設定
                print("🔄 初回プッシュのようです。upstream を設定してリトライします...")
                result = self.run_command(f"git push -u origin {branch}")
                if result:
                    print("✅ プッシュ完了")
                    return True
        return False
    
    def open_github_repo_in_browser(self):
        """GitHub リポジトリをブラウザで開く"""
        if not self.github_cli_available:
            print("GitHub CLI が利用できないため、ブラウザでの確認をスキップします")
            return False
        
        repo_name = self.get_repo_name()
        username = self.get_github_username()
        
        if not username:
            print("GitHub ユーザー名を取得できませんでした")
            return False
        
        repo_url = f"https://github.com/{username}/{repo_name}"
        
        try:
            print(f"🌐 GitHubリポジトリをブラウザで開きます: {repo_url}")
            webbrowser.open(repo_url)
            return True
        except Exception as e:
            print(f"❌ ブラウザでの表示に失敗しました: {e}")
            return False
    
    def confirm_browser_check(self):
        """ブラウザでの確認を提案"""
        if self.confirm_action("GitHubリポジトリをブラウザで確認しますか？"):
            return self.open_github_repo_in_browser()
        return False
    
    def auto_push(self, message=None, branch=None, force=False):
        """自動プッシュのメイン処理"""
        print("🤖 GIT Auto Push 開始")
        print(f"📂 リポジトリ: {self.repo_path}")
        
        # デバッグ情報
        self.debug_print(f"作業ディレクトリ: {os.getcwd()}")
        self.debug_print(f"指定リポジトリ: {self.repo_path}")
        self.debug_print(f"リポジトリ存在チェック: {self.repo_path.exists()}")
        self.debug_print(f".gitパス: {self.git_path}")
        self.debug_print(f".gitパス存在チェック: {self.git_path.exists()}")
        
        # リポジトリディレクトリの存在確認
        if not self.repo_path.exists():
            print(f"❌ エラー: 指定されたディレクトリが見つかりません: {self.repo_path}")
            return False
        
        # Gitプロセスとロックファイルをチェック
        if self.check_git_processes():
            if not self.confirm_action("実行中のGitプロセスが見つかりました。続行しますか？"):
                print("処理を中止しました")
                return False
        
        if self.check_git_locks():
            print("ロックファイルの処理を完了しました")
        
        # Gitリポジトリかチェック
        if not self.is_git_repo():
            print("⚠️  Gitリポジトリではありません。")
            if not self.confirm_action("Gitリポジトリを初期化しますか？"):
                print("処理を中止しました")
                return False
            if not self.init_git_repo():
                print("❌ エラー: Gitリポジトリの初期化に失敗しました")
                return False
        
        # ステータスを表示
        self.debug_print("git statusを取得中...")
        status_result = self.run_command("git status --porcelain -u")
        if status_result and status_result.stdout.strip():
            print("\n📝 変更されたファイル:")
            for line in status_result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            self.debug_print("変更されたファイルはありません")
        
        # ステージングの確認
        if not self.confirm_action("変更をステージングしますか？"):
            print("処理を中止しました")
            return False
        
        # 変更をステージング
        if not self.add_all():
            return False
        
        # コミットの確認
        if not self.confirm_action("コミットしますか？"):
            print("処理を中止しました")
            return False
        
        # コミット
        if not self.commit(message):
            return False
        
        # プッシュの確認とプッシュ
        if not self.push(branch):
            return False
        
        # ブラウザでの確認
        self.confirm_browser_check()
        
        print("🎉 自動プッシュ完了!")
        return True

def main():
    parser = argparse.ArgumentParser(description="GIT Auto Push Script")
    parser.add_argument("repo", help="リポジトリパス（必須）")
    parser.add_argument("--message", "-m", help="コミットメッセージ")
    parser.add_argument("--branch", "-b", help="プッシュするブランチ")
    parser.add_argument("--force", "-f", action="store_true", help="強制プッシュ")
    parser.add_argument("--debug", "-d", action="store_true", help="デバッグモード")
    
    args = parser.parse_args()
    
    # 自動プッシュ実行
    auto_push = GitAutoPush(args.repo, debug=args.debug)
    success = auto_push.auto_push(
        message=args.message,
        branch=args.branch,
        force=args.force
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()