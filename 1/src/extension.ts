import * as vscode from 'vscode';
import { existsSync, statSync } from 'fs';
import { GitAutoPushCore, ExecutionResults } from './gitAutoPushCore';

export function activate(context: vscode.ExtensionContext) {
    console.log('Git Auto Push extension is now active!');

    const disposable = vscode.commands.registerCommand('git-auto-push.push', async () => {
        const gitAutoPush = new GitAutoPush();
        await gitAutoPush.execute();
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}

class GitAutoPush {
    private readonly workspaceRoot: string;
    private readonly outputChannel: vscode.OutputChannel;
    private readonly config: vscode.WorkspaceConfiguration;
    private readonly core: GitAutoPushCore;
    
    private static readonly EXTENSION_NAME = 'Git Auto Push';
    private static readonly CONFIG_SECTION = 'gitAutoPush';

    constructor() {
        this.workspaceRoot = this.getWorkspaceRoot();
        this.outputChannel = vscode.window.createOutputChannel(GitAutoPush.EXTENSION_NAME);
        this.config = vscode.workspace.getConfiguration(GitAutoPush.CONFIG_SECTION);
        
        if (!this.workspaceRoot) {
            throw new Error('No workspace is open');
        }
        
        this.core = new GitAutoPushCore(this.workspaceRoot, this.outputChannel);
    }
    
    private getWorkspaceRoot(): string {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            return '';
        }
        
        // If there's only one folder, use it
        if (workspaceFolders.length === 1) {
            return workspaceFolders[0].uri.fsPath;
        }
        
        // If there are multiple folders, try to find the root git repo
        for (const folder of workspaceFolders) {
            const gitPath = folder.uri.fsPath + '/.git';
            if (existsSync(gitPath) && statSync(gitPath).isDirectory()) {
                return folder.uri.fsPath;
            }
        }
        
        // Default to the first folder if no git repo is found
        return workspaceFolders[0].uri.fsPath;
    }

    async execute(): Promise<void> {
        this.outputChannel.show();
        this.log('🤖 Git Auto Push 開始');

        const executionResults: ExecutionResults = {
            gitInit: false,
            branchSync: false,
            staging: false,
            commit: false,
            push: false,
            browserOpen: false
        };

        try {
            this.log(`📂 リポジトリ: ${this.workspaceRoot}`);

            // リポジトリの確認を求める
            const repoName = this.workspaceRoot.split('/').pop() || '現在のリポジトリ';
            const confirmMessage = `操作対象のリポジトリ: ${repoName}\n${this.workspaceRoot}\n\nこのリポジトリでよろしいですか？`;
            
            const confirm = await vscode.window.showInformationMessage(
                confirmMessage,
                { modal: true },
                'はい', 'キャンセル'
            );

            if (confirm !== 'はい') {
                this.log('処理をキャンセルしました');
                await vscode.window.showInformationMessage('処理をキャンセルしました');
                return;
            }
            
            this.log(`✅ リポジトリを確認しました: ${this.workspaceRoot}`);

            // ディレクトリ分析
            const analysis = await this.core.analyzeCurrentDirectory();

            if (analysis.warningMessage) {
                const shouldContinue = await vscode.window.showWarningMessage(
                    analysis.warningMessage,
                    '続行', 'キャンセル'
                );
                if (shouldContinue !== '続行') {
                    this.log('処理を中止しました');
                    return;
                }
            }

            // Gitリポジトリかチェック
            if (!analysis.isGitRepo) {
                const shouldInit = await vscode.window.showWarningMessage(
                    'Gitリポジトリではありません。初期化しますか？',
                    'はい', 'いいえ'
                );

                if (shouldInit === 'はい') {
                    await this.initGitRepository();
                    executionResults.gitInit = true;
                } else {
                    this.log('処理を中止しました');
                    return;
                }
            }

            // ブランチ分岐チェック
            if (await this.core.checkBranchDivergence()) {
                const resolved = await this.core.handleBranchDivergence();
                executionResults.branchSync = resolved;
                if (!resolved) {
                    this.log('ブランチ分岐の解決に失敗しました');
                    this.core.printExecutionSummary(executionResults);
                    return;
                }
            } else {
                executionResults.branchSync = true;
            }

            // 変更をチェック
            const hasChanges = await this.hasChanges();
            if (!hasChanges) {
                this.log('✅ 変更はありません');

                const shouldPush = await vscode.window.showInformationMessage(
                    '変更がありませんが、プッシュしますか？',
                    'はい', 'いいえ'
                );

                if (shouldPush === 'はい') {
                    await this.push();
                    executionResults.push = true;
                    executionResults.staging = true;
                    executionResults.commit = true;
                }

                this.core.printExecutionSummary(executionResults);
                return;
            }

            // ステージング
            const shouldStage = await vscode.window.showInformationMessage(
                '変更をステージングしますか？',
                'はい', 'いいえ'
            );

            if (shouldStage !== 'はい') {
                this.log('処理を中止しました');
                this.core.printExecutionSummary(executionResults);
                return;
            }

            await this.addAll();
            executionResults.staging = true;

            // コミット
            const commitMessage = await vscode.window.showInputBox({
                prompt: 'コミットメッセージを入力してください',
                value: this.config.get('defaultCommitMessage', 'Auto commit')
            });

            if (!commitMessage) {
                this.log('コミットメッセージが入力されませんでした');
                this.core.printExecutionSummary(executionResults);
                return;
            }

            await this.commit(commitMessage);
            executionResults.commit = true;

            // プッシュ
            const shouldPush = await vscode.window.showInformationMessage(
                'プッシュしますか？',
                'はい', 'いいえ'
            );

            if (shouldPush === 'はい') {
                await this.push();
                executionResults.push = true;

                // ブラウザで開く
                if (this.config.get('autoOpenBrowser', true)) {
                    await this.openInBrowser();
                    executionResults.browserOpen = true;
                }
            }

            this.log('🎉 Git Auto Push 完了！');
            vscode.window.showInformationMessage('Git Auto Push が完了しました！');
            this.core.printExecutionSummary(executionResults);

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.log(`❌ エラー: ${errorMessage}`);
            vscode.window.showErrorMessage(`Git Auto Push エラー: ${errorMessage}`);
            this.core.printExecutionSummary(executionResults);
        }
    }

    private async initGitRepository(): Promise<void> {
        this.log('🔧 Gitリポジトリを初期化中...');
        const result = await this.core.runCommand('git init');
        if (result.success) {
            this.log('✅ Gitリポジトリを初期化しました');
        } else {
            throw new Error('Gitリポジトリの初期化に失敗しました');
        }
    }

    private async hasChanges(): Promise<boolean> {
        const result = await this.core.runCommand('git status --porcelain');
        return result.success && result.stdout.trim().length > 0;
    }

    private async addAll(): Promise<void> {
        this.log('📁 変更をステージング中...');
        const result = await this.core.runCommand('git add .');
        if (result.success) {
            this.log('✅ ステージング完了');
        } else {
            throw new Error('ステージングに失敗しました');
        }
    }

    private async commit(message: string): Promise<void> {
        this.log(`💾 コミット中: ${message}`);

        // ユーザー情報の確認・設定
        await this.ensureGitIdentity();

        const result = await this.core.runCommand(`git commit -m "${message}"`);
        if (result.success) {
            this.log('✅ コミット完了');
        } else {
            throw new Error('コミットに失敗しました');
        }
    }

    private async ensureGitIdentity(): Promise<void> {
        // ユーザー名のチェック
        const nameResult = await this.core.runCommand('git config user.name');
        if (!nameResult.success || !nameResult.stdout.trim()) {
            await this.core.runCommand('git config user.name "Auto Committer"');
        }

        // メールアドレスのチェック
        const emailResult = await this.core.runCommand('git config user.email');
        if (!emailResult.success || !emailResult.stdout.trim()) {
            await this.core.runCommand('git config user.email "autocommit@example.com"');
        }
    }

    private async push(): Promise<void> {
        this.log('🚀 プッシュ中...');

        // 現在のブランチを取得
        const branchResult = await this.core.runCommand('git branch --show-current');
        const currentBranch = branchResult.success ? branchResult.stdout.trim() : 'main';

        // プッシュを試行
        let result = await this.core.runCommand(`git push origin ${currentBranch}`);

        if (!result.success) {
            // リモートが設定されていない場合は upstream を設定してリトライ
            this.log('🔄 upstream を設定してリトライします...');
            result = await this.core.runCommand(`git push -u origin ${currentBranch}`);

            if (!result.success) {
                // それでも失敗した場合はGitHubリポジトリの作成を提案
                const shouldCreateRepo = await vscode.window.showWarningMessage(
                    'プッシュに失敗しました。GitHubリポジトリを作成しますか？',
                    'はい', 'いいえ'
                );

                if (shouldCreateRepo === 'はい') {
                    await this.createGitHubRepository();
                    // 再度プッシュを試行
                    result = await this.core.runCommand(`git push -u origin ${currentBranch}`);
                }
            }
        }

        if (result.success) {
            this.log('✅ プッシュ完了');
        } else {
            throw new Error('プッシュに失敗しました');
        }
    }

    private async createGitHubRepository(): Promise<void> {
        this.log('📦 GitHubリポジトリを作成中...');

        // GitHub CLIの確認
        const ghCheck = await this.core.runCommand('gh --version');
        if (!ghCheck.success) {
            throw new Error('GitHub CLI (gh) が見つかりません。インストールしてください。');
        }

        // 認証状態の確認
        const authCheck = await this.core.runCommand('gh auth status');
        if (!authCheck.success) {
            throw new Error('GitHub CLI の認証が必要です。"gh auth login" を実行してください。');
        }

        // リポジトリ名を取得
        const repoName = this.workspaceRoot.split('/').pop() || 'new-repo';

        // 可視性を選択
        const visibility = await vscode.window.showQuickPick(
            ['public', 'private'],
            { placeHolder: 'リポジトリの可視性を選択してください' }
        );

        if (!visibility) {
            throw new Error('リポジトリの可視性が選択されませんでした');
        }

        // リポジトリを作成
        const visibilityFlag = visibility === 'public' ? '--public' : '--private';
        const createResult = await this.core.runCommand(
            `gh repo create ${repoName} ${visibilityFlag} --source=. --remote=origin --push`
        );

        if (createResult.success) {
            this.log('✅ GitHubリポジトリを作成しました');
        } else {
            throw new Error('GitHubリポジトリの作成に失敗しました');
        }
    }

    private async openInBrowser(): Promise<void> {
        this.log('🌐 GitHubリポジトリをブラウザで開いています...');

        try {
            // まずGitHub CLIで開くのを試みる
            const ghResult = await this.core.runCommand('gh --version');
            if (ghResult.success) {
                const result = await this.core.runCommand('gh repo view --web');
                if (result.success) {
                    this.log('✅ GitHub CLIでリポジトリを開きました');
                    return;
                }
            }
            
            // GitHub CLIが使えない場合は、リモートURLから直接開く
            this.log('GitHub CLIが利用できないため、リモートURLから開きます...');
            
            // リモートURLを取得
            const remoteResult = await this.core.runCommand('git remote get-url origin');
            if (remoteResult.success) {
                let repoUrl = remoteResult.stdout.trim();
                
                // SSH形式のURLをHTTPS形式に変換
                if (repoUrl.startsWith('git@')) {
                    repoUrl = repoUrl
                        .replace(':', '/')
                        .replace('git@', 'https://')
                        .replace('.git', '');
                } else if (repoUrl.endsWith('.git')) {
                    repoUrl = repoUrl.replace('.git', '');
                }
                
                // ブラウザで開く
                await vscode.env.openExternal(vscode.Uri.parse(repoUrl));
                this.log(`✅ ブラウザでリポジトリを開きました: ${repoUrl}`);
            } else {
                throw new Error('リモートリポジトリのURLを取得できませんでした');
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.log(`⚠️ ブラウザでの表示に失敗しました: ${errorMessage}`);
        }
    }

    private log(message: string, level: 'info' | 'warn' | 'error' = 'info'): void {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
        this.outputChannel.appendLine(`${prefix} ${message}`);
        
        if (level === 'error' && this.config.get('showErrorNotifications', true)) {
            vscode.window.showErrorMessage(message);
        } else if (level === 'warn' && this.config.get('showWarningNotifications', true)) {
            vscode.window.showWarningMessage(message);
        }
    }
}
