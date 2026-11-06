# AutoSen

AutoSen 是面向麒麟 Linux 的 ZIP 自动监控与文本整理工具，支持自动解压、重命名、跨目录移动、插入自定义文字片段和生成 CSV 汇总。

当前版本：`1.0.8`。

## 本地开发验证

```bash
npm ci
npm run build
cargo test --manifest-path src-tauri/Cargo.toml
cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
```

## 将本地修改同步到 GitHub

本项目的 Git 仓库根目录是上级 `autoSen`，不是当前 `autosen-tauri` 子目录：

```bash
cd "/Users/hao/Library/Mobile Documents/com~apple~CloudDocs/Code/autoSen"
git status
git add .github/workflows/tauri-build.yml autosen-tauri
git commit -m "fix: improve archive processing and Linux packaging"
git pull --rebase origin master
git push origin master
```

应当先提交本地修改，再执行 `pull --rebase`，最后推送。若 `pull --rebase` 报冲突，应解决冲突并重新运行本地测试后再推送，不要强制覆盖远端。

## GitHub 云端构建 amd64 与 arm64

工作流位于仓库根目录 `.github/workflows/tauri-build.yml`。每次推送到 `master` 都会在以下环境并行构建：

- GitHub `ubuntu-24.04` 原生 amd64 runner；
- GitHub `ubuntu-24.04-arm` 原生 arm64 runner；
- 两者都在 Debian 11 容器中编译，因此构建环境 glibc 固定为 2.31。

构建会检查 Deb 架构、运行依赖字段和二进制引用的最高 GLIBC 符号版本。成功后可在 GitHub 仓库的 **Actions → 对应运行记录 → Artifacts** 下载两个安装包。

也可在 Actions 页面手动运行 `Build AutoSen Linux DEB` 工作流。

## 发布 GitHub Release

仓库已经存在旧的 `v1.0.7` 标签，本次应发布 `v1.0.8`：

```bash
cd "/Users/hao/Library/Mobile Documents/com~apple~CloudDocs/Code/autoSen"
git tag -a v1.0.8 -m "AutoSen v1.0.8"
git push origin v1.0.8
```

标签触发的工作流会先确认标签与 `package.json` 版本一致，再把 amd64、arm64 两个 Deb 及校验文件上传到同一个 GitHub Release。不要移动或覆盖已经发布的旧标签。

## 离线安装

云端生成的单个 Deb 已正确声明 GTK/WebKit 运行依赖，但它本身不是包含整个麒麟软件源的“全离线包”。完全离线部署需要在与目标机器相同的麒麟版本和架构上收集依赖：

```bash
./packaging/build-kylin-offline-bundle.sh
```

请分别在 amd64、arm64 的联网麒麟构建机上运行，并将生成的整个 `release/AutoSen_*_offline/` 目录复制到对应离线机器。详细步骤见 [packaging/README.md](packaging/README.md)。
