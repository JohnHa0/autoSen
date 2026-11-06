#!/usr/bin/env bash
set -euo pipefail

case "$(uname -m)" in
  x86_64) actual_arch=amd64 ;;
  aarch64) actual_arch=arm64 ;;
  *) echo "Unsupported build architecture: $(uname -m)" >&2; exit 1 ;;
esac

if [[ "${EXPECTED_ARCH:-}" != "$actual_arch" ]]; then
  echo "Runner architecture mismatch: expected ${EXPECTED_ARCH:-unset}, got $actual_arch" >&2
  exit 1
fi
if [[ "$(getconf GNU_LIBC_VERSION | awk '{print $2}')" != "2.31" ]]; then
  echo "Builder must use glibc 2.31" >&2
  exit 1
fi

npm ci
npm run tauri build -- --bundles deb

binary=src-tauri/target/release/autosen-tauri
max_glibc="$(objdump -T "$binary" | sed -n 's/.*GLIBC_\([0-9][0-9.]*\).*/\1/p' | sort -V | tail -n 1)"
if [[ -z "$max_glibc" ]] || dpkg --compare-versions "$max_glibc" gt 2.31; then
  echo "Invalid maximum GLIBC symbol: ${max_glibc:-none}" >&2
  exit 1
fi

mapfile -t packages < <(find src-tauri/target/release/bundle/deb -maxdepth 1 -type f -name '*.deb' -print)
if [[ "${#packages[@]}" -ne 1 ]]; then
  echo "Expected exactly one DEB, found ${#packages[@]}" >&2
  exit 1
fi

package_arch="$(dpkg-deb -f "${packages[0]}" Architecture)"
package_depends="$(dpkg-deb -f "${packages[0]}" Depends)"
if [[ "$package_arch" != "$actual_arch" ]]; then
  echo "DEB architecture mismatch: expected $actual_arch, got $package_arch" >&2
  exit 1
fi
if [[ -z "$package_depends" || "$package_depends" != *libwebkit2gtk-4.0-37* ]]; then
  echo "DEB runtime dependency metadata is incomplete: $package_depends" >&2
  exit 1
fi

version="$(node -p "require('./package.json').version")"
output_dir="artifacts/$actual_arch"
mkdir -p "$output_dir"
output_deb="$output_dir/AutoSen_${version}_${actual_arch}_glibc231.deb"
cp "${packages[0]}" "$output_deb"
(
  cd "$output_dir"
  sha256sum "$(basename "$output_deb")" > SHA256SUMS
)

cat > "$output_dir/BUILD-INFO.txt" <<EOF
AutoSen version: $version
Architecture: $actual_arch
Build environment: Debian 11 (glibc 2.31)
Maximum required GLIBC symbol: GLIBC_$max_glibc
Deb dependencies: $package_depends
EOF
