# Git 使用指南

## 一、基础配置

### 1.1 配置用户信息
```bash
# 设置全局用户名
git config --global user.name "你的名字"

# 设置全局邮箱
git config --global user.email "你的邮箱"

# 查看配置
git config --list
```

---

## 二、仓库初始化

### 2.1 创建新仓库
```bash
# 初始化本地仓库
git init

# 添加远程仓库
git remote add origin https://github.com/用户名/仓库名.git

# 查看远程仓库
git remote -v
```

### 2.2 克隆远程仓库
```bash
# 克隆仓库
git clone https://github.com/用户名/仓库名.git

# 克隆到指定目录
git clone https://github.com/用户名/仓库名.git 目录名
```

---

## 三、日常操作流程

### 3.1 查看状态
```bash
# 查看工作区状态
git status

# 简洁模式
git status --short
```

### 3.2 添加文件到暂存区
```bash
# 添加单个文件
git add 文件名

# 添加所有修改
git add .

# 添加指定目录
git add src/

# 交互式添加
git add -p
```

### 3.3 提交代码
```bash
# 提交暂存区的内容
git commit -m "提交信息"

# 多行提交信息
git commit -m "$(cat <<'EOF'
feat: 新功能说明

- 详细说明1
- 详细说明2

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

### 3.4 推送到远程
```bash
# 首次推送（建立追踪）
git push -u origin master

# 后续推送
git push

# 推送到指定分支
git push origin 分支名
```

---

## 四、查看历史

### 4.1 查看提交历史
```bash
# 详细历史
git log

# 简洁模式（推荐）
git log --oneline

# 查看最近N条
git log -5

# 图形化显示
git log --oneline --graph --all

# 查看某个文件的修改历史
git log -p 文件名

# 搜索提交信息
git log --grep="关键词"
```

### 4.2 查看提交详情
```bash
# 查看某次提交的详情
git show commit_id

# 查看某次提交的简要信息
git show --stat commit_id
```

### 4.3 查看文件差异
```bash
# 查看工作区与暂存区的差异
git diff

# 查看暂存区与最新提交的差异
git diff --cached

# 查看两个提交之间的差异
git diff commit1 commit2

# 查看某个文件的差异
git diff 文件名
```

---

## 五、分支管理

### 5.1 分支操作
```bash
# 查看所有分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 创建新分支
git branch 分支名

# 切换分支
git checkout 分支名

# 创建并切换分支
git checkout -b 分支名

# 删除本地分支
git branch -d 分支名

# 强制删除分支
git branch -D 分支名
```

### 5.2 合并分支
```bash
# 切换到主分支
git checkout master

# 合并其他分支到当前分支
git merge 分支名

# 变基（rebase）
git rebase 分支名
```

### 5.3 解决冲突
```bash
# 查看冲突文件
git status

# 编辑冲突文件后
git add 冲突文件

# 完成合并
git commit
```

---

## 六、版本回退

### 6.1 回退命令
```bash
# 回退到上一个版本（保留修改在工作区）
git reset --soft HEAD~1

# 回退到上一个版本（清空暂存区，保留工作区）
git reset --mixed HEAD~1

# 回退到上一个版本（丢弃所有修改，危险！）
git reset --hard HEAD~1

# 回退到指定版本
git reset --hard commit_id

# 只撤销提交，保留代码修改
git reset --mixed HEAD~1
```

### 6.2 回退参数说明
| 参数 | 说明 | 使用场景 |
|------|------|----------|
| `--soft` | 只移动 HEAD，保留暂存区和工作区 | 想重新组织提交 |
| `--mixed` | 移动 HEAD，清空暂存区，保留工作区（默认） | 想重新添加文件 |
| `--hard` | 移动 HEAD，清空暂存区和工作区 | **危险**，完全回退 |

### 6.3 版本号说明
- `HEAD` - 当前提交
- `HEAD~1` - 上一个提交
- `HEAD~3` - 上三个提交
- `commit_id` - 指定提交的哈希值

### 6.4 创建回退提交（安全方式）
```bash
# 用于已推送到远程的提交
git revert HEAD

# 回退多个提交
git revert HEAD~3..HEAD
```

---

## 七、撤销操作

### 7.1 撤销工作区的修改
```bash
# 撤销单个文件的修改
git checkout -- 文件名

# 撤销所有文件的修改
git checkout -- .
```

### 7.2 撤销暂存区的文件
```bash
# 从暂存区移除文件（保留工作区）
git reset HEAD 文件名

# 从暂存区移除所有文件
git reset HEAD .
```

### 7.3 撤销提交
```bash
# 修改最后一次提交的信息
git commit --amend -m "新的提交信息"

# 修改最后一次提交（包含新文件）
git add 新文件
git commit --amend
```

---

## 八、远程仓库操作

### 8.1 远程仓库管理
```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin URL

# 修改远程仓库地址
git remote set-url origin 新URL

# 删除远程仓库
git remote remove origin

# 重命名远程仓库
git remote rename 旧名称 新名称
```

### 8.2 拉取远程更新
```bash
# 拉取并合并
git pull

# 拉取但不合并
git fetch

# 拉取指定分支
git pull origin 分支名
```

### 8.3 推送操作
```bash
# 推送本地分支到远程
git push origin 本地分支:远程分支

# 强制推送（危险！）
git push -f origin 分支名

# 删除远程分支
git push origin --delete 分支名
```

---

## 九、标签管理

### 9.1 标签操作
```bash
# 查看所有标签
git tag

# 创建轻量标签
git tag 标签名

# 创建带注释的标签
git tag -a v1.0.0 -m "版本说明"

# 给历史提交打标签
git tag -a v1.0.0 commit_id

# 推送标签到远程
git push origin 标签名

# 推送所有标签
git push origin --tags

