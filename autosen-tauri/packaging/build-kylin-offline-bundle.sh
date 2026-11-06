#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd -- "$script_dir/.." && pwd)"
version="$(node -p "require('$project_dir/package.json').version")"
architecture="$(dpkg --print-architecture)"

if [[ "$architecture" != "amd64" && "$architecture" != "arm64" ]]; then
  echo "错误：仅支持 amd64 和 arm64，当前架构为 $architecture" >&2
  exit 1
fi

for command_name in node npm cargo dpkg dpkg-deb dpkg-scanpackages objdump sha256sum apt-get; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "错误：缺少构建命令 $command_name，请先查看 packaging/README.md 安装构建依赖。" >&2
    exit 1
  fi
done

host_glibc="$(getconf GNU_LIBC_VERSION | awk '{print $2}')"
if dpkg --compare-versions "$host_glibc" gt "2.31"; then
  echo "错误：当前构建机 glibc=$host_glibc，高于目标 2.31。" >&2
  echo "请在对应架构、glibc 2.31 的麒麟系统或兼容构建容器中运行。" >&2
  exit 1
fi

cd "$project_dir"
npm ci
npm run tauri build -- --bundles deb

binary="$project_dir/src-tauri/target/release/autosen-tauri"
if [[ ! -x "$binary" ]]; then
  echo "错误：未找到构建后的程序 $binary" >&2
  exit 1
fi

max_glibc="$(objdump -T "$binary" | sed -n 's/.*GLIBC_\([0-9][0-9.]*\).*/\1/p' | sort -V | tail -n 1)"
if [[ -n "$max_glibc" ]] && dpkg --compare-versions "$max_glibc" gt "2.31"; then
  echo "错误：程序要求 GLIBC_$max_glibc，无法保证在 glibc 2.31 上运行。" >&2
  exit 1
fi

mapfile -t deb_files < <(find "$project_dir/src-tauri/target/release/bundle/deb" -maxdepth 1 -type f -name '*.deb' -print)
if [[ "${#deb_files[@]}" -ne 1 ]]; then
  echo "错误：预期生成 1 个 deb，实际找到 ${#deb_files[@]} 个。" >&2
  exit 1
fi

deb_arch="$(dpkg-deb -f "${deb_files[0]}" Architecture)"
deb_depends="$(dpkg-deb -f "${deb_files[0]}" Depends)"
if [[ "$deb_arch" != "$architecture" ]]; then
  echo "错误：deb 架构 $deb_arch 与构建机 $architecture 不一致。" >&2
  exit 1
fi
if [[ -z "$deb_depends" ]]; then
  echo "错误：deb 未声明运行依赖，拒绝生成不可安装的离线包。" >&2
  exit 1
fi

output_root="${AUTOSEN_OUTPUT_DIR:-$project_dir/release}"
bundle_dir="$output_root/AutoSen_${version}_kylin_glibc231_${architecture}_offline"
if [[ -e "$bundle_dir" ]]; then
  echo "错误：输出目录已存在，请先移动或改名：$bundle_dir" >&2
  exit 1
fi
mkdir -p "$bundle_dir/debs/partial"
cp "${deb_files[0]}" "$bundle_dir/debs/"
cp "$script_dir/install-offline.sh" "$bundle_dir/"
chmod 755 "$bundle_dir/install-offline.sh"

empty_status="$(mktemp)"
cleanup() {
  rm -f -- "$empty_status"
}
trap cleanup EXIT

if [[ "$EUID" -eq 0 ]]; then
  sudo_command=()
elif command -v sudo >/dev/null 2>&1; then
  sudo_command=(sudo)
else
  echo "错误：收集离线依赖需要 root 权限，但系统没有 sudo。" >&2
  exit 1
fi

"${sudo_command[@]}" apt-get \
  -o "Dir::State::status=$empty_status" \
  -o "Dir::Cache::archives=$bundle_dir/debs" \
  -o APT::Get::List-Cleanup=0 \
  --download-only --no-install-recommends --reinstall \
  install "$bundle_dir/debs/$(basename "${deb_files[0]}")"

rmdir "$bundle_dir/debs/partial" 2>/dev/null || true
(
  cd "$bundle_dir/debs"
  dpkg-scanpackages . /dev/null > Packages
  gzip -9 -k Packages
)

cat > "$bundle_dir/BUILD-INFO.txt" <<EOF
AutoSen version: $version
Architecture: $architecture
Build host glibc: $host_glibc
Maximum required glibc symbol: ${max_glibc:-unknown}
Deb dependencies: $deb_depends
Important: dependencies were collected from this build machine's configured APT repositories.
Install only on the same Kylin release and architecture.
EOF

(
  cd "$bundle_dir"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)

echo "完成：$bundle_dir"
echo "请将整个目录复制到离线机器，然后运行：sudo ./install-offline.sh"
