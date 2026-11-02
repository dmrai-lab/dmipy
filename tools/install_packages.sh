#!/usr/bin/env bash
# Install the packages a build of this site documents, with the docs toolchain, into the active Python.
#
#   released   the releases on PyPI, through this repository's extras: what the root of dmipy.org documents
#   mains      the packages' git mains: what dmipy.org/dev/ documents
#
# Run:  bash tools/install_packages.sh released|mains
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  released)
    pip install "$root[docs,cpu,tract]" matplotlib
    ;;
  mains)
    # the toolchain and the third-party requirements of the mains; the mains name releases of each other that
    # PyPI may not hold yet, so they are installed together without their declared dependencies
    pip install "$root[docs]" "jax[cpu]>=0.6.2" jaxopt matplotlib scipy safetensors threadpoolctl packaging
    mains=()
    for p in dmipy-analytic dmipy-replay dmipy-sim dmipy-fit dmipy-design dmipy-tract; do
      mains+=("$p @ git+https://github.com/dmrai-lab/$p@main")
    done
    pip install --force-reinstall --no-deps "${mains[@]}"
    ;;
  *)
    echo "usage: bash tools/install_packages.sh released|mains" >&2
    exit 2
    ;;
esac
pip list 2>/dev/null | grep -i '^dmipy'
