import * as vscode from 'vscode';
import { join, dirname, extname, parse } from 'path';
import { existsSync, readdirSync, readFileSync, statSync } from 'fs';
import { exec } from 'child_process';
import { platform, release } from 'os';

export interface PlatformInfo {
    system: string;
    type: string;
    name: string;
    shell: string;
    isWindows: boolean;
    isMacOS: boolean;
    isLinux: boolean;
    isWSL: boolean;
}

export interface DirectoryAnalysis {
    isGitRepo: boolean;
    isEmpty: boolean;
    hasSourceFiles: boolean;
    isSystemFolder: boolean;
    isNestedRepo: boolean;
    folderType: string;
    gitInitRecommended: boolean;
    warningMessage?: string;
    actionRecommendation: string;
}

export interface ExecutionResults {
    gitInit: boolean;
    branchSync: boolean;
    staging: boolean;
    commit: boolean;
    push: boolean;
    browserOpen: boolean;
}

export class GitAutoPushCore {
    private workspaceRoot: string;
    private gitPath: string;
    private outputChannel: vscode.OutputChannel;
    private config: vscode.WorkspaceConfiguration;
    private platformInfo: PlatformInfo;

    constructor(workspaceRoot: string, outputChannel: vscode.OutputChannel) {
        this.workspaceRoot = workspaceRoot;
        this.gitPath = join(workspaceRoot, '.git');
        this.outputChannel = outputChannel;
        this.config = vscode.workspace.getConfiguration('gitAutoPush');
        this.platformInfo = this.detectPlatform();
    }

    private detectPlatform(): PlatformInfo {
        const currentPlatform = platform();
        const currentRelease = release();

        let platformInfo: PlatformInfo = {
            system: currentPlatform,
            type: 'unknown',
            name: 'Unknown',
            shell: 'unknown',
            isWindows: false,
            isMacOS: false,
            isLinux: false,
            isWSL: false
        };

        switch (currentPlatform) {
            case 'win32':
                platformInfo = {
                    ...platformInfo,
                    type: 'windows',
                    name: `Windows ${currentRelease}`,
                    shell: 'cmd',
                    isWindows: true
                };
                break;
            case 'darwin':
                platformInfo = {
                    ...platformInfo,
                    type: 'macos',
                    name: `macOS ${currentRelease}`,
                    shell: 'zsh',
                    isMacOS: true
                };
                break;
            case 'linux':
                platformInfo = {
                    ...platformInfo,
                    type: 'linux',
                    name: `Linux ${currentRelease}`,
                    shell: 'bash',
                    isLinux: true
                };

                // WSL検出
                try {
                    const versionInfo = readFileSync('/proc/version', 'utf8').toLowerCase();
                    if (versionInfo.includes('microsoft') || versionInfo.includes('wsl')) {
                        platformInfo.type = 'wsl';
                        platformInfo.name = `WSL ${currentRelease}`;
                        platformInfo.isWSL = true;
                    }
                } catch {
                    // WSLでない場合は無視
                }
                break;
        }

        return platformInfo;
    }

    async analyzeCurrentDirectory(): Promise<DirectoryAnalysis> {
        this.log('📁 現在のディレクトリを分析中...');

        const analysis: DirectoryAnalysis = {
            isGitRepo: await this.isGitRepository(),
            isEmpty: this.isDirectoryEmpty(),
            hasSourceFiles: this.hasSourceFiles(),
            isSystemFolder: this.isSystemFolder(),
            isNestedRepo: await this.isNestedInGitRepo(),
            folderType: 'unknown',
            gitInitRecommended: false,
            actionRecommendation: ''
        };

        // フォルダタイプの判定
        if (analysis.isGitRepo) {
            analysis.folderType = 'existing_git_repo';
            analysis.actionRecommendation = 'このフォルダは既にGitリポジトリです';
        } else if (analysis.isSystemFolder) {
            analysis.folderType = 'system_folder';
            analysis.warningMessage = '⚠️ システムフォルダでのgit init は推奨されません';
            analysis.actionRecommendation = 'システムフォルダ以外での実行をお勧めします';
        } else if (analysis.isNestedRepo) {
            analysis.folderType = 'nested_in_repo';
            analysis.warningMessage = '⚠️ 既存のGitリポジトリ内にネストされています';
            analysis.actionRecommendation = 'サブモジュールとして追加するか、別の場所に移動してください';
        } else if (analysis.isEmpty) {
            analysis.folderType = 'empty_folder';
            analysis.gitInitRecommended = true;
            analysis.actionRecommendation = '空のフォルダです。新しいプロジェクトの開始に適しています';
        } else if (analysis.hasSourceFiles) {
            analysis.folderType = 'source_project';
            analysis.gitInitRecommended = true;
            analysis.actionRecommendation = 'ソースファイルが見つかりました。Gitリポジトリ化をお勧めします';
        } else {
            analysis.folderType = 'general_folder';
            analysis.gitInitRecommended = true;
            analysis.actionRecommendation = '一般的なフォルダです。必要に応じてGitリポジトリ化できます';
        }

        return analysis;
    }

