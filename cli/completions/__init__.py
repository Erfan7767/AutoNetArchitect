"""Shell completion script generators for the AutoNetArchitect CLI."""

from .bash_completion import generate as generate_bash
from .fish_completion import generate as generate_fish
from .zsh_completion import generate as generate_zsh

__all__ = ["generate_bash", "generate_fish", "generate_zsh"]
