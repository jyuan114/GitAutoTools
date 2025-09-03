# Git Auto Stash Watcher

一個簡單的 Python 守護程式，能定期檢查 Git repo 是否有修改，若有就自動 stash。

## 功能
- 定期檢查 Git repo 狀態
- 自動執行 `git stash push`
- 支援包含 untracked 檔案
- 可當作 Linux systemd service / Windows Task Scheduler 背景執行

## 安裝
```bash
git clone https://github.com/yourname/git-auto-stash-watcher.git
cd git-auto-stash-watcher
pip install -r requirements.txt