    private isDirectoryEmpty(): boolean {
        try {
            const files = readdirSync(this.workspaceRoot);
            return files.length === 0;
        } catch {
            return false;
        }
    }

    private hasSourceFiles(): boolean {
        const sourceExtensions = new Set([
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb',
            '.go', '.rs', '.swift', '.kt', '.scala', '.sh', '.bat', '.html',
            '.css', '.vue', '.jsx', '.tsx', '.json', '.xml', '.yaml', '.yml',
            '.md', '.txt', '.sql', '.r', '.m', '.pl'
        ]);

        const configFiles = new Set([
            'package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml',
            'build.gradle', 'Makefile', 'CMakeLists.txt', 'setup.py',
            'pyproject.toml', 'composer.json', 'Gemfile', 'go.mod'
        ]);

        try {
            const files = readdirSync(this.workspaceRoot);

            for (const file of files) {
                const filePath = join(this.workspaceRoot, file);
                const stat = statSync(filePath);

                if (stat.isFile()) {
                    const ext = extname(file).toLowerCase();
                    if (sourceExtensions.has(ext) || configFiles.has(file)) {
                        return true;
                    }
                } else if (stat.isDirectory()) {
                    const commonSrcDirs = ['src', 'lib', 'app', 'components', 'modules'];
                    if (commonSrcDirs.includes(file)) {
                        return true;
                    }
                }
            }
            return false;
        } catch {
            return false;
        }
    }

    private isSystemFolder(): boolean {
        const pathStr = this.workspaceRoot.toLowerCase();

        const windowsSystemPaths = [
            'c:\\windows', 'c:\\program files', 'c:\\program files (x86)',
            'c:\\programdata', 'c:\\users\\public', 'c:\\system volume information',
            '\\appdata\\', '\\temp\\', '\\tmp\\'
        ];

        const unixSystemPaths = [
            '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/var',
            '/tmp', '/sys', '/proc', '/dev', '/boot', '/root'
        ];

        const systemPaths = this.platformInfo.isWindows ? windowsSystemPaths : unixSystemPaths;

        return systemPaths.some(sysPath => pathStr.includes(sysPath));
    }

    private async isNestedInGitRepo(): Promise<boolean> {
        if (await this.isGitRepository()) {
            return false; // 自分自身がリポジトリなら、ネストではない
        }

        let current = dirname(this.workspaceRoot);
        const root = parse(current).root;

        while (current !== root) {
            if (existsSync(join(current, '.git'))) {
                return true;
            }
            current = dirname(current);
        }

        return false;
    }

    async isGitRepository(): Promise<boolean> {
        return existsSync(this.gitPath);
    }

    async checkBranchDivergence(): Promise<boolean> {
        this.log('🔍 ブランチの分岐状況をチェックしています...');

        const result = await this.runCommand('git status --porcelain=v1 --branch');
        if (!result.success) {
            return false;
        }

        const statusLines = result.stdout.trim().split('\n');
        const branchInfo = statusLines[0] || '';

        if (branchInfo.includes('ahead') && branchInfo.includes('behind')) {
            this.log('⚠️ ブランチが分岐しています！');
            return true;
        } else if (branchInfo.includes('behind')) {
            this.log('📥 リモートが先行しています（プル必要）');
            return true;
        } else if (branchInfo.includes('ahead')) {
            this.log('✅ ローカルが先行しています（プッシュ可能）');
        } else {
            this.log('✅ ブランチは同期されています');
        }

        return false;
    }

    async handleBranchDivergence(): Promise<boolean> {
        const choice = await vscode.window.showQuickPick([
            { label: 'git pull --rebase', description: '推奨: リモートの変更を取得してリベース' },
            { label: 'git pull', description: 'リモートの変更を取得してマージ' },
            { label: 'git push --force-with-lease', description: '慎重: ローカルの変更を強制プッシュ' },
            { label: 'スキップ', description: '手動で解決' }
        ], {
            placeHolder: 'ブランチの分岐を解決する方法を選択してください'
        });

        if (!choice) {
            return false;
        }

        switch (choice.label) {
            case 'git pull --rebase':
                return await this.pullRebase();
            case 'git pull':
                return await this.pullMerge();
            case 'git push --force-with-lease':
                const confirmed = await vscode.window.showWarningMessage(
                    '⚠️ 強制プッシュは危険です。リモートの変更が失われる可能性があります。',
                    'はい', 'いいえ'
                );
                if (confirmed === 'はい') {
                    return await this.forcePush();
                }
                return false;
            case 'スキップ':
                this.log('手動での解決を選択しました');
                return true;
            default:
                return false;
        }
    }

    private async pullRebase(): Promise<boolean> {
        this.log('🔄 git pull --rebase を実行中...');
        const result = await this.runCommand('git pull --rebase');
        if (result.success) {
            this.log('✅ リベースが完了しました');
            return true;
        } else {
            this.log('❌ リベースに失敗しました');
            return false;
        }
    }

