"""Bash completion generator."""
from __future__ import annotations


def generate(program: str = "autonet") -> str:
    """Return a Bash completion script for the CLI."""
    variable = "_AUTONET_COMPLETE"
    return f'''# AutoNetArchitect Bash completion\n_{program}_completion() {{\n    local IFS=$'\\n'\n    COMPREPLY=( $(COMP_WORDS="${{COMP_WORDS[*]}}" COMP_CWORD=$COMP_CWORD {variable}=bash_complete {program}) )\n}}\ncomplete -o nosort -F _{program}_completion {program}\n'''


if __name__ == "__main__":
    print(generate())
