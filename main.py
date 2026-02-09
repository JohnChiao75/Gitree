#!/usr/bin/env python3
"""
Gitree - 交互式 CLI Git 管理器
简洁黑白版本，使用 WASD 导航
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import platform

# 第三方依赖：gitpython
try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
    from git.exc import NoSuchPathError
except ImportError:
    print("请先安装依赖：pip install gitpython")
    sys.exit(1)


class GitManager:
    """Git 操作管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).absolute()
        self.repo = None
        
    def is_git_repo(self) -> bool:
        """检查是否为 Git 仓库"""
        try:
            self.repo = Repo(self.repo_path)
            return not self.repo.bare
        except (InvalidGitRepositoryError, NoSuchPathError):
            return False
    
    def init_repo(self) -> bool:
        """初始化新仓库"""
        try:
            self.repo = Repo.init(self.repo_path)
            return True
        except Exception as e:
            print(f"错误: 初始化仓库失败: {e}")
            return False
    
    def open_repo(self, path: str) -> bool:
        """打开现有仓库"""
        try:
            self.repo_path = Path(path).absolute()
            self.repo = Repo(self.repo_path)
            return True
        except Exception as e:
            print(f"错误: 打开仓库失败: {e}")
            return False
    
    def clone_repo(self, url: str, target_dir: Optional[str] = None) -> bool:
        """克隆远程仓库"""
        try:
            target = target_dir or self.repo_path
            self.repo = Repo.clone_from(url, target)
            self.repo_path = Path(target)
            return True
        except Exception as e:
            print(f"错误: 克隆仓库失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, List[str]]:
        """获取仓库状态"""
        if not self.repo:
            return {}
        
        status = {
            'staged': [],
            'unstaged': [],
            'untracked': []
        }
        
        try:
            # 使用 git status --porcelain 解析状态
            output = self.repo.git.status('--porcelain')
            for line in output.split('\n'):
                if not line.strip():
                    continue
                
                code = line[:2]
                filename = line[3:].strip()
                
                if code[0] in ('A', 'M', 'D', 'R'):  # 已暂存
                    status['staged'].append(filename)
                elif code[1] in ('M', 'D'):  # 未暂存
                    status['unstaged'].append(filename)
                elif code == '??':  # 未跟踪
                    status['untracked'].append(filename)
        except Exception:
            pass
        
        return status
    
    def stage_file(self, filepath: str) -> bool:
        """暂存文件"""
        try:
            self.repo.git.add(filepath)
            return True
        except Exception as e:
            print(f"错误: 暂存失败: {e}")
            return False
    
    def unstage_file(self, filepath: str) -> bool:
        """取消暂存"""
        try:
            self.repo.git.reset('--', filepath)
            return True
        except Exception as e:
            print(f"错误: 取消暂存失败: {e}")
            return False
    
    def stash_file(self, filepath: str) -> bool:
        """储藏文件"""
        try:
            # 先暂存再储藏
            self.repo.git.add(filepath)
            self.repo.git.stash()
            # 取消暂存以保持原状
            self.repo.git.reset('--', filepath)
            return True
        except Exception as e:
            print(f"错误: 储藏失败: {e}")
            return False
    
    def stash_all(self) -> bool:
        """储藏所有更改"""
        try:
            self.repo.git.stash()
            return True
        except Exception as e:
            print(f"错误: 储藏失败: {e}")
            return False
    
    def commit(self, message: str) -> bool:
        """提交更改"""
        try:
            self.repo.git.commit('-m', message)
            return True
        except Exception as e:
            print(f"错误: 提交失败: {e}")
            return False
    
    def get_branches(self) -> Dict[str, List[str]]:
        """获取分支列表"""
        if not self.repo:
            return {'local': [], 'remote': [], 'current': ''}
        
        branches = {
            'local': [],
            'remote': [],
            'current': ''
        }
        
        try:
            # 本地分支
            for branch in self.repo.branches:
                branches['local'].append(branch.name)
                if branch == self.repo.active_branch:
                    branches['current'] = branch.name
            
            # 远程分支
            for ref in self.repo.references:
                if ref.name.startswith('origin/'):
                    branches['remote'].append(ref.name.replace('origin/', ''))
        except Exception:
            pass
        
        return branches
    
    def create_branch(self, name: str) -> bool:
        """创建新分支"""
        try:
            self.repo.git.branch(name)
            return True
        except Exception as e:
            print(f"错误: 创建分支失败: {e}")
            return False
    
    def delete_branch(self, name: str, force: bool = False) -> bool:
        """删除分支"""
        try:
            if force:
                self.repo.git.branch('-D', name)
            else:
                self.repo.git.branch('-d', name)
            return True
        except Exception as e:
            print(f"错误: 删除分支失败: {e}")
            return False
    
    def checkout(self, target: str) -> bool:
        """切换分支或提交"""
        try:
            self.repo.git.checkout(target)
            return True
        except Exception as e:
            print(f"错误: 切换失败: {e}")
            return False
    
    def get_history(self, limit: int = 50) -> List[Dict[str, str]]:
        """获取提交历史"""
        if not self.repo:
            return []
        
        history = []
        try:
            # 获取提交历史
            commits = list(self.repo.iter_commits('HEAD', max_count=limit))
            for commit in commits:
                history.append({
                    'hash': commit.hexsha[:8],
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M'),
                    'full_hash': commit.hexsha
                })
        except Exception:
            pass
        
        return history
    
    def pull(self) -> bool:
        """拉取远程更改"""
        try:
            self.repo.git.pull()
            return True
        except Exception as e:
            print(f"错误: 拉取失败: {e}")
            return False
    
    def push(self) -> bool:
        """推送本地更改"""
        try:
            self.repo.git.push()
            return True
        except Exception as e:
            print(f"错误: 推送失败: {e}")
            return False
    
    def fetch(self) -> bool:
        """获取远程更新"""
        try:
            self.repo.git.fetch()
            return True
        except Exception as e:
            print(f"错误: 获取失败: {e}")
            return False


class GitreeUI:
    """Gitree 用户界面管理器 - 黑白简洁版"""
    
    def __init__(self):
        self.git = GitManager()
        self.current_page = "welcome"
        self.selected_index = 0
        self.in_list = False
        self.current_list = []
        self.list_type = ""  # 'unstaged', 'staged', 'history', 'branches'
        self.terminal_mode = False
        self.message_input = ""
        self.show_help = False
        
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_welcome(self):
        """显示欢迎页面"""
        self.clear_screen()
        
        print("=" * 60)
        print(" " * 20 + "Gitree - Git 管理器")
        print(" " * 15 + "交互式命令行 Git 管理工具")
        print("=" * 60)
        print("\n")
        
        print("当前目录:", os.getcwd())
        print("\n")
        
        print("[Q] - 新建仓库")
        print("[E] - 打开本地仓库")
        print("[C] - 克隆远程仓库")
        print("[X] - 退出程序")
        print("\n")
        print("=" * 60)
    
    def display_workbench(self):
        """显示工作台"""
        self.clear_screen()
        
        # 顶部状态栏
        if not self.git.repo:
            print("状态: 未在 Git 仓库中")
        else:
            try:
                branch = self.git.repo.active_branch.name
                repo_name = os.path.basename(self.git.repo.working_dir)
                print(f"仓库: {repo_name} | 分支: {branch}")
                
                # 检查是否有远程
                try:
                    remote = list(self.git.repo.remotes)[0].name
                    print(f"远程: {remote}")
                except:
                    print("远程: 无")
            except:
                print("状态: 仓库状态未知")
        
        print("-" * 60)
        
        # 文件状态区域
        status = self.git.get_status()
        
        print("\n[ 已暂存文件 ]")
        if status.get('staged'):
            for i, file in enumerate(status['staged']):
                prefix = " > " if self.in_list and self.list_type == 'staged' and i == self.selected_index else "   "
                print(f"{prefix}{file}")
        else:
            print("   暂无")
        
        print("\n[ 未暂存文件 ]")
        unstaged_files = status.get('unstaged', []) + status.get('untracked', [])
        if unstaged_files:
            self.current_list = unstaged_files
            self.list_type = 'unstaged'
            
            for i, file in enumerate(unstaged_files):
                prefix = " > " if self.in_list and self.list_type == 'unstaged' and i == self.selected_index else "   "
                file_type = "未跟踪" if file in status.get('untracked', []) else "已修改"
                print(f"{prefix}[{file_type}] {file}")
        else:
            print("   暂无")
        
        # 显示所有工作已完成（如果没有更改）
        total_changes = sum(len(files) for files in status.values())
        if total_changes == 0:
            print("\n" + "=" * 60)
            print("所有工作已完成！")
            print("=" * 60)
        
        print("\n" + "-" * 60)
        
        # 显示菜单栏
        if not self.in_list:
            print("导航: [W]上 [S]下 [A]菜单 [D]列表")
            print("操作: [J]提交 [K]终端 [L]拉取 [;]推送 [']同步")
            print("      [U]历史 [I]分支 [O]储藏 [P]帮助 [X]退出")
        else:
            if self.list_type == 'unstaged':
                print("操作: [A]暂存 [D]储藏 [S]跳过 [X]返回")
            elif self.list_type == 'staged':
                print("操作: [D]取消暂存 [S]跳过 [X]返回")
        
        # 显示帮助（如果启用）
        if self.show_help:
            self.display_help()
    
    def display_history(self):
        """显示历史记录"""
        self.clear_screen()
        
        history = self.git.get_history(30)
        self.current_list = history
        self.list_type = 'history'
        
        print("=" * 60)
        print(" " * 25 + "提交历史")
        print("=" * 60)
        print("\n")
        
        if history:
            for i, commit in enumerate(history):
                prefix = " > " if self.in_list and i == self.selected_index else "   "
                print(f"{prefix}[{commit['hash']}] {commit['message'][:50]}")
                print(f"     作者: {commit['author']} | 时间: {commit['date']}")
                print()
        else:
            print("暂无提交历史")
        
        print("-" * 60)
        print("导航: [W]上 [S]下")
        print("操作: [R]重置 [B]变基 [D]分离 [X]返回")
    
    def display_branches(self):
        """显示分支管理"""
        self.clear_screen()
        
        branches = self.git.get_branches()
        self.current_list = branches.get('local', [])
        self.list_type = 'branches'
        
        print("=" * 60)
        print(" " * 25 + "分支管理")
        print("=" * 60)
        print("\n")
        
        print("[ 本地分支 ]")
        local_branches = branches.get('local', [])
        current_branch = branches.get('current', '')
        
        if local_branches:
            for i, branch in enumerate(local_branches):
                prefix = " > " if self.in_list and i == self.selected_index else "   "
                current = " * " if branch == current_branch else "   "
                print(f"{prefix}{current}{branch}")
        else:
            print("   暂无本地分支")
        
        print("\n[ 远程分支 ]")
        remote_branches = branches.get('remote', [])
        if remote_branches:
            for branch in remote_branches[:10]:  # 显示前10个
                print(f"    {branch}")
        else:
            print("   暂无远程分支")
        
        print("\n" + "-" * 60)
        print("导航: [W]上 [S]下")
        print("操作: [N]新建 [C]切换 [M]合并 [D]删除 [X]返回")
    
    def display_help(self):
        """显示帮助"""
        print("\n" + "=" * 60)
        print(" " * 25 + "帮助")
        print("=" * 60)
        
        print("\n[ 工作台快捷键 ]")
        print("  W - 上移")
        print("  S - 下移")
        print("  A - 进入菜单模式")
        print("  D - 进入列表模式")
        print("  J - 提交更改")
        print("  K - 集成终端")
        print("  L - 拉取 (pull)")
        print("  ; - 推送 (push)")
        print("  ' - 同步 (fetch)")
        print("  U - 查看历史")
        print("  I - 分支管理")
        print("  O - 储藏所有更改")
        print("  P - 显示/隐藏帮助")
        print("  X - 退出")
        
        print("\n[ 列表模式操作 ]")
        print("  A - 暂存选中项")
        print("  D - 储藏选中项")
        print("  S - 跳过此项")
        
        print("\n[ 历史记录操作 ]")
        print("  R - 重置到该提交")
        print("  B - 变基到该提交")
        print("  D - 分离 HEAD")
        
        print("\n[ 分支管理操作 ]")
        print("  N - 新建分支")
        print("  C - 切换分支")
        print("  M - 合并分支")
        print("  D - 删除分支")
        
        print("\n" + "=" * 60)
    
    def run_terminal(self):
        """运行集成终端"""
        self.clear_screen()
        print("集成终端模式 (输入 'exit' 返回)")
        print("-" * 60)
        print()
        
        while True:
            try:
                cmd = input(f"gitree:terminal {os.getcwd()} $ ")
                if cmd.lower() in ['exit', 'quit', 'x']:
                    break
                
                if cmd.strip():
                    # 执行命令
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        capture_output=True, 
                        text=True
                    )
                    
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(f"错误: {result.stderr}")
            except KeyboardInterrupt:
                print("\n终端已中断")
                break
            except EOFError:
                break
    
    def get_commit_message(self) -> Optional[str]:
        """获取提交消息"""
        self.clear_screen()
        print("=" * 60)
        print(" " * 25 + "提交更改")
        print("=" * 60)
        print("\n请输入提交消息 (按 Ctrl+Z 然后回车完成):\n")
        
        lines = []
        try:
            while True:
                try:
                    line = input()
                    lines.append(line)
                except EOFError:
                    break
        except KeyboardInterrupt:
            return None
        
        message = "\n".join(lines)
        if message.strip():
            return message
        return None
    
    def get_input(self, prompt: str = "") -> str:
        """获取用户输入"""
        if prompt:
            print(prompt, end='', flush=True)
        
        try:
            return input().strip()
        except (KeyboardInterrupt, EOFError):
            return ""
    
    def pause(self, message: str = ""):
        """暂停等待用户按键"""
        if message:
            print(message)
        input("按回车键继续...")


