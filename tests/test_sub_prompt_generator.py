"""Tests for sub-prompt generation."""
from execution_protocol.phase_subdivider import SubPrompt
from execution_protocol.sub_prompt_generator import SubPromptGenerator

def test_sub_prompt_generator_renders_files() -> None:
    """The generated prompt contains the requested file path."""
    prompt = SubPromptGenerator().generate(SubPrompt('1.1', 1, ['a.py'], 10), 'build')
    assert 'a.py' in prompt
