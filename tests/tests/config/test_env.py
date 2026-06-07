import environ
import pytest
from django.core.exceptions import ImproperlyConfigured

from api.env import validate_env


def _valid_env():
    """Return a dict of valid env vars for testing."""
    return {
        "SECRET_KEY": "x" * 50,
        "DEBUG": "True",
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "admin",
        "POSTGRES_PASSWORD": "password",
        "EMAIL_ACTIVATION_TOKEN_LIFETIME": "300",
    }


def _make_env(values=None):
    """Create an Env instance with the given ENVIRON values."""
    env = environ.Env()
    env.ENVIRON = values or {}
    return env


# ── Happy path ──────────────────────────────────────────────────────────


def test_validate_env_all_valid():
    env = _make_env(_valid_env())
    config = validate_env(env=env)

    assert config["SECRET_KEY"] == "x" * 50
    assert config["DEBUG"] is True
    assert config["ALLOWED_HOSTS"] == ["localhost", "127.0.0.1"]
    assert config["POSTGRES_HOST"] == "localhost"
    assert config["POSTGRES_PORT"] == 5432
    assert config["POSTGRES_DB"] == "test_db"
    assert config["POSTGRES_USER"] == "admin"
    assert config["POSTGRES_PASSWORD"] == "password"
    assert config["EMAIL_ACTIVATION_TOKEN_LIFETIME"] == 300


# ── SECRET_KEY ──────────────────────────────────────────────────────────


def test_validate_secret_key():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["SECRET_KEY"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty
    env = _make_env(_valid_env())
    env.ENVIRON["SECRET_KEY"] = ""
    with pytest.raises(ImproperlyConfigured, match="at least 50"):
        validate_env(env=env)

    # Too short
    env = _make_env(_valid_env())
    env.ENVIRON["SECRET_KEY"] = "x" * 49
    with pytest.raises(ImproperlyConfigured, match="at least 50"):
        validate_env(env=env)


# ── DEBUG ───────────────────────────────────────────────────────────────


def test_validate_debug():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["DEBUG"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # django-environ's bool() is lenient: any non-truthy string is False.
    # There is no "invalid bool" error case — only "missing".


# ── ALLOWED_HOSTS ───────────────────────────────────────────────────────


def test_validate_allowed_hosts():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["ALLOWED_HOSTS"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty string results in empty list
    env = _make_env(_valid_env())
    env.ENVIRON["ALLOWED_HOSTS"] = ""
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)


# ── POSTGRES_HOST ───────────────────────────────────────────────────────


def test_validate_postgres_host():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["POSTGRES_HOST"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_HOST"] = ""
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)


# ── POSTGRES_PORT ───────────────────────────────────────────────────────


def test_validate_postgres_port():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["POSTGRES_PORT"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Not an integer
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_PORT"] = "abc"
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # < 1
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_PORT"] = "0"
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_PORT must be"):
        validate_env(env=env)

    # > 65535
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_PORT"] = "65536"
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_PORT must be"):
        validate_env(env=env)

    # Negative
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_PORT"] = "-1"
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_PORT must be"):
        validate_env(env=env)


# ── POSTGRES_DB ─────────────────────────────────────────────────────────


def test_validate_postgres_db():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["POSTGRES_DB"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_DB"] = ""
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)


# ── POSTGRES_USER ───────────────────────────────────────────────────────


def test_validate_postgres_user():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["POSTGRES_USER"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_USER"] = ""
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)


# ── POSTGRES_PASSWORD ───────────────────────────────────────────────────


def test_validate_postgres_password():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["POSTGRES_PASSWORD"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Empty
    env = _make_env(_valid_env())
    env.ENVIRON["POSTGRES_PASSWORD"] = ""
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)


# ── EMAIL_ACTIVATION_TOKEN_LIFETIME ─────────────────────────────────────


def test_validate_email_activation_token_lifetime():
    # Missing
    env = _make_env(_valid_env())
    del env.ENVIRON["EMAIL_ACTIVATION_TOKEN_LIFETIME"]
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Not an integer
    env = _make_env(_valid_env())
    env.ENVIRON["EMAIL_ACTIVATION_TOKEN_LIFETIME"] = "abc"
    with pytest.raises(ImproperlyConfigured):
        validate_env(env=env)

    # Zero
    env = _make_env(_valid_env())
    env.ENVIRON["EMAIL_ACTIVATION_TOKEN_LIFETIME"] = "0"
    with pytest.raises(ImproperlyConfigured, match="positive integer"):
        validate_env(env=env)

    # Negative
    env = _make_env(_valid_env())
    env.ENVIRON["EMAIL_ACTIVATION_TOKEN_LIFETIME"] = "-1"
    with pytest.raises(ImproperlyConfigured, match="positive integer"):
        validate_env(env=env)
