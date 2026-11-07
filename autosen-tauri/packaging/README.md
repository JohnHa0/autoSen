# 麒麟 glibc 2.31 离线打包

离线包必须按麒麟版本和 CPU 架构分别制作。不要在高版本 Ubuntu 上构建后直接复制二进制；这样会把更高版本的 glibc 符号带入程序。也不要把 amd64 的依赖包与 arm64 混用。

## 1. 准备两台联网构建环境

- amd64 麒麟系统一台；
- arm64 麒麟系统一台；
- 两台系统均应与最终离线机器采用相同的麒麟发行版、补丁级别和 APT 软件源，glibc 不高于 2.31。

安装基础工具、Node.js 20+、Rust stable，以及 Tauri 1 的 Linux 编译依赖。常见依赖如下（实际包名以该麒麟版本的软件源为准）：

```bash
sudo apt-get install build-essential curl file libgtk-3-dev \
  libwebkit2gtk-4.0-dev libayatana-appindicator3-dev librsvg2-dev \
  patchelf dpkg-dev binutils
```

## 2. 在每个架构上生成离线包

```bash
chmod +x packaging/build-kylin-offline-bundle.sh packaging/install-offline.sh
./packaging/build-kylin-offline-bundle.sh
```

脚本会执行生产构建、校验 deb 架构和依赖字段、检查最高 GLIBC 符号版本，并从当前麒麟 APT 源下载完整依赖闭包。输出位于 `release/AutoSen_版本_kylin_glibc231_架构_offline/`。

依赖闭包来自构建机启用的软件源，因此这一步必须在与离线目标相同的麒麟版本上执行。生成后不要只复制主 deb，必须复制整个目录。

## 3. 在离线机器安装

```bash
cd AutoSen_*_offline
sudo ./install-offline.sh
```

安装脚本会先校验全部文件的 SHA-256、检查 CPU 架构，再临时使用目录内的软件包仓库解析依赖；不会访问网络，也不会永久修改 `/etc/apt/sources.list`。

## 4. 验收

```bash
dpkg -s auto-sen
ldd /usr/bin/auto-sen | grep 'not found' && echo '存在缺失库' || echo '动态库完整'
```

建议在一台未安装开发依赖的干净离线麒麟机器上完成最终验收，并分别保存 amd64、arm64 的安装日志。
