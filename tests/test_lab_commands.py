"""Tests for lab CLI commands."""
from __future__ import annotations

from click.testing import CliRunner

from cli.app import cli


def test_lab_help_declares_validation_scope():
    result = CliRunner().invoke(cli, ["lab", "--help"])
    assert result.exit_code == 0
    assert "validation" in result.output.lower()
    assert "deploy" in result.output


def test_lab_deploy_requires_lab_name():
    result = CliRunner().invoke(cli, ["lab", "deploy"])
    assert result.exit_code == 2
    assert "--lab" in result.output
