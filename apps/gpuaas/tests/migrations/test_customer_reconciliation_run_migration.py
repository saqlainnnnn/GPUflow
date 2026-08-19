from alembic.config import Config
from alembic.script import ScriptDirectory


MIGRATION_REVISION = "a4c8e2f6b711"
PARENT_REVISION = "9b3e7f1c5a66"


def test_customer_reconciliation_run_migration_exists():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.revision == MIGRATION_REVISION


def test_customer_reconciliation_run_migration_has_expected_parent():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.down_revision == PARENT_REVISION


def test_customer_reconciliation_run_migration_is_current_head():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    assert MIGRATION_REVISION in script.get_heads()
