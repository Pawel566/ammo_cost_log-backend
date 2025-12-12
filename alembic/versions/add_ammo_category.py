"""Add category field to ammo table

Revision ID: add_ammo_category
Revises: add_group_cm_final_score
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_ammo_category'
down_revision: Union[str, None] = 'add_group_cm_final_score'
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
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Dla PostgreSQL - utworzenie enumu
    if is_postgres:
        # Sprawdź czy enum już istnieje
        conn = bind.connect()
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'ammo_category_enum'
            );
        """))
        enum_exists = result.scalar()
        conn.close()
        
        if not enum_exists:
            # Utwórz enum
            ammo_category_enum = postgresql.ENUM(
                'pistol', 'revolver', 'rifle', 'shotgun', 'other',
                name='ammo_category_enum',
                create_type=True
            )
            ammo_category_enum.create(bind, checkfirst=True)
    
    # Dodaj kolumnę category tylko jeśli nie istnieje
    if not _column_exists('ammo', 'category'):
        if is_postgres:
            # PostgreSQL - użyj enumu
            op.add_column('ammo', sa.Column('category', postgresql.ENUM(
                'pistol', 'revolver', 'rifle', 'shotgun', 'other',
                name='ammo_category_enum',
                create_type=False  # enum już utworzony
            ), nullable=True))
        else:
            # SQLite - użyj VARCHAR (SQLite nie ma enumów)
            op.add_column('ammo', sa.Column('category', sa.String(length=20), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'
    
    # Usuń kolumnę jeśli istnieje
    if _column_exists('ammo', 'category'):
        op.drop_column('ammo', 'category')
    
    # Dla PostgreSQL - usuń enum (tylko jeśli nie jest używany)
    if is_postgres:
        conn = bind.connect()
        result = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'ammo_category_enum'
            );
        """))
        enum_exists = result.scalar()
        conn.close()
        
        if enum_exists:
            # Sprawdź czy enum jest używany przez inne tabele
            conn = bind.connect()
            result = conn.execute(sa.text("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE udt_name = 'ammo_category_enum';
            """))
            usage_count = result.scalar()
            conn.close()
            
            if usage_count == 0:
                op.execute(sa.text("DROP TYPE IF EXISTS ammo_category_enum"))

