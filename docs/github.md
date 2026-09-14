# GitHub 发布

目标账号 fawei-GitHup；项目独立维护，不并入其他作者或用途的技能仓库。原始 PPT 与病例不得进入 Git。
准备完并通过检查后，首次发布需要明确 public/private。以 public 为例（仅在用户选定后执行）：

```sh
git init -b main
git add .
git commit -m "Release medical presentation architect 1.0.0"
gh repo create fawei-GitHup/medical-presentation-architect --public --source . --remote origin --push
git tag v1.0.0
git push origin v1.0.0
```

私有仓库将 --public 改为 --private；私有仓库使用有权限的 git/gh 下载，匿名 curl 无法获取。不要把 token 写入 URL 或脚本。现有仓库上传通过新分支/PR 进行，检查权限与远端分支后再提交。
