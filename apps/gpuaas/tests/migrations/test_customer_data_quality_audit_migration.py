from alembic.config import Config
from alembic.script import ScriptDirectory


MIGRATION_REVISION = "b7d4e9f2c813"
PARENT_REVISION = "a4c8e2f6b711"


def test_customer_data_quality_audit_migration_exists():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.revision == MIGRATION_REVISION


def test_customer_data_quality_audit_migration_has_expected_parent():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.down_revision == PARENT_REVISION
