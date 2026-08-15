"""Zsh completion generator."""
from __future__ import annotations


def generate(program: str = "autonet") -> str:
    """Return a Zsh completion script for the CLI."""
    variable = "_AUTONET_COMPLETE"
    return f'''# AutoNetArchitect Zsh completion\n_{program}_completion() {{\n    local -a reply\n    reply=($({variable}=zsh_complete {program} -- "$words[@]"))\n    _describe 'values' reply\n}}\ncompdef _{program}_completion {program}\n'''


if __name__ == "__main__":
    print(generate())