# 删除本地标签
git tag -d 标签名

# 删除远程标签
git push origin --delete 标签名
```

---

## 十、暂存和恢复

### 10.1 暂存工作
```bash
# 暂存当前工作
git stash

# 暂存并添加说明
git stash save "说明信息"

# 查看暂存列表
git stash list

# 恢复最近一次暂存
git stash pop

# 恢复指定暂存
git stash apply stash@{编号}

# 删除暂存
git stash drop stash@{编号}

# 清空所有暂存
git stash clear
```

---

## 十一、忽略文件

### 11.1 .gitignore 配置
```bash
# 忽略所有 .log 文件
*.log

# 忽略 node_modules 目录
node_modules/

# 忽略特定文件
config.local.js

# 忽略除特定文件外的所有文件
*
!important_file.txt

# 忽略目录
build/
dist/

# 忽略临时文件
*.tmp
*.cache
```

### 11.2 已跟踪文件的忽略
```bash
# 从 Git 追踪中移除（但保留本地文件）
git rm --cached 文件名

# 从 Git 追踪中移除目录
git rm -r --cached 目录名/

# 提交更改
git commit -m "chore: 更新 .gitignore"
```

---

## 十二、常用工作流

### 12.1 功能开发流程
```bash
# 1. 从主分支创建功能分支
git checkout -b feature/功能名

# 2. 开发并提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送到远程
git push -u origin feature/功能名

# 4. 在 GitHub 上创建 Pull Request

# 5. 合并后删除本地分支
git checkout master
git branch -d feature/功能名
```

### 12.2 修复 Bug 流程
```bash
# 1. 创建修复分支
git checkout -b fix/bug描述

# 2. 修复并提交
git add .
git commit -m "fix: 修复某某问题"

# 3. 推送并创建 PR
git push -u origin fix/bug描述
```

### 12.3 紧急修复（Hotfix）
```bash
# 1. 从主分支创建热修复分支
git checkout -b hotfix/问题描述

# 2. 修复并提交
git add .
git commit -m "hotfix: 紧急修复某某问题"

# 3. 合并到主分支并打标签
git checkout master
git merge hotfix/问题描述
git tag -a v1.0.1 -m "修复某某问题"

# 4. 推送到远程
git push && git push --tags
```

---

## 十三、提交信息规范

### 13.1 常用类型
```
feat:     新功能
fix:      修复 bug
docs:     文档更新
style:    代码格式（不影响代码运行的变动）
refactor: 重构（既不是新增功能，也不是修改bug的代码变动）
test:     增加测试
chore:    构建过程或辅助工具的变动
perf:     性能优化
ci:       CI/CD 相关改动
```

### 13.2 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

示例：
```
feat(user): 添加用户登录功能

- 实现用户名密码登录
- 添加 JWT token 验证
- 集成第三方登录

Closes #123
```

---

## 十四、常见问题解决

### 14.1 推送冲突
```bash
# 1. 先拉取远程更新
git pull --rebase

# 2. 解决冲突
# 编辑冲突文件

# 3. 继续 rebase
git rebase --continue

# 4. 推送
git push
```

### 14.2 误删除文件
```bash
# 恢复已删除的文件
git checkout HEAD -- 文件名

# 恢复已删除的目录
git checkout HEAD -- 目录名/
```

### 14.3 清理大文件历史
```bash
# 使用 git filter-branch（谨慎使用）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 大文件名" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 十五、实用别名配置

```bash
# 配置别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"
git config --global alias.last "log -1 HEAD"
```

使用：
```bash
git st        # 等同于 git status
git co        # 等同于 git checkout
git lg        # 查看图形化日志
```

---

## 十六、安全注意事项

1. **不要提交敏感信息**
   - API 密钥、密码、Token
   - 数据库连接字符串
   - 私钥文件（.pem, .key）

2. **使用 .gitignore 忽略**
   ```
   .env
   *.key
   *.pem
   config/secrets.yml
   ```

3. **使用环境变量**
   - 开发环境：.env.local
   - 生产环境：服务器环境变量

4. **定期检查提交历史**
   ```bash
   # 搜索敏感信息
   git log -p | grep -i "password\|secret\|api_key"
   ```

---

## 十七、项目实际使用的命令

基于本项目（AI Career Agent）的实际操作：

```bash
# 1. 初始化仓库
git init

# 2. 添加所有文件
git add .

# 3. 创建提交
git commit -m "feat: 初始化项目"

# 4. 添加远程仓库
git remote add origin https://github.com/j16014004-star/-.git

# 5. 推送到远程
git push -u origin master

# 6. 日常开发
git status                    # 查看状态
git add .                     # 添加修改
git commit -m "feat: 新功能"  # 提交
git push                      # 推送

# 7. 查看历史
git log --oneline

# 8. 版本回退（如需要）
git reset --soft HEAD~1       # 安全回退
git reset --hard HEAD~1       # 完全回退（危险）
```

---

## 附录：命令速查表

| 操作 | 命令 |
|------|------|
| 初始化仓库 | `git init` |
| 克隆仓库 | `git clone URL` |
| 查看状态 | `git status` |
| 添加文件 | `git add .` |
| 提交 | `git commit -m "msg"` |
| 推送 | `git push` |
| 拉取 | `git pull` |
| 查看日志 | `git log --oneline` |
| 创建分支 | `git branch 名称` |
| 切换分支 | `git checkout 名称` |
| 合并分支 | `git merge 名称` |
| 回退版本 | `git reset --hard HEAD~1` |
| 暂存工作 | `git stash` |
| 恢复暂存 | `git stash pop` |
| 查看差异 | `git diff` |
| 添加远程 | `git remote add origin URL` |
| 查看远程 | `git remote -v` |
| 打标签 | `git tag v1.0.0` |
