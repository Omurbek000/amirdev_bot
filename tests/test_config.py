import os
from unittest.mock import patch

import config


def test_int_list_parsing():
    assert config._int_list("123,456") == [123, 456]
    assert config._int_list("123, 456 ") == [123, 456]
    assert config._int_list("") == []
    assert config._int_list("abc,123") == [123]


def test_int_safe_parsing():
    assert config._int("30", 10) == 30
    assert config._int("abc", 10) == 10
    assert config._int("", 10) == 10
    assert config._int("notanumber", 5) == 5


def test_validate_missing_token():
    with patch.object(config, "BOT_TOKEN", ""), patch.object(
        config, "ADMIN_IDS", [123]
    ):
        try:
            config.validate()
        except RuntimeError as e:
            assert "BOT_TOKEN" in str(e)
            return
    raise AssertionError("validate should raise RuntimeError when BOT_TOKEN is empty")


def test_validate_missing_admins():
    with patch.object(config, "BOT_TOKEN", "123:ABC"), patch.object(
        config, "ADMIN_IDS", []
    ):
        try:
            config.validate()
        except RuntimeError as e:
            assert "ADMIN_IDS" in str(e)
            return
    raise AssertionError("validate should raise RuntimeError when ADMIN_IDS is empty")


def test_validate_ok():
    with patch.object(config, "BOT_TOKEN", "123:ABC"), patch.object(
        config, "ADMIN_IDS", [123]
    ):
        config.validate()  # should not raise