    private async pullMerge(): Promise<boolean> {
        this.log('🔄 git pull を実行中...');
        const result = await this.runCommand('git pull');
        if (result.success) {
            this.log('✅ マージが完了しました');
            return true;
        } else {
            this.log('❌ マージに失敗しました');
            return false;
        }
    }

    private async forcePush(): Promise<boolean> {
        const branchResult = await this.runCommand('git branch --show-current');
        const currentBranch = branchResult.success ? branchResult.stdout.trim() : 'main';

        this.log(`🚀 ${currentBranch} ブランチに強制プッシュ中...`);
        const result = await this.runCommand(`git push --force-with-lease origin ${currentBranch}`);

        if (result.success) {
            this.log('✅ 強制プッシュが完了しました');
            return true;
        } else {
            this.log('❌ 強制プッシュに失敗しました');
            return false;
        }
    }

    printExecutionSummary(results: ExecutionResults): void {
        this.log('');
        this.log(''.padEnd(60, '='));
        this.log('📊 実行結果サマリー');
        this.log(''.padEnd(60, '='));

        const statusIcon = (success: boolean) => success ? '✅' : '❌';
        const statusText = (success: boolean) => success ? '成功' : '未実行/失敗';

        this.log(`${statusIcon(results.gitInit)} Git初期化: ${statusText(results.gitInit)}`);
        this.log(`${statusIcon(results.branchSync)} ブランチ同期: ${statusText(results.branchSync)}`);
        this.log(`${statusIcon(results.staging)} ステージング: ${statusText(results.staging)}`);
        this.log(`${statusIcon(results.commit)} コミット: ${statusText(results.commit)}`);
        this.log(`${statusIcon(results.push)} プッシュ: ${statusText(results.push)}`);
        this.log(`${statusIcon(results.browserOpen)} ブラウザ確認: ${statusText(results.browserOpen)}`);

        const successCount = Object.values(results).filter(Boolean).length;
        const totalCount = Object.keys(results).length;

        this.log('');
        this.log(`🎯 成功率: ${successCount}/${totalCount} (${(successCount/totalCount*100).toFixed(1)}%)`);

        if (successCount === totalCount) {
            this.log('🎉 すべての操作が正常に完了しました！');
        } else {
            this.log('⚠️ 一部の操作が失敗しました。上記の結果を確認してください。');
        }

        this.log(''.padEnd(60, '='));
    }

    async runCommand(command: string): Promise<{ success: boolean; stdout: string; stderr: string; error?: any }> {
        return new Promise((resolve) => {
            const startTime = Date.now();
            this.log(`🔍 実行中: ${command}`);

            try {
                const child = exec(command, { 
                    cwd: this.workspaceRoot,
                    maxBuffer: 10 * 1024 * 1024, // 10MB buffer
                    timeout: 5 * 60 * 1000 // 5 minutes timeout
                }, (error, stdout, stderr) => {
                    const executionTime = ((Date.now() - startTime) / 1000).toFixed(2);
                    const success = !error;

                    // Always log errors, regardless of debug mode
                    if (error) {
                        this.log(`❌ コマンドが失敗しました (${executionTime}秒)`);
                        this.log(`   コマンド: ${command}`);
                        if (error.code !== null) {
                            this.log(`   終了コード: ${error.code}`);
                        }
                        if (error.signal) {
                            this.log(`   シグナル: ${error.signal}`);
                        }
                    } else if (this.config.get('enableDebugMode', false)) {
                        this.log(`✅ コマンドが成功しました (${executionTime}秒)`);
                    }

                    // Debug output for stdout/stderr when in debug mode
                    if (this.config.get('enableDebugMode', false)) {
                        if (stdout) {
                            this.log(`   stdout: ${stdout.trim()}`);
                        }
                        if (stderr) {
                            this.log(`   stderr: ${stderr.trim()}`);
                        }
                    }

                    resolve({ success, stdout, stderr, error });
                });

                // Handle process events for better error tracking
                child.on('error', (error) => {
                    this.log(`⚠️ コマンド実行エラー: ${error.message}`);
                    if (error.stack) {
                        this.log(`   スタックトレース: ${error.stack}`);
                    }
                });

                // Handle process exit
                child.on('exit', (code, signal) => {
                    if (code !== 0) {
                        this.log(`⚠️ プロセスが異常終了しました: コード=${code}, シグナル=${signal}`);
                    }
                });

            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                this.log(`❌ コマンド実行中に予期せぬエラーが発生しました: ${errorMessage}`);
                if (error instanceof Error && error.stack) {
                    this.log(`   スタックトレース: ${error.stack}`);
                }
                resolve({ 
                    success: false, 
                    stdout: '', 
                    stderr: errorMessage,
                    error: error
                });
            }
        });
    }

    private log(message: string): void {
        const timestamp = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${timestamp}] ${message}`);
    }
}
