"""Fish completion generator."""
from __future__ import annotations


def generate(program: str = "autonet") -> str:
    """Return a Fish completion script for the CLI."""
    variable = "_AUTONET_COMPLETE"
    return f'''# AutoNetArchitect Fish completion\nfunction __{program}_complete\n    set -lx COMP_WORDS (commandline -opc)\n    set -lx COMP_CWORD (math (count $COMP_WORDS) - 1)\n    set -lx {variable} fish_complete\n    {program}\nend\ncomplete -c {program} -f -a '(__{program}_complete)'\n'''


if __name__ == "__main__":
    print(generate())
