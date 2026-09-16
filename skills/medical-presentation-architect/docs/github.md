# GitHub 发布

本项目现已发布到公开仓库：[fawei-GitHup/medical-presentation-architect](https://github.com/fawei-GitHup/medical-presentation-architect)。仓库独立维护；原始 PPT、病例和本地运行产物不得进入 Git。首次公开发布由用户明确选择公开后完成。GitHub 连接器用于核对账号与仓库；由于它没有创建仓库的操作，本次使用已登录的官方 `gh` CLI 创建并推送。

## 更新已有仓库

```sh
git status --short
python scripts/release_check.py
python -m unittest discover -s tests -v
git add .
git commit -m "Describe the change"
git push origin main
```

每次发布新版本时，先更新 `VERSION`、`CHANGELOG.md`，重建 ZIP 并计算 SHA-256；本地检查通过后再创建版本标签和 GitHub Release：

```sh
python scripts/package.py --output ../medical-presentation-architect-vX.Y.Z.zip
git tag vX.Y.Z
git push origin vX.Y.Z
gh release create vX.Y.Z ../medical-presentation-architect-vX.Y.Z.zip ../medical-presentation-architect-vX.Y.Z.zip.sha256 --title "vX.Y.Z" --notes-file CHANGELOG.md
```

不要把 token 写入 URL、脚本或提交。仓库可见性由仓库所有者控制；不要在未获明确授权时更改为私有或公开。
