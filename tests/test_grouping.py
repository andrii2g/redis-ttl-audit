import pytest

from redis_ttl_audit.grouping import group_key


def test_group_key_depth_2() -> None:
    assert group_key("cache:user:123", 2) == "cache:user"


def test_group_key_depth_1() -> None:
    assert group_key("cache:user:123", 1) == "cache"


def test_group_key_simple_key() -> None:
    assert group_key("simplekey", 2) == "simplekey"


def test_group_key_depth_too_large() -> None:
    assert group_key("cache:user", 5) == "cache:user"


def test_group_key_empty_key() -> None:
    assert group_key("", 2) == ""


def test_group_key_invalid_depth() -> None:
    with pytest.raises(ValueError):
        group_key("cache:user:123", 0)
