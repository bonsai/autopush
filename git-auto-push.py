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

class GitAutoPush:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path).resolve()
        self.git_path = self.repo_path / ".git"
        
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
            if response in ['y', 'yes', 'はい']:
                return True
            elif response in ['n', 'no', 'いいえ']:
                return False
            else:
                print("y/n で答えてください")
    
    def init_git_repo(self):
        """Gitリポジトリを初期化"""
        print("📁 Gitリポジトリを初期化中...")
        result = self.run_command("git init")
        if result:
            print("✅ Gitリポジトリを初期化しました")
            return True
        return False
    
    def run_command(self, command, capture_output=True):
        """コマンドを実行"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ エラー: {e}")
            if e.stdout:
                print(f"出力: {e.stdout}")
            if e.stderr:
                print(f"エラー: {e.stderr}")
            return None
    
    def get_status(self):
        """git statusを取得"""
        result = self.run_command("git status --porcelain")
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
            # 初回プッシュの場合、upstream を設定
            print("🔄 初回プッシュのようです。upstream を設定してリトライします...")
            result = self.run_command(f"git push -u origin {branch}")
            if result:
                print("✅ プッシュ完了")
                return True
        return False
    
    def auto_push(self, message=None, branch=None, force=False):
        """自動プッシュのメイン処理"""
        print("🤖 GIT Auto Push 開始")
        print(f"📂 リポジトリ: {self.repo_path}")
        
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
        status_result = self.run_command("git status --porcelain")
        if status_result and status_result.stdout.strip():
            print("\n📝 変更されたファイル:")
            for line in status_result.stdout.strip().split('\n'):
                print(f"  {line}")
        
        # 変更があるかチェック
        if not self.has_changes():
            print("ℹ️  変更がありません")
            return True
        
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
        
        print("🎉 自動プッシュ完了!")
        return True

def main():
    parser = argparse.ArgumentParser(description="GIT Auto Push Script")
    parser.add_argument("repo", help="リポジトリパス（必須）")
    parser.add_argument("--message", "-m", help="コミットメッセージ")
    parser.add_argument("--branch", "-b", help="プッシュするブランチ")
    parser.add_argument("--force", "-f", action="store_true", help="強制プッシュ")
    
    args = parser.parse_args()
    
    # 自動プッシュ実行
    auto_push = GitAutoPush(args.repo)
    success = auto_push.auto_push(
        message=args.message,
        branch=args.branch,
        force=args.force
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 