from alembic.config import Config
from alembic.script import ScriptDirectory


MIGRATION_REVISION = "8f2c6d1a4e55"
PARENT_REVISION = "7e1c4a9b2d33"


def test_customer_data_quality_migration_exists():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.revision == MIGRATION_REVISION


def test_customer_data_quality_migration_has_expected_parent():
    script = ScriptDirectory.from_config(
        Config("alembic.ini")
    )

    migration = script.get_revision(
        MIGRATION_REVISION
    )

    assert migration is not None
    assert migration.down_revision == PARENT_REVISION
