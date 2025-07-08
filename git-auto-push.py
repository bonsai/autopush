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
            result = subprocess.run("gh --version", shell=True, capture_output=True)
            if result.returncode == 0:
                self.debug_print("✅ GitHub CLI (gh) が利用可能です")
                return True
            else:
                self.debug_print("❌ GitHub CLI (gh) が見つかりません")
                return False
        except Exception as e:
            self.debug_print(f"⚠️ GitHub CLI チェックエラー: {e}")
            return False

    def check_github_auth(self):
        """GitHub CLI の認証状態をチェック"""
        if not self.github_cli_available:
            return False

        try:
            result = subprocess.run("gh auth status", shell=True, capture_output=True)
            if result.returncode == 0:
                self.debug_print("✅ GitHub CLI 認証済み")
                return True
            else:
                self.debug_print("❌ GitHub CLI 認証が必要")
                return False
        except Exception as e:
            self.debug_print(f"⚠️ GitHub CLI 認証チェックエラー: {e}")
            return False

    def get_repo_name(self):
        """リポジトリ名を取得"""
        return self.repo_path.name

    def get_github_username(self):
        """GitHub ユーザー名を取得"""
        if not self.github_cli_available:
            return None

        try:
            result = subprocess.run("gh api user", shell=True, capture_output=True)
            if result.returncode == 0:
                stdout = (
                    result.stdout.decode("utf-8", errors="ignore")
                    if result.stdout
                    else ""
                )
                user_data = json.loads(stdout)
                username = user_data.get("login")
                self.debug_print(f"👤 GitHub ユーザー名: {username}")
                return username
        except Exception as e:
            self.debug_print(f"⚠️ GitHub ユーザー名取得エラー: {e}")

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
                text=True,
            )
            if result.returncode == 0:
                self.debug_print(
                    f"✅ GitHub リポジトリ {username}/{repo_name} が存在します"
                )
                return True
            else:
                self.debug_print(
                    f"❌ GitHub リポジトリ {username}/{repo_name} が見つかりません"
                )
                return False
        except Exception as e:
            self.debug_print(f"⚠️ リモートリポジトリチェックエラー: {e}")
            return None

    def create_github_repo(self):
        """GitHub リポジトリを作成し、リモート追加まで自動化"""
        if not self.github_cli_available:
            print(
                "❌ GitHub CLI (gh) が利用できません。手動でリポジトリを作成してください。"
            )
            return False
        if not self.check_github_auth():
            print(
                "❌ GitHub CLI の認証が必要です。'gh auth login' を実行してください。"
            )
            return False
        repo_name = self.get_repo_name()
        print(f"📦 GitHub リポジトリ '{repo_name}' を作成しています...")
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
        description = self.get_user_input("リポジトリの説明 (オプション)", "")
        cmd = (
            f"gh repo create {repo_name} {visibility} --source=. --remote=origin --push"
        )
        if description:
            cmd += f' --description "{description}"'
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, cwd=self.repo_path
            )
            if result.returncode == 0:
                print(
                    f"✅ GitHub リポジトリ '{repo_name}' を作成し、リモート追加・初回pushまで完了しました"
                )
                return True
            else:
                stderr = (
                    result.stderr.decode("utf-8", errors="ignore")
                    if result.stderr
                    else ""
                )
                print(f"❌ GitHub リポジトリの作成に失敗しました: {stderr}")
                return False
        except Exception as e:
            print(f"❌ GitHub リポジトリ作成エラー: {e}")
            return False

    def handle_github_repository(self):
        """GitHub リポジトリの確認と作成処理"""
        if not self.github_cli_available:
            print(
                "ℹ️  GitHub CLI が利用できません。手動でリポジトリを確認してください。"
            )
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
            self.debug_print(f"🔍 実行中: {command}")

            # Windows環境での文字エンコーディング問題を解決
            # バイナリモードで実行して、適切にデコード
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True)

            # バイナリ出力を安全にデコード
            def safe_decode(data):
                if not data:
                    return ""

                # 複数のエンコーディングを試行
                encodings = ["utf-8", "cp932", "shift_jis", "iso-8859-1"]

                for encoding in encodings:
                    try:
                        return data.decode(encoding)
                    except (UnicodeDecodeError, LookupError):
                        continue

                # 全て失敗した場合は、エラーを無視してデコード
                return data.decode("utf-8", errors="ignore")

            stdout = safe_decode(result.stdout)
            stderr = safe_decode(result.stderr)

            # 結果オブジェクトを作成
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            decoded_result = Result(
                result.returncode, stdout, stderr
            )  # git initは成功時でも標準エラー出力に出力することがある
            if decoded_result.returncode == 0:
                self.debug_print(f"✅ 成功: stdout={stdout}, stderr={stderr}")
                return decoded_result
            else:
                self.last_error = stderr
                self.debug_print(
                    f"❌ 失敗: returncode={decoded_result.returncode}, stderr={stderr}"
                )
                return None
        except Exception as e:
            self.last_error = str(e)
            self.debug_print(f"⚠️ 例外: {e}")
            return None

    def debug_print(self, message):
        """デバッグメッセージを出力"""
        if self.debug:
            print(f"🔍 {message}")

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
            if hasattr(self, "last_error") and self.last_error:
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
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            else:
                print("'y' または 'n' を入力してください")

    def check_git_processes(self):
        """実行中のGitプロセスをチェック"""
        self.debug_print("🔍 実行中のGitプロセスをチェック中...")
        try:
            # Windowsの場合
            if os.name == "nt":
                result = subprocess.run(
                    'tasklist /FI "IMAGENAME eq git.exe"',
                    shell=True,
                    capture_output=True,
                )
                stdout = (
                    result.stdout.decode("utf-8", errors="ignore")
                    if result.stdout
                    else ""
                )
                if "git.exe" in stdout:
                    print("⚠️  実行中のGitプロセスが見つかりました:")
                    print(stdout)
                    return True
            # Unix系の場合
            else:
                result = subprocess.run(
                    "ps aux | grep git", shell=True, capture_output=True
                )
                stdout = (
                    result.stdout.decode("utf-8", errors="ignore")
                    if result.stdout
                    else ""
                )
                git_processes = [
                    line
                    for line in stdout.split("\n")
                    if "git" in line and "grep" not in line
                ]
                if git_processes:
                    print("⚠️  実行中のGitプロセスが見つかりました:")
                    for process in git_processes:
                        print(process)
                    return True

            self.debug_print("✅ 実行中のGitプロセスはありません")
            return False
        except Exception as e:
            self.debug_print(f"⚠️ プロセスチェックエラー: {e}")
            return False

    def clean_git_locks(self):
        """全てのGitロックファイルを強制的にクリーンアップ"""
        print("🧹 Gitロックファイルを強制クリーンアップ中...")
        lock_patterns = [
            "index.lock",
            "HEAD.lock",
            "config.lock",
            "refs/heads/*.lock",
            "refs/remotes/*/**.lock",
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
        self.debug_print("🔍 Gitロックファイルをチェック中...")
        lock_files = [
            self.git_path / "index.lock",
            self.git_path / "HEAD.lock",
            self.git_path / "config.lock",
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
            self.debug_print("✅ ロックファイルはありません")
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
            for line in result.stdout.strip().split("\n"):
                branch = line.strip().replace("* ", "")
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

    def ensure_git_identity(self):
        # ユーザー名
        name_result = self.run_command("git config user.name")
        if not name_result or not name_result.stdout.strip():
            self.run_command('git config user.name "Auto Committer"')
        # メールアドレス
        email_result = self.run_command("git config user.email")
        if not email_result or not email_result.stdout.strip():
            self.run_command('git config user.email "autocommit@example.com"')

    def commit(self, message=None):
        self.ensure_git_identity()  # ユーザー名・メールアドレスを自動設定
        if not message:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_message = f"Auto commit: {timestamp}"
            message = self.get_user_input(
                "コミットメッセージを入力してください", default_message
            )

        print(f"💾 コミット中: {message}")
        result = self.run_command(f'git commit -m "{message}"')
        if result:
            print("✅ コミット完了")
            return True
        return False

    def push(self, branch=None, force=False):
        """プッシュを実行（リモートがなければ自動作成）"""
        if not branch:
            current_branch = self.get_current_branch()
            branches = self.get_branches()
            print(f"\n利用可能なブランチ: {', '.join(branches)}")
            print(f"現在のブランチ: {current_branch}")
            branch = self.get_user_input(
                "プッシュするブランチを選択してください", current_branch
            )
            if branch not in branches:
                print(
                    f"⚠️  ブランチ '{branch}' は存在しません。新しいブランチとして作成されます。"
                )

        if not self.confirm_action(f"'{branch}' ブランチにプッシュしますか？"):
            print("プッシュをキャンセルしました")
            return False

        print(f"🚀 {branch}ブランチにプッシュ中...")
        push_cmd = f"git push origin {branch}"
        if force:
            push_cmd += " --force"
        result = self.run_command(push_cmd)
        if result:
            print("✅ プッシュ完了")
            return True
        else:
            # リモートリポジトリが存在しない場合は自動作成
            print("🔄 プッシュに失敗しました。リモートリポジトリを確認中...")
            remote_url_result = self.run_command("git remote get-url origin")
            if not remote_url_result or not remote_url_result.stdout.strip():
                print(
                    "⚠️  リモートリポジトリが設定されていません。GitHubリポジトリを作成します。"
                )
                if self.create_github_repo():
                    print(
                        "🔄 リモートリポジトリが設定されました。再度プッシュします..."
                    )
                    result = self.run_command(f"git push -u origin {branch}")
                    if result:
                        print("✅ プッシュ完了")
                        return True
                    else:
                        print("❌ プッシュに失敗しました")
                        return False
                else:
                    print("❌ GitHubリポジトリの作成に失敗しました")
                    return False
            else:
                # 既存リモートがある場合は upstream 設定で再試行
                print("🔄 初回プッシュのようです。upstream を設定してリトライします...")
                result = self.run_command(f"git push -u origin {branch}")
                if result:
                    print("✅ プッシュ完了")
                    return True
        return False

    def open_github_repo_in_browser(self):
        """GitHub リポジトリをブラウザで開く"""
        if not self.github_cli_available:
            print("⚠️  GitHub CLI が利用できないため、ブラウザでの確認をスキップします")
            return False

        repo_name = self.get_repo_name()
        username = self.get_github_username()

        if not username:
            print("⚠️  GitHub ユーザー名を取得できませんでした")
            return False

        repo_url = f"https://github.com/{username}/{repo_name}"

        try:
            print(f"🌐 GitHubリポジトリをブラウザで開いています...")
            print(f"🔗 URL: {repo_url}")
            webbrowser.open(repo_url)
            print("✅ ブラウザでGitHubリポジトリを開きました")
            return True
        except Exception as e:
            print(f"❌ ブラウザでの表示に失敗しました: {e}")
            print(f"🔗 手動で以下のURLにアクセスしてください: {repo_url}")
            return False

    def confirm_browser_check(self):
        """ブラウザでの確認を自動実行"""
        print("🌐 GitHubリポジトリをブラウザで自動確認します...")
        return self.open_github_repo_in_browser()

    def check_branch_divergence(self):
        """ブランチの分岐状況をチェック"""
        print("🔍 ブランチの分岐状況をチェックしています...")

        # git statusの詳細な出力を取得
        result = self.run_command("git status --porcelain=v1 --branch")
        if not result:
            return False

        status_lines = result.stdout.strip().split("\n")
        branch_info = status_lines[0] if status_lines else ""

        # ブランチの分岐を検出
        if "ahead" in branch_info and "behind" in branch_info:
            print("⚠️  ブランチが分岐しています！")
            print(f"📊 状況: {branch_info}")

            # 詳細な状況を表示
            ahead_match = __import__("re").search(r"ahead (\d+)", branch_info)
            behind_match = __import__("re").search(r"behind (\d+)", branch_info)

            if ahead_match and behind_match:
                ahead = ahead_match.group(1)
                behind = behind_match.group(1)
                print(f"📤 ローカルが {ahead} コミット先行")
                print(f"📥 リモートが {behind} コミット先行")

            return True
        elif "ahead" in branch_info:
            ahead_match = __import__("re").search(r"ahead (\d+)", branch_info)
            if ahead_match:
                ahead = ahead_match.group(1)
                print(f"✅ ローカルが {ahead} コミット先行（プッシュ可能）")
        elif "behind" in branch_info:
            behind_match = __import__("re").search(r"behind (\d+)", branch_info)
            if behind_match:
                behind = behind_match.group(1)
                print(f"📥 リモートが {behind} コミット先行（プル必要）")
                return True
        else:
            print("✅ ブランチは同期されています")

        return False

    def handle_branch_divergence(self):
        """ブランチの分岐を処理"""
        print("\n🔄 ブランチの分岐を解決します")
        print("以下の選択肢があります:")
        print("1. git pull --rebase (推奨: リモートの変更を取得してリベース)")
        print("2. git pull (リモートの変更を取得してマージ)")
        print("3. git push --force-with-lease (慎重: ローカルの変更を強制プッシュ)")
        print("4. スキップ (手動で解決)")

        while True:
            choice = input("選択 (1/2/3/4): ").strip()

            if choice == "1":
                return self.pull_rebase()
            elif choice == "2":
                return self.pull_merge()
            elif choice == "3":
                if self.confirm_action(
                    "⚠️  強制プッシュは危険です。リモートの変更が失われる可能性があります。続行しますか？"
                ):
                    return self.force_push()
                else:
                    continue
            elif choice == "4":
                print("手動での解決を選択しました")
                return True
            else:
                print("1, 2, 3, 4 のいずれかを選択してください")

    def pull_rebase(self):
        """git pull --rebase を実行"""
        print("🔄 git pull --rebase を実行中...")
        result = self.run_command("git pull --rebase")
        if result:
            print("✅ リベースが完了しました")
            return True
        else:
            print("❌ リベースに失敗しました")
            if "CONFLICT" in str(self.last_error):
                print("⚠️  マージコンフリクトが発生しました")
                self.handle_merge_conflict()
            return False

    def pull_merge(self):
        """git pull を実行"""
        print("🔄 git pull を実行中...")
        result = self.run_command("git pull")
        if result:
            print("✅ マージが完了しました")
            return True
        else:
            print("❌ マージに失敗しました")
            if "CONFLICT" in str(self.last_error):
                print("⚠️  マージコンフリクトが発生しました")
                self.handle_merge_conflict()
            return False

    def force_push(self):
        """git push --force-with-lease を実行"""
        current_branch = self.get_current_branch()
        print(f"🚀 {current_branch} ブランチに強制プッシュ中...")
        result = self.run_command(
            f"git push --force-with-lease origin {current_branch}"
        )
        if result:
            print("✅ 強制プッシュが完了しました")
            return True
        else:
            print("❌ 強制プッシュに失敗しました")
            return False

    def handle_merge_conflict(self):
        """マージコンフリクトを処理"""
        print("🔧 マージコンフリクトの解決が必要です")
        print("以下の選択肢があります:")
        print("1. VSCodeでコンフリクトを解決")
        print("2. 手動で解決")
        print("3. マージを中止")

        while True:
            choice = input("選択 (1/2/3): ").strip()

            if choice == "1":
                try:
                    subprocess.run("code .", shell=True, cwd=self.repo_path)
                    print("✅ VSCodeを開きました。コンフリクトを解決してください")
                    input("コンフリクトを解決したら Enter キーを押してください...")
                    return True
                except Exception as e:
                    print(f"❌ VSCodeの起動に失敗しました: {e}")
                    continue
            elif choice == "2":
                print("手動でコンフリクトを解決してください")
                input("コンフリクトを解決したら Enter キーを押してください...")
                return True
            elif choice == "3":
                result = self.run_command("git merge --abort")
                if result:
                    print("✅ マージを中止しました")
                else:
                    print("❌ マージの中止に失敗しました")
                return False
            else:
                print("1, 2, 3 のいずれかを選択してください")

    def check_working_tree_clean(self):
        """ワーキングツリーがクリーンかチェック"""
        status = self.get_status()
        if not status:
            print("ℹ️  ワーキングツリーはクリーンです（変更なし）")
            return True
        return False

    def auto_push(self, message=None, branch=None, force=False):
        """自動プッシュのメイン処理"""
        print("🤖 GIT Auto Push 開始")
        print(f"📂 リポジトリ: {self.repo_path}")

        # 実行結果を記録する辞書
        execution_results = {
            "git_init": False,
            "branch_sync": False,
            "staging": False,
            "commit": False,
            "push": False,
            "browser_open": False,
        }

        # デバッグ情報
        self.debug_print(f"📁 作業ディレクトリ: {os.getcwd()}")
        self.debug_print(f"📂 指定リポジトリ: {self.repo_path}")
        self.debug_print(f"✅ リポジトリ存在チェック: {self.repo_path.exists()}")
        self.debug_print(f"🔧 .gitパス: {self.git_path}")
        self.debug_print(f"✅ .gitパス存在チェック: {self.git_path.exists()}")

        # リポジトリディレクトリの存在確認
        if not self.repo_path.exists():
            print(
                f"❌ エラー: 指定されたディレクトリが見つかりません: {self.repo_path}"
            )
            self.print_execution_summary(execution_results)
            return False

        # Gitプロセスとロックファイルをチェック
        if self.check_git_processes():
            if not self.confirm_action(
                "実行中のGitプロセスが見つかりました。続行しますか？"
            ):
                print("処理を中止しました")
                self.print_execution_summary(execution_results)
                return False

        if self.check_git_locks():
            print("ロックファイルの処理を完了しました")

        # Gitリポジトリかチェック
        if not self.is_git_repo():
            print("⚠️  Gitリポジトリではありません。")
            if not self.confirm_action("Gitリポジトリを初期化しますか？"):
                print("処理を中止しました")
                self.print_execution_summary(execution_results)
                return False
            if not self.init_git_repo():
                print("❌ エラー: Gitリポジトリの初期化に失敗しました")
                self.print_execution_summary(execution_results)
                return False
            execution_results["git_init"] = True

        # ブランチの分岐状況をチェック
        if self.check_branch_divergence():
            if self.handle_branch_divergence():
                execution_results["branch_sync"] = True
            else:
                print("❌ ブランチの分岐解決に失敗しました")
                self.print_execution_summary(execution_results)
                return False
        else:
            execution_results["branch_sync"] = True

        # ステータスを表示
        self.debug_print("📝 git statusを取得中...")
        status_result = self.run_command("git status --porcelain -u")
        if status_result and status_result.stdout.strip():
            print("\n📝 変更されたファイル:")
            for line in status_result.stdout.strip().split("\n"):
                print(f"  {line}")
        else:
            self.debug_print("✅ 変更されたファイルはありません")

        # ワーキングツリーがクリーンな場合の処理
        if self.check_working_tree_clean():
            print("✅ すべての変更は既にコミット済みです")
            execution_results["staging"] = True
            execution_results["commit"] = True

            # プッシュの確認
            if self.confirm_action("最新の状態をリモートにプッシュしますか？"):
                if self.push(branch):
                    execution_results["push"] = True
                else:
                    print("❌ プッシュに失敗しました")
                    self.print_execution_summary(execution_results)
                    return False
            else:
                print("プッシュをスキップしました")
                execution_results["push"] = True  # スキップも成功として扱う

            # ブラウザでの確認
            print("\n" + "=" * 50)
            print("🎉 すべての操作が完了しました！")
            print("=" * 50)

            if self.confirm_browser_check():
                execution_results["browser_open"] = True
            else:
                print("⚠️  ブラウザでの確認に失敗しました")

            # 実行結果サマリーを表示
            self.print_execution_summary(execution_results)
            print("🎉 自動プッシュ完了!")
            return True

        # ステージングの確認
        if not self.confirm_action("変更をステージングしますか？"):
            print("処理を中止しました")
            self.print_execution_summary(execution_results)
            return False

        # 変更をステージング
        if not self.add_all():
            print("❌ ステージングに失敗しました")
            self.print_execution_summary(execution_results)
            return False
        execution_results["staging"] = True

        # コミットの確認
        if not self.confirm_action("コミットしますか？"):
            print("処理を中止しました")
            self.print_execution_summary(execution_results)
            return False

        # コミット
        if not self.commit(message):
            print("❌ コミットに失敗しました")
            self.print_execution_summary(execution_results)
            return False
        execution_results["commit"] = True

        # プッシュの確認とプッシュ
        if not self.push(branch):
            print("❌ プッシュに失敗しました")
            self.print_execution_summary(execution_results)
            return False
        execution_results["push"] = True

        # ブラウザでの確認（必須）
        print("\n" + "=" * 50)
        print("🎉 すべての操作が完了しました！")
        print("=" * 50)

        if self.confirm_browser_check():
            execution_results["browser_open"] = True
        else:
            print("⚠️  ブラウザでの確認に失敗しました")

        # 実行結果サマリーを表示
        self.print_execution_summary(execution_results)

        print("🎉 自動プッシュ完了!")
        return True

    def print_execution_summary(self, results):
        """実行結果のサマリーを表示"""
        print("\n" + "=" * 60)
        print("📊 実行結果サマリー")
        print("=" * 60)

        status_icons = {True: "✅", False: "❌"}

        print(
            f"{status_icons[results['git_init']]} Git初期化: {'成功' if results['git_init'] else '未実行/失敗'}"
        )
        print(
            f"{status_icons[results['branch_sync']]} ブランチ同期: {'成功' if results['branch_sync'] else '未実行/失敗'}"
        )
        print(
            f"{status_icons[results['staging']]} ステージング: {'成功' if results['staging'] else '未実行/失敗'}"
        )
        print(
            f"{status_icons[results['commit']]} コミット: {'成功' if results['commit'] else '未実行/失敗'}"
        )
        print(
            f"{status_icons[results['push']]} プッシュ: {'成功' if results['push'] else '未実行/失敗'}"
        )
        print(
            f"{status_icons[results['browser_open']]} ブラウザ確認: {'成功' if results['browser_open'] else '未実行/失敗'}"
        )

        # 成功した項目の数を計算
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)

        print(
            f"\n🎯 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)"
        )

        if success_count == total_count:
            print("🎉 すべての操作が正常に完了しました！")
        else:
            print("⚠️  一部の操作が失敗しました。上記の結果を確認してください。")

        print("=" * 60)


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
        message=args.message, branch=args.branch, force=args.force
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
