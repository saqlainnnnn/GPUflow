from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


REPO_ROOT = Path(__file__).resolve().parents[4]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

MIGRATION_REVISION = "7e1c4a9b2d33"
PARENT_REVISION = "5d7a9e4c2b11"


def test_customer_identity_timestamp_fix_migration_exists():
    script = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    )

    migration = script.get_revision(MIGRATION_REVISION)

    assert migration is not None


def test_customer_identity_timestamp_fix_migration_is_head():
    script = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    )

    assert MIGRATION_REVISION in script.get_heads()


def test_customer_identity_timestamp_fix_migration_has_expected_parent():
    script = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    )

    migration = script.get_revision(MIGRATION_REVISION)

    assert migration is not None
    assert migration.down_revision == PARENT_REVISION
