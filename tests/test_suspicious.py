from redis_ttl_audit.suspicious import is_suspicious_persistent_group


def test_cache_group_is_suspicious() -> None:
    assert is_suspicious_persistent_group("cache:user") is True


def test_session_group_is_suspicious() -> None:
    assert is_suspicious_persistent_group("session:web") is True


def test_temp_group_is_suspicious() -> None:
    assert is_suspicious_persistent_group("temp:job") is True


def test_rate_limit_group_is_suspicious() -> None:
    assert is_suspicious_persistent_group("rate-limit:api") is True


def test_config_group_is_not_suspicious() -> None:
    assert is_suspicious_persistent_group("config:feature") is False


def test_lookup_group_is_not_suspicious() -> None:
    assert is_suspicious_persistent_group("lookup:country") is False

