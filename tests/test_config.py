"""Tests for API key loading (Task 6 infrastructure).

Secret handling is worth testing directly: a silent failure here means either
a confusing crash mid-run, or a key ending up somewhere it should not.
"""
import os

import pytest

from nutrition_engine.config import (
    API_KEY_VAR,
    MissingAPIKeyError,
    get_api_key,
    load_dotenv,
    mask,
    parse_env_text,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(API_KEY_VAR, raising=False)


# --- .env parsing ----------------------------------------------------------

def test_parses_plain_assignment():
    assert parse_env_text("USDA_API_KEY=abc123") == {"USDA_API_KEY": "abc123"}


def test_ignores_comments_and_blank_lines():
    text = "# a comment\n\nUSDA_API_KEY=abc123\n\n# trailing\n"
    assert parse_env_text(text) == {"USDA_API_KEY": "abc123"}


def test_strips_export_prefix():
    # People paste shell-style lines straight out of a tutorial.
    assert parse_env_text("export USDA_API_KEY=abc123") == {"USDA_API_KEY": "abc123"}


@pytest.mark.parametrize("raw", ['USDA_API_KEY="abc123"', "USDA_API_KEY='abc123'"])
def test_strips_surrounding_quotes(raw):
    assert parse_env_text(raw) == {"USDA_API_KEY": "abc123"}


def test_value_containing_equals_is_preserved():
    assert parse_env_text("KEY=a=b=c") == {"KEY": "a=b=c"}


def test_lines_without_equals_are_ignored():
    assert parse_env_text("not a setting\nKEY=v") == {"KEY": "v"}


# --- Loading into the environment -----------------------------------------

def test_load_writes_into_environ(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("USDA_API_KEY=from_file", encoding="utf-8")
    load_dotenv(env_file)
    # Task 1's USDAClient reads os.getenv, so this is what makes it work
    # without any change to API_File.py.
    assert os.environ[API_KEY_VAR] == "from_file"


def test_existing_environment_variable_wins(tmp_path, monkeypatch):
    # CI sets real secrets in the environment; a stale local file must not
    # silently override them.
    monkeypatch.setenv(API_KEY_VAR, "from_environment")
    env_file = tmp_path / ".env"
    env_file.write_text("USDA_API_KEY=from_file", encoding="utf-8")
    load_dotenv(env_file)
    assert os.environ[API_KEY_VAR] == "from_environment"


def test_override_forces_the_file_value(tmp_path, monkeypatch):
    monkeypatch.setenv(API_KEY_VAR, "from_environment")
    env_file = tmp_path / ".env"
    env_file.write_text("USDA_API_KEY=from_file", encoding="utf-8")
    load_dotenv(env_file, override=True)
    assert os.environ[API_KEY_VAR] == "from_file"


def test_missing_env_file_is_not_an_error(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}


# --- get_api_key -----------------------------------------------------------

def test_missing_key_raises_with_setup_instructions(tmp_path, monkeypatch):
    monkeypatch.setattr("nutrition_engine.config.DEFAULT_ENV_PATH", tmp_path / ".env")
    with pytest.raises(MissingAPIKeyError) as error:
        get_api_key()
    message = str(error.value)
    assert "api-key-signup" in message
    assert ".env" in message


def test_optional_key_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr("nutrition_engine.config.DEFAULT_ENV_PATH", tmp_path / ".env")
    assert get_api_key(required=False) is None


def test_whitespace_only_key_counts_as_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("nutrition_engine.config.DEFAULT_ENV_PATH", tmp_path / ".env")
    monkeypatch.setenv(API_KEY_VAR, "   ")
    assert get_api_key(required=False) is None


# --- Masking ---------------------------------------------------------------

def test_mask_hides_the_middle():
    masked = mask("abcd1234567890wxyz")
    assert masked.startswith("abcd")
    assert masked.endswith("wxyz")
    assert "1234567890" not in masked


def test_short_keys_are_fully_hidden():
    assert set(mask("short")) == {"*"}


def test_mask_handles_empty():
    assert mask("") == "(empty)"
