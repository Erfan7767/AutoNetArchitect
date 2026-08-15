#!/usr/bin/env bash
set -euo pipefail

PROGRAM="${1:-autonet}"
TARGET_DIR="${2:-${HOME}/.local/share/${PROGRAM}/completions}"
mkdir -p "${TARGET_DIR}"
python3 - "${PROGRAM}" "${TARGET_DIR}" <<'PY'
from pathlib import Path
import sys
from cli.completions.bash_completion import generate as bash_generate
from cli.completions.zsh_completion import generate as zsh_generate
from cli.completions.fish_completion import generate as fish_generate

program = sys.argv[1]
target = Path(sys.argv[2])
target.joinpath(f'{program}.bash').write_text(bash_generate(program), encoding='utf-8')
target.joinpath(f'_{program}').write_text(zsh_generate(program), encoding='utf-8')
target.joinpath(f'{program}.fish').write_text(fish_generate(program), encoding='utf-8')
print(f'completion files written to {target}')
PY
