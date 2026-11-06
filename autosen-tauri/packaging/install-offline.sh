#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$EUID" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    exec sudo -- "$0" "$@"
  fi
  echo "错误：安装需要 root 权限，请使用 root 运行本脚本。" >&2
  exit 1
fi

cd "$script_dir"
sha256sum -c SHA256SUMS

mapfile -t app_debs < <(find "$script_dir/debs" -maxdepth 1 -type f -name 'autosen-tauri_*.deb' -print)
if [[ "${#app_debs[@]}" -ne 1 ]]; then
  echo "错误：离线包中应当只有一个 AutoSen 主安装包。" >&2
  exit 1
fi

system_arch="$(dpkg --print-architecture)"
package_arch="$(dpkg-deb -f "${app_debs[0]}" Architecture)"
if [[ "$system_arch" != "$package_arch" ]]; then
  echo "错误：当前系统架构为 $system_arch，安装包架构为 $package_arch。" >&2
  exit 1
fi

temporary_dir="$(mktemp -d)"
cleanup() {
  if [[ -n "${temporary_dir:-}" && "$temporary_dir" == /tmp/* ]]; then
    rm -rf -- "$temporary_dir"
  fi
}
trap cleanup EXIT
mkdir -p "$temporary_dir/lists/partial"

repository_path="${script_dir// /%20}/debs"
source_list="$temporary_dir/autosen-offline.list"
printf 'deb [trusted=yes] file:%s ./\n' "$repository_path" > "$source_list"

apt_options=(
  -o "Dir::Etc::sourcelist=$source_list"
  -o "Dir::Etc::sourceparts=-"
  -o "Dir::State::lists=$temporary_dir/lists"
  -o APT::Get::List-Cleanup=0
)

apt-get "${apt_options[@]}" update
apt-get "${apt_options[@]}" --no-download install "${app_debs[0]}"

echo "AutoSen 安装完成。"
