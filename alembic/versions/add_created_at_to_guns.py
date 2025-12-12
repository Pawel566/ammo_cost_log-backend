"""add created_at to guns

Revision ID: add_created_at_to_guns
Revises: add_group_cm_final_score
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_created_at_to_guns'
down_revision: Union[str, None] = 'add_ammo_category'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Sprawdza czy kolumna istnieje w tabeli"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Dodaj created_at tylko jeśli nie istnieje
    if not _column_exists('guns', 'created_at'):
        # Dodaj kolumnę jako nullable (SQLite nie obsługuje ALTER COLUMN dla NOT NULL)
        op.add_column('guns', sa.Column('created_at', sa.Date(), nullable=True))
        # Dla istniejących rekordów ustaw datę na dzisiaj (działa dla SQLite i PostgreSQL)
        bind = op.get_bind()
        if bind.dialect.name == 'sqlite':
            op.execute("UPDATE guns SET created_at = date('now') WHERE created_at IS NULL")
        else:
            op.execute("UPDATE guns SET created_at = CURRENT_DATE WHERE created_at IS NULL")
            # W PostgreSQL możemy zmienić na NOT NULL
            op.alter_column('guns', 'created_at', nullable=False)


def downgrade() -> None:
    # Usuń kolumnę jeśli istnieje
    if _column_exists('guns', 'created_at'):
        op.drop_column('guns', 'created_at')