class GitreeApp:
    """Gitree 主应用"""
    
    def __init__(self):
        self.ui = GitreeUI()
        self.running = True
    
    def run(self):
        """运行主应用"""
        # 检查是否为 Git 仓库
        if not self.ui.git.is_git_repo():
            self.ui.current_page = "welcome"
        else:
            self.ui.current_page = "workbench"
        
        # 主循环
        while self.running:
            try:
                # 根据当前页面显示对应界面
                if self.ui.current_page == "welcome":
                    self.handle_welcome()
                elif self.ui.current_page == "workbench":
                    self.handle_workbench()
                elif self.ui.current_page == "history":
                    self.handle_history()
                elif self.ui.current_page == "branches":
                    self.handle_branches()
                
            except KeyboardInterrupt:
                print("\n操作已中断")
                if self.ui.current_page == "welcome":
                    self.running = False
                else:
                    self.ui.pause()
            except Exception as e:
                print(f"\n错误: {e}")
                self.ui.pause()
    
    def handle_welcome(self):
        """处理欢迎页面"""
        self.ui.display_welcome()
        key = self.ui.get_input("\n请选择操作: ").upper()
        
        if key == 'Q':
            # 新建仓库
            if self.ui.git.init_repo():
                self.ui.current_page = "workbench"
                self.ui.pause("✅ 仓库初始化成功！")
        elif key == 'E':
            # 打开本地仓库
            path = self.ui.get_input("请输入仓库路径: ")
            if path and self.ui.git.open_repo(path):
                self.ui.current_page = "workbench"
                self.ui.pause(f"✅ 已打开仓库: {path}")
        elif key == 'C':
            # 克隆仓库
            url = self.ui.get_input("请输入仓库 URL: ")
            if url:
                target = self.ui.get_input("目标目录 (可选): ")
                if self.ui.git.clone_repo(url, target or None):
                    self.ui.current_page = "workbench"
                    self.ui.pause("✅ 仓库克隆成功！")
        elif key == 'X':
            # 退出
            self.running = False
            print("👋 再见！")
    
    def handle_workbench(self):
        """处理工作台"""
        self.ui.display_workbench()
        
        # 获取单个字符输入（跨平台）
        try:
            if platform.system() == 'Windows':
                import msvcrt
                key = msvcrt.getch().decode('utf-8').upper()
            else:
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    key = sys.stdin.read(1).upper()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (KeyboardInterrupt, EOFError):
            return
        
        # 处理按键
        if key == 'X':
            if self.ui.in_list:
                self.ui.in_list = False
                self.ui.selected_index = 0
            elif self.ui.current_page == "workbench":
                # 返回欢迎页面
                self.ui.current_page = "welcome"
        elif key == 'P':
            # 显示/隐藏帮助
            self.ui.show_help = not self.ui.show_help
        elif key == 'K':
            # 进入终端
            self.ui.run_terminal()
        elif key == 'U':
            # 进入历史记录
            self.ui.current_page = "history"
            self.ui.in_list = True
            self.ui.selected_index = 0
        elif key == 'I':
            # 进入分支管理
            self.ui.current_page = "branches"
            self.ui.in_list = True
            self.ui.selected_index = 0
        elif key == 'J':
            # 提交更改
            message = self.ui.get_commit_message()
            if message and self.ui.git.commit(message):
                self.ui.pause("✅ 提交成功！")
        elif key == 'O':
            # 储藏所有更改
            confirm = self.ui.get_input("确认储藏所有更改？(y/N): ").lower()
            if confirm == 'y' and self.ui.git.stash_all():
                self.ui.pause("✅ 已储藏所有更改！")
        elif key in ['L', ';', "'"]:
            # Git 操作
            self.handle_git_operation(key)
        elif key in ['W', 'S']:
            # 导航
            self.handle_navigation(key)
        elif key == 'A':
            # 进入菜单模式或暂存文件
            if self.ui.in_list and self.ui.list_type == 'unstaged':
                self.handle_file_operation('A')
            else:
                self.ui.in_list = False
        elif key == 'D':
            # 进入列表模式或储藏/取消暂存
            if self.ui.in_list:
                self.handle_file_operation('D')
            else:
                self.ui.in_list = True
                # 设置正确的列表类型
                status = self.ui.git.get_status()
                if status.get('staged'):
                    self.ui.list_type = 'staged'
                    self.ui.current_list = status['staged']
                else:
                    self.ui.list_type = 'unstaged'
                    self.ui.current_list = status.get('unstaged', []) + status.get('untracked', [])
                self.ui.selected_index = 0
        elif self.ui.in_list and key in ['A', 'D', 'S']:
            # 文件操作
            self.handle_file_operation(key)
    
    def handle_history(self):
        """处理历史记录"""
        self.ui.display_history()
        key = self.ui.get_input("\n请选择操作: ").upper()
        
        if key == 'X':
            # 返回工作台
            self.ui.current_page = "workbench"
            self.ui.in_list = False
        elif key == 'W':
            # 上移
            if self.ui.selected_index > 0:
                self.ui.selected_index -= 1
        elif key == 'S':
            # 下移
            if self.ui.selected_index < len(self.ui.current_list) - 1:
                self.ui.selected_index += 1
        elif key in ['R', 'B', 'D'] and self.ui.current_list:
            # 历史记录操作
            commit = self.ui.current_list[self.ui.selected_index]
            self.handle_history_operation(key, commit)
    
    def handle_branches(self):
        """处理分支管理"""
        self.ui.display_branches()
        key = self.ui.get_input("\n请选择操作: ").upper()
        
        if key == 'X':
            # 返回工作台
            self.ui.current_page = "workbench"
            self.ui.in_list = False
        elif key == 'W':
            # 上移
            if self.ui.selected_index > 0:
                self.ui.selected_index -= 1
        elif key == 'S':
            # 下移
            if self.ui.selected_index < len(self.ui.current_list) - 1:
                self.ui.selected_index += 1
        elif key == 'N':
            # 新建分支
            name = self.ui.get_input("请输入新分支名: ")
            if name and self.ui.git.create_branch(name):
                self.ui.pause(f"✅ 分支 '{name}' 创建成功！")
        elif key in ['C', 'M', 'D'] and self.ui.current_list:
            # 分支操作
            branch = self.ui.current_list[self.ui.selected_index]
            self.handle_branch_operation(key, branch)
    
    def handle_git_operation(self, op: str):
        """处理 Git 操作"""
        try:
            if op == 'L':  # 拉取
                if self.ui.git.pull():
                    self.ui.pause("✅ 拉取成功！")
            elif op == ';':  # 推送
                if self.ui.git.push():
                    self.ui.pause("✅ 推送成功！")
            elif op == "'":  # 同步
                if self.ui.git.fetch():
                    self.ui.pause("✅ 同步成功！")
        except Exception as e:
            print(f"错误: {e}")
            self.ui.pause()
    
    def handle_file_operation(self, op: str):
        """处理文件操作"""
        if not self.ui.current_list or self.ui.selected_index >= len(self.ui.current_list):
            return
        
        filepath = self.ui.current_list[self.ui.selected_index]
        
        if op == 'A':  # 暂存
            if self.ui.git.stage_file(filepath):
                print(f"✅ 已暂存: {filepath}")
                # 移动到下一项
                if self.ui.selected_index < len(self.ui.current_list) - 1:
                    self.ui.selected_index += 1
                self.ui.pause()
        elif op == 'D':  # 储藏或取消暂存
            if self.ui.list_type == 'staged':  # 取消暂存
                if self.ui.git.unstage_file(filepath):
                    print(f"✅ 已取消暂存: {filepath}")
            else:  # 储藏
                if self.ui.git.stash_file(filepath):
                    print(f"✅ 已储藏: {filepath}")
            # 移动到下一项
            if self.ui.selected_index < len(self.ui.current_list) - 1:
                self.ui.selected_index += 1
            self.ui.pause()
        elif op == 'S':  # 跳过
            # 移动到下一项
            if self.ui.selected_index < len(self.ui.current_list) - 1:
                self.ui.selected_index += 1
    
    def handle_history_operation(self, op: str, commit: dict):
        """处理历史记录操作"""
        if op == 'R':  # 重置
            confirm = self.ui.get_input(f"确认重置到 {commit['hash']}? (y/N): ").lower()
            if confirm == 'y':
                try:
                    self.ui.git.repo.git.reset('--hard', commit['full_hash'])
                    self.ui.pause(f"✅ 已重置到 {commit['hash']}")
                except Exception as e:
                    print(f"错误: {e}")
                    self.ui.pause()
        elif op == 'B':  # 变基
            confirm = self.ui.get_input(f"确认变基到 {commit['hash']}? (y/N): ").lower()
            if confirm == 'y':
                try:
                    self.ui.git.repo.git.rebase(commit['full_hash'])
                    self.ui.pause(f"✅ 已变基到 {commit['hash']}")
                except Exception as e:
                    print(f"错误: {e}")
                    self.ui.pause()
        elif op == 'D':  # 分离
            confirm = self.ui.get_input(f"确认分离 HEAD 到 {commit['hash']}? (y/N): ").lower()
            if confirm == 'y':
                if self.ui.git.checkout(commit['full_hash']):
                    self.ui.pause(f"✅ 已分离 HEAD 到 {commit['hash']}")
    
    def handle_branch_operation(self, op: str, branch: str):
        """处理分支操作"""
        if op == 'C':  # 切换分支
            if self.ui.git.checkout(branch):
                self.ui.pause(f"✅ 已切换到分支: {branch}")
        elif op == 'M':  # 合并分支
            confirm = self.ui.get_input(f"确认合并分支 '{branch}' 到当前分支? (y/N): ").lower()
            if confirm == 'y':
                try:
                    self.ui.git.repo.git.merge(branch)
                    self.ui.pause(f"✅ 已合并分支: {branch}")
                except Exception as e:
                    print(f"错误: {e}")
                    self.ui.pause()
        elif op == 'D':  # 删除分支
            confirm = self.ui.get_input(f"确认删除分支 '{branch}'? (y/N): ").lower()
            if confirm == 'y':
                force = self.ui.get_input("强制删除? (y/N): ").lower() == 'y'
                if self.ui.git.delete_branch(branch, force):
                    self.ui.pause(f"✅ 已删除分支: {branch}")
    
    def handle_navigation(self, direction: str):
        """处理导航"""
        if not self.ui.in_list or not self.ui.current_list:
            return
        
        if direction == 'W':  # 上
            self.ui.selected_index = max(0, self.ui.selected_index - 1)
        elif direction == 'S':  # 下
            self.ui.selected_index = min(
                len(self.ui.current_list) - 1, 
                self.ui.selected_index + 1
            )


def main():
    """主函数"""
    # 检查必要依赖
    try:
        from git import Repo
    except ImportError:
        print("请安装依赖：pip install gitpython")
        return
    
    # 创建并运行应用
    app = GitreeApp()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n程序已被中断")
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()