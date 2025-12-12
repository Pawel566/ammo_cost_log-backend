"""add group_cm and final_score to shooting_sessions

Revision ID: add_group_cm_final_score
Revises: 6e6f8a7821cf
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_group_cm_final_score'
down_revision: Union[str, None] = '6e6f8a7821cf'
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
    # Dodaj group_cm tylko jeśli nie istnieje
    if not _column_exists('shooting_sessions', 'group_cm'):
        op.add_column('shooting_sessions', sa.Column('group_cm', sa.Float(), nullable=True))
    
    # Dodaj final_score tylko jeśli nie istnieje
    if not _column_exists('shooting_sessions', 'final_score'):
        op.add_column('shooting_sessions', sa.Column('final_score', sa.Float(), nullable=True))


def downgrade() -> None:
    # Usuń kolumny jeśli istnieją
    if _column_exists('shooting_sessions', 'final_score'):
        op.drop_column('shooting_sessions', 'final_score')
    
    if _column_exists('shooting_sessions', 'group_cm'):
        op.drop_column('shooting_sessions', 'group_cm')

