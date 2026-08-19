from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.pool import StaticPool

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.customer_identity import CustomerIdentity


REPO_ROOT = Path(__file__).resolve().parents[4]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

MIGRATION_REVISION = "5d7a9e4c2b11"
PARENT_REVISION = "184e24945722"


def test_customer_identity_migration_exists():
    script = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    )

    migration = script.get_revision(MIGRATION_REVISION)

    assert migration is not None
    assert migration.revision == MIGRATION_REVISION


def test_customer_identity_migration_declares_expected_parent():
    script = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    )

    migration = script.get_revision(MIGRATION_REVISION)

    assert migration is not None
    assert migration.down_revision == PARENT_REVISION


def test_customer_identity_table_shape():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    try:
        metadata = MetaData()

        Customer.__table__.to_metadata(metadata)
        CustomerIdentity.__table__.to_metadata(metadata)

        metadata.create_all(engine)

        inspector = inspect(engine)

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "customer_identities"
            )
        }

        assert columns == {
            "id",
            "customer_id",
            "source",
            "entity_type",
            "external_id",
            "created_at",
            "updated_at",
        }

        unique_constraints = inspector.get_unique_constraints(
            "customer_identities"
        )

        unique_column_sets = {
            tuple(sorted(constraint["column_names"]))
            for constraint in unique_constraints
        }

        assert (
            ("entity_type", "external_id", "source")
            in unique_column_sets
        )

        assert (
            ("customer_id", "entity_type", "source")
            in unique_column_sets
        )
    finally:
        engine.dispose()
