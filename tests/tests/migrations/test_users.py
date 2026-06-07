import pytest
from django.db import connection


@pytest.mark.django_db(transaction=True)
class TestUserMigration:
    """Migration ladder test for the users app.

    Uses django-test-migrations to start from a clean state (no users
    tables) and run through the full forward→reverse→forward cycle.
    The migrator fixture handles setup and teardown automatically.
    """

    def test_ladder(self, migrator):
        # Step 0: start from a clean state — no users tables yet
        migrator.apply_initial_migration(("users", None))

        tables = self._get_tables()
        assert "users_user" not in tables
        assert "users_useractivationtoken" not in tables

        # Step 1: apply forward
        migrator.apply_tested_migration(("users", "0001_initial"))

        tables = self._get_tables()
        assert "users_user" in tables
        assert "users_useractivationtoken" in tables

        # Step 2: reverse back to before any users migration
        migrator.apply_tested_migration(("users", None))

        tables = self._get_tables()
        assert "users_user" not in tables
        assert "users_useractivationtoken" not in tables

        # Step 3: re-apply forward
        migrator.apply_tested_migration(("users", "0001_initial"))

        tables = self._get_tables()
        assert "users_user" in tables
        assert "users_useractivationtoken" in tables

    @staticmethod
    def _get_tables():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            return {row[0] for row in cursor.fetchall()}
